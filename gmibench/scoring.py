"""Scoring for the GMI Open Model Standard: five dimensions, roll-ups and tiers.

All functions are pure: they take raw run records (dicts as written by the runner),
model metadata and the standard's rules (a plain dict), and return plain dicts.

Suite roles come from the standard (`rules["roles"]`): `core` suites set the tier,
`stress` suites form a separate stress score, anything else is experimental. If the
rules have no roles (for example in unit tests), every suite counts as core.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .checkers import strip_thinking
from .config import ModelSpec

TIER_RECOMMENDED = "GMI Recommended"
TIER_PRODUCTION = "GMI Production Ready"
TIER_VERIFIED = "GMI Verified"
TIER_NONE = "Not verified"


# --------------------------------------------------------------------------- loading


def load_raw(results_dir: Path, model: ModelSpec,
             tasks_by_suite: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Raw records for one model: the last record per (task, run), made with the current task.

    Records made with an older version of a task (different `task_hash`) are ignored;
    the runner will run those tasks again.
    """
    out: dict[str, list[dict[str, Any]]] = {}
    for ts, tasks in tasks_by_suite.items():
        p = results_dir / "raw" / model.slug / f"{ts}.jsonl"
        if not p.exists():
            continue
        hashes = {t["id"]: t.get("hash") for t in tasks}
        latest: dict[tuple[str, int], dict[str, Any]] = {}
        for line in p.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            want = hashes.get(rec["task_id"], "<removed>")
            if want == "<removed>" or (want is not None and rec.get("task_hash") != want):
                continue
            latest[(rec["task_id"], int(rec["run"]))] = rec
        if latest:
            out[ts] = list(latest.values())
    return out


def roles_of(rules: dict[str, Any], names: Iterable[str]) -> dict[str, str]:
    """Role per suite name. No roles in the rules means every suite is core."""
    roles = rules.get("roles")
    names = list(names)
    if roles is None:
        return {n: "core" for n in names}
    return {n: roles.get(n, "experimental") for n in names}


# --------------------------------------------------------------------------- small helpers


def _median(xs: Iterable[float | None]) -> float | None:
    vals = [x for x in xs if x is not None]
    return statistics.median(vals) if vals else None


def run_cost(rec: dict[str, Any], model: ModelSpec | None) -> float | None:
    """USD cost of one run. Uses the prices saved with the run; falls back to models.yaml.

    None if a price is unknown.
    """
    pin = rec.get("price_in_per_m", model.input_price_per_m if model else None)
    pout = rec.get("price_out_per_m", model.output_price_per_m if model else None)
    if pin is None or pout is None:
        return None
    pt = rec.get("prompt_tokens") or 0
    ct = rec.get("completion_tokens") or 0
    return pt * pin / 1e6 + ct * pout / 1e6


def tokens_per_second(rec: dict[str, Any]) -> float | None:
    """Output tokens per second of generation time (after the first token)."""
    ct, gen = rec.get("completion_tokens"), rec.get("gen_time_s")
    if rec.get("error") or not ct or not gen or gen <= 0:
        return None
    return ct / gen


