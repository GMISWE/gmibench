#!/usr/bin/env python3
"""GMI Open Model Standard benchmark CLI.

    python bench.py run --models all --tasks all
    python bench.py run --models gpt-oss-120b --tasks coding --runs 1
    python bench.py score
    python bench.py report
    python bench.py generate          # rebuild tasks/*.jsonl and tasks/assets/*.png

Add --dry-run to any command to use the offline fake client and `results_dryrun/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gmibench.config import (ROOT, TASK_SETS, TASKS_DIR, load_dotenv, load_models, load_thresholds,
                             select_models, select_task_sets)


def _results_dir(args: argparse.Namespace) -> Path:
    if args.results_dir:
        return Path(args.results_dir)
    return ROOT / ("results_dryrun" if args.dry_run else "results")


def _tasks_per_set() -> dict[str, int]:
    from gmibench.tasks import load_tasks
    return {ts: len(load_tasks(ts)) for ts in TASK_SETS}


def cmd_generate(args: argparse.Namespace) -> int:
    from gmibench.tasks import generate_all
    counts = generate_all(TASKS_DIR)
    print("Generated:", ", ".join(f"{k}={v}" for k, v in counts.items()), f"in {TASKS_DIR}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from gmibench.client import FakeClient, make_client, resolve_models
    from gmibench.estimate import estimate, print_estimate
    from gmibench.runner import RunSettings, run_all

    thresholds = load_thresholds()
    models = select_models(load_models(), args.models)
    task_sets = select_task_sets(args.tasks)
    settings = RunSettings.from_config(thresholds.get("run", {}), runs_per_task=args.runs,
                                       concurrency_per_model=args.concurrency, dry_run=args.dry_run,
                                       retry_errors=args.retry_errors)
    if args.dry_run:
        settings.backoff_base_s = 0.01
    results_dir = _results_dir(args)
    _tasks_per_set()  # generates task files if missing

    if args.dry_run:
        client: Any = FakeClient(models)
        print("DRY RUN: fake client, no network. Results go to", results_dir)
    else:
        load_dotenv()
        client = make_client(settings.request_timeout_s)
    resolved = resolve_models(client, models)
    print(f"Resolved {len(resolved)} model IDs on /v1/models.")

    rows = estimate(models, task_sets, settings, results_dir, thresholds.get("cost_estimate", {}))
    print_estimate(rows)
    if not any(r["runs"] for r in rows):
        print("Nothing to run: every selected run is already recorded. Use --retry-errors to redo failed calls.")
        return 0
    if not args.dry_run and not args.yes:
        if not sys.stdin.isatty():
            print("Refusing to spend tokens without confirmation. Re-run with --yes.")
            return 1
        if input("Proceed with the real run? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 1

    summary = run_all(client, models, resolved, task_sets, settings, results_dir)
    errors = sum(c["errors"] for c in summary.values())
    print(f"\nDone. Raw results in {results_dir / 'raw'}. Runs with API errors: {errors}.")
    print("Next: python bench.py score" + (" --dry-run" if args.dry_run else ""))
    return 0


def _score(args: argparse.Namespace) -> list[dict[str, Any]]:
    from gmibench.scoring import score_all

    thresholds = load_thresholds()
    models = load_models(warn=False)
    runs = args.runs or thresholds.get("run", {}).get("runs_per_task", 3)
    results_dir = _results_dir(args)
    cards = score_all(models, results_dir, _tasks_per_set(), runs, thresholds)
    (results_dir / "scores.json").parent.mkdir(parents=True, exist_ok=True)
    (results_dir / "scores.json").write_text(json.dumps(cards, indent=2))
    return cards


def cmd_score(args: argparse.Namespace) -> int:
    cards = _score(args)
    if not cards:
        print(f"No raw results in {_results_dir(args) / 'raw'}. Run `python bench.py run` first.")
        return 1
    print(f"{'model':<26}{'pass %':>8}{'consist %':>11}{'TTFT s':>8}{'$/success':>12}  tier")
    for c in cards:
        o = c["overall"]
        cps = o.get("cost_per_success")
        print(f"{c['name']:<26}{o.get('pass_rate') or 0:>8.1f}{o.get('consistency') or 0:>11.1f}"
              f"{(o.get('ttft_median_s') or 0):>8.2f}{('–' if cps is None else f'{cps:.5f}'):>12}  {c['tier']}")
    print(f"\nWrote {_results_dir(args) / 'scores.json'}. Next: python bench.py report"
          + (" --dry-run" if args.dry_run else ""))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from gmibench.report import write_reports

    cards = _score(args)
    if not cards:
        print(f"No raw results in {_results_dir(args) / 'raw'}. Run `python bench.py run` first.")
        return 1
    paths = write_reports(cards, _results_dir(args), load_thresholds(), dry_run=args.dry_run)
    print("Wrote:")
    for p in paths:
        print("  ", p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)
    return 0


def cmd_spend(args: argparse.Namespace) -> int:
    """Sum the cost of every recorded run (all records, including superseded ones)."""
    from gmibench.scoring import run_cost

    models = {m.slug: m for m in load_models(warn=False)}
    raw = _results_dir(args) / "raw"
    total = 0.0
    for d in sorted(p for p in raw.iterdir() if p.is_dir()) if raw.exists() else []:
        m = models.get(d.name)
        cost = runs = 0
        for f in d.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                runs += 1
                cost += (run_cost(rec, m) or 0.0) if m else 0.0
        total += cost
        print(f"{d.name:<26}{runs:>6} runs  ${cost:.4f}")
    print(f"{'TOTAL':<26}{'':>6}       ${total:.4f}")
    return 0


def cmd_recheck(args: argparse.Namespace) -> int:
    """Re-apply the checkers to saved runs (no API calls). Use after a checker fix."""
    from gmibench import checkers
    from gmibench.tasks import load_tasks

    tasks = {ts: {t["id"]: t for t in load_tasks(ts)} for ts in TASK_SETS}
    timeout = load_thresholds().get("run", {}).get("coding_timeout_s", 10)
    changed = total = 0
    for f in sorted((_results_dir(args) / "raw").glob("*/*.jsonl")):
        out_lines = []
        for line in f.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            task = tasks.get(rec.get("task_set"), {}).get(rec.get("task_id"))
            if task is not None and not rec.get("error"):
                total += 1
                kind = rec["task_set"].removesuffix("_hard")
                if kind == "coding":
                    ok, check = checkers.check_coding(task, rec.get("response") or "", timeout)
                elif kind == "tool_use":
                    ok, check = checkers.check_tool_use(task, rec.get("tool_calls") or [], rec.get("response") or "")
                else:
                    ok, check = checkers.check_document(task, rec.get("response") or "")
                if ok != rec.get("passed"):
                    changed += 1
                    print(f"{rec['model']} {rec['task_id']} run {rec['run']}: {rec.get('passed')} -> {ok}")
                rec["passed"], rec["check"] = ok, check
            out_lines.append(json.dumps(rec, ensure_ascii=False))
        tmp = f.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(out_lines) + "\n")
        tmp.replace(f)
    print(f"Rechecked {total} runs, {changed} changed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench.py", description="GMI Open Model Standard benchmark")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="offline fake client; uses results_dryrun/")
    common.add_argument("--results-dir", help="override the results folder")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", parents=[common], help="run tasks against models")
    p.add_argument("--models", default="all", help="'all' or comma list of names/IDs from models.yaml")
    p.add_argument("--tasks", default="all", help="'all' or comma list of: " + ", ".join(TASK_SETS))
    p.add_argument("--runs", type=int, help="runs per task (default from thresholds.yaml, 3)")
    p.add_argument("--concurrency", type=int, help="parallel requests per model (default 4)")
    p.add_argument("--retry-errors", action="store_true", help="re-run recorded runs that ended in an API error")
    p.add_argument("--yes", "-y", action="store_true", help="skip the cost confirmation prompt")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("score", parents=[common], help="compute scores from raw results")
    p.add_argument("--runs", type=int, help="expected runs per task for completeness (default 3)")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("report", parents=[common], help="write scorecards, summary and charts")
    p.add_argument("--runs", type=int, help="expected runs per task for completeness (default 3)")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("recheck", parents=[common], help="re-grade saved runs with current checkers (no API)")
    p.set_defaults(func=cmd_recheck)

    p = sub.add_parser("spend", parents=[common], help="total USD spent on recorded runs")
    p.set_defaults(func=cmd_spend)

    p = sub.add_parser("generate", help="regenerate task files and document images")
    p.set_defaults(func=cmd_generate, dry_run=False, results_dir=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
