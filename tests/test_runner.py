"""Runner tests: retries, 429 handling, resume and the dry-run pipeline."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from gmibench.client import FakeClient, FakeRateLimitError, FakeTransientError
from gmibench.config import ModelSpec
from gmibench.runner import (APICallFailed, ResultStore, RunSettings, call_with_retries, classify_error,
                             pending_jobs, retry_after_seconds, run_all, run_single)
from gmibench.scoring import score_all


class _ScriptedClient:
    """Raises the scripted exceptions in order, then streams 'ok'."""

    def __init__(self, errors):
        self.errors = list(errors)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.calls.append(kw)
        if self.errors:
            raise self.errors.pop(0)
        return iter([
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ok", tool_calls=None),
                                                     finish_reason="stop")], usage=None),
            SimpleNamespace(choices=[], usage=SimpleNamespace(prompt_tokens=3, completion_tokens=1,
                                                              completion_tokens_details=None)),
        ])


class _BadRequest(Exception):
    status_code = 400


def _settings(**kw):
    return RunSettings(backoff_base_s=0.0, **kw)


def test_transient_errors_retried_then_succeed():
    c = _ScriptedClient([FakeTransientError("503"), FakeTransientError("503")])
    sleeps = []
    res, retries, waits = call_with_retries(c, "m", [], 10, _settings(), None, {}, sleep=sleeps.append)
    assert res.content == "ok" and retries == 2 and waits == 0 and len(sleeps) == 2
    assert res.prompt_tokens == 3 and res.completion_tokens == 1 and res.ttft_s is not None


def test_retries_capped_at_three():
    c = _ScriptedClient([FakeTransientError("503")] * 4)
    with pytest.raises(APICallFailed) as exc:
        call_with_retries(c, "m", [], 10, _settings(max_api_retries=3), None, {}, sleep=lambda s: None)
    assert exc.value.retries == 3


def test_rate_limit_waits_retry_after_and_is_not_a_retry():
    c = _ScriptedClient([FakeRateLimitError(7.5)])
    sleeps = []
    _, retries, waits = call_with_retries(c, "m", [], 10, _settings(), None, {}, sleep=sleeps.append)
    assert sleeps == [7.5] and retries == 0 and waits == 1


def test_retry_after_header_parsing():
    exc = Exception()
    exc.response = SimpleNamespace(headers={"retry-after": "12"}, status_code=429)
    assert retry_after_seconds(exc) == 12.0
    assert classify_error(exc) == "rate_limit"


def test_seed_rejected_drops_seed():
    c = _ScriptedClient([_BadRequest("Unsupported parameter: seed")])
    quirks = {}
    call_with_retries(c, "m", [], 10, _settings(seed=1), None, quirks, sleep=lambda s: None)
    assert quirks["no_seed"] and "seed" in c.calls[0] and "seed" not in c.calls[1]


def test_other_bad_request_fails_fast():
    c = _ScriptedClient([_BadRequest("model does not support images")])
    with pytest.raises(APICallFailed):
        call_with_retries(c, "m", [], 10, _settings(), None, {}, sleep=lambda s: None)
    assert len(c.calls) == 1


def test_pending_jobs_resume():
    tasks = [{"id": "a"}, {"id": "b"}]
    done = {("a", 0): {"error": None}, ("b", 0): {"error": "boom"}}
    assert [(t["id"], r) for t, r in pending_jobs(tasks, done, 2, retry_errors=False)] == [("a", 1), ("b", 1)]
    assert ("b", 0) in [(t["id"], r) for t, r in pending_jobs(tasks, done, 2, retry_errors=True)]


def test_dry_run_end_to_end_and_resume(tmp_path, thresholds, suites):
    models = [
        ModelSpec(name="fake-vision", id="lab/fake-vision", total_params_b=30, active_params_b=3,
                  license="mit", context_length=200000, precision="FP8", input_price_per_m=0.1,
                  output_price_per_m=0.5, vision=True, weights_url="https://x"),
        ModelSpec(name="fake-text", id="lab/fake-text", total_params_b=120, active_params_b=5,
                  license="apache-2.0", context_length=131072, precision="BF16", input_price_per_m=0.05,
                  output_price_per_m=0.25, vision=False, weights_url="https://x"),
    ]
    client = FakeClient(models)
    settings = RunSettings(runs_per_task=2, backoff_base_s=0.0, dry_run=True)
    resolved = {m.name: m.id for m in models}
    sets = [suites[n] for n in ("coding", "tool_use", "documents")]
    first = run_all(client, models, resolved, sets, settings, tmp_path)
    assert first["fake-vision"]["done"] == 120 and first["fake-text"]["done"] == 80

    # Resume: nothing left to do.
    again = run_all(client, models, resolved, sets, settings, tmp_path)
    assert again["fake-vision"]["done"] == 0 and again["fake-vision"]["skipped"] == 120

    cards = score_all(models, tmp_path, sets, 2, thresholds)
    by = {c["name"]: c for c in cards}
    assert by["fake-text"]["sets"]["documents"]["status"] == "n/a"
    assert by["fake-vision"]["overall"]["completed_all"]
    assert 0 < by["fake-vision"]["overall"]["pass_rate"] <= 100
    store = ResultStore(tmp_path)
    assert len(store.load(models[0], "documents")) == 40


class _EmptyStreamClient:
    """Returns an empty stream when tools are given (like a buggy endpoint), works without streaming."""

    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.calls.append(kw)
        if kw.get("stream"):
            return iter([])
        msg = SimpleNamespace(content=None, model_extra={}, tool_calls=[SimpleNamespace(
            id="c1", function=SimpleNamespace(name="get_weather", arguments='{"city": "Paris"}'))])
        return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="tool_calls")],
                               usage=SimpleNamespace(prompt_tokens=50, completion_tokens=10,
                                                     completion_tokens_details=None))


def test_empty_stream_with_tools_falls_back_to_non_streaming():
    c = _EmptyStreamClient()
    quirks = {}
    res, retries, _ = call_with_retries(c, "m", [], 10, _settings(), [{"type": "function"}], quirks,
                                        sleep=lambda s: None)
    assert quirks["no_stream_tools"] and retries == 0
    assert res.tool_calls[0]["name"] == "get_weather" and not res.streamed and res.ttft_s is None
    assert "stream" not in c.calls[-1]


def test_empty_stream_without_tools_is_retried():
    c = _EmptyStreamClient()
    with pytest.raises(APICallFailed) as exc:
        call_with_retries(c, "m", [], 10, _settings(max_api_retries=2), None, {}, sleep=lambda s: None)
    assert exc.value.retries == 2


def test_mid_stream_api_error_is_retryable():
    class APIError(Exception):
        pass
    assert classify_error(APIError("Internal server error")) == "retryable"


def test_no_available_endpoints_429_is_an_outage():
    exc = Exception("Error code: 429 - No available endpoints")
    exc.status_code = 429
    assert classify_error(exc) == "retryable"


def test_circuit_breaker_stops_dead_model(tmp_path, suites):
    class Dead:
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: (_ for _ in ()).throw(
            FakeTransientError("523"))))
    m = ModelSpec(name="dead", id="x/dead")
    settings = RunSettings(runs_per_task=1, backoff_base_s=0.0, max_api_retries=0, circuit_breaker_errors=3,
                           concurrency_per_model=1)
    out = run_all(Dead(), [m], {"dead": "x/dead"}, [suites["coding"], suites["tool_use"]], settings, tmp_path)
    assert out["dead"]["done"] == 3 and out["dead"]["errors"] == 3
    assert len(ResultStore(tmp_path).load(m, "coding")) == 3


def test_mid_stream_error_retries_without_streaming():
    class APIError(Exception):
        pass

    calls = []

    def create(**kw):
        calls.append(kw)
        if kw.get("stream"):
            def gen():
                raise APIError("Internal server error")
                yield  # noqa
            return gen()
        msg = SimpleNamespace(content="ok", model_extra={}, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")], usage=None)

    c = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    res, retries, _ = call_with_retries(c, "m", [], 10, _settings(), None, {}, sleep=lambda s: None)
    assert res.content == "ok" and not res.streamed and retries == 1
    assert calls[0].get("stream") and not calls[1].get("stream")


class _ReasoningClient:
    """Require echoed reasoning; hold B's rejection until A has repaired its history."""

    def __init__(self, task, *, parallel=False, reject_repaired=False, reasoning="Look up Paris"):
        self.task = task
        self.reject_repaired = reject_repaired
        self.reasoning = reasoning
        self.barrier = threading.Barrier(2, timeout=5) if parallel else None
        self.repaired = threading.Event()
        self.lock = threading.Lock()
        self.workers = {}
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        messages = kw["messages"]
        with self.lock:
            worker = self.workers.setdefault(threading.get_ident(), len(self.workers))
            self.calls.append((worker, messages))
        assistants = [m for m in messages if m["role"] == "assistant"]
        if not assistants:
            call = self.task["reference_calls"][0]
            tc = SimpleNamespace(index=0, id="c1", function=SimpleNamespace(
                name=call["name"], arguments=json.dumps(call["args"])))
            delta = SimpleNamespace(content=None, reasoning_content=self.reasoning, tool_calls=[tc])
            finish = "tool_calls"
        elif "reasoning_content" not in assistants[0]:
            if self.barrier:
                self.barrier.wait()
                if worker == 1:
                    assert self.repaired.wait(5), "A did not repair its conversation"
            raise _BadRequest("reasoning_content is required on assistant messages")
        else:
            assert assistants[0]["reasoning_content"] == self.reasoning
            self.repaired.set()
            if self.reject_repaired:
                raise _BadRequest("reasoning_content is still rejected")
            delta = SimpleNamespace(content=self.task["reference_answer"], tool_calls=None)
            finish = "stop"
        return iter([SimpleNamespace(choices=[SimpleNamespace(delta=delta, finish_reason=finish)], usage=None)])