def by_task(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[r["task_id"]].append(r)
    return groups


def consistency(records: list[dict[str, Any]]) -> float | None:
    """Percent of tasks whose every recorded run passed."""
    groups = by_task(records)
    if not groups:
        return None
    return 100.0 * sum(all(r.get("passed") for r in rs) for rs in groups.values()) / len(groups)


def mean_retries_per_task(records: list[dict[str, Any]]) -> float | None:
    """Sum of API retries across a task's runs, averaged over tasks."""
    groups = by_task(records)
    if not groups:
        return None
    return sum(sum(r.get("retries") or 0 for r in rs) for rs in groups.values()) / len(groups)


def tool_call_accuracy(records: list[dict[str, Any]]) -> float | None:
    """Percent of tool-use runs that made every expected call with correct arguments."""
    if not records:
        return None
    ok = sum(bool((r.get("check") or {}).get("tool_calls_correct")) for r in records)
    return 100.0 * ok / len(records)


# --------------------------------------------------------------------------- per set / per model


def score_set(records: list[dict[str, Any]], model: ModelSpec, expected_runs: int) -> dict[str, Any]:
    """Metrics for one model on one task set."""
    n = len(records)
    passed = sum(bool(r.get("passed")) for r in records)
    errors = sum(bool(r.get("error")) for r in records)
    costs = [run_cost(r, model) for r in records]
    cost = None if any(c is None for c in costs) else sum(c for c in costs if c is not None)
    return {
        "status": "ok" if n >= expected_runs and expected_runs > 0 else ("incomplete" if n else "not run"),
        "runs": n,
        "expected_runs": expected_runs,
        "passed_runs": passed,
        "errors": errors,
        "pass_rate": 100.0 * passed / n if n else None,
        "error_rate": errors / n if n else None,
        "consistency": consistency(records),
        "tool_call_accuracy": (tool_call_accuracy(records)
                               if any("tool_calls_correct" in (r.get("check") or {}) for r in records) else None),
        "mean_retries_per_task": mean_retries_per_task(records),
        "ttft_median_s": _median(r.get("ttft_s") for r in records if not r.get("error")),
        "tps_median": _median(tokens_per_second(r) for r in records),
        "non_streamed_runs": sum(r.get("streamed") is False for r in records),
        "truncated_runs": sum(r.get("finish_reason") == "length" for r in records),
        "empty_answer_runs": sum(not r.get("error") and r.get("finish_reason") != "length"
                                 and not strip_thinking(r.get("response") or "").strip() for r in records),
        "prompt_tokens": sum(r.get("prompt_tokens") or 0 for r in records),
        "completion_tokens": sum(r.get("completion_tokens") or 0 for r in records),
        "cost_usd": cost,
        "cost_per_success": (cost / passed) if (cost is not None and passed) else None,
    }


def size_class(model: ModelSpec, thresholds: dict[str, Any]) -> str:
    """Name of the size class for a model, or 'unknown' if params are missing."""
    cfg = thresholds.get("size_classes", {})
    value = getattr(model, cfg.get("basis", "total_params_b"), None)
    if value is None:
        return "unknown"
    for c in cfg.get("classes", []):
        if c.get("max_b") is None or value <= c["max_b"]:
            return c["name"]
    return "unknown"


def deployability(model: ModelSpec, thresholds: dict[str, Any]) -> dict[str, bool]:
    """Pass/fail checklist."""
    d = thresholds.get("deployability", {})
    allowed = {x.lower() for x in d.get("allowed_licenses", [])}
    items = {
        "license_osi_or_openmdw": bool(model.license) and str(model.license).lower() in allowed,
        "context_ge_128k": (model.context_length or 0) >= d.get("min_context_tokens", 128000),
        "precision_documented": bool(model.precision),
        "weights_downloadable": bool(model.weights_url),
    }
    return items


def score_model(model: ModelSpec, raw: dict[str, list[dict[str, Any]]], tasks_per_set: dict[str, int],
                runs_per_task: int, rules: dict[str, Any], not_applicable: Iterable[str] = ()) -> dict[str, Any]:
    """Score one model across the suites in `tasks_per_set` (no cross-model tier yet)."""
    roles = roles_of(rules, tasks_per_set)
    na = set(not_applicable)
    sets: dict[str, Any] = {}
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ts in tasks_per_set:
        if ts in na:
            sets[ts] = {"status": "n/a", "role": roles[ts]}
            continue
        recs = raw.get(ts, [])
        sets[ts] = score_set(recs, model, tasks_per_set[ts] * runs_per_task)
        sets[ts]["role"] = roles[ts]
        by_role[roles[ts]].extend(recs)
    core = [n for n, r in roles.items() if r == "core"]
    stress_names = [n for n, r in roles.items() if r == "stress"]

    overall = score_set(by_role["core"], model, 0) if by_role["core"] else {}
    overall.pop("status", None)
    overall.pop("tool_call_accuracy", None)
    accs = [sets[n]["tool_call_accuracy"] for n in core if sets[n].get("tool_call_accuracy") is not None]
    overall["tool_call_accuracy"] = accs[0] if len(accs) == 1 else (statistics.mean(accs) if accs else None)
    overall["completed_all"] = all(sets[s]["status"] in ("ok", "n/a") for s in core)
    pr = overall.get("pass_rate")
    overall["quality_per_active_b"] = (pr / model.active_params_b) if (pr is not None and model.active_params_b) else None

    ran = {k: v for k, v in sets.items()
           if k in core and v.get("status") in ("ok", "incomplete") and v.get("pass_rate") is not None}

    # Stress score: reported separately. It does not affect the tier.
    stress: dict[str, Any] = {}
    if by_role["stress"]:
        stress = score_set(by_role["stress"], model, 0)
        stress.pop("status", None)
        accs = [sets[n]["tool_call_accuracy"] for n in stress_names
                if sets[n].get("tool_call_accuracy") is not None]
        stress["tool_call_accuracy"] = statistics.mean(accs) if accs else None
        stress["completed_all"] = all(sets[s]["status"] in ("ok", "n/a") for s in stress_names)
    best_for = (max(ran, key=lambda k: (ran[k]["pass_rate"], -(ran[k]["cost_per_success"] or 1e9)))
                if ran and any(v["pass_rate"] > 0 for v in ran.values()) else None)

    return {
        "name": model.name, "id": model.id, "focus": model.focus, "lab": model.lab,
        "total_params_b": model.total_params_b, "active_params_b": model.active_params_b,
        "license": model.license, "context_length": model.context_length, "precision": model.precision,
        "input_price_per_m": model.input_price_per_m, "output_price_per_m": model.output_price_per_m,
        "vision": model.vision, "size_class": size_class(model, rules),
        "sets": sets, "overall": overall, "stress": stress, "deployability": deployability(model, rules),
        "best_for": best_for,
    }


# --------------------------------------------------------------------------- tiers


def base_tier(card: dict[str, Any], thresholds: dict[str, Any]) -> tuple[str, list[str]]:
    """Verified / Production Ready, with the list of unmet criteria for the next tier."""
    t = thresholds["tiers"]
    o = card["overall"]
    unmet: list[str] = []
    if not o:
        return TIER_NONE, ["no runs recorded"]
    if not o.get("completed_all"):
        unmet.append("did not complete all applicable task sets")
    err = o.get("error_rate") or 0.0
    if err >= t["verified"]["max_error_rate"]:
        unmet.append(f"error rate {err:.1%} >= {t['verified']['max_error_rate']:.0%}")
    if unmet:
        return TIER_NONE, unmet
    p = t["production_ready"]
    if (o.get("pass_rate") or 0) < p["min_pass_rate"]:
        unmet.append(f"pass rate {o.get('pass_rate') or 0:.1f} < {p['min_pass_rate']}")
    if (o.get("consistency") or 0) < p["min_consistency"]:
        unmet.append(f"consistency {o.get('consistency') or 0:.1f} < {p['min_consistency']}")
    ttft = o.get("ttft_median_s")
    if ttft is None or ttft > p["max_ttft_median_s"]:
        unmet.append(f"TTFT median {'n/a' if ttft is None else f'{ttft:.2f}s'} > {p['max_ttft_median_s']}s")
    return (TIER_VERIFIED, unmet) if unmet else (TIER_PRODUCTION, [])


def assign_tiers(cards: list[dict[str, Any]], thresholds: dict[str, Any]) -> list[dict[str, Any]]:
    """Add `tier`, `tier_unmet` and `recommended_for` to each card (mutates and returns them).

    Recommended: Production Ready and the lowest cost per successful task on a task set
    among Production Ready models of the same size class that ran that set.
    """
    for c in cards:
        c["tier"], c["tier_unmet"] = base_tier(c, thresholds)
        c["recommended_for"] = []
    prod = [c for c in cards if c["tier"] == TIER_PRODUCTION]
    all_sets = {ts for c in cards for ts in c["sets"]}
    for ts in sorted(n for n, r in roles_of(thresholds, all_sets).items() if r == "core"):
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in prod:
            s = c["sets"].get(ts, {})
            if s.get("status") == "ok" and s.get("cost_per_success") is not None:
                groups[c["size_class"]].append(c)
        for size, members in groups.items():
            best = min(members, key=lambda c: c["sets"][ts]["cost_per_success"])
            best["recommended_for"].append(ts)
    for c in prod:
        if c["recommended_for"]:
            c["tier"] = TIER_RECOMMENDED
        else:
            c["tier_unmet"] = ["not the lowest cost per successful task in any workload for its size class"]
    return cards


def score_all(models: list[ModelSpec], results_dir: Path, suites: list[Any], runs_per_task: int,
              rules: dict[str, Any]) -> list[dict[str, Any]]:
    """Score every model that has any current raw results, then assign tiers.

    `suites` are `Suite` objects in report order.
    """
    tasks_by_suite = {s.name: s.load_tasks() for s in suites}
    tasks_per_set = {n: len(t) for n, t in tasks_by_suite.items()}
    cards = []
    for m in models:
        raw = load_raw(results_dir, m, tasks_by_suite)
        if not raw:
            continue
        na = [s.name for s in suites if not m.applies_to(s)]
        cards.append(score_model(m, raw, tasks_per_set, runs_per_task, rules, na))
    return assign_tiers(cards, rules)
