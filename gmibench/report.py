"""Scorecards, cohort summary (Markdown + CSV) and charts."""

from __future__ import annotations

import csv
import os
from datetime import date
from pathlib import Path
from typing import Any

# Suite titles (from each suite.yaml) and the standard's label; set by `write_reports`.
SET_LABELS: dict[str, str] = {}
STANDARD_LABEL = ""
ROLE_NOTE = {"core": "core: sets the tier", "stress": "stress: separate score",
             "experimental": "experimental: not in the tier or the stress score"}


def label(ts: str) -> str:
    return SET_LABELS.get(ts) or ts.replace("_", " ").capitalize()


def set_names(cards: list[dict[str, Any]]) -> list[str]:
    """Suite names in report order (the order the cards were scored in)."""
    seen: dict[str, None] = {}
    for c in cards:
        for ts in c["sets"]:
            seen.setdefault(ts, None)
    return list(seen)


def _f(x: Any, fmt: str = "{:.1f}", none: str = "–") -> str:
    return none if x is None else fmt.format(x)


def _usd(x: float | None) -> str:
    if x is None:
        return "–"
    return f"${x:.5f}" if x < 0.01 else f"${x:.4f}"


def _deploy_count(card: dict[str, Any]) -> str:
    d = card["deployability"]
    return f"{sum(d.values())}/{len(d)}"


def best_for_line(card: dict[str, Any]) -> str:
    """One-line 'best for' derived from the top task set."""
    ts = card.get("best_for")
    if not ts:
        return "Best for: not enough data yet."
    s = card["sets"][ts]
    extra = f", {_usd(s['cost_per_success'])} per successful task" if s.get("cost_per_success") is not None else ""
    return f"Best for: {label(ts).lower()} ({_f(s['pass_rate'])}% pass rate{extra})."


# --------------------------------------------------------------------------- scorecards