@pytest.mark.parametrize("reject_repaired", [False, True])
def test_parallel_runs_repair_their_own_reasoning(model, suites, reject_repaired):
    suite = suites["tool_use"]
    task = next(t for t in suite.load_tasks() if t["id"] == "tool-01")
    client = _ReasoningClient(task, parallel=True, reject_repaired=reject_repaired)
    quirks = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_single, client, model, model.id, suite, task, r, _settings(), quirks)
                   for r in range(2)]
        records = [f.result(timeout=10) for f in futures]
    assert quirks["send_reasoning"]
    assert len(client.calls) == 6  # initial, missing reasoning, repaired: once per worker
    assert all(r["tool_call_count"] == 1 for r in records)
    if reject_repaired:
        assert all(r["error"] and not r["passed"] for r in records)
    else:
        assert all(r["error"] is None and r["passed"] for r in records)


@pytest.mark.parametrize("reasoning", ["Look up Paris", ""])
@pytest.mark.parametrize("reject_repaired", [False, True])
def test_single_run_reasoning_repair_terminates(model, suites, reasoning, reject_repaired):
    suite = suites["tool_use"]
    task = next(t for t in suite.load_tasks() if t["id"] == "tool-01")
    client = _ReasoningClient(task, reasoning=reasoning, reject_repaired=reject_repaired)
    rec = run_single(client, model, model.id, suite, task, 0, _settings(), {})
    assert len(client.calls) == 3
    assert rec["passed"] is not reject_repaired
    assert bool(rec["error"]) is reject_repaired


def test_known_reasoning_quirk_echoes_empty_reasoning(model, suites):
    suite = suites["tool_use"]
    task = next(t for t in suite.load_tasks() if t["id"] == "tool-01")
    client = _ReasoningClient(task, reasoning="")
    rec = run_single(client, model, model.id, suite, task, 0, _settings(), {"send_reasoning": True})
    assert rec["passed"] and rec["error"] is None
    assert len(client.calls) == 2
