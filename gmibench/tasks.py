"""Write and load the JSONL task sets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import TASK_SETS, TASKS_DIR
from .tasks_coding import build_coding_tasks
from .tasks_coding_hard import build_coding_hard_tasks
from .tasks_documents import build_document_tasks
from .tasks_documents_hard import build_document_hard_tasks
from .tasks_tooluse import build_tool_tasks
from .tasks_tooluse_hard import build_tool_hard_tasks


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write rows as one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def generate_all(tasks_dir: Path = TASKS_DIR) -> dict[str, int]:
    """(Re)generate all three task sets and the document PNGs. Returns counts per set."""
    sets = {
        "coding": build_coding_tasks(),
        "tool_use": build_tool_tasks(),
        "documents": build_document_tasks(tasks_dir / "assets"),
        "coding_hard": build_coding_hard_tasks(),
        "tool_use_hard": build_tool_hard_tasks(),
        "documents_hard": build_document_hard_tasks(tasks_dir / "assets"),
    }
    for name, rows in sets.items():
        write_jsonl(tasks_dir / f"{name}.jsonl", rows)
    return {k: len(v) for k, v in sets.items()}


def load_tasks(task_set: str, tasks_dir: Path = TASKS_DIR) -> list[dict[str, Any]]:
    """Load one task set. Generates the files first if they are missing."""
    if task_set not in TASK_SETS:
        raise ValueError(f"unknown task set {task_set}")
    path = tasks_dir / f"{task_set}.jsonl"
    if not path.exists():
        generate_all(tasks_dir)
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]