def scorecard_md(card: dict[str, Any], thresholds: dict[str, Any]) -> str:
    """Markdown scorecard for one model."""
    o = card["overall"]
    lines = [
        f"# Scorecard: {card['name']}",
        "",
        f"`{card['id']}` · {card.get('lab') or 'lab unknown'} · size class: **{card['size_class']}**",
        "",
        *([f"Scored under **{STANDARD_LABEL}**.", ""] if STANDARD_LABEL else []),
        f"## Tier: {card['tier']}",
        "",
    ]
    if card.get("recommended_for"):
        lines.append("Recommended for: " + ", ".join(label(s) for s in card["recommended_for"])
                     + f" ({card['size_class']} models).")
    if card.get("tier_unmet"):
        lines.append("Not met for the next tier:")
        lines += [f"- {u}" for u in card["tier_unmet"]]
    lines += ["", best_for_line(card), ""]

    lines += ["## 1. Capability", "", "| Suite | Role | Status | Runs | Pass rate | Consistency |",
              "|---|---|---|---|---|---|"]
    for ts, s in card["sets"].items():
        role = s.get("role", "core")
        if role != "core" and s["status"] == "not run":
            continue
        if s["status"] == "n/a":
            lines.append(f"| {label(ts)} | {role} | n/a (no vision) | – | – | – |")
        else:
            lines.append(f"| {label(ts)} | {role} | {s['status']} | {s['runs']}/{s['expected_runs']} | "
                         f"{_f(s['pass_rate'])}% | {_f(s['consistency'])}% |")
    lines += [f"| **All core suites (tier)** | | | {o.get('runs', 0)} | **{_f(o.get('pass_rate'))}%** | "
              f"{_f(o.get('consistency'))}% |"]
    st = card.get("stress") or {}
    if st:
        lines += [f"| **Stress: all stress suites** | | | {st.get('runs', 0)} | **{_f(st.get('pass_rate'))}%** | "
                  f"{_f(st.get('consistency'))}% |"]
    lines += ["", "The tier uses the core suites only. Stress suites are a separate score; "
              "experimental suites are shown but never count.", ""]

    lines += [
        "## 2. Efficiency", "",
        f"- Median output speed: {_f(o.get('tps_median'))} tokens/s",
        f"- Median time to first token: {_f(o.get('ttft_median_s'), '{:.2f}')} s",
        *([f"- Note: {o['non_streamed_runs']} runs could not stream (the endpoint returned an empty stream "
           "with tools), so they ran without streaming and have no TTFT or speed measurement."]
          if o.get("non_streamed_runs") else []),
        f"- Quality per active parameter: {_f(o.get('quality_per_active_b'), '{:.2f}')} pass-rate points per "
        f"active B (active params: {_f(card.get('active_params_b'), '{:g}B', 'unknown')})",
        "",
        "## 3. Agent reliability", "",
        f"- Tool-call accuracy: {_f(o.get('tool_call_accuracy'))}%",
        f"- Mean API retries per task: {_f(o.get('mean_retries_per_task'), '{:.2f}')}",
        f"- Consistency (tasks passed in every run): {_f(o.get('consistency'))}%",
        f"- Error rate (runs that failed after retries): {_f((o.get('error_rate') or 0) * 100, '{:.2f}')}%",
        f"- Truncated runs (hit max_tokens before finishing): {o.get('truncated_runs', 0)}",
        f"- Empty answers (finished, but no visible text; e.g. the answer went to the reasoning channel): "
        f"{o.get('empty_answer_runs', 0)}",
        "",
        "## 4. Unit economics", "",
        f"Prices: ${_f(card.get('input_price_per_m'), '{:g}', '?')} in / "
        f"${_f(card.get('output_price_per_m'), '{:g}', '?')} out per 1M tokens.", "",
        "| Task set | Prompt tokens | Completion tokens | Cost | Cost per successful task |", "|---|---|---|---|---|",
    ]
    for ts, s in card["sets"].items():
        if s["status"] in ("n/a", "not run"):
            continue
        lines.append(f"| {label(ts)} | {s['prompt_tokens']:,} | {s['completion_tokens']:,} | "
                     f"{_usd(s['cost_usd'])} | {_usd(s['cost_per_success'])} |")
    lines += [f"| **All core sets** | {o.get('prompt_tokens', 0):,} | {o.get('completion_tokens', 0):,} | "
              f"{_usd(o.get('cost_usd'))} | **{_usd(o.get('cost_per_success'))}** |", ""]

    labels = {
        "license_osi_or_openmdw": f"License is OSI-approved or OpenMDW ({card.get('license') or 'unknown'})",
        "context_ge_128k": f"Served context ≥ 128k ({_f(card.get('context_length'), '{:,}', 'unknown')} tokens)",
        "precision_documented": f"Served precision documented ({card.get('precision') or 'unknown'})",
        "weights_downloadable": "Weights downloadable",
    }
    lines += ["## 5. Deployability", "", "| Check | Result |", "|---|---|"]
    lines += [f"| {labels[k]} | {'pass' if v else 'fail'} |" for k, v in card["deployability"].items()]
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- summary


def _sort_cost(cards: list[dict[str, Any]], ts: str | None) -> list[dict[str, Any]]:
    def key(c: dict[str, Any]) -> tuple[int, float]:
        s = c["overall"] if ts is None else c["sets"].get(ts, {})
        v = s.get("cost_per_success")
        return (0, v) if v is not None else (1, 0.0)
    return sorted(cards, key=key)


