"""Shared pass/fail helpers used by the kinds and tool environments."""

from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .tools import normalize_city, safe_eval

PASS_MARKER = "ALL_TESTS_PASSED"
NUM_TOL_ABS = 0.01
VENDOR_MIN_RATIO = 0.85

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)[ \t]*\n(.*?)```", re.DOTALL)
_OPEN_FENCE_RE = re.compile(r"```(?:python3?|py)?[ \t]*\n(.*)\Z", re.DOTALL | re.IGNORECASE)
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def strip_thinking(text: str | None) -> str:
    """Drop inline `<think>...</think>` blocks (and an unclosed leading one)."""
    text = _THINK_RE.sub("", text or "")
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


# --------------------------------------------------------------------------- coding


def extract_code(response: str, entry_point: str | None = None) -> str | None:
    """Pick the code block that defines `entry_point`; fall back to the longest block or raw text."""
    text = strip_thinking(response)
    blocks = [body for lang, body in _FENCE_RE.findall(text) if lang.lower() in ("", "python", "py", "python3")]
    if not blocks:
        # An opening fence with no closing fence (the reply stops after the code).
        m = _OPEN_FENCE_RE.search(text)
        if m:
            blocks = [m.group(1)]
    if entry_point:
        pat = re.compile(rf"^\s*(def|class)\s+{re.escape(entry_point)}\b", re.MULTILINE)
        hits = [b for b in blocks if pat.search(b)]
        if hits:
            return max(hits, key=len)
        if not blocks and pat.search(text):
            return text
    if blocks:
        return max(blocks, key=len)
    return text if re.search(r"^\s*(def|class)\s+\w+", text, re.MULTILINE) else None


