"""Test suites: discovery, task loading, generation and fingerprints.

A suite is one folder under `suites/`:

    suites/<name>/
      suite.yaml     title, version (semver), kind, optional environment, description
      build.py       def build(suite_dir: Path) -> list[dict]   (makes the tasks)
      tasks.jsonl    the generated tasks; this file, not build.py, is what runs
      assets/        optional files the tasks point to (images)
      env.py         optional tool environment (for kind: tool_use)

Adding a folder adds a suite. Nothing else in the code needs to change.

Every task carries a `hash`: a fingerprint of its JSON plus the bytes of any file it
points to. Every result records the hash of the task it ran. If a task changes, its
old results stop counting and the runner runs it again.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import ROOT

SUITES_DIR = ROOT / "suites"
HASH_LEN = 12
# Fields that may differ between machines when images are re-rendered (fonts), so
# `generate --check` ignores them. The task hash still covers the committed bytes.
_VOLATILE_FIELDS = ("hash",)

_TASK_CACHE: dict[tuple[str, float], list[dict[str, Any]]] = {}


@dataclass(frozen=True)
class Suite:
    """One test suite, as described by its `suite.yaml`."""

    name: str
    title: str
    version: str
    kind: str
    dir: Path
    description: str = ""
    environment: str | None = None
    extra: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    @property
    def tasks_path(self) -> Path:
        return self.dir / "tasks.jsonl"

    # -- tasks

    def load_tasks(self) -> list[dict[str, Any]]:
        """The committed tasks. Generates them first if the file is missing."""
        if not self.tasks_path.exists():
            generate_suite(self)
        key = (str(self.tasks_path), self.tasks_path.stat().st_mtime)
        if key not in _TASK_CACHE:
            _TASK_CACHE[key] = read_jsonl(self.tasks_path)
        return _TASK_CACHE[key]

    def build(self, out_dir: Path | None = None) -> list[dict[str, Any]]:
        """Run `build.py` into `out_dir` (default: the suite folder) and add task hashes."""
        out = out_dir or self.dir
        tasks = self.module("build").build(out)
        ids = [t["id"] for t in tasks]
        if len(ids) != len(set(ids)):
            raise ValueError(f"suite {self.name}: duplicate task ids")
        for t in tasks:
            t["hash"] = task_hash(t, out)
        return tasks

    def fingerprint(self) -> str:
        """One hash for the whole suite: changes when any task changes."""
        joined = "\n".join(sorted(f"{t['id']}:{t['hash']}" for t in self.load_tasks()))
        return hashlib.sha256(joined.encode()).hexdigest()[:HASH_LEN]

    # -- code

    def module(self, name: str) -> Any:
        """Import `suites/<suite>/<name>.py`."""
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        return importlib.import_module(f"suites.{self.name}.{name}")

    def env_class(self) -> Any:
        """The tool environment class named by `environment:`.

        `env:SupportEnv` is a module inside the suite folder; `gmibench.tools:BasicToolsEnv`
        is any importable module.
        """
        if not self.environment:
            raise ValueError(f"suite {self.name} has no `environment` in suite.yaml")
        mod_name, _, cls_name = self.environment.partition(":")
        if "." in mod_name:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            mod = importlib.import_module(mod_name)
        else:
            mod = self.module(mod_name)
        return getattr(mod, cls_name)


# --------------------------------------------------------------------------- discovery


def discover(suites_dir: Path = SUITES_DIR) -> dict[str, Suite]:
    """All suites under `suites_dir`, by name (sorted)."""
    out: dict[str, Suite] = {}
    for d in sorted(p for p in suites_dir.iterdir() if (p / "suite.yaml").exists()):
        data = yaml.safe_load((d / "suite.yaml").read_text()) or {}
        missing = [k for k in ("title", "version", "kind") if not data.get(k)]
        if missing:
            raise ValueError(f"{d / 'suite.yaml'}: missing {', '.join(missing)}")
        known = {"title", "version", "kind", "description", "environment"}
        out[d.name] = Suite(name=d.name, title=data["title"], version=str(data["version"]), kind=data["kind"],
                            dir=d, description=str(data.get("description") or "").strip(),
                            environment=data.get("environment"),
                            extra={k: v for k, v in data.items() if k not in known})
    return out


def get_suites(names: list[str] | None = None, suites_dir: Path = SUITES_DIR) -> list[Suite]:
    """Suites by name, in the given order (all suites if `names` is None)."""
    found = discover(suites_dir)
    if names is None:
        return list(found.values())
    unknown = [n for n in names if n not in found]
    if unknown:
        raise SystemExit(f"Unknown suite(s): {', '.join(unknown)}. Choose from: {', '.join(found)}")
    return [found[n] for n in names]


# --------------------------------------------------------------------------- hashing / files


def task_hash(task: dict[str, Any], base_dir: Path) -> str:
    """Fingerprint of a task: its JSON (without `hash`) plus the bytes of its `image`, if any."""
    payload = {k: v for k, v in task.items() if k != "hash"}
    h = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode())
    if task.get("image"):
        h.update((base_dir / task["image"]).read_bytes())
    return h.hexdigest()[:HASH_LEN]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def generate_suite(suite: Suite) -> int:
    """Rebuild `tasks.jsonl` (and assets) for one suite. Returns the task count."""
    tasks = suite.build()
    write_jsonl(suite.tasks_path, tasks)
    return len(tasks)


def check_generated(suite: Suite) -> list[str]:
    """Build into a temp folder and compare with the committed tasks (no files change).

    Image bytes are not compared (fonts differ between machines); the task JSON is.
    """
    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"gmibench-{suite.name}-") as tmp:
        fresh = {t["id"]: t for t in suite.build(Path(tmp))}
    committed = {t["id"]: t for t in read_jsonl(suite.tasks_path)} if suite.tasks_path.exists() else {}
    for tid in sorted(set(fresh) | set(committed)):
        if tid not in committed:
            problems.append(f"{suite.name}/{tid}: built by build.py but not in tasks.jsonl")
        elif tid not in fresh:
            problems.append(f"{suite.name}/{tid}: in tasks.jsonl but no longer built by build.py")
        else:
            a = {k: v for k, v in fresh[tid].items() if k not in _VOLATILE_FIELDS}
            b = {k: v for k, v in committed[tid].items() if k not in _VOLATILE_FIELDS}
            if a != b:
                keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                problems.append(f"{suite.name}/{tid}: build.py and tasks.jsonl differ in {', '.join(keys)}")
    return problems


def verify_hashes(suite: Suite) -> list[str]:
    """Check that every stored task hash matches the task content (catches hand edits)."""
    problems = []
    for t in read_jsonl(suite.tasks_path):
        if t.get("hash") != task_hash(t, suite.dir):
            problems.append(f"{suite.name}/{t['id']}: stored hash does not match the content "
                            "(run `python bench.py generate --suite " + suite.name + "`)")
    return problems