def summary_md(cards: list[dict[str, Any]], dry_run: bool) -> str:
    """Cohort summary: overall table plus one table per workload, sorted by cost per successful task."""
    lines = [f"# GMI Open Model Standard: cohort summary ({date.today().isoformat()})", ""]
    if STANDARD_LABEL:
        lines += [f"Scored under **{STANDARD_LABEL}**.", ""]
    if dry_run:
        lines += ["> **DRY RUN.** These numbers come from the fake client, not from real models.", ""]
    lines += ["## Overall (sorted by cost per successful task)", "",
              "| Model | Tier | Size | Pass rate | Hard pass rate | Consistency | TTFT median | Tokens/s | "
              "Cost / success | Deployability | Best for |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in _sort_cost(cards, None):
        o = c["overall"]
        hard = (c.get("stress") or {}).get("pass_rate")
        lines.append(f"| {c['name']} | {c['tier']} | {c['size_class']} | {_f(o.get('pass_rate'))}% | "
                     f"{_f(hard)}{'%' if hard is not None else ''} | {_f(o.get('consistency'))}% | {_f(o.get('ttft_median_s'), '{:.2f}')} s | "
                     f"{_f(o.get('tps_median'))} | {_usd(o.get('cost_per_success'))} | {_deploy_count(c)} | "
                     f"{label(c['best_for']) if c.get('best_for') else '–'} |")
    lines += ["", "Pass rate, consistency, TTFT and cost use the core suites (these set the tier). "
              "Hard pass rate is the separate stress score over the stress suites."]
    for ts in set_names(cards):
        rows = [c for c in cards if c["sets"].get(ts, {}).get("status") not in (None, "n/a", "not run")]
        if not rows:
            continue
        role = rows[0]["sets"][ts].get("role", "core")
        lines += ["", f"## {label(ts)} ({ROLE_NOTE.get(role, role)}; sorted by cost per successful task)", "",
                  "| Model | Size | Status | Pass rate | Consistency | TTFT median | Cost / success | Recommended |",
                  "|---|---|---|---|---|---|---|---|"]
        for c in _sort_cost(rows, ts):
            s = c["sets"][ts]
            rec = "yes" if ts in c.get("recommended_for", []) else ""
            lines.append(f"| {c['name']} | {c['size_class']} | {s['status']} | {_f(s.get('pass_rate'))}% | "
                         f"{_f(s.get('consistency'))}% | {_f(s.get('ttft_median_s'), '{:.2f}')} s | "
                         f"{_usd(s.get('cost_per_success'))} | {rec} |")
        na = [c["name"] for c in cards if c["sets"].get(ts, {}).get("status") == "n/a"]
        if na:
            lines += ["", f"n/a (not vision-capable): {', '.join(na)}"]
    lines.append("")
    return "\n".join(lines)


CSV_FIELDS = ["model", "model_id", "workload", "tier", "size_class", "status", "runs", "passed_runs", "pass_rate",
              "consistency", "tool_call_accuracy", "error_rate", "mean_retries_per_task", "ttft_median_s",
              "tps_median", "quality_per_active_b", "prompt_tokens", "completion_tokens", "cost_usd",
              "cost_per_success", "deployability_passed"]


def summary_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flat rows for the CSV: one per model and workload, plus 'all'. Sorted by cost within each workload."""
    rows: list[dict[str, Any]] = []
    for ts in ["all", "stress", *set_names(cards)]:
        if ts == "all":
            subset = cards
        elif ts == "stress":
            subset = [c for c in cards if c.get("stress")]
        else:
            subset = [c for c in cards if c["sets"].get(ts, {}).get("status") not in (None, "n/a", "not run")]
        for c in _sort_cost(subset, None if ts in ("all", "stress") else ts):
            s = c["overall"] if ts == "all" else c["stress"] if ts == "stress" else c["sets"][ts]
            rows.append({
                "model": c["name"], "model_id": c["id"], "workload": ts, "tier": c["tier"],
                "size_class": c["size_class"], "status": "ok" if ts == "all" and c["overall"].get("completed_all")
                else s.get("status", "incomplete"),
                **{k: s.get(k) for k in CSV_FIELDS if k in s},
                "quality_per_active_b": c["overall"].get("quality_per_active_b") if ts == "all" else None,
                "deployability_passed": sum(c["deployability"].values()),
            })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})


# --------------------------------------------------------------------------- charts


def write_charts(cards: list[dict[str, Any]], out_dir: Path, thresholds: dict[str, Any] | None = None) -> list[Path]:
    """Three PNG charts: pass rate vs cost/success, TTFT by model, consistency by model."""
    os.environ.setdefault("MPLCONFIGDIR", str(out_dir / ".mplcache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    names = [c["name"] for c in cards]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    pts = [(c["overall"].get("cost_per_success"), c["overall"].get("pass_rate"), c["name"]) for c in cards]
    pts = [p for p in pts if p[0] is not None and p[1] is not None]
    if pts:
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=60, color="#2f6fb3")
        for x, y, n in pts:
            ax.annotate(n, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=8)
        ax.set_xscale("log")
    ax.set_xlabel("Cost per successful task (USD, log scale)")
    ax.set_ylabel("Pass rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Pass rate vs cost per successful task")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = out_dir / "pass_rate_vs_cost.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    prod = ((thresholds or {}).get("tiers") or {}).get("production_ready", {})
    hard_cards = [c for c in cards if (c.get("stress") or {}).get("pass_rate") is not None]
    if hard_cards:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        x = range(len(hard_cards))
        core = [c["overall"].get("pass_rate") or 0 for c in hard_cards]
        hard = [c["stress"]["pass_rate"] for c in hard_cards]
        ax.bar([i - 0.2 for i in x], core, width=0.4, label="Core suites", color="#9db8d9")
        ax.bar([i + 0.2 for i in x], hard, width=0.4, label="Stress suites", color="#2f6fb3")
        ax.set_xticks(list(x), [c["name"] for c in hard_cards], rotation=30, ha="right")
        ax.set_ylabel("Pass rate (%)")
        ax.set_ylim(0, 105)
        ax.set_title("Core vs hard pass rate by model")
        ax.legend(fontsize=8)
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        p = out_dir / "core_vs_hard_pass_rate.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        paths.append(p)

    for key, label, fname, fmt, line in [
        ("ttft_median_s", "Median time to first token (s)", "ttft_by_model.png", "{:.2f}",
         prod.get("max_ttft_median_s")),
        ("consistency", "Consistency (% of tasks passed in every run)", "consistency_by_model.png", "{:.0f}",
         prod.get("min_consistency")),
    ]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        vals = [c["overall"].get(key) or 0 for c in cards]
        bars = ax.bar(names, vals, color="#2f6fb3")
        for b, v in zip(bars, vals):
            ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, v), ha="center", va="bottom", fontsize=8)
        if line is not None:
            ax.axhline(line, color="#c0392b", linestyle="--", linewidth=1,
                       label=f"Production Ready threshold ({line:g})")
            ax.legend(fontsize=8, loc="upper right")
        ax.set_ylabel(label)
        ax.set_title(label.split(" (")[0] + " by model")
        ax.tick_params(axis="x", rotation=30)
        plt.setp(ax.get_xticklabels(), ha="right")
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        p = out_dir / fname
        fig.savefig(p, dpi=150)
        plt.close(fig)
        paths.append(p)
    return paths


def write_reports(cards: list[dict[str, Any]], results_dir: Path, thresholds: dict[str, Any],
                  dry_run: bool = False, labels: dict[str, str] | None = None,
                  standard_label: str = "") -> list[Path]:
    """Write every report file and return their paths."""
    global STANDARD_LABEL
    SET_LABELS.clear()
    SET_LABELS.update(labels or {})
    STANDARD_LABEL = standard_label
    results_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for c in cards:
        p = results_dir / f"scorecard_{c['name']}.md"
        p.write_text(scorecard_md(c, thresholds))
        written.append(p)
    p = results_dir / "summary.md"
    p.write_text(summary_md(cards, dry_run))
    written.append(p)
    p = results_dir / "summary.csv"
    write_csv(p, summary_rows(cards))
    written.append(p)
    written += write_charts(cards, results_dir / "charts", thresholds)
    return written
