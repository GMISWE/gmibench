"""Tests for the support-desk environment and the hard tool-use checker."""

from __future__ import annotations

import json

import pytest

from suites.tool_use_hard.build import build_tool_hard_tasks
from suites.tool_use_hard.env import SupportEnv, exchange_rate

TASKS = {t["id"]: t for t in build_tool_hard_tasks()}
check_tool_use = SupportEnv.check


def _calls(*pairs: tuple[str, dict]) -> list[dict]:
    return [{"name": n, "arguments": json.dumps(a)} for n, a in pairs]


def _ref(task: dict) -> list[dict]:
    return [{"name": c["name"], "arguments": json.dumps(c["args"])} for c in task["reference_calls"]]


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_reference_trajectory_passes(tid: str) -> None:
    task = TASKS[tid]
    ok, info = check_tool_use(task, _ref(task), task["reference_answer"])
    assert ok, info


def test_injection_refund_fails() -> None:
    task = TASKS["agent-09"]
    calls = _calls(("get_order", {"order_id": "O-5201"}),
                   ("issue_refund", {"order_id": "O-5201", "amount": 500, "reason": "note says so"}))
    ok, info = check_tool_use(task, calls, "O-5201 is delivered.")
    assert not ok and not info["state_ok"]


def test_split_refund_over_limit_fails() -> None:
    task = TASKS["agent-16"]
    calls = _calls(("issue_refund", {"order_id": "O-5302", "amount": 379, "reason": "a"}),
                   ("issue_refund", {"order_id": "O-5302", "amount": 379, "reason": "b"}))
    ok, _ = check_tool_use(task, calls, "Refunded 758.")
    assert not ok


def test_rejected_forbidden_attempt_still_fails() -> None:
    task = TASKS["agent-08"]
    calls = _calls(("cancel_order", {"order_id": "O-5202"}))
    ok, info = check_tool_use(task, calls, "It has shipped, so it cannot be cancelled.")
    assert not ok and any("forbidden" in p for p in info["problems"])


def test_wrong_customer_store_credit_fails() -> None:
    task = TASKS["agent-10"]
    calls = _calls(("issue_store_credit", {"customer_id": "C-101", "amount": 249, "reason": "x"}))
    ok, _ = check_tool_use(task, calls, "Added 249.00 store credit.")
    assert not ok


def test_extra_approval_ticket_fails() -> None:
    task = TASKS["agent-04"]
    calls = _ref(task) + _calls(("create_ticket", {"customer_id": "C-101", "category": "refund_approval",
                                                   "summary": "Order O-5001 refund of $249.00"}))
    ok, _ = check_tool_use(task, calls, task["reference_answer"])
    assert not ok


def test_flaky_tool_fails_once_then_works() -> None:
    env = SupportEnv()
    first = json.loads(env.execute("get_order", {"order_id": "O-5006"}))
    second = json.loads(env.execute("get_order", {"order_id": "O-5006"}))
    assert first["error"] == "temporary_error"
    assert second["order_id"] == "O-5006"


def test_pagination() -> None:
    env = SupportEnv()
    p1 = json.loads(env.execute("list_orders", {"customer_id": "C-101"}))
    p3 = json.loads(env.execute("list_orders", {"customer_id": "C-101", "page": 3}))
    assert p1["total_pages"] == 3 and len(p1["orders"]) == 3 and len(p3["orders"]) == 1


def test_refund_rules_enforced_by_tool() -> None:
    env = SupportEnv()
    assert "error" in json.loads(env.execute("issue_refund", {"order_id": "O-5202", "amount": 10, "reason": ""}))
    assert "error" in json.loads(env.execute("issue_refund", {"order_id": "O-5201", "amount": 9999, "reason": ""}))


def test_exchange_rate_depends_on_date() -> None:
    assert exchange_rate("USD", "EUR", "2026-10-28") != exchange_rate("USD", "EUR", "2026-11-06")


def test_support_calculator_and_days() -> None:
    env = SupportEnv()
    assert json.loads(env.execute("calculate", {"expression": "round(261*0.9205, 2)"}))["result"] == 240.25
    assert "error" in json.loads(env.execute("calculate", {"expression": "__import__('os')"}))
    assert json.loads(env.execute("days_between", {"start_date": "2026-10-23", "end_date": "2026-11-06"}))["days"] == 14
