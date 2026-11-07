"""Tool use: a multi-turn loop with a tool environment named in `suite.yaml`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .base import Kind

if TYPE_CHECKING:
    from ..suites import Suite


class ToolUseKind(Kind):
    name = "tool_use"

    def environment(self, task: dict[str, Any], suite: "Suite") -> Any:
        return suite.env_class()()

    def check(self, task: dict[str, Any], suite: "Suite", final: str, calls: list[dict[str, Any]],
              coding_timeout_s: float = 10.0) -> tuple[bool, dict[str, Any]]:
        return suite.env_class().check(task, calls, final)

    def reference(self, task: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        calls = [{"name": c["name"], "arguments": json.dumps(c["args"])} for c in task["reference_calls"]]
        return task["reference_answer"], calls

    def fake_answer(self, task: dict[str, Any], messages: list[dict[str, Any]],
                    fail: bool) -> tuple[str, list[dict[str, Any]]]:
        # First turn: make the reference calls. After tool results: give the reference answer.
        if not any(m.get("role") == "tool" for m in messages):
            if fail and len(task["id"]) % 2 == 0:
                return "I think the answer is 42.", []
            return "", [{"name": c["name"], "arguments": json.dumps(c["args"])} for c in task["reference_calls"]]
        return ("I could not determine that." if fail else task["reference_answer"]), []

    def estimate(self, task: dict[str, Any], suite: "Suite", cfg: dict[str, Any]) -> tuple[float, float, float]:
        cpt = cfg.get("chars_per_token", 4)
        frac = cfg.get("expected_output_fraction", 0.35)
        turns = max(cfg.get("tool_turns_estimate", 3), len(task.get("reference_calls", [])) // 2 + 2)
        base = (len(task.get("prompt", "")) + len(task.get("system", ""))) / cpt
        tools = len(json.dumps(suite.env_class().schemas)) / cpt
        tin = turns * (base + tools) + 200 * turns * (turns - 1) / 2
        return tin, turns * frac * task["max_tokens"] / 3, float(turns * task["max_tokens"])
