"""API client creation, model-ID resolution, and the fake client used by `--dry-run`."""

from __future__ import annotations

import base64
import difflib
import hashlib
import json
import os
import threading
import time
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

from .config import TASK_SETS, TASKS_DIR, ModelSpec, base_kind

DEFAULT_BASE_URL = "https://api.gmi-serving.com/v1/"


def make_client(timeout_s: float = 300.0) -> Any:
    """Create the real OpenAI-compatible client for GMI Cloud.

    Retries are handled by the runner, so the SDK's own retries are disabled.
    """
    from openai import OpenAI

    key = os.environ.get("GMI_API_KEY")
    if not key:
        raise SystemExit("GMI_API_KEY is not set. Put it in .env or export it.")
    base_url = os.environ.get("GMI_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(base_url=base_url, api_key=key, max_retries=0, timeout=timeout_s)


def resolve_models(client: Any, models: list[ModelSpec]) -> dict[str, str]:
    """Check every configured model ID against `GET /v1/models`.

    Returns a map of model name -> exact served ID. Exits with a clear message
    if any ID is missing. A case-only difference is accepted and reported.
    """
    served = [m.id for m in client.models.list().data]
    by_lower = {s.lower(): s for s in served}
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for m in models:
        if m.id in served:
            resolved[m.name] = m.id
        elif m.id.lower() in by_lower:
            resolved[m.name] = by_lower[m.id.lower()]
            print(f"NOTE: {m.name}: using served ID '{resolved[m.name]}' (case differs from models.yaml)")
        else:
            close = difflib.get_close_matches(m.id, served, n=3, cutoff=0.5)
            hint = f" Closest served IDs: {', '.join(close)}" if close else ""
            missing.append(f"  - {m.name}: '{m.id}' is not served.{hint}")
    if missing:
        raise SystemExit("Model IDs not found on GET /v1/models:\n" + "\n".join(missing)
                         + "\nFix models.yaml and run again.")
    return resolved


# --------------------------------------------------------------------------- fake client


class FakeTransientError(Exception):
    """Simulated 5xx / connection error (retryable)."""


class FakeRateLimitError(Exception):
    """Simulated HTTP 429 with a Retry-After value."""

    def __init__(self, retry_after: float) -> None:
        super().__init__("rate limited (fake)")
        self.retry_after = retry_after


def _h(*parts: Any) -> float:
    """Deterministic hash of the parts mapped to [0, 1)."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(digest[:12], 16) / float(16**12)


def _ns(**kw: Any) -> SimpleNamespace:
    return SimpleNamespace(**kw)


class _FakeCompletions:
    def __init__(self, parent: "FakeClient") -> None:
        self.parent = parent

    def create(self, **kwargs: Any) -> Iterator[SimpleNamespace]:
        return self.parent._create(**kwargs)


class FakeClient:
    """Offline stand-in for the OpenAI client.

    It knows the task files, so it can answer like a model: correctly most of the
    time, wrongly at a per-model rate, with simulated latency, streaming chunks,
    token usage, tool calls, transient errors and 429s.
    """

    def __init__(self, models: list[ModelSpec], tasks_dir: Path = TASKS_DIR, error_rate: float = 0.02) -> None:
        self.error_rate = error_rate
        self.chat = _ns(completions=_FakeCompletions(self))
        # Mirrors `client.models.list().data[i].id` of the real SDK.
        self.models = _ns(list=lambda: _ns(data=[_ns(id=m.id) for m in models]))
        self._by_prompt: dict[str, dict[str, Any]] = {}
        self._by_image: dict[str, dict[str, Any]] = {}
        self._counter: dict[tuple[str, str], int] = defaultdict(int)
        self._lock = threading.Lock()
        for ts in TASK_SETS:
            path = tasks_dir / f"{ts}.jsonl"
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                task = json.loads(line)
                task["_set"] = base_kind(ts)
                if base_kind(ts) == "documents":
                    data = base64.b64encode((tasks_dir / task["image"]).read_bytes()).decode()
                    self._by_image[data] = task
                else:
                    self._by_prompt[task["prompt"]] = task

    # -- helpers

    def _find_task(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg["content"]
            if isinstance(content, str) and content in self._by_prompt:
                return self._by_prompt[content]
            if isinstance(content, list):
                for part in content:
                    if part.get("type") == "image_url":
                        b64 = part["image_url"]["url"].split(",", 1)[1]
                        if b64 in self._by_image:
                            return self._by_image[b64]
        raise ValueError("fake client: unknown task")

    def _answer(self, model: str, task: dict[str, Any], messages: list[dict[str, Any]],
                fail: bool) -> tuple[str, list[dict[str, Any]]]:
        ts = task["_set"]
        if ts == "coding":
            code = task["reference_solution"]
            if fail:
                code = code.replace("return", "return None and", 1)
            return f"```python\n{code}```", []
        if ts == "documents":
            gt = dict(task["expected"])
            if fail:
                gt["total"] = round(gt["total"] + 1.0, 2)
            return "```json\n" + json.dumps(gt) + "\n```", []
        # tool use
        if not any(m.get("role") == "tool" for m in messages):
            calls = [{"name": c["name"], "arguments": json.dumps(c["args"])} for c in task["reference_calls"]]
            if fail and _h(model, task["id"], "skip") < 0.5:
                return "I think the answer is 42.", []
            return "", calls
        answer = task["reference_answer"]
        return ("I could not determine that." if fail else answer), []

    def _create(self, *, model: str, messages: list[dict[str, Any]], max_tokens: int = 512,
                stream: bool = False, **_: Any) -> Iterator[SimpleNamespace]:
        task = self._find_task(messages)
        first_turn = not any(m.get("role") == "assistant" for m in messages)
        with self._lock:
            if first_turn:
                self._counter[(model, task["id"])] += 1
            n = self._counter[(model, task["id"])]
            call_no = sum(self._counter.values())
        roll = _h(model, task["id"], n, len(messages), call_no)
        if roll < self.error_rate:
            raise FakeTransientError("simulated 503")
        if roll < self.error_rate * 1.5:
            raise FakeRateLimitError(retry_after=0.01)
        # Mostly task-level outcomes (real models are fairly consistent at temperature 0),
        # plus a little per-run noise so consistency is not always 100%.
        skill = 0.60 + 0.38 * _h(model, "skill")              # per-model pass probability
        set_bias = 0.15 * (_h(model, task["_set"]) - 0.5)
        fail = _h(model, task["id"], "fail") > skill + set_bias or _h(model, task["id"], n, "noise") < 0.03
        content, calls = self._answer(model, task, messages, fail)
        return self._stream(model, messages, content, calls, max_tokens)

    def _stream(self, model: str, messages: list[dict[str, Any]], content: str,
                calls: list[dict[str, Any]], max_tokens: int) -> Iterator[SimpleNamespace]:
        speed = 0.3 + _h(model, "speed")                     # relative slowness
        time.sleep(0.01 * speed + 0.005)
        reasoning = "Let me think about this carefully. " * 4
        yield _ns(choices=[_ns(delta=_ns(content=None, reasoning_content=reasoning, tool_calls=None),
                               finish_reason=None)], usage=None)
        for i in range(0, len(content), 40):
            time.sleep(0.0005 * speed)
            yield _ns(choices=[_ns(delta=_ns(content=content[i:i + 40], tool_calls=None), finish_reason=None)],
                      usage=None)
        for idx, call in enumerate(calls):
            args = call["arguments"]
            half = len(args) // 2
            yield _ns(choices=[_ns(delta=_ns(content=None, tool_calls=[_ns(
                index=idx, id=f"call_{idx}", function=_ns(name=call["name"], arguments=args[:half]))]),
                finish_reason=None)], usage=None)
            yield _ns(choices=[_ns(delta=_ns(content=None, tool_calls=[_ns(
                index=idx, id=None, function=_ns(name=None, arguments=args[half:]))]),
                finish_reason=None)], usage=None)
        prompt_chars = 0
        has_image = False
        for m in messages:
            content = m.get("content")
            if isinstance(content, list):
                for part in content:
                    if part.get("type") == "image_url":
                        has_image = True
                    else:
                        prompt_chars += len(part.get("text", ""))
            else:
                prompt_chars += len(json.dumps(content))
        prompt_tokens = prompt_chars // 4 + (1200 if has_image else 0)
        completion_tokens = min(max_tokens, (len(content) + len(reasoning) + 60 * len(calls)) // 4)
        yield _ns(choices=[_ns(delta=_ns(content=None, tool_calls=None),
                               finish_reason="tool_calls" if calls else "stop")], usage=None)
        yield _ns(choices=[], usage=_ns(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                                        completion_tokens_details=_ns(reasoning_tokens=len(reasoning) // 4)))
