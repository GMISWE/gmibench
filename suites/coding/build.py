"""Coding task definitions: 20 self-contained Python functions with hidden tests.

Each entry has a public spec (sent to the model), a reference solution (never sent;
used by the dry-run client and by our own tests), and hidden assert-based tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

CODING_MAX_TOKENS = 16384

_SPECS: list[dict[str, str]] = [
    {
        "id": "coding-01", "category": "strings",
        "signature": "is_balanced(s: str) -> bool",
        "spec": "Return True if every bracket in `s` ('()', '[]', '{}') is closed in the correct order. "
                "Characters other than brackets are ignored.",
        "solution": '''
def is_balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack
''',
        "tests": '''
assert is_balanced("")
assert is_balanced("a(b[c]{d}e)f")
assert not is_balanced("(]")
assert not is_balanced("((")
assert not is_balanced("())")
assert is_balanced("{[()()]}")
assert not is_balanced("}{")
''',
    },
    {
        "id": "coding-02", "category": "intervals",
        "signature": "merge_intervals(intervals: list[list[int]]) -> list[list[int]]",
        "spec": "Merge all overlapping or touching closed intervals ([1,3] and [3,5] merge) and return them "
                "sorted by start. The input may be unsorted and may be empty. Do not modify the input.",
        "solution": '''
def merge_intervals(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out
''',
        "tests": '''
assert merge_intervals([]) == []
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
assert merge_intervals([[1,4],[4,5]]) == [[1,5]]
assert merge_intervals([[5,7],[1,2],[2,3]]) == [[1,3],[5,7]]
assert merge_intervals([[1,10],[2,3],[4,5]]) == [[1,10]]
x = [[3,4],[1,2]]
merge_intervals(x)
assert x == [[3,4],[1,2]]
''',
    },
    {
        "id": "coding-03", "category": "parsing",
        "signature": "roman_to_int(s: str) -> int",
        "spec": "Convert a valid Roman numeral (1 to 3999, standard subtractive notation) to an integer.",
        "solution": '''
def roman_to_int(s):
    v = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, ch in enumerate(s):
        if i + 1 < len(s) and v[ch] < v[s[i + 1]]:
            total -= v[ch]
        else:
            total += v[ch]
    return total
''',
        "tests": '''
assert roman_to_int("III") == 3
assert roman_to_int("IV") == 4
assert roman_to_int("IX") == 9
assert roman_to_int("LVIII") == 58
assert roman_to_int("MCMXCIV") == 1994
assert roman_to_int("MMMCMXCIX") == 3999
''',
    },
    {
        "id": "coding-04", "category": "formatting",
        "signature": "int_to_roman(n: int) -> str",
        "spec": "Convert an integer from 1 to 3999 to a Roman numeral using standard subtractive notation. "
                "Raise ValueError for numbers outside that range.",
        "solution": '''
def int_to_roman(n):
    if not isinstance(n, int) or not 1 <= n <= 3999:
        raise ValueError("out of range")
    table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
             (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = []
    for value, sym in table:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)
''',
        "tests": '''
assert int_to_roman(1) == "I"
assert int_to_roman(4) == "IV"
assert int_to_roman(1994) == "MCMXCIV"
assert int_to_roman(3999) == "MMMCMXCIX"
assert int_to_roman(444) == "CDXLIV"
for bad in (0, 4000, -5):
    try:
        int_to_roman(bad)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
''',
    },
    {
        "id": "coding-05", "category": "dynamic-programming",
        "signature": "lcs_length(a: str, b: str) -> int",
        "spec": "Return the length of the longest common subsequence of strings `a` and `b`. "
                "Must handle strings up to 2000 characters each within a few seconds.",
        "solution": '''
def lcs_length(a, b):
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b):
            cur.append(prev[j] + 1 if ca == cb else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]
''',
        "tests": '''
assert lcs_length("", "abc") == 0
assert lcs_length("abcde", "ace") == 3
assert lcs_length("abc", "def") == 0
assert lcs_length("AGGTAB", "GXTXAYB") == 4
import random
random.seed(1)
a = "".join(random.choice("ACGT") for _ in range(1500))
b = "".join(random.choice("ACGT") for _ in range(1500))
r = lcs_length(a, b)
assert 900 < r < 1300, r
''',
    },
    {
        "id": "coding-06", "category": "collections",
        "signature": "top_k_frequent(words: list[str], k: int) -> list[str]",
        "spec": "Return the `k` most frequent words, ordered by frequency (highest first); "
                "ties are broken alphabetically (a before b). If k exceeds the number of distinct words, "
                "return all distinct words in that order.",
        "solution": '''
from collections import Counter

def top_k_frequent(words, k):
    c = Counter(words)
    return sorted(c, key=lambda w: (-c[w], w))[:k]
''',
        "tests": '''
assert top_k_frequent(["i","love","leetcode","i","love","coding"], 2) == ["i","love"]
assert top_k_frequent(["the","day","is","sunny","the","the","the","sunny","is","is"], 4) == ["the","is","sunny","day"]
assert top_k_frequent(["b","a","c"], 2) == ["a","b"]
assert top_k_frequent(["x"], 5) == ["x"]
assert top_k_frequent([], 3) == []
''',
    },
    {
        "id": "coding-07", "category": "strings",
        "signature": "rle_encode(s: str) -> str",
        "spec": "Run-length encode `s` as count followed by character for every run, e.g. 'aaabcc' -> '3a1b2c'. "
                "Runs are maximal sequences of the same character. The empty string encodes to ''.",
        "solution": '''
def rle_encode(s):
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)
''',
        "tests": '''
assert rle_encode("") == ""
assert rle_encode("aaabcc") == "3a1b2c"
assert rle_encode("a") == "1a"
assert rle_encode("aaaaaaaaaaaa") == "12a"
assert rle_encode("abab") == "1a1b1a1b"
assert rle_encode("  x") == "2 1x"
''',
    },
    {
        "id": "coding-08", "category": "recursion",
        "signature": "flatten(nested: list) -> list",
        "spec": "Flatten an arbitrarily nested list (lists and tuples count as nesting) into a flat list, "
                "keeping order. Strings are atoms, not sequences. Must handle nesting depth of 5000 "
                "without raising RecursionError.",
        "solution": '''
def flatten(nested):
    out = []
    stack = [iter(nested)]
    while stack:
        for item in stack[-1]:
            if isinstance(item, (list, tuple)):
                stack.append(iter(item))
                break
            out.append(item)
        else:
            stack.pop()
    return out
''',
        "tests": '''
assert flatten([]) == []
assert flatten([1, [2, [3, (4, 5)]], "ab", [[[]]]]) == [1, 2, 3, 4, 5, "ab"]
assert flatten([[["x"]], "yz"]) == ["x", "yz"]
deep = [7]
for _ in range(5000):
    deep = [deep]
assert flatten(deep) == [7]
''',
    },
    {
        "id": "coding-09", "category": "data-structures",
        "signature": "class LRUCache with __init__(self, capacity: int), get(self, key) -> int, put(self, key, value) -> None",
        "spec": "Implement an LRU cache. `get` returns the value or -1 if missing and marks the key as most "
                "recently used. `put` inserts or updates a key (marking it most recently used) and evicts the "
                "least recently used key when size exceeds `capacity`. Both operations must be O(1) on average.",
        "solution": '''
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.d = OrderedDict()

    def get(self, key):
        if key not in self.d:
            return -1
        self.d.move_to_end(key)
        return self.d[key]

    def put(self, key, value):
        self.d[key] = value
        self.d.move_to_end(key)
        if len(self.d) > self.capacity:
            self.d.popitem(last=False)
''',
        "tests": '''
c = LRUCache(2)
c.put(1, 1); c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) == -1
c.put(4, 4)
assert c.get(1) == -1
assert c.get(3) == 3
assert c.get(4) == 4
c2 = LRUCache(1)
c2.put("a", 1); c2.put("a", 2)
assert c2.get("a") == 2
c2.put("b", 3)
assert c2.get("a") == -1
''',
    },
    {
        "id": "coding-10", "category": "dynamic-programming",
        "signature": "edit_distance(a: str, b: str) -> int",
        "spec": "Return the Levenshtein distance (insert, delete, substitute; each costs 1) between `a` and `b`.",
        "solution": '''
def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
''',
        "tests": '''
assert edit_distance("", "") == 0
assert edit_distance("kitten", "sitting") == 3
assert edit_distance("flaw", "lawn") == 2
assert edit_distance("abc", "") == 3
assert edit_distance("intention", "execution") == 5
''',
    },
    {
        "id": "coding-11", "category": "parsing",
        "signature": "parse_duration(text: str) -> int",
        "spec": "Parse a duration like '1h30m', '45s', '2d3h', '1h 5m 10s' into total seconds. Units: d, h, m, s. "
                "Each unit may appear at most once and units must appear in the order d, h, m, s. "
                "Whitespace between parts is allowed. Raise ValueError for empty, malformed, repeated or "
                "out-of-order input.",
        "solution": '''
import re

def parse_duration(text):
    s = text.replace(" ", "")
    m = re.fullmatch(r"(?:(\\d+)d)?(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?", s)
    if not s or not m:
        raise ValueError(text)
    d, h, mi, se = (int(g) if g else 0 for g in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se
''',
        "tests": '''
assert parse_duration("45s") == 45
assert parse_duration("1h30m") == 5400
assert parse_duration("2d3h") == 2 * 86400 + 3 * 3600
assert parse_duration("1h 5m 10s") == 3910
assert parse_duration("0s") == 0
for bad in ("", "5x", "1m1h", "1h1h", "h", "10"):
    try:
        parse_duration(bad)
        raise AssertionError("expected ValueError for " + repr(bad))
    except ValueError:
        pass
''',
    },
    {
        "id": "coding-12", "category": "matrices",
        "signature": "spiral_order(matrix: list[list[int]]) -> list[int]",
        "spec": "Return the elements of a rectangular matrix in clockwise spiral order starting at the top-left. "
                "An empty matrix (or one with empty rows) returns [].",
        "solution": '''
def spiral_order(matrix):
    out = []
    m = [list(r) for r in matrix]
    while m and m[0]:
        out.extend(m.pop(0))
        m = [list(r) for r in zip(*m)][::-1] if m else []
    return out
''',
        "tests": '''
assert spiral_order([]) == []
assert spiral_order([[]]) == []
assert spiral_order([[1,2,3],[4,5,6],[7,8,9]]) == [1,2,3,6,9,8,7,4,5]
assert spiral_order([[1,2,3,4],[5,6,7,8],[9,10,11,12]]) == [1,2,3,4,8,12,11,10,9,5,6,7]
assert spiral_order([[1],[2],[3]]) == [1,2,3]
assert spiral_order([[1,2,3]]) == [1,2,3]
''',
    },
    {
        "id": "coding-13", "category": "arrays",
        "signature": "next_permutation(nums: list[int]) -> list[int]",
        "spec": "Return a new list with the next lexicographically greater permutation of `nums`. "
                "If `nums` is the last permutation, return the first (sorted ascending). Duplicates are allowed.",
        "solution": '''
def next_permutation(nums):
    a = list(nums)
    i = len(a) - 2
    while i >= 0 and a[i] >= a[i + 1]:
        i -= 1
    if i >= 0:
        j = len(a) - 1
        while a[j] <= a[i]:
            j -= 1
        a[i], a[j] = a[j], a[i]
    a[i + 1:] = reversed(a[i + 1:])
    return a
''',
        "tests": '''
assert next_permutation([1,2,3]) == [1,3,2]
assert next_permutation([3,2,1]) == [1,2,3]
assert next_permutation([1,1,5]) == [1,5,1]
assert next_permutation([1,3,2]) == [2,1,3]
assert next_permutation([2,2,0,4,3,1]) == [2,2,1,0,3,4]
assert next_permutation([]) == []
assert next_permutation([7]) == [7]
''',
    },
    {
        "id": "coding-14", "category": "dynamic-programming",
        "signature": "word_break(s: str, words: list[str]) -> bool",
        "spec": "Return True if `s` can be segmented into a sequence of one or more words from `words` "
                "(words may be reused). Must handle len(s) up to 300 quickly. The empty string returns True.",
        "solution": '''
def word_break(s, words):
    ws = set(words)
    ok = [True] + [False] * len(s)
    for i in range(1, len(s) + 1):
        ok[i] = any(ok[j] and s[j:i] in ws for j in range(i))
    return ok[-1]
''',
        "tests": '''
assert word_break("leetcode", ["leet","code"])
assert word_break("applepenapple", ["apple","pen"])
assert not word_break("catsandog", ["cats","dog","sand","and","cat"])
assert word_break("", ["a"])
assert not word_break("a" * 150 + "b", ["a","aa","aaa","aaaa"])
''',
    },
    {
        "id": "coding-15", "category": "parsing",
        "signature": "eval_rpn(tokens: list[str]) -> int",
        "spec": "Evaluate an expression in Reverse Polish Notation. Operators: +, -, *, /. Operands are integers "
                "(possibly negative, like '-3'). Division truncates toward zero (so -7/2 == -3).",
        "solution": '''
def eval_rpn(tokens):
    st = []
    for t in tokens:
        if t in ("+", "-", "*", "/"):
            b, a = st.pop(), st.pop()
            if t == "+": st.append(a + b)
            elif t == "-": st.append(a - b)
            elif t == "*": st.append(a * b)
            else:
                q = abs(a) // abs(b)
                st.append(q if (a < 0) == (b < 0) else -q)
        else:
            st.append(int(t))
    return st[-1]
''',
        "tests": '''
assert eval_rpn(["2","1","+","3","*"]) == 9
assert eval_rpn(["4","13","5","/","+"]) == 6
assert eval_rpn(["10","6","9","3","+","-11","*","/","*","17","+","5","+"]) == 22
assert eval_rpn(["-7","2","/"]) == -3
assert eval_rpn(["7","-2","/"]) == -3
assert eval_rpn(["42"]) == 42
''',
    },
    {
        "id": "coding-16", "category": "graphs",
        "signature": "shortest_paths(n: int, edges: list[tuple[int, int, int]], src: int) -> list[int]",
        "spec": "Nodes are 0..n-1. `edges` holds directed edges (u, v, w) with non-negative weight w. "
                "Return the list of shortest distances from `src` to every node; use -1 for unreachable nodes. "
                "Must handle 10,000 nodes and 50,000 edges in under a second.",
        "solution": '''
import heapq

def shortest_paths(n, edges, src):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    dist = [None] * n
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if dist[u] is not None:
            continue
        dist[u] = d
        for v, w in adj[u]:
            if dist[v] is None:
                heapq.heappush(pq, (d + w, v))
    return [-1 if d is None else d for d in dist]
''',
        "tests": '''
assert shortest_paths(1, [], 0) == [0]
assert shortest_paths(4, [(0,1,4),(0,2,1),(2,1,2),(1,3,1)], 0) == [0,3,1,4]
assert shortest_paths(3, [(1,2,5)], 0) == [0,-1,-1]
assert shortest_paths(3, [(0,1,0),(1,2,0)], 0) == [0,0,0]
import random, time
random.seed(3)
n = 10000
edges = [(i, i + 1, 1) for i in range(n - 1)] + [(random.randrange(n), random.randrange(n), random.randint(0, 50)) for _ in range(40000)]
t = time.time()
r = shortest_paths(n, edges, 0)
assert time.time() - t < 3
assert r[0] == 0 and all(0 <= d <= n for d in r)
''',
    },
    {
        "id": "coding-17", "category": "collections",
        "signature": "group_anagrams(words: list[str]) -> list[list[str]]",
        "spec": "Group words that are anagrams of each other. Sort the words inside each group alphabetically, "
                "and sort the groups by their first word. Duplicates stay as separate entries.",
        "solution": '''
def group_anagrams(words):
    groups = {}
    for w in words:
        groups.setdefault("".join(sorted(w)), []).append(w)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: g[0])
''',
        "tests": '''
assert group_anagrams([]) == []
assert group_anagrams(["eat","tea","tan","ate","nat","bat"]) == [["ate","eat","tea"],["bat"],["nat","tan"]]
assert group_anagrams(["a","a"]) == [["a","a"]]
assert group_anagrams(["", "b", ""]) == [["",""],["b"]]
''',
    },
    {
        "id": "coding-18", "category": "parsing",
        "signature": "compare_semver(a: str, b: str) -> int",
        "spec": "Compare two Semantic Versioning 2.0.0 strings and return -1, 0 or 1. Follow the spec's "
                "precedence rules: compare major.minor.patch numerically; a version with a pre-release "
                "(e.g. '1.0.0-alpha.1') is lower than the same version without one; pre-release identifiers are "
                "compared dot by dot (numeric identifiers numerically and lower than alphanumeric ones, "
                "alphanumeric ones in ASCII order, and a shorter set is lower if all preceding are equal). "
                "Build metadata after '+' is ignored.",
        "solution": '''
def compare_semver(a, b):
    def parse(v):
        v = v.split("+", 1)[0]
        core, _, pre = v.partition("-")
        nums = tuple(int(x) for x in core.split("."))
        return nums, (pre.split(".") if pre else [])

    def cmp_ids(x, y):
        xd, yd = x.isdigit(), y.isdigit()
        if xd and yd:
            x, y = int(x), int(y)
        elif xd != yd:
            return -1 if xd else 1
        return (x > y) - (x < y)

    (na, pa), (nb, pb) = parse(a), parse(b)
    if na != nb:
        return -1 if na < nb else 1
    if not pa or not pb:
        return (not pa) - (not pb) if pa or pb else 0
    for x, y in zip(pa, pb):
        c = cmp_ids(x, y)
        if c:
            return c
    return (len(pa) > len(pb)) - (len(pa) < len(pb))
''',
        "tests": '''
assert compare_semver("1.0.0", "1.0.0") == 0
assert compare_semver("1.0.0", "2.0.0") == -1
assert compare_semver("1.10.0", "1.9.0") == 1
assert compare_semver("1.0.0-alpha", "1.0.0") == -1
assert compare_semver("1.0.0", "1.0.0-rc.1") == 1
chain = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0"]
for lo, hi in zip(chain, chain[1:]):
    assert compare_semver(lo, hi) == -1, (lo, hi)
    assert compare_semver(hi, lo) == 1, (hi, lo)
assert compare_semver("1.0.0+build.5", "1.0.0+build.9") == 0
''',
    },
    {
        "id": "coding-19", "category": "parsing",
        "signature": "parse_csv_line(line: str) -> list[str]",
        "spec": "Split one CSV line into fields. Fields are separated by commas. A field may be wrapped in double "
                "quotes; inside quotes, commas are literal and a doubled quote (\"\") means one quote character. "
                "Do not strip whitespace. An empty line returns ['']. Do not use the csv module.",
        "solution": '''
def parse_csv_line(line):
    fields, cur, i, q = [], [], 0, False
    while i < len(line):
        ch = line[i]
        if q:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"'); i += 1
                else:
                    q = False
            else:
                cur.append(ch)
        elif ch == '"':
            q = True
        elif ch == ",":
            fields.append("".join(cur)); cur = []
        else:
            cur.append(ch)
        i += 1
    fields.append("".join(cur))
    return fields
''',
        "tests": '''
assert parse_csv_line("") == [""]
assert parse_csv_line("a,b,c") == ["a","b","c"]
assert parse_csv_line('"x,y",z') == ["x,y","z"]
assert parse_csv_line('"he said ""hi""",2') == ['he said "hi"',"2"]
assert parse_csv_line("a,,b,") == ["a","","b",""]
assert parse_csv_line(" a , b ") == [" a "," b "]
assert parse_csv_line('""') == [""]
''',
    },
    {
        "id": "coding-20", "category": "arrays",
        "signature": "trap_rain_water(heights: list[int]) -> int",
        "spec": "Given non-negative bar heights of width 1, return how many units of rain water are trapped "
                "between the bars. Must run in O(n) for n up to 1,000,000.",
        "solution": '''
