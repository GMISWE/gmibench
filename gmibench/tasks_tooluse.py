"""Tool-use task definitions: 20 tasks over get_weather, lookup_order and calculate.

`expected.calls` lists the calls that must appear (name plus argument constraints).
An entry with no `args` only requires the tool to be called at least once.
`expression_value` means the `calculate` expression must evaluate to that number.
The final answer must contain every `answer_numbers` value (tolerance 0.01) and,
if given, at least one `answer_any` phrase (case-insensitive).

`reference_calls` and `reference_answer` are an ideal trajectory. They are never sent
to a model; the dry-run client and the tests use them.
"""

from __future__ import annotations

from typing import Any

TOOL_MAX_TOKENS = 4096

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. Use the tools to get facts and to do arithmetic; "
    "do not guess values. When you have the information, give a short final answer that states the numbers."
)


def _t(i: int, category: str, prompt: str, calls: list[dict[str, Any]], ref_calls: list[dict[str, Any]],
       ref_answer: str, numbers: list[float] | None = None, any_of: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": f"tool-{i:02d}",
        "category": category,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "checker": "tool_calls_and_answer",
        "max_tokens": TOOL_MAX_TOKENS,
        "expected": {"calls": calls, "answer_numbers": numbers or [], "answer_any": any_of or []},
        "reference_calls": ref_calls,
        "reference_answer": ref_answer,
    }


def _w(city: str, unit: str | None = None) -> dict[str, Any]:
    args: dict[str, Any] = {"city": city}
    if unit:
        args["unit"] = unit
    return {"name": "get_weather", "args": args}


def _o(order_id: str) -> dict[str, Any]:
    return {"name": "lookup_order", "args": {"order_id": order_id}}


def _c(expr: str) -> dict[str, Any]:
    return {"name": "calculate", "args": {"expression": expr}}


def build_tool_tasks() -> list[dict[str, Any]]:
    """Return the 20 tool-use tasks as JSON-serialisable dicts."""
    t = [
        _t(1, "single-call", "What is the temperature in Paris right now, in Celsius?",
           [_w("Paris", "celsius")], [_w("Paris", "celsius")], "It is 18 °C in Paris.", [18]),
        _t(2, "single-call", "What's the current temperature in Tokyo in Fahrenheit?",
           [_w("Tokyo", "fahrenheit")], [_w("Tokyo", "fahrenheit")], "Tokyo is 75.2 °F.", [75.2]),
        _t(3, "single-call", "What is the status of order A1001?",
           [_o("A1001")], [_o("A1001")], "Order A1001 has shipped.", None, ["shipped"]),
        _t(4, "single-call", "How much did order B2002 cost in total?",
           [_o("B2002")], [_o("B2002")], "Order B2002 cost $149.97.", [149.97]),
        _t(5, "single-call", "Use the calculator to compute 1234 * 5678.",
           [{"name": "calculate", "args": {"expression_value": 7006652}}], [_c("1234*5678")],
           "1234 * 5678 = 7,006,652.", [7006652]),
        _t(6, "single-call", "Calculate (2^16 - 1) / 5 with the calculator.",
           [{"name": "calculate", "args": {"expression_value": 13107}}], [_c("(2**16-1)/5")],
           "The result is 13107.", [13107]),
        _t(7, "multi-call", "Which is warmer right now, London or Berlin? Give both temperatures in Celsius.",
           [_w("London"), _w("Berlin")], [_w("London"), _w("Berlin")],
           "London is warmer at 12 °C; Berlin is 9 °C.", [12, 9], ["london"]),
        _t(8, "chained", "Look up order C3003 and tell me its total including 8.25% sales tax, rounded to cents.",
           [_o("C3003"), {"name": "calculate"}], [_o("C3003"), _c("89.50*1.0825")],
           "With tax, order C3003 comes to $96.88.", [96.88]),
        _t(9, "single-call", "How hot is it in Cairo in Fahrenheit?",
           [_w("Cairo", "fahrenheit")], [_w("Cairo", "fahrenheit")], "Cairo is 91.4 °F.", [91.4]),
        _t(10, "single-call", "When is order D4004 expected to arrive?",
           [_o("D4004")], [_o("D4004")], "Order D4004 is expected on 2026-11-11.", None,
           ["2026-11-11", "november 11", "nov 11", "11 november", "11 nov", "11/11"]),
        _t(11, "multi-call", "What is the combined total of orders A1001 and B2002?",
           [_o("A1001"), _o("B2002")], [_o("A1001"), _o("B2002"), _c("58.40+149.97")],
           "Together they total $208.37.", [208.37]),
        _t(12, "multi-call", "What is the temperature difference in Celsius between Sydney and Toronto right now?",
           [_w("Sydney"), _w("Toronto")], [_w("Sydney"), _w("Toronto"), _c("26-5")],
           "Sydney is 21 °C warmer than Toronto (26 °C vs 5 °C).", [21]),
        _t(13, "single-call", "Use the calculator: $1000 invested at 5% annual interest, compounded yearly for "
                              "10 years. What is the final balance, rounded to cents?",
           [{"name": "calculate", "args": {"expression_value": 1628.894627}}], [_c("1000*1.05**10")],
           "The final balance is $1628.89.", [1628.89]),
        _t(14, "single-call", "How many units in total (sum of quantities across all items) are in order E5005?",
           [_o("E5005")], [_o("E5005")], "Order E5005 contains 18 units.", [18]),
        _t(15, "error-handling", "What is the status of order Z9999?",
           [_o("Z9999")], [_o("Z9999")], "Order Z9999 was not found.", None,
           ["not found", "couldn't find", "could not find", "no order", "does not exist", "doesn't exist",
            "no record", "unable to find", "not exist"]),
        _t(16, "single-call", "What are the current weather conditions in New York? Include the temperature in Celsius.",
           [_w("New York")], [_w("New York")], "It is clear and 21 °C in New York.", [21], ["clear"]),
        _t(17, "single-call", "Use the calculator to find the average of 17.5, 22.25 and 30.",
           [{"name": "calculate", "args": {"expression_value": 23.25}}], [_c("(17.5+22.25+30)/3")],
           "The average is 23.25.", [23.25]),
        _t(18, "single-call", "Which carrier is shipping order F6006?",
           [_o("F6006")], [_o("F6006")], "Order F6006 ships with DHL.", None, ["dhl"]),
        _t(19, "chained", "Get the current Celsius temperature in Tokyo, then use the calculator to multiply it by 3.",
           [_w("Tokyo"), {"name": "calculate", "args": {"expression_value": 72}}], [_w("Tokyo"), _c("24*3")],
           "24 °C × 3 = 72.", [72]),
        _t(20, "chained", "A customer wants a 15% refund on order B2002. How much should we refund? Round to cents.",
           [_o("B2002"), {"name": "calculate"}], [_o("B2002"), _c("149.97*0.15")],
           "Refund $22.50.", [22.4955]),
    ]
    assert len(t) == 20
    return t
