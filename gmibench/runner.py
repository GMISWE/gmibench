"""Run tasks against models: streaming calls, retries, tool loop, resume-safe raw results."""

from __future__ import annotations

import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .client import FakeRateLimitError, FakeTransientError
from .config import ModelSpec
from .kinds import kind_of
from .suites import Suite

_PRINT_LOCK = threading.Lock()


def log(msg: str) -> None:
    """Thread-safe print."""
    with _PRINT_LOCK:
        print(msg, flush=True)


# --------------------------------------------------------------------------- settings / errors


@dataclass
class RunSettings:
    """Run parameters: the standard's `protocol`, then `settings.yaml` -> run, then CLI overrides."""

    runs_per_task: int = 3
    temperature: float = 0.0
    seed: int | None = 1234
    concurrency_per_model: int = 4
    max_api_retries: int = 3
    max_rate_limit_waits: int = 20
    request_timeout_s: float = 300.0
    max_tool_turns: int = 6
    coding_timeout_s: float = 10.0
    backoff_base_s: float = 2.0
    retry_errors: bool = False
    circuit_breaker_errors: int = 8
    dry_run: bool = False
    manifest_id: str | None = None
    rerun: bool = False

    @classmethod
    def from_config(cls, cfg: dict[str, Any], *more: dict[str, Any], **overrides: Any) -> "RunSettings":
        known = set(cls.__dataclass_fields__)
        vals = {k: v for k, v in (cfg or {}).items() if k in known}
        for extra in more:
            vals.update({k: v for k, v in (extra or {}).items() if k in known})
        vals.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**vals)


class EmptyStreamError(Exception):
    """The server closed the stream without sending a single chunk."""


class APICallFailed(Exception):
    """A request failed after all retries."""

    def __init__(self, message: str, retries: int, rate_limit_waits: int) -> None:
        super().__init__(message)
        self.retries = retries
        self.rate_limit_waits = rate_limit_waits


def _status_code(exc: Exception) -> int | None:
    code = getattr(exc, "status_code", None)
    if code is None and getattr(exc, "response", None) is not None:
        code = getattr(exc.response, "status_code", None)
    return code


