"""Scoring math tests with hand-computed expected values."""

from __future__ import annotations

import copy

import pytest

from conftest import make_rec
from gmibench import scoring
from gmibench.config import ModelSpec


def _coding_records():
    # 2 tasks x 3 runs. t1 passes all 3, t2 passes 1 of 3 -> pass rate 4/6, consistency 1/2.
    return [make_rec("t1", r, True) for r in range(3)] + \
           [make_rec("t2", 0, True), make_rec("t2", 1, False), make_rec("t2", 2, False, retries=2)]


def test_score_set_basic(model):
    s = scoring.score_set(_coding_records(), model, expected_runs=6)
    assert s["status"] == "ok"
    assert s["pass_rate"] == pytest.approx(100 * 4 / 6)
    assert s["consistency"] == pytest.approx(50.0)
    # each run: 1000 in * $1/M + 500 out * $2/M = $0.002; 6 runs = $0.012; 4 passes -> $0.003
    assert s["cost_usd"] == pytest.approx(0.012)
    assert s["cost_per_success"] == pytest.approx(0.003)
    assert s["ttft_median_s"] == pytest.approx(0.5)
    assert s["tps_median"] == pytest.approx(100.0)          # 500 tokens / 5 s
    assert s["mean_retries_per_task"] == pytest.approx(1.0)  # (0 + 2) / 2 tasks
    assert s["error_rate"] == 0


def test_score_set_incomplete_and_zero_passes(model):
    recs = [make_rec("t1", 0, False)]
    s = scoring.score_set(recs, model, expected_runs=6)
    assert s["status"] == "incomplete"
    assert s["cost_per_success"] is None


def test_unknown_price_gives_no_cost(model):
    m = copy.copy(model)
    m.output_price_per_m = None
    s = scoring.score_set(_coding_records(), m, expected_runs=6)
    assert s["cost_usd"] is None and s["cost_per_success"] is None


def test_errors_excluded_from_ttft_and_tps(model):
    recs = [make_rec("t1", 0, True, ttft=1.0), make_rec("t1", 1, False, error="boom", ttft=9.0)]
    s = scoring.score_set(recs, model, expected_runs=2)
    assert s["ttft_median_s"] == 1.0
    assert s["error_rate"] == 0.5


def test_tool_call_accuracy(model):
    recs = [make_rec("x", r, ok, "tool_use", tool_ok=ok) for r, ok in enumerate([True, True, False, True])]
    s = scoring.score_set(recs, model, expected_runs=4)
    assert s["tool_call_accuracy"] == pytest.approx(75.0)


def test_quality_per_active_param(model):
    raw = {"coding": _coding_records(), "tool_use": [make_rec("x", r, True, "tool_use", tool_ok=True)
                                                       for r in range(3)]}
    card = scoring.score_model(model, raw, {"coding": 2, "tool_use": 1, "documents": 20}, 3, {"size_classes": {}},
                               not_applicable=["documents"])
    # overall: 7 passes / 9 runs = 77.78%, / 4B active
    assert card["overall"]["pass_rate"] == pytest.approx(700 / 9)
    assert card["overall"]["quality_per_active_b"] == pytest.approx(700 / 9 / 4)
    assert card["overall"]["completed_all"] is True
    assert card["sets"]["documents"]["status"] == "n/a"


def test_deployability(model, thresholds):
    assert all(scoring.deployability(model, thresholds).values())
    m = copy.copy(model)
    m.license, m.context_length, m.precision, m.weights_url = "llama3", 32768, None, None
    assert not any(scoring.deployability(m, thresholds).values())
    m.license = "OpenMDW-1.1"
    assert scoring.deployability(m, thresholds)["license_osi_or_openmdw"]


def test_size_class(model, thresholds):
    assert scoring.size_class(model, thresholds) == "small"
    m = copy.copy(model)
    m.total_params_b = 120
    assert scoring.size_class(m, thresholds) == "mid"
    m.total_params_b = 300
    assert scoring.size_class(m, thresholds) == "large"
    m.total_params_b = None
    assert scoring.size_class(m, thresholds) == "unknown"


# ----------------------------------------------------------------- tiers

def _card(name: str, *, pass_rate=90.0, consistency=90.0, ttft=0.5, err=0.0, complete=True,
          cps=0.001, size="small"):
    return {
        "name": name, "size_class": size,
        "overall": {"pass_rate": pass_rate, "consistency": consistency, "ttft_median_s": ttft,
                    "error_rate": err, "completed_all": complete},
        "sets": {"coding": {"status": "ok", "cost_per_success": cps}, "tool_use": {"status": "n/a"},
                 "documents": {"status": "n/a"}},
    }


def test_tier_ladder(thresholds):
    cards = [
        _card("cheap", cps=0.001),
        _card("pricey", cps=0.002),
        _card("slow", ttft=2.0),
        _card("flaky", err=0.05),
        _card("partial", complete=False),
        _card("weak", pass_rate=60),
        _card("big", cps=0.005, size="large"),
    ]
    out = {c["name"]: c for c in scoring.assign_tiers(cards, thresholds)}
    assert out["cheap"]["tier"] == scoring.TIER_RECOMMENDED and out["cheap"]["recommended_for"] == ["coding"]
    assert out["pricey"]["tier"] == scoring.TIER_PRODUCTION
    assert out["slow"]["tier"] == scoring.TIER_VERIFIED
    assert any("TTFT" in u for u in out["slow"]["tier_unmet"])
    assert out["flaky"]["tier"] == scoring.TIER_NONE
    assert out["partial"]["tier"] == scoring.TIER_NONE
    assert out["weak"]["tier"] == scoring.TIER_VERIFIED
    # Only model in its size class -> cheapest there.
    assert out["big"]["tier"] == scoring.TIER_RECOMMENDED


def test_error_rate_boundary(thresholds):
    just_under = _card("a", err=0.0199)
    at_limit = _card("b", err=0.02, cps=0.0005)
    out = {c["name"]: c for c in scoring.assign_tiers([just_under, at_limit], thresholds)}
    assert out["a"]["tier"] != scoring.TIER_NONE
    assert out["b"]["tier"] == scoring.TIER_NONE


def test_recommended_ignores_non_production_models(thresholds):
    # A cheaper model that fails Production Ready must not block the Recommended badge.
    cards = [_card("ok", cps=0.003), _card("cheap-but-slow", cps=0.0001, ttft=3.0)]
    out = {c["name"]: c for c in scoring.assign_tiers(cards, thresholds)}
    assert out["ok"]["tier"] == scoring.TIER_RECOMMENDED


def test_spec_missing_fields():
    m = ModelSpec(name="x", id="y/x")
    assert "license" in m.missing_fields() and "active_params_b" in m.missing_fields()
