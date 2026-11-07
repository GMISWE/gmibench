"""Documents: an image goes in, structured JSON comes out."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any

from .. import checkers
from .base import Kind

if TYPE_CHECKING:
    from ..suites import Suite


def _b64(suite: "Suite", task: dict[str, Any]) -> str:
    return base64.b64encode((suite.dir / task["image"]).read_bytes()).decode()


class DocumentsKind(Kind):
    name = "documents"
    needs_vision = True

    def messages(self, task: dict[str, Any], suite: "Suite") -> list[dict[str, Any]]:
        # Image first, then text (the common VLM convention).
        return [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(suite, task)}"}},
            {"type": "text", "text": task["prompt"]},
        ]}]

    def check(self, task: dict[str, Any], suite: "Suite", final: str, calls: list[dict[str, Any]],
              coding_timeout_s: float = 10.0) -> tuple[bool, dict[str, Any]]:
        return checkers.check_document(task, final)

    def reference(self, task: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        return "```json\n" + json.dumps(task["expected"]) + "\n```", []

    def fake_answer(self, task: dict[str, Any], messages: list[dict[str, Any]],
                    fail: bool) -> tuple[str, list[dict[str, Any]]]:
        gt = dict(task["expected"])
        if fail:
            gt["total"] = round(gt["total"] + 1.0, 2)
        return "```json\n" + json.dumps(gt) + "\n```", []

    def fake_key(self, task: dict[str, Any], suite: "Suite") -> str:
        return _b64(suite, task)

    def estimate(self, task: dict[str, Any], suite: "Suite", cfg: dict[str, Any]) -> tuple[float, float, float]:
        tin, typ, mx = super().estimate(task, suite, cfg)
        return tin + cfg.get("image_tokens", 1500), typ, mx
