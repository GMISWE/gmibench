"""Checker tests: every reference answer passes, and common wrong answers fail."""

from __future__ import annotations

import json

import pytest

from gmibench import checkers
from gmibench.tools import execute_tool, safe_eval


# ----------------------------------------------------------------- coding

def test_all_reference_solutions_pass(coding_tasks):
    assert len(coding_tasks) == 20
    for t in coding_tasks:
        ok, details = checkers.check_coding(t, f"```python\n{t['reference_solution']}```")
        assert ok, (t["id"], details)


def test_coding_wrong_answer_fails(coding_tasks):
    t = next(x for x in coding_tasks if x["entry_point"] == "is_balanced")
    ok, details = checkers.check_coding(t, "```python\ndef is_balanced(s):\n    return True\n```")
    assert not ok and details["reason"] == "tests failed"


def test_coding_timeout(coding_tasks):
    t = next(x for x in coding_tasks if x["entry_point"] == "is_balanced")
    ok, details = checkers.check_coding(t, "```python\ndef is_balanced(s):\n    while True: pass\n```", timeout_s=1)
    assert not ok and "timeout" in details["reason"]


def test_coding_no_code():
    ok, details = checkers.check_coding({"tests": "", "entry_point": "f"}, "I cannot help with that.")
    assert not ok and details["reason"] == "no code found"


def test_extract_code_prefers_block_with_entry_point():
    resp = "<think>```python\ndef f(): pass\n```</think>\nHere:\n```python\nimport os\n```\n```python\ndef target(x):\n    return x\n```"
    code = checkers.extract_code(resp, "target")
    assert code is not None and "def target" in code


def test_main_guard_does_not_run(coding_tasks):
    t = next(x for x in coding_tasks if x["entry_point"] == "is_balanced")
    code = t["reference_solution"] + "\nif __name__ == '__main__':\n    print(input())\n"
    ok, _ = checkers.check_coding(t, f"```python\n{code}```")
    assert ok


# ----------------------------------------------------------------- tool use

def _calls(task):
    return [{"name": c["name"], "arguments": json.dumps(c["args"])} for c in task["reference_calls"]]


def test_all_reference_trajectories_pass(tool_tasks):
    assert len(tool_tasks) == 20
    for t in tool_tasks:
        ok, details = checkers.check_tool_use(t, _calls(t), t["reference_answer"])
        assert ok, (t["id"], details)


def test_reference_answers_match_tool_results(tool_tasks):
    """The expected numbers really come from the mock tools (guards against typos in task data)."""
    for t in tool_tasks:
        results = [json.loads(execute_tool(c["name"], c["args"])) for c in t["reference_calls"]]
        assert not any("error" in r for r in results if t["id"] != "tool-15"), t["id"]


def test_tool_missing_call_fails(tool_tasks):
    t = next(x for x in tool_tasks if x["id"] == "tool-01")
    ok, d = checkers.check_tool_use(t, [], "It is 18 °C in Paris.")
    assert not ok and not d["tool_calls_correct"] and d["answer_numbers_ok"]


def test_tool_wrong_args_fail(tool_tasks):
    t = next(x for x in tool_tasks if x["id"] == "tool-02")  # Tokyo in fahrenheit
    ok, d = checkers.check_tool_use(t, [{"name": "get_weather", "arguments": '{"city": "Tokyo"}'}], "75.2 F")
    assert not ok and not d["tool_calls_correct"]


def test_tool_answer_must_use_result(tool_tasks):
    t = next(x for x in tool_tasks if x["id"] == "tool-04")
    ok, d = checkers.check_tool_use(t, _calls(t), "It cost about $150.")
    assert not ok and d["tool_calls_correct"] and not d["answer_numbers_ok"]


def test_tool_two_lookups_need_two_calls(tool_tasks):
    t = next(x for x in tool_tasks if x["id"] == "tool-11")
    one = [{"name": "lookup_order", "arguments": '{"order_id": "A1001"}'}]
    ok, d = checkers.check_tool_use(t, one, "Total $208.37")
    assert not ok and d["matched_calls"] == 1


