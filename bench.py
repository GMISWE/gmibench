#!/usr/bin/env python3
"""GMI Open Model Standard benchmark CLI.

    python bench.py suites                      # list suites, versions, roles, status
    python bench.py run --models all --suites all
    python bench.py run --models gemma-4-26b-a4b --suites coding --runs 1
    python bench.py score                       # under the latest released standard
    python bench.py report
    python bench.py score --standard dev        # score work in progress (no pins)
    python bench.py generate --suite coding     # rebuild a suite's tasks.jsonl (and assets)
    python bench.py validate                    # checks CI runs on every change
    python bench.py release 1.1                 # pin the current suites as a new standard

Add --dry-run to run/score/report to use the offline fake client and `results_dryrun/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gmibench.config import ROOT, load_dotenv, load_models, load_settings, select_models


def _results_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "results_dir", None):
        return Path(args.results_dir)
    return ROOT / ("results_dryrun" if getattr(args, "dry_run", False) else "results")


def _standard(args: argparse.Namespace) -> Any:
    from gmibench.standard import load_standard
    return load_standard(getattr(args, "standard", None) or "latest")


def _select_suites(selector: str, std: Any) -> list[Any]:
    """`all`, `core`, `stress` (alias `hard`), `experimental`, or a comma list of suite names."""
    from gmibench.suites import discover, get_suites

    found = discover()
    key = selector.strip().lower()
    if key == "hard":
        key = "stress"
    if key == "all":
        names = std.ordered(list(found))
    elif key in ("core", "stress", "experimental"):
        names = std.names(key, list(found))
    else:
        names = [s.strip() for s in selector.split(",") if s.strip()]
    return get_suites(names)


def _scoring_suites(std: Any) -> list[Any]:
    """Every suite on disk, in standard order. Refuses a released standard whose pins no longer match."""
    from gmibench.suites import discover

    found = discover()
    problems = std.check_pins(found)
    if problems:
        raise SystemExit(
            f"Cannot score under v{std.version}: the suites on disk differ from what it pins.\n  - "
            + "\n  - ".join(problems)
            + "\nScore work in progress with `--standard dev`, or release a new standard "
              "(`python bench.py release X.Y`). To reproduce an old standard, check out its git tag.")
    return [found[n] for n in std.ordered(list(found))]


# --------------------------------------------------------------------------- commands


def cmd_suites(args: argparse.Namespace) -> int:
    from gmibench.suites import discover

    std = _standard(args)
    found = discover()
    print(f"Standard: {std.label}\n")
    print(f"{'suite':<18}{'version':<10}{'kind':<11}{'role':<14}{'tasks':>6}  {'fingerprint':<14}status")
    for name in std.ordered(list(found)):
        s = found[name]
        fp = s.fingerprint()
        pin = std.pins.get(name)
        if pin is None:
            status = "not in standard (experimental)"
        elif pin["version"] == s.version and pin["fingerprint"] == fp:
            status = "matches standard"
        elif pin["version"] == s.version:
            status = "CHANGED: bump the suite version"
        else:
            status = f"changed: {pin['version']} -> {s.version} (release a new standard)"
        print(f"{name:<18}{s.version:<10}{s.kind:<11}{std.role(name):<14}{len(s.load_tasks()):>6}  {fp:<14}{status}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from gmibench.suites import check_generated, generate_suite, get_suites

    suites = get_suites([x.strip() for x in args.suite.split(",")] if args.suite else None)
    if args.check:
        problems = [p for s in suites for p in check_generated(s)]
        for p in problems:
            print("  -", p)
        print(f"{'FAIL' if problems else 'OK'}: build.py and tasks.jsonl "
              f"{'differ' if problems else 'agree'} for {len(suites)} suite(s).")
        return 1 if problems else 0
    for s in suites:
        before = s.fingerprint() if s.tasks_path.exists() else None
        n = generate_suite(s)
        after = s.fingerprint()
        note = "unchanged" if before == after else f"CHANGED {before} -> {after} (bump {s.name}/suite.yaml version)"
        print(f"{s.name}: {n} tasks, fingerprint {after} ({note})")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Every check that keeps the suites and standards consistent. CI runs this."""
    from gmibench.kinds import get_kind
    from gmibench.standard import load_standard, released_versions
    from gmibench.suites import discover, verify_hashes

    problems: list[str] = []
    found = discover()
    for s in found.values():
        try:
            kind = get_kind(s.kind)
        except ValueError as exc:
            problems.append(f"{s.name}: {exc}")
            continue
        if not s.tasks_path.exists():
            problems.append(f"{s.name}: tasks.jsonl is missing (run `python bench.py generate --suite {s.name}`)")
            continue
        problems += verify_hashes(s)
        for t in s.load_tasks():
            problems += kind.validate(t, s)
    for major, minor in released_versions():
        std = load_standard(f"{major}.{minor}")
        for name in std.pins:
            if name not in found:
                problems.append(f"v{std.version} pins suite '{name}', which no longer exists")
    latest = load_standard("latest")
    for name, pin in latest.pins.items():
        s = found.get(name)
        if s and s.version == pin["version"] and s.fingerprint() != pin["fingerprint"]:
            problems.append(f"{name}: tasks changed but suite.yaml version is still {s.version}. "
                            "Bump the version (then release a new standard when ready).")
    for p in problems:
        print("  -", p)
    n_tasks = sum(len(s.load_tasks()) for s in found.values() if s.tasks_path.exists())
    print(f"{'FAIL' if problems else 'OK'}: {len(found)} suites, {n_tasks} tasks, "
          f"{len(released_versions())} released standard(s); {len(problems)} problem(s).")
    return 1 if problems else 0