def check_coding(task: dict[str, Any], response: str, timeout_s: float = 10.0) -> tuple[bool, dict[str, Any]]:
    """Run the hidden tests against the model's code in a subprocess.

    Passes only if the process exits 0 within `timeout_s` and prints the pass marker.
    """
    code = extract_code(response, task.get("entry_point"))
    if code is None:
        return False, {"reason": "no code found"}
    with tempfile.TemporaryDirectory(prefix="gmibench-") as tmp:
        Path(tmp, "solution.py").write_text(code)
        Path(tmp, "run_tests.py").write_text(
            "from solution import *\n" + task["tests"] + f"\nprint({PASS_MARKER!r})\n")
        try:
            proc = subprocess.run(
                [sys.executable, "-s", "-E", "run_tests.py"], cwd=tmp, capture_output=True, text=True,
                timeout=timeout_s, stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return False, {"reason": f"timeout after {timeout_s}s"}
    passed = proc.returncode == 0 and PASS_MARKER in proc.stdout
    details: dict[str, Any] = {"returncode": proc.returncode}
    if not passed:
        details["reason"] = "tests failed"
        details["stderr_tail"] = proc.stderr.replace(os.path.realpath(tmp), "<tmp>").replace(tmp, "<tmp>")[-600:]
    return passed, details


# --------------------------------------------------------------------------- tool use


def _parse_args(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    try:
        val = json.loads(arguments or "{}")
        return val if isinstance(val, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _close(a: float, b: float, tol: float = NUM_TOL_ABS) -> bool:
    return abs(a - b) <= tol or abs(a - b) <= 1e-6 * max(abs(a), abs(b))


def call_matches(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    """True if an actual call satisfies the expected name and argument constraints."""
    if expected["name"] != actual.get("name"):
        return False
    args = _parse_args(actual.get("arguments"))
    for key, want in (expected.get("args") or {}).items():
        if key == "expression_value":
            try:
                if not _close(float(safe_eval(str(args.get("expression", "")))), float(want)):
                    return False
            except (ValueError, ZeroDivisionError, OverflowError):
                return False
        elif key == "city":
            if normalize_city(args.get("city", "")) != normalize_city(want):
                return False
        elif key == "unit":
            if str(args.get("unit") or "celsius").strip().lower() != str(want).lower():
                return False
        elif key == "order_id":
            if str(args.get("order_id", "")).strip().upper() != str(want).upper():
                return False
        elif str(args.get(key, "")).strip().casefold() != str(want).strip().casefold():
            return False
    return True


def numbers_in(text: str) -> list[float]:
    """All numbers in a text. Handles '1,234.56' and the decimal comma '1.234,56' / '208,37'."""
    cleaned = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    out = [float(x) for x in _NUM_RE.findall(cleaned)]
    # Decimal-comma reading: drop '.' thousands separators, then ',' -> '.'.
    euro = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", text)
    euro = re.sub(r"(?<=\d),(?=\d{1,2}\b)", ".", euro)
    out += [float(x) for x in _NUM_RE.findall(euro) if "." in x]
    return out


def check_tool_use(task: dict[str, Any], calls: list[dict[str, Any]], final_answer: str) -> tuple[bool, dict[str, Any]]:
    """Every expected call must appear (one actual call per expected call) and the answer must use the results."""
    exp = task["expected"]
    used: set[int] = set()
    matched = 0
    for want in exp["calls"]:
        for i, got in enumerate(calls):
            if i not in used and call_matches(want, got):
                used.add(i)
                matched += 1
                break
    calls_ok = matched == len(exp["calls"])
    answer = strip_thinking(final_answer)
    nums = numbers_in(answer)
    numbers_ok = all(any(_close(n, float(w)) for n in nums) for w in exp.get("answer_numbers", []))
    phrases = exp.get("answer_any") or []
    phrase_ok = not phrases or any(p.lower() in answer.lower() for p in phrases)
    for group in exp.get("answer_all") or []:
        phrase_ok = phrase_ok and any(p.lower() in answer.lower() for p in group)
    passed = calls_ok and numbers_ok and phrase_ok
    return passed, {
        "expected_calls": len(exp["calls"]),
        "matched_calls": matched,
        "tool_calls_correct": calls_ok,
        "answer_numbers_ok": numbers_ok,
        "answer_phrase_ok": phrase_ok,
    }


def answer_ok(exp: dict[str, Any], answer: str) -> tuple[bool, bool]:
    nums = numbers_in(answer)
    numbers_ok = all(any(_close(n, float(w)) for n in nums) for w in exp.get("answer_numbers", []))
    low = answer.lower()
    phrase_ok = all(any(p.lower() in low for p in group) for group in exp.get("answer_all") or [])
    return numbers_ok, phrase_ok


# --------------------------------------------------------------------------- documents

_VENDOR_SUFFIXES = {"llc", "inc", "co", "ltd", "gmbh", "corp", "corporation", "company", "limited"}


def normalize_vendor(name: str) -> str:
    """Lower-case, '&' -> 'and', drop punctuation and legal suffixes."""
    s = str(name).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    words = [w for w in s.split() if w not in _VENDOR_SUFFIXES]
    return " ".join(words)


def vendor_matches(got: Any, want: str, min_ratio: float = VENDOR_MIN_RATIO) -> bool:
    """Fuzzy vendor match on normalized names."""
    a, b = normalize_vendor(got or ""), normalize_vendor(want)
    return bool(a) and difflib.SequenceMatcher(None, a, b).ratio() >= min_ratio


def to_number(value: Any) -> float | None:
    """Parse 1234.5, '1,234.50', '$1,234.50' into a float."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = re.sub(r"[^\d.\-]", "", value.replace(",", ""))
        try:
            return float(s)
        except ValueError:
            return None
    return None


def extract_json(response: str) -> dict[str, Any] | None:
    """Find the JSON object in a response (fenced block first, then outermost braces)."""
    text = strip_thinking(response)
    candidates = [body for lang, body in _FENCE_RE.findall(text) if lang.lower() in ("", "json")]
    if "{" in text and "}" in text:
        candidates.append(text[text.index("{"): text.rindex("}") + 1])
    for c in candidates:
        try:
            val = json.loads(c)
        except json.JSONDecodeError:
            continue
        if isinstance(val, dict):
            return val
    return None


def line_item_f1(got: Any, want: list[dict[str, Any]]) -> float:
    """Diagnostic only: F1 of line items matched on amount (±0.01) and fuzzy description."""
    if not isinstance(got, list) or not got:
        return 0.0
    used: set[int] = set()
    hits = 0
    for w in want:
        for i, g in enumerate(got):
            if i in used or not isinstance(g, dict):
                continue
            amt = to_number(g.get("amount"))
            desc_ok = difflib.SequenceMatcher(None, str(g.get("description", "")).lower(),
                                              w["description"].lower()).ratio() >= 0.6
            if amt is not None and abs(amt - w["amount"]) <= 0.01 and desc_ok:
                used.add(i)
                hits += 1
                break
    if hits == 0:
        return 0.0
    p, r = hits / len(got), hits / len(want)
    return round(2 * p * r / (p + r), 4)


def check_document(task: dict[str, Any], response: str) -> tuple[bool, dict[str, Any]]:
    """Exact match on total (to the cent) and ISO date, fuzzy match on vendor."""
    want = task["expected"]
    got = extract_json(response)
    if got is None:
        return False, {"reason": "no JSON object found"}
    total = to_number(got.get("total"))
    total_ok = total is not None and abs(total - float(want["total"])) < 0.005
    date_ok = str(got.get("date", "")).strip() == want["date"]
    vendor_ok = vendor_matches(got.get("vendor"), want["vendor"])
    return total_ok and date_ok and vendor_ok, {
        "total_ok": total_ok, "date_ok": date_ok, "vendor_ok": vendor_ok,
        "line_item_f1": line_item_f1(got.get("line_items"), want["line_items"]),
    }
