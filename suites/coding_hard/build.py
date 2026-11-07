"""Hard coding tasks (stress set): 20 problems with tight edge cases, performance limits and
bans on shortcuts (eval, re, json). Same format as `suites/coding/build.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from suites.coding.build import PROMPT_TEMPLATE

CODING_HARD_MAX_TOKENS = 32768

_BAN = '''
import re as _re
_src = open("solution.py").read()
'''

_SPECS: list[dict[str, str]] = [
    {
        "id": "hcoding-01", "category": "regex-engine",
        "signature": "regex_match(s: str, p: str) -> bool",
        "spec": "Return True if pattern `p` matches the whole string `s`. Pattern syntax: lowercase letters match "
                "themselves, '.' matches any single character, and a quantifier may follow a letter or '.': "
                "'*' (zero or more), '+' (one or more), '?' (zero or one). Patterns are always valid. "
                "Must not take exponential time on patterns like 'a*a*a*...c'. Do not use the re module.",
        "solution": '''
from functools import lru_cache

def regex_match(s, p):
    @lru_cache(maxsize=None)
    def m(i, j):
        if j == len(p):
            return i == len(s)
        first = i < len(s) and p[j] in (s[i], ".")
        if j + 1 < len(p) and p[j + 1] in "*+?":
            q = p[j + 1]
            if q == "*":
                return m(i, j + 2) or (first and m(i + 1, j))
            if q == "+":
                return first and (m(i + 1, j) or m(i + 1, j + 2))
            return m(i, j + 2) or (first and m(i + 1, j + 2))
        return first and m(i + 1, j + 1)
    return m(0, 0)
''',
        "tests": _BAN + '''
assert not _re.search(r"^\\s*(import\\s+re\\b|from\\s+re\\s+import)", _src, _re.M), "re module is not allowed"
import random
assert regex_match("aa", "a*")
assert not regex_match("aa", "a")
assert regex_match("ab", ".*")
assert regex_match("aab", "c*a*b")
assert not regex_match("mississippi", "mis*is*p*.")
assert regex_match("", "a?b*")
assert not regex_match("", "a+")
assert regex_match("aaa", "a+a")
assert regex_match("ac", "ab?c")
assert not regex_match("a" * 40 + "b", "a*" * 20 + "c")
random.seed(11)
for _ in range(400):
    s = "".join(random.choice("ab") for _ in range(random.randint(0, 8)))
    p = ""
    for _ in range(random.randint(0, 6)):
        p += random.choice("ab.")
        if random.random() < 0.5:
            p += random.choice("*+?")
    assert regex_match(s, p) == bool(_re.fullmatch(p, s)), (s, p)
''',
    },
    {
        "id": "hcoding-02", "category": "parser",
        "signature": "calc(expr: str) -> float",
        "spec": "Evaluate an arithmetic expression containing non-negative integer and decimal literals "
                "(like 3, 2.5, .5), the binary operators + - * / **, unary + and -, parentheses and spaces. "
                "Follow Python's precedence and associativity exactly: ** is right-associative and binds tighter "
                "than a unary minus on its left (so -2**2 == -4) but its right operand may be unary (2**-1 == 0.5); "
                "/ is true division. Return the same value Python would. Do not use eval, exec, compile or ast.",
        "solution": '''
import re

def calc(expr):
    toks = re.findall(r"\\d+\\.\\d*|\\.\\d+|\\d+|\\*\\*|[-+*/()]", expr)
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def take():
        nonlocal pos
        t = toks[pos]
        pos += 1
        return t

    def expr_():
        v = term()
        while peek() in ("+", "-"):
            op = take()
            r = term()
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = unary()
        while peek() in ("*", "/"):
            op = take()
            r = unary()
            v = v * r if op == "*" else v / r
        return v

    def unary():
        if peek() in ("+", "-"):
            op = take()
            v = unary()
            return v if op == "+" else -v
        return power()

    def power():
        base = atom()
        if peek() == "**":
            take()
            return base ** unary()
        return base

    def atom():
        t = take()
        if t == "(":
            v = expr_()
            take()
            return v
        return float(t) if "." in t else int(t)

    return expr_()
''',
        "tests": _BAN + '''
assert not _re.search(r"\\b(eval|exec|compile)\\s*\\(|^\\s*(import\\s+ast|from\\s+ast\\s+import)", _src, _re.M), "eval/exec/compile/ast not allowed"
import math, random
assert calc("1 + 2 * 3") == 7
assert calc("-2**2") == -4
assert calc("2**-1") == 0.5
assert calc("2**3**2") == 512
assert calc("(1+2)*-3") == -9
assert calc("--3") == 3
assert abs(calc("7 / 2 - .5") - 3.0) < 1e-12
random.seed(5)
def gen(d):
    if d == 0 or random.random() < 0.3:
        return str(random.choice([random.randint(0, 20), round(random.uniform(0, 10), 2)]))
    k = random.random()
    if k < 0.15:
        return "-" + gen(d - 1)
    if k < 0.3:
        return "(" + gen(d - 1) + ")"
    if k < 0.4:
        return "(" + gen(d - 1) + ")**" + str(random.randint(0, 3))
    return gen(d - 1) + random.choice([" + ", " - ", " * ", " / "]) + gen(d - 1)
n = 0
while n < 300:
    e = gen(4)
    try:
        want = eval(e)
    except (ZeroDivisionError, OverflowError):
        continue
    if isinstance(want, complex):
        continue
    got = calc(e)
    assert math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-9), (e, got, want)
    n += 1
''',
    },
    {
        "id": "hcoding-03", "category": "dynamic-programming",
        "signature": "lis_length(nums: list[int]) -> int",
        "spec": "Return the length of the longest strictly increasing subsequence. Must handle 200,000 numbers "
                "in well under a second (O(n log n)).",
        "solution": '''
from bisect import bisect_left

def lis_length(nums):
    tails = []
    for x in nums:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
''',
        "tests": '''
import random, time
assert lis_length([]) == 0
assert lis_length([10, 9, 2, 5, 3, 7, 101, 18]) == 4
assert lis_length([7, 7, 7]) == 1
assert lis_length([0, 1, 0, 3, 2, 3]) == 4
random.seed(2)
for _ in range(100):
    a = [random.randint(0, 10) for _ in range(random.randint(0, 12))]
    best = [1] * len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]:
                best[i] = max(best[i], best[j] + 1)
    assert lis_length(a) == (max(best) if a else 0), a
big = [random.randint(0, 10**9) for _ in range(200000)]
t = time.time()
r = lis_length(big)
assert time.time() - t < 3 and 700 < r < 1100, r
''',
    },
    {
        "id": "hcoding-04", "category": "sliding-window",
        "signature": "min_window(s: str, t: str) -> str",
        "spec": "Return the shortest substring of `s` that contains every character of `t` including duplicates "
                "(case-sensitive). If several are equally short, return the leftmost. Return '' if there is none "
                "or if `t` is empty. Must run in linear time for |s| up to 200,000.",
        "solution": '''
from collections import Counter

def min_window(s, t):
    if not t:
        return ""
    need = Counter(t)
    missing = len(t)
    left = 0
    best = (float("inf"), 0, 0)
    for right, ch in enumerate(s, 1):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1
        if missing == 0:
            while need[s[left]] < 0:
                need[s[left]] += 1
                left += 1
            if right - left < best[0]:
                best = (right - left, left, right)
            need[s[left]] += 1
            missing += 1
            left += 1
    return "" if best[0] == float("inf") else s[best[1]:best[2]]
''',
        "tests": '''
import random, time
from collections import Counter
assert min_window("ADOBECODEBANC", "ABC") == "BANC"
assert min_window("a", "a") == "a"
assert min_window("a", "aa") == ""
assert min_window("abc", "") == ""
assert min_window("aaflslflsldkalskaaa", "aaa") == "aaa"
def brute(s, t):
    if not t:
        return ""
    need = Counter(t)
    for L in range(len(t), len(s) + 1):
        for i in range(len(s) - L + 1):
            if not need - Counter(s[i:i + L]):
                return s[i:i + L]
    return ""
random.seed(4)
for _ in range(300):
    s = "".join(random.choice("abcA") for _ in range(random.randint(0, 12)))
    t = "".join(random.choice("abcA") for _ in range(random.randint(0, 4)))
    assert min_window(s, t) == brute(s, t), (s, t)
big = "".join(random.choice("abcdefghij") for _ in range(200000)) + "XYZ"
t0 = time.time()
assert min_window(big, "ZYX") == "XYZ"
assert time.time() - t0 < 3
''',
    },
    {
        "id": "hcoding-05", "category": "formatting",
        "signature": "justify(words: list[str], width: int) -> list[str]",
        "spec": "Full text justification. Pack as many words as fit on each line (words separated by at least one "
                "space). Pad every line to exactly `width` characters. On each line except the last, distribute "
                "extra spaces as evenly as possible between words; if they do not divide evenly, the leftmost gaps "
                "get more. A line with a single word is left-justified and padded on the right. The last line is "
                "left-justified with single spaces and padded on the right. Every word is at most `width` long.",
        "solution": '''
def justify(words, width):
    lines, cur, cur_len = [], [], 0
    for w in words:
        if cur and cur_len + len(cur) + len(w) > width:
            lines.append(cur)
            cur, cur_len = [], 0
        cur.append(w)
        cur_len += len(w)
    out = []
    for line in lines:
        if len(line) == 1:
            out.append(line[0].ljust(width))
            continue
        gaps = len(line) - 1
        spaces = width - sum(map(len, line))
        q, r = divmod(spaces, gaps)
        s = ""
        for i, w in enumerate(line[:-1]):
            s += w + " " * (q + (1 if i < r else 0))
        out.append(s + line[-1])
    if cur:
        out.append(" ".join(cur).ljust(width))
    return out
''',
        "tests": '''
assert justify(["This", "is", "an", "example", "of", "text", "justification."], 16) == [
    "This    is    an", "example  of text", "justification.  "]
assert justify(["What", "must", "be", "acknowledgment", "shall", "be"], 16) == [
    "What   must   be", "acknowledgment  ", "shall be        "]
assert justify(["Science", "is", "what", "we", "understand", "well", "enough", "to", "explain", "to", "a",
                "computer.", "Art", "is", "everything", "else", "we", "do"], 20) == [
    "Science  is  what we", "understand      well", "enough to explain to", "a  computer.  Art is",
    "everything  else  we", "do                  "]
assert justify(["a"], 3) == ["a  "]
assert justify(["ab", "cd", "ef"], 5) == ["ab cd", "ef   "]
assert justify(["a", "b", "c", "d"], 7) == ["a b c d"]
''',
    },
    {
        "id": "hcoding-06", "category": "search",
        "signature": "solve_sudoku(grid: list[list[int]]) -> list[list[int]]",
        "spec": "Solve a 9x9 Sudoku. `grid` holds digits 1-9 and 0 for empty cells and has exactly one solution. "
                "Return the solved grid as a list of 9 lists of 9 ints. Must solve very hard puzzles in under "
                "2 seconds.",
        "solution": '''
def solve_sudoku(grid):
    g = [row[:] for row in grid]
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empty = []
    for r in range(9):
        for c in range(9):
            v = g[r][c]
            if v:
                rows[r].add(v); cols[c].add(v); boxes[r // 3 * 3 + c // 3].add(v)
            else:
                empty.append((r, c))

    def search():
        if not empty:
            return True
        best_i, best_opts = None, None
        for i, (r, c) in enumerate(empty):
            opts = [v for v in range(1, 10)
                    if v not in rows[r] and v not in cols[c] and v not in boxes[r // 3 * 3 + c // 3]]
            if best_opts is None or len(opts) < len(best_opts):
                best_i, best_opts = i, opts
                if len(opts) <= 1:
                    break
        r, c = empty.pop(best_i)
        b = r // 3 * 3 + c // 3
        for v in best_opts:
            g[r][c] = v
            rows[r].add(v); cols[c].add(v); boxes[b].add(v)
            if search():
                return True
            rows[r].discard(v); cols[c].discard(v); boxes[b].discard(v)
        g[r][c] = 0
        empty.insert(best_i, (r, c))
        return False

    search()
    return g
''',
        "tests": '''
import time
def parse(s):
    return [[int(s[r * 9 + c]) for c in range(9)] for r in range(9)]
def valid(sol, puzzle):
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] and sol[r][c] != puzzle[r][c]:
                return False
    groups = [sol[r] for r in range(9)] + [[sol[r][c] for r in range(9)] for c in range(9)]
    groups += [[sol[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)] for br in (0, 3, 6) for bc in (0, 3, 6)]
    return all(sorted(g) == list(range(1, 10)) for g in groups)
easy = parse("530070000600195000098000060800060003400803001700020006060000280000419005000080079")
assert valid(solve_sudoku(easy), easy)
for s in ["800000000003600000070090200050007000000045700000100030001000068008500010090000400",
          "000000010400000000020000000000050407008000300001090000300400200050100000000806000"]:
    p = parse(s)
    t = time.time()
    sol = solve_sudoku(p)
    assert valid(sol, p)
    assert time.time() - t < 4
''',
    },
    {
        "id": "hcoding-07", "category": "graphs",
        "signature": "topo_order(n: int, edges: list[tuple[int, int]]) -> list[int] | None",
        "spec": "Nodes are 0..n-1 and an edge (u, v) means u must come before v. Return the lexicographically "
                "smallest topological order, or None if the graph has a cycle. Duplicate edges may appear. "
                "Must handle 100,000 nodes and 200,000 edges quickly.",
        "solution": '''
import heapq

def topo_order(n, edges):
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v in edges:
        adj[u].append(v)
        indeg[v] += 1
    heap = [i for i in range(n) if indeg[i] == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        u = heapq.heappop(heap)
        out.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(heap, v)
    return out if len(out) == n else None
''',
        "tests": '''
import random, time
assert topo_order(3, []) == [0, 1, 2]
assert topo_order(4, [(3, 0), (2, 0)]) == [1, 2, 3, 0]
assert topo_order(2, [(0, 1), (1, 0)]) is None
assert topo_order(3, [(1, 2), (1, 2), (0, 2)]) == [0, 1, 2]
assert topo_order(1, [(0, 0)]) is None
assert topo_order(5, [(4, 1), (1, 0), (3, 2)]) == [3, 2, 4, 1, 0]
random.seed(9)
n = 100000
perm = list(range(n)); random.shuffle(perm)
edges = []
for _ in range(200000):
    a, b = sorted(random.sample(range(n), 2))
    edges.append((perm[a], perm[b]))
t = time.time()
order = topo_order(n, edges)
assert time.time() - t < 4
pos = {v: i for i, v in enumerate(order)}
assert len(order) == n and all(pos[u] < pos[v] for u, v in edges)
''',
    },
    {
        "id": "hcoding-08", "category": "parser",
        "signature": "parse_json(text: str) -> object",
        "spec": "Parse a JSON document (RFC 8259) into Python objects: object -> dict, array -> list, string -> str, "
                "number -> int if it has no fraction or exponent else float, true/false/null -> True/False/None. "
                "Support whitespace, all string escapes including \\\\uXXXX (no surrogate pairs needed), negative "
                "numbers and exponents. Raise ValueError for invalid input, including trailing commas, single quotes, "
                "leading zeros like 01, a bare '-', '1.', unterminated strings and trailing characters. "
                "Do not use the json module.",
        "solution": '''
def parse_json(text):
    i = 0
    n = len(text)

    def ws():
        nonlocal i
        while i < n and text[i] in " \\t\\n\\r":
            i += 1

    def err(msg="invalid JSON"):
        raise ValueError(f"{msg} at {i}")

    def value():
        nonlocal i
        ws()
        if i >= n:
            err()
        ch = text[i]
        if ch == "{":
            return obj()
        if ch == "[":
            return arr()
        if ch == '"':
            return string()
        for lit, val in (("true", True), ("false", False), ("null", None)):
            if text.startswith(lit, i):
                i += len(lit)
                return val
        if ch == "-" or ch.isdigit():
            return number()
        err()

    def obj():
        nonlocal i
        i += 1
        out = {}
        ws()
        if i < n and text[i] == "}":
            i += 1
            return out
        while True:
            ws()
            if i >= n or text[i] != '"':
                err("expected key")
            k = string()
            ws()
            if i >= n or text[i] != ":":
                err("expected :")
            i += 1
            out[k] = value()
            ws()
            if i < n and text[i] == ",":
                i += 1
                continue
            if i < n and text[i] == "}":
                i += 1
                return out
            err()

    def arr():
        nonlocal i
        i += 1
        out = []
        ws()
        if i < n and text[i] == "]":
            i += 1
            return out
        while True:
            out.append(value())
            ws()
            if i < n and text[i] == ",":
                i += 1
                continue
            if i < n and text[i] == "]":
                i += 1
                return out
            err()

    def string():
        nonlocal i
        i += 1
        buf = []
        esc = {'"': '"', "\\\\": "\\\\", "/": "/", "b": "\\b", "f": "\\f", "n": "\\n", "r": "\\r", "t": "\\t"}
        while True:
            if i >= n:
                err("unterminated string")
            ch = text[i]
            if ch == '"':
                i += 1
                return "".join(buf)
            if ch == "\\\\":
                i += 1
                if i >= n:
                    err()
                e = text[i]
                if e in esc:
                    buf.append(esc[e]); i += 1
                elif e == "u":
                    h = text[i + 1:i + 5]
                    if len(h) != 4 or any(c not in "0123456789abcdefABCDEF" for c in h):
                        err("bad unicode escape")
                    buf.append(chr(int(h, 16))); i += 5
                else:
                    err("bad escape")
            elif ord(ch) < 0x20:
                err("control character")
            else:
                buf.append(ch); i += 1

    def number():
        nonlocal i
        start = i
        if text[i] == "-":
            i += 1
        if i >= n or not text[i].isdigit():
            err()
        if text[i] == "0":
            i += 1
            if i < n and text[i].isdigit():
                err("leading zero")
        else:
            while i < n and text[i].isdigit():
                i += 1
        is_float = False
        if i < n and text[i] == ".":
            is_float = True
            i += 1
            if i >= n or not text[i].isdigit():
                err()
            while i < n and text[i].isdigit():
                i += 1
        if i < n and text[i] in "eE":
            is_float = True
            i += 1
            if i < n and text[i] in "+-":
                i += 1
            if i >= n or not text[i].isdigit():
                err()
            while i < n and text[i].isdigit():
                i += 1
        s = text[start:i]
        return float(s) if is_float else int(s)

    v = value()
    ws()
    if i != n:
        err("trailing characters")
    return v
''',
        "tests": '''
import sys
assert "json" not in sys.modules, "the json module is not allowed"
import json
docs = ['{}', '[]', '0', '-0.5E-2', '1e3', '"a\\\\n\\\\t\\\\"\\\\\\\\\\\\/\\\\u00e9z"', 'true', 'null',
        '{"a": [1, 2.5, {"b": null}], "c": "x y", "d": false, "e": -12}',
        ' \\n [ 1 , [ ] , { } , "" ] \\t', '{"nested": {"deep": [[[[1]]]]}, "k": 123456789012345678901}']
for d in docs:
    got = parse_json(d)
    want = json.loads(d)
    assert got == want and type(got) == type(want), (d, got, want)
assert type(parse_json("10")) is int and type(parse_json("10.0")) is float
for bad in ["", "[1,]", "{'a': 1}", "01", "-", "1.", "[1 2]", '{"a" 1}', "tru", '"abc', "[1]x", '{"a":1,}', "+1",
            ".5", '"\\\\x"', "[", "nul"]:
    try:
        parse_json(bad)
    except ValueError:
        continue
    raise AssertionError("accepted invalid JSON: " + repr(bad))
''',
    },
    {
        "id": "hcoding-09", "category": "search",
        "signature": "count_n_queens(n: int) -> int",
        "spec": "Return the number of ways to place n non-attacking queens on an n x n board. Must return the "
                "answer for n = 11 in under 2 seconds.",
        "solution": '''
def count_n_queens(n):
    full = (1 << n) - 1

    def go(cols, d1, d2):
        if cols == full:
            return 1
        total = 0
        free = full & ~(cols | d1 | d2)
        while free:
            bit = free & -free
            free ^= bit
            total += go(cols | bit, ((d1 | bit) << 1) & full, (d2 | bit) >> 1)
        return total

    return go(0, 0, 0) if n > 0 else 1
''',
        "tests": '''
import time
expected = [1, 1, 0, 0, 2, 10, 4, 40, 92, 352, 724, 2680]
for n in range(1, 11):
    assert count_n_queens(n) == expected[n], n
t = time.time()
assert count_n_queens(11) == 2680
assert time.time() - t < 4
''',
    },
    {
        "id": "hcoding-10", "category": "dynamic-programming",
        "signature": "wildcard_match(s: str, p: str) -> bool",
        "spec": "Return True if pattern `p` matches all of `s`. '?' matches exactly one character and '*' matches any "
                "sequence, including the empty one. Other characters match themselves. Must handle |s| = 2000 and "
                "|p| = 1000 with many '*' in under a second.",
        "solution": '''
def wildcard_match(s, p):
    i = j = 0
    star = -1
    mark = 0
    while i < len(s):
        if j < len(p) and (p[j] == "?" or p[j] == s[i]):
            i += 1; j += 1
        elif j < len(p) and p[j] == "*":
            star, mark = j, i
            j += 1
        elif star != -1:
            j = star + 1
            mark += 1
            i = mark
        else:
            return False
    while j < len(p) and p[j] == "*":
        j += 1
    return j == len(p)
''',
        "tests": '''
import random, re, time
assert not wildcard_match("aa", "a")
assert wildcard_match("aa", "*")
assert not wildcard_match("cb", "?a")
assert wildcard_match("adceb", "*a*b")
assert not wildcard_match("acdcb", "a*c?b")
assert wildcard_match("", "***")
assert not wildcard_match("", "?")
random.seed(8)
for _ in range(500):
    s = "".join(random.choice("ab") for _ in range(random.randint(0, 8)))
    p = "".join(random.choice("ab?*") for _ in range(random.randint(0, 6)))
    want = re.fullmatch("".join(".*" if c == "*" else "." if c == "?" else c for c in p), s, re.S) is not None
    assert wildcard_match(s, p) == want, (s, p)
t = time.time()
assert not wildcard_match("a" * 2000, "*" + "a*" * 500 + "b")
assert wildcard_match("ab" * 1000, "*" + "a*b" * 499 + "*")
assert time.time() - t < 3
''',
    },
    {
        "id": "hcoding-11", "category": "dates",
        "signature": "business_days(start: str, end: str, holidays: list[str]) -> int",
        "spec": "Dates are ISO strings 'YYYY-MM-DD'. Count the weekdays (Monday to Friday) d with start <= d < end "
                "that are not in `holidays`. If end < start, return the negative of business_days(end, start, holidays). "
                "Holidays may repeat or fall on weekends. Must be fast for ranges spanning 400 years.",
        "solution": '''
import datetime as dt

def business_days(start, end, holidays):
    a, b = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    if b < a:
        return -business_days(end, start, holidays)
    days = (b - a).days
    full, rem = divmod(days, 7)
    count = full * 5
    for k in range(rem):
        if (a + dt.timedelta(days=full * 7 + k)).weekday() < 5:
            count += 1
    for h in set(holidays):
        d = dt.date.fromisoformat(h)
        if a <= d < b and d.weekday() < 5:
            count -= 1
    return count
''',
        "tests": '''
import datetime as dt, random, time
assert business_days("2026-11-02", "2026-11-09", []) == 5
assert business_days("2026-11-07", "2026-11-09", []) == 0
assert business_days("2026-11-02", "2026-11-09", ["2026-11-03", "2026-11-03", "2026-11-07"]) == 4
assert business_days("2026-11-09", "2026-11-02", []) == -5
assert business_days("2026-11-04", "2026-11-04", []) == 0
random.seed(6)
base = dt.date(2025, 1, 1)
for _ in range(200):
    a = base + dt.timedelta(days=random.randint(0, 800))
    b = a + dt.timedelta(days=random.randint(-60, 60))
    hol = [(base + dt.timedelta(days=random.randint(0, 860))).isoformat() for _ in range(random.randint(0, 30))]
    lo, hi = min(a, b), max(a, b)
    want = sum(1 for k in range((hi - lo).days) if (lo + dt.timedelta(days=k)).weekday() < 5
               and (lo + dt.timedelta(days=k)).isoformat() not in set(hol))
    if b < a:
        want = -want
    assert business_days(a.isoformat(), b.isoformat(), hol) == want, (a, b, hol)
t = time.time()
assert business_days("1800-01-01", "2200-01-01", []) == 104355
assert time.time() - t < 2
''',
    },
    {
        "id": "hcoding-12", "category": "dynamic-programming",
        "signature": "num_decodings(s: str) -> int",
        "spec": "A message of letters A-Z was encoded as numbers 'A'->1 ... 'Z'->26 and concatenated. The string `s` "
                "contains digits and '*', where '*' stands for any digit 1-9 (never 0). Return the number of ways to "
                "decode `s`, modulo 1_000_000_007. Must handle |s| = 100,000.",
        "solution": '''
def num_decodings(s):
    M = 10**9 + 7

    def one(c):
        return 9 if c == "*" else (0 if c == "0" else 1)

    def two(a, b):
        if a == "*":
            if b == "*":
                return 15
            return 2 if b <= "6" else 1
        if a == "1":
            return 9 if b == "*" else 1
        if a == "2":
            return 6 if b == "*" else (1 if b <= "6" else 0)
        return 0

    prev2, prev1 = 1, one(s[0]) if s else 1
    for i in range(1, len(s)):
        cur = (one(s[i]) * prev1 + two(s[i - 1], s[i]) * prev2) % M
        prev2, prev1 = prev1, cur
    return prev1 % M
''',
        "tests": '''
import time, itertools
assert num_decodings("*") == 9
assert num_decodings("1*") == 18
assert num_decodings("2*") == 15
assert num_decodings("**") == 96
assert num_decodings("0") == 0
assert num_decodings("*0") == 2
assert num_decodings("3*") == 9
assert num_decodings("226") == 3
assert num_decodings("06") == 0
assert num_decodings("10") == 1
def brute(s):
    total = 0
    stars = [i for i, c in enumerate(s) if c == "*"]
    for fill in itertools.product("123456789", repeat=len(stars)):
        t = list(s)
        for i, d in zip(stars, fill):
            t[i] = d
        t = "".join(t)
        ways = [1] + [0] * len(t)
        for i in range(1, len(t) + 1):
            if t[i - 1] != "0":
                ways[i] += ways[i - 1]
            if i >= 2 and 10 <= int(t[i - 2:i]) <= 26 and t[i - 2] != "0":
                ways[i] += ways[i - 2]
        total += ways[-1]
    return total
for s in ["*1*1*0", "1*72*", "**0*", "2*6*", "*10*"]:
    assert num_decodings(s) == brute(s) % (10**9 + 7), s
t = time.time()
r = num_decodings("*1" * 50000)
assert isinstance(r, int) and 0 <= r < 10**9 + 7
assert time.time() - t < 3
''',
    },
    {
        "id": "hcoding-13", "category": "data-structures",
        "signature": "median_sliding_window(nums: list[int], k: int) -> list[float]",
        "spec": "Return the median of every window of size k as it slides one step at a time from left to right "
                "(len(nums) - k + 1 values, each a float). For even k the median is the mean of the two middle values. "
                "Must handle 100,000 numbers with k = 5000 in under 3 seconds (re-sorting every window is too slow).",
        "solution": '''
from bisect import bisect_left, insort

def median_sliding_window(nums, k):
    win = sorted(nums[:k])
    out = []
    for i in range(k, len(nums) + 1):
        m = (win[k // 2] + win[(k - 1) // 2]) / 2
        out.append(float(m))
        if i == len(nums):
            break
        del win[bisect_left(win, nums[i - k])]
        insort(win, nums[i])
    return out
''',
        "tests": '''
import random, time, statistics
assert median_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]
assert median_sliding_window([1, 2, 3, 4, 2, 3, 1, 4, 2], 3) == [2.0, 3.0, 3.0, 3.0, 2.0, 3.0, 2.0]
assert median_sliding_window([2147483647, 2147483647], 2) == [2147483647.0]
assert median_sliding_window([5], 1) == [5.0]
random.seed(1)
for _ in range(50):
    a = [random.randint(-5, 5) for _ in range(random.randint(1, 15))]
    k = random.randint(1, len(a))
    want = [float(statistics.median(a[i:i + k])) for i in range(len(a) - k + 1)]
    assert median_sliding_window(a, k) == want, (a, k)
big = [random.randint(-10**6, 10**6) for _ in range(100000)]
t = time.time()
r = median_sliding_window(big, 5000)
assert len(r) == 95001 and time.time() - t < 5
assert r[500] == float(statistics.median(big[500:5500]))
''',
    },
    {
        "id": "hcoding-14", "category": "graphs",
        "signature": "alien_order(words: list[str]) -> str",
        "spec": "`words` is a list sorted lexicographically by an unknown alphabet over lowercase letters. Return the "
                "lexicographically smallest (by normal a-z order) string containing every distinct letter that appears "
                "in `words` exactly once, in an order consistent with the list. Return '' if no order is consistent "
                "(a cycle, or a word followed by its own proper prefix such as ['abc', 'ab']).",
        "solution": '''
import heapq

def alien_order(words):
    letters = {c for w in words for c in w}
    adj = {c: set() for c in letters}
    indeg = {c: 0 for c in letters}
    for a, b in zip(words, words[1:]):
        for x, y in zip(a, b):
            if x != y:
                if y not in adj[x]:
                    adj[x].add(y)
                    indeg[y] += 1
                break
        else:
            if len(a) > len(b):
                return ""
    heap = [c for c in letters if indeg[c] == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        c = heapq.heappop(heap)
        out.append(c)
        for d in adj[c]:
            indeg[d] -= 1
            if indeg[d] == 0:
                heapq.heappush(heap, d)
    return "".join(out) if len(out) == len(letters) else ""
''',
        "tests": '''
assert alien_order(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"
assert alien_order(["z", "x"]) == "zx"
assert alien_order(["z", "x", "z"]) == ""
assert alien_order(["abc", "ab"]) == ""
assert alien_order(["ab", "abc"]) == "abc"
assert alien_order(["z", "z"]) == "z"
assert alien_order(["ba", "bc", "ac", "cab"]) == "bac"
assert alien_order([]) == ""
assert alien_order(["dz", "dy", "q"]) == "dqzy"
''',
    },
    {
        "id": "hcoding-15", "category": "geometry",
        "signature": "max_points(points: list[tuple[int, int]]) -> int",
        "spec": "Return the maximum number of points that lie on one straight line. Coordinates are integers and "
                "points may be duplicated (duplicates each count). Use exact arithmetic (no float slopes). "
                "An empty list returns 0.",
        "solution": '''
from math import gcd
from collections import Counter

def max_points(points):
    n = len(points)
    if n <= 2:
        return n
    best = 0
    for i in range(n):
        slopes = Counter()
        dup = 1
        for j in range(i + 1, n):
            dx = points[j][0] - points[i][0]
            dy = points[j][1] - points[i][1]
            if dx == 0 and dy == 0:
                dup += 1
                continue
            g = gcd(dx, dy)
            dx, dy = dx // g, dy // g
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            slopes[(dx, dy)] += 1
        best = max(best, dup + (max(slopes.values()) if slopes else 0))
    return best
''',
        "tests": '''
import random
from itertools import combinations
assert max_points([]) == 0
assert max_points([(1, 1)]) == 1
assert max_points([(1, 1), (2, 2), (3, 3)]) == 3
assert max_points([(1, 1), (3, 2), (5, 3), (4, 1), (2, 3), (1, 4)]) == 4
assert max_points([(0, 0), (0, 0), (0, 0)]) == 3
assert max_points([(0, 0), (94911151, 94911150), (94911152, 94911151)]) == 2
assert max_points([(1, 1), (1, 1), (2, 3)]) == 3
def brute(pts):
    if len(pts) <= 2:
        return len(pts)
    best = 0
    for a, b in combinations(range(len(pts)), 2):
        (x1, y1), (x2, y2) = pts[a], pts[b]
        if (x1, y1) == (x2, y2):
            cnt = sum(1 for p in pts if p == (x1, y1))
        else:
            cnt = sum(1 for (x, y) in pts if (x2 - x1) * (y - y1) == (y2 - y1) * (x - x1))
        best = max(best, cnt)
    return best
random.seed(12)
for _ in range(150):
    pts = [(random.randint(-3, 3), random.randint(-3, 3)) for _ in range(random.randint(0, 9))]
    assert max_points(pts) == brute(pts), pts
''',
    },
    {
        "id": "hcoding-16", "category": "binary-search",
        "signature": "kth_smallest_distance(nums: list[int], k: int) -> int",
        "spec": "Among all pairs i < j, the distance is |nums[i] - nums[j]|. Return the k-th smallest distance "
                "(k is 1-based). Must handle 20,000 numbers (about 200 million pairs) in under 2 seconds.",
        "solution": '''
def kth_smallest_distance(nums, k):
    a = sorted(nums)
    n = len(a)

    def count(d):
        c = left = 0
        for right in range(n):
            while a[right] - a[left] > d:
                left += 1
            c += right - left
        return c

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
''',
        "tests": '''
import random, time
assert kth_smallest_distance([1, 3, 1], 1) == 0
assert kth_smallest_distance([1, 1, 1], 2) == 0
assert kth_smallest_distance([1, 6, 1], 3) == 5
assert kth_smallest_distance([62, 100, 4], 2) == 58
random.seed(13)
for _ in range(60):
    a = [random.randint(0, 30) for _ in range(random.randint(2, 12))]
    d = sorted(abs(a[i] - a[j]) for i in range(len(a)) for j in range(i + 1, len(a)))
    k = random.randint(1, len(d))
    assert kth_smallest_distance(a, k) == d[k - 1], (a, k)
big = [random.randint(0, 10**6) for _ in range(20000)]
t = time.time()
r = kth_smallest_distance(big, 100000000)
assert time.time() - t < 6 and 0 < r < 10**6
''',
    },
    {
        "id": "hcoding-17", "category": "union-find",
        "signature": "islands_after_adds(rows: int, cols: int, positions: list[tuple[int, int]]) -> list[int]",
        "spec": "Start with a rows x cols grid of water. Each position turns that cell into land (adding a cell "
                "that is already land changes nothing). After each addition, record the number of islands "
                "(groups of land cells connected up, down, left or right). Return the list of counts. Must handle "
                "a 300 x 300 grid with 60,000 additions in under 2 seconds.",
        "solution": '''
def islands_after_adds(rows, cols, positions):
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    out, count = [], 0
    for r, c in positions:
        key = r * cols + c
        if key in parent:
            out.append(count)
            continue
        parent[key] = key
        count += 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nk = nr * cols + nc
                if nk in parent:
                    a, b = find(key), find(nk)
                    if a != b:
                        parent[a] = b
                        count -= 1
        out.append(count)
    return out
''',
        "tests": '''
import random, time
assert islands_after_adds(3, 3, [(0, 0), (0, 1), (1, 2), (2, 1)]) == [1, 1, 2, 3]
assert islands_after_adds(1, 1, [(0, 0), (0, 0)]) == [1, 1]
assert islands_after_adds(2, 2, [(0, 0), (1, 1), (0, 1)]) == [1, 2, 1]
def brute(R, C, pos):
    land, out = set(), []
    for p in pos:
        land.add(p)
        seen, n = set(), 0
        for cell in land:
            if cell in seen:
                continue
            n += 1
            stack = [cell]
            seen.add(cell)
            while stack:
                r, c = stack.pop()
                for q in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if q in land and q not in seen:
                        seen.add(q); stack.append(q)
        out.append(n)
    return out
random.seed(14)
for _ in range(40):
    R, C = random.randint(1, 5), random.randint(1, 5)
    pos = [(random.randrange(R), random.randrange(C)) for _ in range(random.randint(0, 15))]
    assert islands_after_adds(R, C, pos) == brute(R, C, pos), (R, C, pos)
pos = [(random.randrange(300), random.randrange(300)) for _ in range(60000)]
t = time.time()
r = islands_after_adds(300, 300, pos)
assert len(r) == 60000 and time.time() - t < 5
''',
    },
    {
        "id": "hcoding-18", "category": "parsing",
        "signature": "words_to_number(text: str) -> int",
        "spec": "Convert an English number phrase to an int. Vocabulary: zero, one..nineteen, twenty..ninety, "
                "hundred, thousand, million, billion, the optional word 'and', and a leading 'minus'. Tens and units "
                "may be joined by a hyphen ('forty-two') or a space ('forty two'). Input is lower case with single "
                "spaces. Values range from -999,999,999,999 to 999,999,999,999.",
        "solution": '''
def words_to_number(text):
    units = {w: i for i, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
        "sixteen seventeen eighteen nineteen".split())}
    tens = {w: 10 * i for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split(), 2)}
    scales = {"thousand": 10**3, "million": 10**6, "billion": 10**9}
    words = text.replace("-", " ").split()
    sign = 1
    if words and words[0] == "minus":
        sign, words = -1, words[1:]
    total = cur = 0
    for w in words:
        if w == "and":
            continue
        if w in units:
            cur += units[w]
        elif w in tens:
            cur += tens[w]
        elif w == "hundred":
            cur *= 100
        elif w in scales:
            total += cur * scales[w]
            cur = 0
        else:
            raise ValueError(w)
    return sign * (total + cur)
''',
        "tests": '''
cases = {
    "zero": 0, "seven": 7, "nineteen": 19, "forty-two": 42, "forty two": 42, "one hundred": 100,
    "one hundred and five": 105, "nine hundred ninety-nine": 999, "one thousand": 1000,
    "twelve thousand three hundred forty-five": 12345, "minus eight": -8,
    "one million two hundred thousand": 1200000, "three billion and one": 3000000001,
    "nine hundred ninety-nine billion nine hundred ninety-nine million nine hundred ninety-nine thousand nine hundred ninety-nine": 999999999999,
    "two hundred million and seventy": 200000070, "minus one billion one hundred and one": -1000000101,
    "eleven thousand and eleven": 11011,
}
for text, want in cases.items():
    assert words_to_number(text) == want, (text, words_to_number(text), want)
''',
    },
    {
        "id": "hcoding-19", "category": "parser",
        "signature": "eval_bool(expr: str, env: dict[str, bool]) -> bool",
        "spec": "Evaluate a boolean expression. Tokens: identifiers (letters, digits, underscore; not starting with a "
                "digit) looked up in `env`, the literals true and false, the operators not, and, or, and parentheses. "
                "Precedence: not > and > or; and/or are left-associative. Tokens may be separated by any whitespace "
                "and parentheses need no spaces. Raise KeyError for an unknown identifier. Do not use eval or exec.",
        "solution": '''
import re

def eval_bool(expr, env):
    toks = re.findall(r"\\(|\\)|[A-Za-z_][A-Za-z0-9_]*", expr)
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def or_():
        v = and_()
        while peek() == "or":
            take()
            r = and_()
            v = v or r
        return v

    def and_():
        v = not_()
        while peek() == "and":
            take()
            r = not_()
            v = v and r
        return v

    def not_():
        if peek() == "not":
            take()
            return not not_()
        return atom()

    def atom():
        t = take()
        if t == "(":
            v = or_()
            take()
            return v
        if t == "true":
            return True
        if t == "false":
            return False
        return bool(env[t])

    return or_()
''',
        "tests": _BAN + '''
assert not _re.search(r"\\b(eval|exec|compile)\\s*\\(", _src), "eval/exec/compile not allowed"
import random
env = {"a": True, "b": False, "c": True, "x_1": False}
assert eval_bool("a and b", env) is False
assert eval_bool("a or b and b", env) is True
assert eval_bool("not a or c", env) is True
assert eval_bool("not (a or c)", env) is False
assert eval_bool("not not b", env) is False
assert eval_bool("(a)and(not b)", env) is True
assert eval_bool("true and\\n\\tx_1", env) is False
try:
    eval_bool("a and zz", env)
    raise AssertionError("expected KeyError")
except KeyError:
    pass
random.seed(15)
def gen(d):
    if d == 0 or random.random() < 0.25:
        return random.choice(["a", "b", "c", "x_1", "true", "false"])
    k = random.random()
    if k < 0.2:
        return "not " + gen(d - 1)
    if k < 0.4:
        return "(" + gen(d - 1) + ")"
    return gen(d - 1) + random.choice([" and ", " or "]) + gen(d - 1)
for _ in range(400):
    e = gen(5)
    want = eval(e.replace("true", "True").replace("false", "False"), {}, dict(env))
    assert eval_bool(e, env) == bool(want), e
''',
    },
    {
        "id": "hcoding-20", "category": "strings",
        "signature": "longest_palindrome(s: str) -> str",
        "spec": "Return the longest palindromic substring of `s`. If there are several of the same length, return the "
                "leftmost. The empty string returns ''. Must handle |s| = 20,000 in under 2 seconds, including inputs "
                "like 'aaaa...a'.",
        "solution": '''
def longest_palindrome(s):
    if not s:
        return ""
    t = "^#" + "#".join(s) + "#$"
    p = [0] * len(t)
    center = right = 0
    for i in range(1, len(t) - 1):
        if i < right:
            p[i] = min(right - i, p[2 * center - i])
        while t[i + p[i] + 1] == t[i - p[i] - 1]:
            p[i] += 1
        if i + p[i] > right:
            center, right = i, i + p[i]
    best_len, best_c = 0, 0
    for i, v in enumerate(p):
        if v > best_len:
            best_len, best_c = v, i
    start = (best_c - best_len) // 2
    return s[start:start + best_len]
''',
        "tests": '''
import random, time
assert longest_palindrome("") == ""
assert longest_palindrome("babad") == "bab"
assert longest_palindrome("cbbd") == "bb"
assert longest_palindrome("a") == "a"
assert longest_palindrome("abacdfgdcaba") == "aba"
assert longest_palindrome("forgeeksskeegfor") == "geeksskeeg"
def brute(s):
    best = ""
    for i in range(len(s)):
        for j in range(i + len(best) + 1, len(s) + 1):
            if s[i:j] == s[i:j][::-1]:
                best = s[i:j]
    return best
random.seed(16)
for _ in range(200):
    s = "".join(random.choice("ab") for _ in range(random.randint(0, 14)))
    assert longest_palindrome(s) == brute(s), s
t = time.time()
assert longest_palindrome("a" * 20000) == "a" * 20000
big = "".join(random.choice("abc") for _ in range(20000))
r = longest_palindrome(big)
assert r == r[::-1] and time.time() - t < 4
''',
    },
]


def build_coding_hard_tasks() -> list[dict[str, Any]]:
    """Return the 20 hard coding tasks as JSON-serialisable dicts."""
    tasks = []
    for s in _SPECS:
        sig = s["signature"]
        entry = sig.split()[1] if sig.startswith("class ") else sig.split("(")[0]
        tasks.append({
            "id": s["id"],
            "category": s["category"],
            "prompt": PROMPT_TEMPLATE.format(signature=sig, spec=s["spec"]),
            "entry_point": entry,
            "checker": "python_unit_tests",
            "max_tokens": CODING_HARD_MAX_TOKENS,
            "tests": s["tests"].strip() + "\n",
            "reference_solution": s["solution"].strip() + "\n",
        })
    assert len(tasks) == 20
    return tasks


def build(suite_dir: Path) -> list[dict[str, Any]]:
    """Suite entry point."""
    return build_coding_hard_tasks()
