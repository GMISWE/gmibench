"""Load and validate `models.yaml` and `thresholds.yaml`."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODELS_FILE = ROOT / "models.yaml"
DEFAULT_THRESHOLDS_FILE = ROOT / "thresholds.yaml"
TASKS_DIR = ROOT / "tasks"
CORE_SETS: tuple[str, ...] = ("coding", "tool_use", "documents")
HARD_SETS: tuple[str, ...] = ("coding_hard", "tool_use_hard", "documents_hard")
TASK_SETS: tuple[str, ...] = CORE_SETS + HARD_SETS


def base_kind(task_set: str) -> str:
    """'tool_use_hard' -> 'tool_use'. The kind decides messages, tools and checker."""
    return task_set.removesuffix("_hard")

METADATA_FIELDS: tuple[str, ...] = (
    "lab",
    "total_params_b",
    "active_params_b",
    "license",
    "context_length",
    "precision",
    "input_price_per_m",
    "output_price_per_m",
    "weights_url",
)


@dataclass
class ModelSpec:
    """One model in the cohort, as written in `models.yaml`."""

    name: str
    id: str
    focus: str = ""
    lab: str | None = None
    total_params_b: float | None = None
    active_params_b: float | None = None
    license: str | None = None
    context_length: int | None = None
    precision: str | None = None
    input_price_per_m: float | None = None
    output_price_per_m: float | None = None
    vision: bool = False
    weights_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        """Filesystem-safe name used for result folders and file names."""
        return self.name.replace("/", "_")

    def applicable_sets(self) -> list[str]:
        """Task sets this model runs. Documents need vision."""
        return [s for s in TASK_SETS if base_kind(s) != "documents" or self.vision]

    def missing_fields(self) -> list[str]:
        """Metadata fields that are still `null`."""
        return [f for f in METADATA_FIELDS if getattr(self, f) is None]


def load_models(path: Path = DEFAULT_MODELS_FILE, warn: bool = True) -> list[ModelSpec]:
    """Parse the cohort file. Print a warning for every unknown metadata field."""
    data = yaml.safe_load(path.read_text())
    known = set(ModelSpec.__dataclass_fields__) - {"extra"}
    models: list[ModelSpec] = []
    for raw in data.get("models", []):
        kwargs = {k: v for k, v in raw.items() if k in known}
        extra = {k: v for k, v in raw.items() if k not in known}
        if "name" not in kwargs or "id" not in kwargs:
            raise ValueError(f"models.yaml entry needs `name` and `id`: {raw}")
        spec = ModelSpec(**kwargs, extra=extra)
        models.append(spec)
        if warn:
            for f in spec.missing_fields():
                print(f"WARNING: {spec.name}: `{f}` is null in models.yaml", file=sys.stderr)
    names = [m.name for m in models]
    if len(names) != len(set(names)):
        raise ValueError("models.yaml has duplicate `name` values")
    return models


def load_thresholds(path: Path = DEFAULT_THRESHOLDS_FILE) -> dict[str, Any]:
    """Parse the thresholds file."""
    return yaml.safe_load(path.read_text())


def select_models(models: list[ModelSpec], selector: str) -> list[ModelSpec]:
    """Pick models from a comma list of names or IDs, or `all`."""
    if selector.strip().lower() == "all":
        return models
    wanted = [s.strip().lower() for s in selector.split(",") if s.strip()]
    picked: list[ModelSpec] = []
    for w in wanted:
        match = [
            m for m in models
            if w in (m.name.lower(), m.id.lower(), m.id.split("/")[-1].lower())
        ]
        if not match:
            choices = ", ".join(m.name for m in models)
            raise SystemExit(f"Unknown model '{w}'. Choose from: {choices}")
        picked.extend(x for x in match if x not in picked)
    return picked


def select_task_sets(selector: str) -> list[str]:
    """Pick task sets from a comma list, or `all` / `core` / `hard`."""
    key = selector.strip().lower()
    if key == "all":
        return list(TASK_SETS)
    if key == "core":
        return list(CORE_SETS)
    if key == "hard":
        return list(HARD_SETS)
    sets = [s.strip() for s in selector.split(",") if s.strip()]
    for s in sets:
        if s not in TASK_SETS:
            raise SystemExit(f"Unknown task set '{s}'. Choose from: {', '.join(TASK_SETS)}")
    return sets


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimal `.env` loader. Existing environment variables win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
