"""Base class for kinds."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..suites import Suite


class Kind:
    """Interface every kind implements. Defaults suit plain text-in, text-out tasks."""

    name: str = ""
    needs_vision: bool = False

    # -- running

    def messages(self, task: dict[str, Any], suite: "Suite") -> list[dict[str, Any]]:
        """The chat messages for the first turn."""
        system = [{"role": "system", "content": task["system"]}] if task.get("system") else []
        return system + [{"role": "user", "content": task["prompt"]}]

    def environment(self, task: dict[str, Any], suite: "Suite") -> Any | None:
        """A fresh tool environment for one run, or None for a single-turn task."""
        return None

    def check(self, task: dict[str, Any], suite: "Suite", final: str, calls: list[dict[str, Any]],
              coding_timeout_s: float = 10.0) -> tuple[bool, dict[str, Any]]:
        raise NotImplementedError

    # -- reference answer (validation and the dry-run client)

    def reference(self, task: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        """(ideal final answer, ideal tool calls) for a task."""
        raise NotImplementedError

    def validate(self, task: dict[str, Any], suite: "Suite") -> list[str]:
        """Problems with a task. Default: its reference answer must pass its own checker."""
        final, calls = self.reference(task)
        ok, info = self.check(task, suite, final, calls)
        return [] if ok else [f"{suite.name}/{task['id']}: reference answer fails the checker: {info}"]

    def fake_answer(self, task: dict[str, Any], messages: list[dict[str, Any]],
                    fail: bool) -> tuple[str, list[dict[str, Any]]]:
        """Answer for the offline fake client. `fail` asks for a wrong answer."""
        final, _ = self.reference(task)
        return ("I am not sure." if fail else final), []

    def fake_key(self, task: dict[str, Any], suite: "Suite") -> str:
        """What the fake client uses to recognise this task in incoming messages."""
        return task["prompt"]

    # -- cost estimate

    def estimate(self, task: dict[str, Any], suite: "Suite", cfg: dict[str, Any]) -> tuple[float, float, float]:
        """(input tokens, typical output tokens, max output tokens) for one run."""
        cpt = cfg.get("chars_per_token", 4)
        frac = cfg.get("expected_output_fraction", 0.35)
        tin = (len(task.get("prompt", "")) + len(task.get("system", ""))) / cpt
        return tin, frac * task["max_tokens"], float(task["max_tokens"])
