"""Shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gmibench.config import ModelSpec, load_thresholds  # noqa: E402
from gmibench.tasks import load_tasks  # noqa: E402


@pytest.fixture(scope="session")
def thresholds() -> dict[str, Any]:
    return load_thresholds()


@pytest.fixture(scope="session")
def coding_tasks() -> list[dict[str, Any]]:
    return load_tasks("coding")


@pytest.fixture(scope="session")
def tool_tasks() -> list[dict[str, Any]]:
    return load_tasks("tool_use")


@pytest.fixture(scope="session")
def doc_tasks() -> list[dict[str, Any]]:
    return load_tasks("documents")


@pytest.fixture
def model() -> ModelSpec:
    """A small, fully specified model: $1 in / $2 out per 1M tokens, 4B active."""
    return ModelSpec(name="m-small", id="lab/m-small", lab="Lab", total_params_b=30, active_params_b=4,
                     license="apache-2.0", context_length=131072, precision="FP8",
                     input_price_per_m=1.0, output_price_per_m=2.0, vision=False,
                     weights_url="https://example.org/w")


def make_rec(task_id: str, run: int, passed: bool, task_set: str = "coding", *, error: str | None = None,
             prompt_tokens: int = 1000, completion_tokens: int = 500, ttft: float = 0.5, gen: float = 5.0,
             retries: int = 0, tool_ok: bool | None = None) -> dict[str, Any]:
    """Build a raw run record like the runner writes."""
    check: dict[str, Any] = {}
    if tool_ok is not None:
        check["tool_calls_correct"] = tool_ok
    return {"task_id": task_id, "run": run, "task_set": task_set, "passed": passed, "error": error,
            "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "ttft_s": ttft,
            "gen_time_s": gen, "retries": retries, "check": check}