def trap_rain_water(heights):
    l, r = 0, len(heights) - 1
    lm = rm = total = 0
    while l < r:
        if heights[l] < heights[r]:
            lm = max(lm, heights[l]); total += lm - heights[l]; l += 1
        else:
            rm = max(rm, heights[r]); total += rm - heights[r]; r -= 1
    return total
''',
        "tests": '''
assert trap_rain_water([]) == 0
assert trap_rain_water([0,1,0,2,1,0,1,3,2,1,2,1]) == 6
assert trap_rain_water([4,2,0,3,2,5]) == 9
assert trap_rain_water([1,2,3]) == 0
import time
big = [1000] + [0] * 999998 + [1000]
t = time.time()
assert trap_rain_water(big) == 1000 * 999998
assert time.time() - t < 3
''',
    },
]

PROMPT_TEMPLATE = (
    "Write a Python 3 implementation of `{signature}`.\n\n"
    "{spec}\n\n"
    "Use only the standard library. Return only the code in a single ```python code block. "
    "Do not include tests, example usage, or input() calls."
)


def build_coding_tasks() -> list[dict[str, Any]]:
    """Return the 20 coding tasks as JSON-serialisable dicts."""
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
            "max_tokens": CODING_MAX_TOKENS,
            "tests": s["tests"].strip() + "\n",
            "reference_solution": s["solution"].strip() + "\n",
        })
    assert len(tasks) == 20
    return tasks


def build(suite_dir: Path) -> list[dict[str, Any]]:
    """Suite entry point."""
    return build_coding_tasks()
