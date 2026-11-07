"""Coding: the model writes a Python function; hidden tests run in a subprocess."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .. import checkers
from .base import Kind

if TYPE_CHECKING:
    from ..suites import Suite


class CodingKind(Kind):
    name = "coding"

    def check(self, task: dict[str, Any], suite: "Suite", final: str, calls: list[dict[str, Any]],
              coding_timeout_s: float = 10.0) -> tuple[bool, dict[str, Any]]:
        return checkers.check_coding(task, final, coding_timeout_s)

    def reference(self, task: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        return f"```python\n{task['reference_solution']}```", []

    def fake_answer(self, task: dict[str, Any], messages: list[dict[str, Any]],
                    fail: bool) -> tuple[str, list[dict[str, Any]]]:
        code = task["reference_solution"]
        if fail:
            code = code.replace("return", "return None and", 1)
        return f"```python\n{code}```", []