def cmd_release(args: argparse.Namespace) -> int:
    from gmibench.standard import load_standard, release
    from gmibench.suites import discover

    found = discover()
    latest = load_standard("latest")
    roles = dict(latest.roles)
    for role in ("core", "stress"):
        for name in filter(None, (getattr(args, role) or "").split(",")):
            roles[name.strip()] = role
    for name in filter(None, (args.drop or "").split(",")):
        roles.pop(name.strip(), None)
    unknown = [n for n in roles if n not in found]
    if unknown:
        raise SystemExit(f"Unknown suite(s): {', '.join(unknown)}")
    path = release(args.version, found, roles, notes=args.notes or "")
    print(f"Wrote {path.relative_to(ROOT)}.")
    print("Next: edit its `notes`, add a CHANGELOG.md entry, run `python bench.py validate`, commit, and tag:\n"
          f"  git tag standard-v{args.version}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from gmibench.client import FakeClient, make_client, resolve_models
    from gmibench.estimate import estimate, print_estimate
    from gmibench.manifest import new_manifest_id, write_manifest
    from gmibench.runner import RunSettings, run_all

    std = _standard(args)
    settings_cfg = load_settings()
    models = select_models(load_models(), args.models)
    suites = _select_suites(args.suites, std)
    settings = RunSettings.from_config(std.protocol, settings_cfg.get("run", {}), runs_per_task=args.runs,
                                       concurrency_per_model=args.concurrency, dry_run=args.dry_run,
                                       retry_errors=args.retry_errors)
    if args.dry_run:
        settings.backoff_base_s = 0.01
    results_dir = _results_dir(args)

    if args.dry_run:
        client: Any = FakeClient(models)
        print("DRY RUN: fake client, no network. Results go to", results_dir)
    else:
        load_dotenv()
        client = make_client(settings.request_timeout_s)
    resolved = resolve_models(client, models)
    print(f"Resolved {len(resolved)} model IDs on /v1/models. Suites: {', '.join(s.name for s in suites)}")

    rows = estimate(models, suites, settings, results_dir, settings_cfg.get("cost_estimate", {}))
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

    settings.manifest_id = new_manifest_id()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    common = dict(standard=std, suites=suites, models=models, resolved=resolved, settings=settings,
                  argv=sys.argv[1:], started=started)
    write_manifest(results_dir, settings.manifest_id, **common)
    summary = run_all(client, models, resolved, suites, settings, results_dir)
    mpath = write_manifest(results_dir, settings.manifest_id, summary=summary, **common)
    errors = sum(c["errors"] for c in summary.values())
    print(f"\nDone. Raw results in {results_dir / 'raw'}. Runs with API errors: {errors}.")
    print(f"Manifest: {mpath}")
    print("Next: python bench.py score" + (" --dry-run" if args.dry_run else ""))
    return 0


def _score(args: argparse.Namespace) -> tuple[list[dict[str, Any]], Any, list[Any]]:
    from gmibench.scoring import score_all

    std = _standard(args)
    suites = _scoring_suites(std)
    runs = args.runs or std.protocol.get("runs_per_task", 3)
    results_dir = _results_dir(args)
    cards = score_all(load_models(warn=False), results_dir, suites, runs, std.scoring_dict())
    out = {"standard": std.version, "standard_label": std.label, "cards": cards}
    (results_dir / "scores.json").parent.mkdir(parents=True, exist_ok=True)
    (results_dir / "scores.json").write_text(json.dumps(out, indent=2))
    return cards, std, suites


def cmd_score(args: argparse.Namespace) -> int:
    cards, std, _ = _score(args)
    if not cards:
        print(f"No raw results in {_results_dir(args) / 'raw'}. Run `python bench.py run` first.")
        return 1
    print(f"{std.label}\n")
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

    cards, std, suites = _score(args)
    if not cards:
        print(f"No raw results in {_results_dir(args) / 'raw'}. Run `python bench.py run` first.")
        return 1
    paths = write_reports(cards, _results_dir(args), std.scoring_dict(), dry_run=args.dry_run,
                          labels={s.name: s.title for s in suites}, standard_label=std.label)
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
                cost += run_cost(rec, m) or 0.0
        total += cost
        print(f"{d.name:<26}{runs:>6} runs  ${cost:.4f}")
    print(f"{'TOTAL':<26}{'':>6}       ${total:.4f}")
    return 0


def cmd_recheck(args: argparse.Namespace) -> int:
    """Re-apply the checkers to saved runs (no API calls). Use after a checker fix."""
    from gmibench.kinds import kind_of
    from gmibench.runner import is_current
    from gmibench.standard import load_standard
    from gmibench.suites import discover

    found = discover()
    tasks = {n: {t["id"]: t for t in s.load_tasks()} for n, s in found.items()}
    timeout = load_standard("latest").protocol.get("coding_timeout_s", 10)
    changed = total = 0
    for f in sorted((_results_dir(args) / "raw").glob("*/*.jsonl")):
        out_lines = []
        for line in f.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            suite = found.get(rec.get("task_set"))
            task = tasks.get(rec.get("task_set"), {}).get(rec.get("task_id"))
            if suite is not None and task is not None and is_current(rec, task) and not rec.get("error"):
                total += 1
                ok, check = kind_of(suite).check(task, suite, rec.get("response") or "",
                                                 rec.get("tool_calls") or [], timeout)
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


# --------------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench.py", description="GMI Open Model Standard benchmark")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="offline fake client; uses results_dryrun/")
    common.add_argument("--results-dir", help="override the results folder")
    std_opt = argparse.ArgumentParser(add_help=False)
    std_opt.add_argument("--standard", default="latest", help="latest (default), dev, or a version like 1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("suites", parents=[std_opt], help="list suites, versions, roles and status")
    p.set_defaults(func=cmd_suites)

    p = sub.add_parser("run", parents=[common, std_opt], help="run suites against models")
    p.add_argument("--models", default="all", help="'all' or comma list of names/IDs from models.yaml")
    p.add_argument("--suites", "--tasks", dest="suites", default="all",
                   help="all, core, stress (or hard), experimental, or a comma list of suite names")
    p.add_argument("--runs", type=int, help="runs per task (default from the standard's protocol)")
    p.add_argument("--concurrency", type=int, help="parallel requests per model (default 4)")
    p.add_argument("--retry-errors", action="store_true", help="re-run recorded runs that ended in an API error")
    p.add_argument("--yes", "-y", action="store_true", help="skip the cost confirmation prompt")
    p.set_defaults(func=cmd_run)

    for name, func, help_ in (("score", cmd_score, "compute scores from raw results"),
                              ("report", cmd_report, "write scorecards, summary and charts")):
        p = sub.add_parser(name, parents=[common, std_opt], help=help_)
        p.add_argument("--runs", type=int, help="expected runs per task for completeness (default from standard)")
        p.set_defaults(func=func)

    p = sub.add_parser("recheck", parents=[common], help="re-grade saved runs with current checkers (no API)")
    p.set_defaults(func=cmd_recheck)

    p = sub.add_parser("spend", parents=[common], help="total USD spent on recorded runs")
    p.set_defaults(func=cmd_spend)

    p = sub.add_parser("generate", help="rebuild tasks.jsonl (and assets) from build.py")
    p.add_argument("--suite", help="comma list of suites (default: all)")
    p.add_argument("--check", action="store_true", help="only compare build.py with tasks.jsonl; write nothing")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("validate", help="check suites, task hashes, reference answers and standards")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("release", help="write standards/vX.Y.yaml pinning the current suites")
    p.add_argument("version", help="new standard version, e.g. 1.1")
    p.add_argument("--core", help="comma list of suites to make core")
    p.add_argument("--stress", help="comma list of suites to make stress")
    p.add_argument("--drop", help="comma list of suites to remove from the standard")
    p.add_argument("--notes", help="one-line summary of the change")
    p.set_defaults(func=cmd_release)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
