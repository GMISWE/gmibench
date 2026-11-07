"""Token and cost estimate printed before a real run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import TASKS_DIR, ModelSpec, base_kind
from .runner import ResultStore, RunSettings, pending_jobs
from .tasks import load_tasks
from .support_env import SUPPORT_TOOL_SCHEMAS
from .tools import TOOL_SCHEMAS


def estimate(models: list[ModelSpec], task_sets: list[str], settings: RunSettings, results_dir: Path,
             cfg: dict[str, Any], tasks_dir: Path = TASKS_DIR) -> list[dict[str, Any]]:
    """Per model: pending runs, estimated tokens and cost (typical and upper bound).

    Only runs that are not yet recorded are counted, so a resumed run shows what is left.
    """
    cpt = cfg.get("chars_per_token", 4)
    img = cfg.get("image_tokens", 1500)
    frac = cfg.get("expected_output_fraction", 0.35)
    turns = cfg.get("tool_turns_estimate", 3)
    tool_tokens_basic = len(json.dumps(TOOL_SCHEMAS)) // cpt
    tool_tokens_support = len(json.dumps(SUPPORT_TOOL_SCHEMAS)) // cpt
    store = ResultStore(results_dir)
    rows = []
    for m in models:
        jobs_n = 0
        tin = tout_typ = tout_max = 0.0
        for ts in task_sets:
            if ts not in m.applicable_sets():
                continue
            tasks = load_tasks(ts, tasks_dir)
            jobs = pending_jobs(tasks, store.load(m, ts), settings.runs_per_task, settings.retry_errors)
            jobs_n += len(jobs)
            for t, _ in jobs:
                base = (len(t["prompt"]) + len(t.get("system", ""))) // cpt
                if base_kind(ts) == "documents":
                    tin += base + img
                    tout_typ += frac * t["max_tokens"]
                    tout_max += t["max_tokens"]
                elif base_kind(ts) == "tool_use":
                    support = t.get("toolset") == "support"
                    tool_tokens = tool_tokens_support if support else tool_tokens_basic
                    n = 2 * turns if support else turns
                    tin += n * (base + tool_tokens) + 250 * n * (n - 1) / 2
                    tout_typ += n * frac * t["max_tokens"] / 4
                    tout_max += n * t["max_tokens"]
                else:
                    tin += base
                    tout_typ += frac * t["max_tokens"]
                    tout_max += t["max_tokens"]
        pin, pout = m.input_price_per_m, m.output_price_per_m
        priced = pin is not None and pout is not None
        rows.append({
            "model": m.name, "runs": jobs_n, "input_tokens": int(tin),
            "output_tokens_typical": int(tout_typ), "output_tokens_max": int(tout_max),
            "cost_typical": (tin * pin + tout_typ * pout) / 1e6 if priced else None,
            "cost_max": (tin * pin + tout_max * pout) / 1e6 if priced else None,
        })
    return rows


def print_estimate(rows: list[dict[str, Any]]) -> tuple[float, float]:
    """Print the estimate table. Returns (typical total, upper-bound total)."""
    print("\nEstimated usage for this run (only runs not yet recorded):")
    print(f"{'model':<26}{'runs':>6}{'in tok':>12}{'out tok (typ)':>15}{'out tok (max)':>15}"
          f"{'cost (typ)':>12}{'cost (max)':>12}")
    typ = mx = 0.0
    for r in rows:
        ct = "?" if r["cost_typical"] is None else f"${r['cost_typical']:.3f}"
        cm = "?" if r["cost_max"] is None else f"${r['cost_max']:.3f}"
        typ += r["cost_typical"] or 0
        mx += r["cost_max"] or 0
        print(f"{r['model']:<26}{r['runs']:>6}{r['input_tokens']:>12,}{r['output_tokens_typical']:>15,}"
              f"{r['output_tokens_max']:>15,}{ct:>12}{cm:>12}")
    print(f"{'TOTAL':<26}{'':>6}{'':>12}{'':>15}{'':>15}{'$' + format(typ, '.3f'):>12}{'$' + format(mx, '.3f'):>12}")
    print("'typ' assumes outputs use ~35% of max_tokens; 'max' assumes every output hits max_tokens.")
    print("Models with unknown prices show '?' and are not in the total.\n")
    return typ, mx