@pytest.mark.parametrize("args,ok", [
    ({"city": "tokyo, Japan", "unit": "Fahrenheit"}, True),
    ({"city": "Tokyo", "unit": "celsius"}, False),
    ({"city": "Kyoto", "unit": "fahrenheit"}, False),
])
def test_call_matches_weather(args, ok):
    want = {"name": "get_weather", "args": {"city": "Tokyo", "unit": "fahrenheit"}}
    assert checkers.call_matches(want, {"name": "get_weather", "arguments": json.dumps(args)}) is ok


@pytest.mark.parametrize("expr,ok", [("1234*5678", True), ("5678 * 1234", True), ("1234+5678", False),
                                     ("import os", False)])
def test_call_matches_expression_value(expr, ok):
    want = {"name": "calculate", "args": {"expression_value": 7006652}}
    assert checkers.call_matches(want, {"name": "calculate", "arguments": json.dumps({"expression": expr})}) is ok


def test_numbers_in_handles_commas():
    assert 7006652 in checkers.numbers_in("The result is 7,006,652.")
    assert 1628.89 in checkers.numbers_in("$1,628.89")


def test_safe_eval_rejects_code():
    assert safe_eval("2^10") == 1024
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('true')")
    with pytest.raises(ValueError):
        safe_eval("9**999999")


# ----------------------------------------------------------------- documents

def test_all_ground_truth_passes(doc_tasks):
    assert len(doc_tasks) == 20
    for t in doc_tasks:
        ok, d = checkers.check_document(t, "```json\n" + json.dumps(t["expected"]) + "\n```")
        assert ok and d["line_item_f1"] == 1.0, (t["id"], d)


def test_document_fuzzy_vendor_exact_total_and_date(doc_tasks):
    t = doc_tasks[0]
    gt = t["expected"]
    variant = {"vendor": gt["vendor"].upper().replace(" LLC", ", L.L.C."), "date": gt["date"],
               "total": f"${gt['total']:,.2f}", "line_items": []}
    ok, d = checkers.check_document(t, "Here you go: " + json.dumps(variant))
    assert ok, d
    assert d["line_item_f1"] == 0.0

    wrong_total = dict(variant, total=gt["total"] + 0.01)
    assert not checkers.check_document(t, json.dumps(wrong_total))[0]
    wrong_date = dict(variant, date="2026-1-1")
    assert not checkers.check_document(t, json.dumps(wrong_date))[0]
    wrong_vendor = dict(variant, vendor="Acme Robotics")
    assert not checkers.check_document(t, json.dumps(wrong_vendor))[0]


def test_document_no_json(doc_tasks):
    ok, d = checkers.check_document(doc_tasks[0], "I can't read this image.")
    assert not ok and d["reason"] == "no JSON object found"


def test_vendor_normalisation():
    assert checkers.vendor_matches("Cedar and Pine Furniture", "Cedar & Pine Furniture")
    assert checkers.vendor_matches("Blue Harbor Coffee", "Blue Harbor Coffee Co.")
    assert not checkers.vendor_matches("", "Blue Harbor Coffee Co.")
    assert not checkers.vendor_matches("Silverline Plumbing", "Atlas Hardware Depot")


def test_numbers_in_decimal_comma():
    assert 208.37 in checkers.numbers_in("Die Summe beträgt **208,37 USD**.")
    assert 1234.56 in checkers.numbers_in("1.234,56 EUR")
    assert 7006652 in checkers.numbers_in("7,006,652")


# ----------------------------------------------------------------- hard (stress) sets

def test_every_suite_reference_answer_passes(suites):
    """Each task's reference answer must pass its own checker (the same check `bench.py validate` runs)."""
    from gmibench.kinds import kind_of
    for suite in suites.values():
        kind = kind_of(suite)
        for t in suite.load_tasks():
            assert kind.validate(t, suite) == [], (suite.name, t["id"])


def test_answer_all_needs_every_group(suites):
    suite = suites["tool_use_hard"]
    env_cls = suite.env_class()
    t = next(x for x in suite.load_tasks() if x["id"] == "agent-19")
    calls = _calls(t)
    assert env_cls.check(t, calls, "O-5602 was already returned.")[0]
    assert not env_cls.check(t, calls, "No refund is possible.")[0]


def test_extract_code_unclosed_fence() -> None:
    from gmibench.checkers import extract_code

    resp = "```python\ndef f(x):\n    return x + 1\n"
    assert extract_code(resp, "f") == "def f(x):\n    return x + 1"
