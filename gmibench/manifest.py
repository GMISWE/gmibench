"""Run manifests: one JSON file per `bench.py run` that records what produced the results.

Saved in `<results>/manifests/<id>.json`. Every raw record carries the same `manifest_id`,
so any result can be traced back to the git commit, standard, suite versions, model
prices and settings that produced it.
"""

from __future__ import annotations

import json
import secrets
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ROOT, ModelSpec


def git_info(root: Path = ROOT) -> dict[str, Any]:
    """Current commit, branch and whether there are uncommitted changes."""
    def run(*args: str) -> str | None:
        try:
            out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    status = run("status", "--porcelain")
    return {"commit": run("rev-parse", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(status) if status is not None else None}


def new_manifest_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(2)


def write_manifest(results_dir: Path, manifest_id: str, *, standard: Any, suites: list[Any],
                   models: list[ModelSpec], resolved: dict[str, str], settings: Any,
                   argv: list[str], summary: dict[str, Any] | None = None,
                   started: str | None = None) -> Path:
    """Write (or overwrite) the manifest for one run."""
    path = results_dir / "manifests" / f"{manifest_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "manifest_id": manifest_id,
        "started": started or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "finished": datetime.now(timezone.utc).isoformat(timespec="seconds") if summary is not None else None,
        "command": " ".join(["bench.py", *argv]),
        "python": sys.version.split()[0],
        "git": git_info(),
        "standard": standard.version,
        "suites": {s.name: {"version": s.version, "fingerprint": s.fingerprint(), "kind": s.kind} for s in suites},
        "models": [{"name": m.name, "id": resolved.get(m.name, m.id),
                    "input_price_per_m": m.input_price_per_m, "output_price_per_m": m.output_price_per_m}
                   for m in models],
        "settings": asdict(settings),
        "summary": summary,
    }
    path.write_text(json.dumps(doc, indent=2))
    return path
