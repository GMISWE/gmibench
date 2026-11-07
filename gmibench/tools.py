"""Mock tools for the tool-use task set: schemas, data, and safe implementations."""

from __future__ import annotations

import ast
import json
import operator
from typing import Any, Callable

WEATHER: dict[str, dict[str, Any]] = {
    "paris": {"city": "Paris", "temp_c": 18.0, "condition": "cloudy", "humidity": 71},
    "tokyo": {"city": "Tokyo", "temp_c": 24.0, "condition": "sunny", "humidity": 55},
    "london": {"city": "London", "temp_c": 12.0, "condition": "light rain", "humidity": 88},
    "new york": {"city": "New York", "temp_c": 21.0, "condition": "clear", "humidity": 48},
    "sydney": {"city": "Sydney", "temp_c": 26.0, "condition": "sunny", "humidity": 60},
    "berlin": {"city": "Berlin", "temp_c": 9.0, "condition": "overcast", "humidity": 77},
    "cairo": {"city": "Cairo", "temp_c": 33.0, "condition": "sunny", "humidity": 20},
    "toronto": {"city": "Toronto", "temp_c": 5.0, "condition": "snow", "humidity": 83},
    "mumbai": {"city": "Mumbai", "temp_c": 31.0, "condition": "humid", "humidity": 79},
    "reykjavik": {"city": "Reykjavik", "temp_c": -3.0, "condition": "windy", "humidity": 65},
}

ORDERS: dict[str, dict[str, Any]] = {
    "A1001": {"order_id": "A1001", "ship_to_city": "Paris", "status": "shipped", "total": 58.40, "carrier": "UPS",
              "eta": "2026-11-09", "items": [{"sku": "MUG-01", "qty": 2}, {"sku": "TEA-12", "qty": 1}]},
    "B2002": {"order_id": "B2002", "ship_to_city": "Tokyo", "status": "processing", "total": 149.97, "carrier": None,
              "eta": "2026-11-14", "items": [{"sku": "HDP-77", "qty": 3}]},
    "C3003": {"order_id": "C3003", "ship_to_city": "London", "status": "delivered", "total": 89.50, "carrier": "FedEx",
              "eta": "2026-11-01", "items": [{"sku": "LMP-04", "qty": 1}, {"sku": "BLB-09", "qty": 4}]},
    "D4004": {"order_id": "D4004", "ship_to_city": "New York", "status": "shipped", "total": 312.00, "carrier": "USPS",
              "eta": "2026-11-11", "items": [{"sku": "CHR-22", "qty": 2}]},
    "E5005": {"order_id": "E5005", "ship_to_city": "Berlin", "status": "cancelled", "total": 0.00, "carrier": None,
              "eta": None, "items": [{"sku": "PEN-01", "qty": 10}, {"sku": "INK-02", "qty": 5},
                                     {"sku": "PAD-03", "qty": 3}]},
    "F6006": {"order_id": "F6006", "ship_to_city": "Sydney", "status": "shipped", "total": 1240.75, "carrier": "DHL",
              "eta": "2026-11-20", "items": [{"sku": "LAP-15", "qty": 1}]},
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"],
                             "description": "Temperature unit. Default celsius."},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by its ID. Returns status, total (USD), carrier, eta and items.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "Order ID, e.g. 'A1001'"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic expression. Supports + - * / ** % // and parentheses.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "e.g. '(2+3)*4'"}},
                "required": ["expression"],
            },
        },
    },
]

_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_UNARY_OPS: dict[type, Callable[[Any], Any]] = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_eval(expression: str) -> float:
    """Evaluate a pure arithmetic expression without `eval`.

    Raises:
        ValueError: if the expression has anything other than numbers and operators.
    """
    expression = expression.replace("^", "**").replace(",", "")

    def _ev(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            left, right = _ev(node.left), _ev(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("exponent too large")
            return _BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_ev(node.operand))
        raise ValueError(f"unsupported expression: {ast.dump(node)[:60]}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"invalid expression: {expression!r}") from exc
    return _ev(tree)


def normalize_city(city: Any) -> str:
    """'Tokyo, Japan' -> 'tokyo'. Used by the tool and by the checker."""
    return str(city).split(",")[0].strip().lower()


def get_weather(city: str, unit: str = "celsius") -> dict[str, Any]:
    """Mock weather lookup."""
    row = WEATHER.get(normalize_city(city))
    if row is None:
        return {"error": f"no weather data for city '{city}'"}
    unit = (unit or "celsius").lower()
    temp = row["temp_c"] if unit != "fahrenheit" else round(row["temp_c"] * 9 / 5 + 32, 1)
    return {"city": row["city"], "temperature": temp, "unit": "fahrenheit" if unit == "fahrenheit" else "celsius",
            "condition": row["condition"], "humidity_pct": row["humidity"]}


def lookup_order(order_id: str) -> dict[str, Any]:
    """Mock order lookup."""
    row = ORDERS.get(str(order_id).strip().upper())
    if row is None:
        return {"error": f"order '{order_id}' not found"}
    return dict(row)


def calculate(expression: str) -> dict[str, Any]:
    """Mock calculator backed by `safe_eval`."""
    try:
        value = safe_eval(str(expression))
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        return {"error": str(exc)}
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return {"expression": expression, "result": value}


TOOL_FUNCS: dict[str, Callable[..., dict[str, Any]]] = {
    "get_weather": get_weather,
    "lookup_order": lookup_order,
    "calculate": calculate,
}


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Run a mock tool and return its JSON result string. Never raises."""
    func = TOOL_FUNCS.get(name)
    if func is None:
        return json.dumps({"error": f"unknown tool '{name}'"})
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else dict(arguments or {})
        if not isinstance(args, dict):
            raise ValueError("arguments must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        return json.dumps({"error": f"bad arguments: {exc}"})
    try:
        return json.dumps(func(**args))
    except TypeError as exc:
        return json.dumps({"error": f"bad arguments: {exc}"})


class BasicToolsEnv:
    """Environment for the core tool-use suite: stateless weather / order / calculator tools.

    Tool environments share one shape, so a new suite can bring its own:
      - `schemas`: the OpenAI tool definitions sent to the model
      - `execute(name, arguments) -> str`: run one call, return the JSON result
      - classmethod `check(task, calls, final_answer) -> (passed, details)`
    """

    schemas = TOOL_SCHEMAS

    def execute(self, name: str, arguments: str | dict[str, Any]) -> str:
        return execute_tool(name, arguments)

    @classmethod
    def check(cls, task: dict[str, Any], calls: list[dict[str, Any]], final_answer: str) -> tuple[bool, dict[str, Any]]:
        from .checkers import check_tool_use
        return check_tool_use(task, calls, final_answer)