def retry_after_seconds(exc: Exception) -> float | None:
    """Read `Retry-After` (seconds or HTTP date) from a 429 error, if present."""
    if isinstance(exc, FakeRateLimitError):
        return exc.retry_after
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) or {}
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        from email.utils import parsedate_to_datetime
        try:
            return max(0.0, (parsedate_to_datetime(raw) - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError):
            return None


def classify_error(exc: Exception) -> str:
    """Return 'rate_limit', 'retryable', 'bad_request' or 'fatal'."""
    if isinstance(exc, FakeRateLimitError):
        return "rate_limit"
    if isinstance(exc, (FakeTransientError, EmptyStreamError)):
        return "retryable"
    name = type(exc).__name__
    code = _status_code(exc)
    if code == 429 or name == "RateLimitError":
        # GMI answers 429 "No available endpoints" when a model has no capacity at all.
        # That is an outage, not throttling: retry with normal backoff.
        if "no available endpoints" in str(exc).lower():
            return "retryable"
        return "rate_limit"
    if name == "APIError":
        # Error event in the middle of a stream (no HTTP status). Usually a backend 5xx.
        return "retryable"
    if name in ("APIConnectionError", "APITimeoutError", "InternalServerError", "ConnectError",
                "ReadTimeout", "RemoteProtocolError", "ReadError", "TimeoutException"):
        return "retryable"
    if code is not None and (code >= 500 or code in (408, 409)):
        return "retryable"
    if code == 400:
        return "bad_request"
    return "fatal"


# --------------------------------------------------------------------------- one streamed call


@dataclass
class CallResult:
    """Everything recorded from one streamed completion."""

    content: str = ""
    reasoning: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    ttft_s: float | None = None
    ttft_content_s: float | None = None
    latency_s: float = 0.0
    gen_time_s: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    reasoning_tokens: int | None = None
    finish_reason: str | None = None
    streamed: bool = True


def stream_once(client: Any, model_id: str, messages: list[dict[str, Any]], max_tokens: int,
                settings: RunSettings, tools: list[dict[str, Any]] | None, quirks: dict[str, bool],
                force_non_stream: bool = False) -> CallResult:
    """One streamed chat completion. Raises SDK exceptions unchanged."""
    kwargs: dict[str, Any] = {
        "model": model_id, "messages": messages, "max_tokens": max_tokens,
        "temperature": settings.temperature, "stream": True,
    }
    if not quirks.get("no_stream_usage"):
        kwargs["stream_options"] = {"include_usage": True}
    if settings.seed is not None and not quirks.get("no_seed"):
        kwargs["seed"] = settings.seed
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if force_non_stream or (tools and quirks.get("no_stream_tools")):
        return _non_streamed(client, kwargs)
    res = CallResult()
    calls: dict[int, dict[str, Any]] = {}
    t0 = time.perf_counter()
    stream = client.chat.completions.create(**kwargs)
    n_chunks = 0
    for chunk in stream:
        n_chunks += 1
        now = time.perf_counter() - t0
        usage = getattr(chunk, "usage", None)
        if usage is not None:
            res.prompt_tokens = getattr(usage, "prompt_tokens", None)
            res.completion_tokens = getattr(usage, "completion_tokens", None)
            details = getattr(usage, "completion_tokens_details", None)
            res.reasoning_tokens = getattr(details, "reasoning_tokens", None) if details else None
        for choice in getattr(chunk, "choices", None) or []:
            delta = choice.delta
            if choice.finish_reason:
                res.finish_reason = choice.finish_reason
            if delta is None:
                continue
            reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
            content = getattr(delta, "content", None)
            tcs = getattr(delta, "tool_calls", None)
            if (reasoning or content or tcs) and res.ttft_s is None:
                res.ttft_s = now
            if (content or tcs) and res.ttft_content_s is None:
                res.ttft_content_s = now
            if reasoning:
                res.reasoning += reasoning
            if content:
                res.content += content
            for tc in tcs or []:
                slot = calls.setdefault(tc.index if tc.index is not None else len(calls),
                                        {"id": None, "name": "", "arguments": ""})
                if getattr(tc, "id", None):
                    slot["id"] = tc.id
                fn = getattr(tc, "function", None)
                if fn is not None:
                    if getattr(fn, "name", None):
                        slot["name"] += fn.name
                    if getattr(fn, "arguments", None):
                        slot["arguments"] += fn.arguments
    if n_chunks == 0:
        raise EmptyStreamError("stream closed with no chunks")
    res.latency_s = time.perf_counter() - t0
    res.gen_time_s = res.latency_s - (res.ttft_s if res.ttft_s is not None else res.latency_s)
    res.tool_calls = [calls[k] for k in sorted(calls)]
    return res


def _non_streamed(client: Any, kwargs: dict[str, Any]) -> CallResult:
    """Fallback for endpoints that return an empty stream when tools are given.

    TTFT and generation time cannot be measured, so they stay None.
    """
    kwargs = {k: v for k, v in kwargs.items() if k not in ("stream", "stream_options")}
    t0 = time.perf_counter()
    resp = client.chat.completions.create(**kwargs)
    res = CallResult(streamed=False, latency_s=time.perf_counter() - t0)
    res.gen_time_s = None  # type: ignore[assignment]
    choice = resp.choices[0]
    msg = choice.message
    res.content = msg.content or ""
    extra = getattr(msg, "model_extra", None) or {}
    res.reasoning = getattr(msg, "reasoning_content", None) or extra.get("reasoning_content") \
        or extra.get("reasoning") or ""
    res.tool_calls = [{"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments or ""}
                      for tc in (msg.tool_calls or [])]
    res.finish_reason = choice.finish_reason
    usage = getattr(resp, "usage", None)
    if usage is not None:
        res.prompt_tokens = usage.prompt_tokens
        res.completion_tokens = usage.completion_tokens
        details = getattr(usage, "completion_tokens_details", None)
        res.reasoning_tokens = getattr(details, "reasoning_tokens", None) if details else None
    return res


def call_with_retries(client: Any, model_id: str, messages: list[dict[str, Any]], max_tokens: int,
                      settings: RunSettings, tools: list[dict[str, Any]] | None,
                      quirks: dict[str, bool], sleep: Callable[[float], None] = time.sleep,
                      ) -> tuple[CallResult, int, int]:
    """Call with retries. Returns (result, retries, rate_limit_waits).

    API errors (5xx, timeouts, connection errors) are retried up to `max_api_retries`
    times with exponential backoff and jitter. A 429 waits for `Retry-After` (or backoff)
    and does not use up a retry, but is capped by `max_rate_limit_waits`.
    A 400 that names an unsupported parameter (seed, stream_options, reasoning_content)
    switches that quirk for the model and tries again for free.
    """
    retries = waits = 0
    non_stream = False
    while True:
        try:
            return (stream_once(client, model_id, messages, max_tokens, settings, tools, quirks, non_stream),
                    retries, waits)
        except Exception as exc:  # noqa: BLE001 - classify everything the SDK can raise
            kind = classify_error(exc)
            msg = f"{type(exc).__name__}: {str(exc)[:300]}"
            if type(exc).__name__ == "APIError" and not non_stream and retries < settings.max_api_retries:
                # The stream died with an in-stream error. Some GMI endpoints fail every time on
                # certain inputs when streaming but work without it: retry once unstreamed.
                retries += 1
                non_stream = True
                continue
            if isinstance(exc, EmptyStreamError) and tools and not quirks.get("no_stream_tools"):
                quirks["no_stream_tools"] = True   # switch this model to non-streamed tool calls
                continue
            if kind == "bad_request":
                text = str(exc).lower()
                if "seed" in text and not quirks.get("no_seed"):
                    quirks["no_seed"] = True
                    continue
                if "stream_options" in text and not quirks.get("no_stream_usage"):
                    quirks["no_stream_usage"] = True
                    continue
                if "reasoning_content" in text and any(
                    m.get("role") == "assistant" and "reasoning_content" not in m for m in messages
                ):
                    # Another run may already have learned the quirk, but this
                    # conversation still needs its earlier assistant turns repaired.
                    quirks["send_reasoning"] = True
                    raise _ResendWithReasoning() from exc
                raise APICallFailed(msg, retries, waits) from exc
            if kind == "rate_limit":
                waits += 1
                if waits > settings.max_rate_limit_waits:
                    raise APICallFailed(msg, retries, waits) from exc
                wait = retry_after_seconds(exc)
                sleep(wait if wait is not None else min(60.0, settings.backoff_base_s * 2 ** min(waits, 5)))
                continue
            if kind == "retryable" and retries < settings.max_api_retries:
                retries += 1
                sleep(settings.backoff_base_s * 2 ** (retries - 1) + random.uniform(0, 0.5))
                continue
            raise APICallFailed(msg, retries, waits) from exc


class _ResendWithReasoning(Exception):
    """Internal: the server wants `reasoning_content` echoed back on assistant turns."""


# --------------------------------------------------------------------------- one task run


def _base_record(model: ModelSpec, model_id: str, suite: Suite, task: dict[str, Any], run: int,
                 settings: RunSettings) -> dict[str, Any]:
    return {
        "model": model.name, "model_id": model_id, "task_set": suite.name, "task_id": task["id"],
        "category": task.get("category"), "run": run, "dry_run": settings.dry_run,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # What produced this result: lets old results be told apart from new ones.
        "task_hash": task.get("hash"), "suite_version": suite.version, "kind": suite.kind,
        "price_in_per_m": model.input_price_per_m, "price_out_per_m": model.output_price_per_m,
        "manifest_id": settings.manifest_id,
    }


def _fill_usage(rec: dict[str, Any], results: list[CallResult], messages_chars: int) -> None:
    pt = [r.prompt_tokens for r in results]
    ct = [r.completion_tokens for r in results]
    rt = [r.reasoning_tokens for r in results]
    rec["usage_estimated"] = any(x is None for x in pt + ct)
    rec["prompt_tokens"] = sum(x if x is not None else messages_chars // 4 for x in pt)
    rec["completion_tokens"] = sum(
        c if c is not None else (len(r.content) + len(r.reasoning)) // 4 for c, r in zip(ct, results))
    rec["reasoning_tokens"] = sum(x for x in rt if x is not None) if any(x is not None for x in rt) else None


def run_single(client: Any, model: ModelSpec, model_id: str, suite: Suite, task: dict[str, Any], run: int,
               settings: RunSettings, quirks: dict[str, bool]) -> dict[str, Any]:
    """Run one task once and return its raw record (never raises for API errors)."""
    rec = _base_record(model, model_id, suite, task, run, settings)
    kind = kind_of(suite)
    messages = kind.messages(task, suite)
    env = kind.environment(task, suite)  # fresh tool state per run, or None
    tools: list[dict[str, Any]] | None = env.schemas if env is not None else None
    results: list[CallResult] = []
    retries = waits = 0
    made_calls: list[dict[str, Any]] = []
    final = ""
    try:
        for turn in range(task.get("max_turns", settings.max_tool_turns) if tools else 1):
            try:
                res, r, w = call_with_retries(client, model_id, messages, task["max_tokens"], settings, tools, quirks)
            except _ResendWithReasoning:
                messages = _with_reasoning(messages, results)
                res, r, w = call_with_retries(client, model_id, messages, task["max_tokens"], settings, tools, quirks)
            retries += r
            waits += w
            results.append(res)
            final = res.content
            if not tools or not res.tool_calls:
                break
            assistant: dict[str, Any] = {"role": "assistant", "content": res.content or None, "tool_calls": []}
            if quirks.get("send_reasoning"):
                assistant["reasoning_content"] = res.reasoning
            for i, tc in enumerate(res.tool_calls):
                tc_id = tc["id"] or f"call_{turn}_{i}"
                assistant["tool_calls"].append({"id": tc_id, "type": "function",
                                                "function": {"name": tc["name"], "arguments": tc["arguments"] or "{}"}})
                made_calls.append({"name": tc["name"], "arguments": tc["arguments"]})
            messages = messages + [assistant] + [
                {"role": "tool", "tool_call_id": a["id"], "content": env.execute(a["function"]["name"],
                                                                                  a["function"]["arguments"])}
                for a in assistant["tool_calls"]]
        rec["error"] = None
    except APICallFailed as exc:
        rec["error"] = str(exc)
        retries += exc.retries
        waits += exc.rate_limit_waits

    rec.update({
        "retries": retries, "rate_limit_waits": waits, "turns": len(results),
        "tool_call_count": len(made_calls), "tool_calls": made_calls,
        "ttft_s": results[0].ttft_s if results else None,
        "ttft_content_s": results[0].ttft_content_s if results else None,
        "latency_s": round(sum(r.latency_s for r in results), 4) if results else None,
        "gen_time_s": (round(sum(r.gen_time_s for r in results), 4)
                       if results and all(r.gen_time_s is not None for r in results) else None),
        "streamed": all(r.streamed for r in results) if results else None,
        "finish_reason": results[-1].finish_reason if results else None,
        "response": final, "reasoning_chars": sum(len(r.reasoning) for r in results),
    })
    _fill_usage(rec, results, len(json.dumps(messages)))

    if rec["error"]:
        rec["passed"], rec["check"] = False, {"reason": "api_error"}
    else:
        rec["passed"], rec["check"] = kind.check(task, suite, final, made_calls, settings.coding_timeout_s)
    return rec


def _with_reasoning(messages: list[dict[str, Any]], results: list[CallResult]) -> list[dict[str, Any]]:
    """Add the recorded reasoning to earlier assistant turns (in order)."""
    out, i = [], 0
    for m in messages:
        if m.get("role") == "assistant" and i < len(results):
            m = dict(m, reasoning_content=results[i].reasoning or "")
            i += 1
        out.append(m)
    return out


# --------------------------------------------------------------------------- results store / resume


class ResultStore:
    """Append-only JSONL per model and task set. The last record for a (task, run) wins."""

    def __init__(self, results_dir: Path) -> None:
        self.raw_dir = results_dir / "raw"
        self._lock = threading.Lock()

    def path(self, model: ModelSpec, task_set: str) -> Path:
        return self.raw_dir / model.slug / f"{task_set}.jsonl"

    def load(self, model: ModelSpec, task_set: str) -> dict[tuple[str, int], dict[str, Any]]:
        """Read existing records. Ignores a truncated last line from a crash."""
        p = self.path(model, task_set)
        out: dict[tuple[str, int], dict[str, Any]] = {}
        if not p.exists():
            return out
        text = p.read_text()
        if text and not text.endswith("\n"):
            # A crash left a partial last line. End it so the next append starts clean.
            with self._lock, p.open("a") as fh:
                fh.write("\n")
        for line in text.splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[(rec["task_id"], int(rec["run"]))] = rec
        return out

    def append(self, model: ModelSpec, task_set: str, rec: dict[str, Any]) -> None:
        p = self.path(model, task_set)
        with self._lock:
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()


def is_current(rec: dict[str, Any] | None, task: dict[str, Any]) -> bool:
    """True if a record was made with the current version of the task."""
    return rec is not None and (task.get("hash") is None or rec.get("task_hash") == task.get("hash"))


def pending_jobs(tasks: list[dict[str, Any]], done: dict[tuple[str, int], dict[str, Any]], runs: int,
                 retry_errors: bool, rerun: bool = False) -> list[tuple[dict[str, Any], int]]:
    """(task, run) pairs that still need to run: missing, made with an older task, or (opt-in) API errors.

    `rerun` re-measures everything (a new time window); the new record supersedes the old one,
    which stays in the file for audit.
    """
    jobs = []
    for run in range(runs):
        for t in tasks:
            prev = done.get((t["id"], run))
            if rerun or not is_current(prev, t) or (retry_errors and prev.get("error")):
                jobs.append((t, run))
    return jobs


def run_model(client: Any, model: ModelSpec, model_id: str, suites: list[Suite], settings: RunSettings,
              store: ResultStore) -> dict[str, int]:
    """Run every applicable suite for one model with `concurrency_per_model` workers."""
    quirks: dict[str, bool] = {}
    counts = {"done": 0, "passed": 0, "errors": 0, "skipped": 0, "not_run": 0}
    breaker = {"streak": 0, "open": False}
    breaker_lock = threading.Lock()

    def job(suite: Suite, t: dict[str, Any], r: int) -> dict[str, Any] | None:
        if breaker["open"]:
            return None  # endpoint looks down: leave unrecorded so a later run resumes it
        rec = run_single(client, model, model_id, suite, t, r, settings, quirks)
        with breaker_lock:
            breaker["streak"] = breaker["streak"] + 1 if rec.get("error") else 0
            if breaker["streak"] >= settings.circuit_breaker_errors and not breaker["open"]:
                breaker["open"] = True
                log(f"[{model.name}] {breaker['streak']} runs in a row failed with API errors. "
                    "Stopping this model; re-run later with --retry-errors to resume.")
        return rec

    for suite in suites:
        ts = suite.name
        if breaker["open"]:
            break
        if not model.applies_to(suite):
            log(f"[{model.name}] {ts}: n/a (model is not vision-capable)")
            continue
        tasks = suite.load_tasks()
        done = store.load(model, ts)
        jobs = pending_jobs(tasks, done, settings.runs_per_task, settings.retry_errors, settings.rerun)
        total = len(tasks) * settings.runs_per_task
        counts["skipped"] += total - len(jobs)
        if not jobs:
            log(f"[{model.name}] {ts}: all {total} runs already recorded, skipping")
            continue
        log(f"[{model.name}] {ts}: {len(jobs)} runs to do ({total - len(jobs)} already recorded)")
        n = 0
        with ThreadPoolExecutor(max_workers=settings.concurrency_per_model) as pool:
            futs = {pool.submit(job, suite, t, r): (t, r) for t, r in jobs}
            for fut in as_completed(futs):
                t, r = futs[fut]
                try:
                    rec = fut.result()
                    if rec is None:
                        counts["not_run"] += 1
                        continue
                except Exception as exc:  # noqa: BLE001 - keep the run going, record the crash
                    rec = _base_record(model, model_id, suite, t, r, settings)
                    rec.update({"passed": False, "error": f"harness: {type(exc).__name__}: {exc}",
                                "check": {"reason": "harness_error"}, "retries": 0, "rate_limit_waits": 0})
                store.append(model, ts, rec)
                n += 1
                counts["done"] += 1
                counts["passed"] += bool(rec.get("passed"))
                counts["errors"] += bool(rec.get("error"))
                if rec.get("error"):
                    log(f"[{model.name}] {ts} {t['id']} run {r}: ERROR {rec['error'][:160]}")
                if n % 10 == 0 or n == len(jobs):
                    log(f"[{model.name}] {ts}: {n}/{len(jobs)}")
    return counts


def run_all(client: Any, models: list[ModelSpec], resolved: dict[str, str], suites: list[Suite],
            settings: RunSettings, results_dir: Path) -> dict[str, dict[str, int]]:
    """Run all models in parallel (each with its own worker pool)."""
    store = ResultStore(results_dir)
    out: dict[str, dict[str, int]] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(models))) as pool:
        futs = {pool.submit(run_model, client, m, resolved[m.name], suites, settings, store): m
                for m in models}
        for fut in as_completed(futs):
            m = futs[fut]
            out[m.name] = fut.result()
            c = out[m.name]
            log(f"[{m.name}] finished: {c['done']} new runs, {c['passed']} passed, {c['errors']} errors, "
                f"{c['skipped']} resumed" + (f", {c['not_run']} not run (endpoint down)" if c["not_run"] else ""))
    return out
