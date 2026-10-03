"""Tests for the CPython-compatibility shims of the MicroPython sandbox.

Two layers:
1. Differential tests: the shim sources run under CPython and are compared with the real standard library.
2. Sandbox tests: solutions that use the shimmed modules really execute inside MicroPython/WASM.
"""

import bisect
import collections
import copy
import functools
import heapq
import itertools

import pytest

from sandboxes.mpy_compat import build_prelude, load_shims_for_testing, required_shims
from sandboxes.python_wasm import WASM_AVAILABLE, run_function_in_wasm

pytestmark = pytest.mark.filterwarnings("ignore")

needs_wasm = pytest.mark.skipif(not WASM_AVAILABLE, reason="micropython_wasm is not installed")


# ── import detection ────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("import copy", ["copy"]),
        ("from typing import Dict, List", ["typing"]),
        ("from collections import defaultdict", ["collections"]),
        ("from collections import deque, OrderedDict", ["collections"]),
        ("from collections import OrderedDict, namedtuple", []),  # MicroPython already has these
        ("import collections", ["collections"]),
        ("from collections.abc import Mapping", ["collections"]),
        ("import heapq", ["heapq"]),  # heapq.nlargest(...) is attribute access, invisible to the import scan
        ("from heapq import heappush, heappop", []),  # the native functions are enough
        ("from heapq import nlargest", ["heapq"]),
        ("def f():\n    import functools\n    from itertools import chain", ["functools", "itertools"]),
        ("import math, re, json", []),
        ("def broken(:", []),
        ("from . import sibling", []),
    ],
)
def test_required_shims(code, expected):
    assert required_shims(code) == expected


def test_no_prelude_when_nothing_needed():
    assert build_prelude("import math\nx = 1") == ""


# ── differential tests: shim vs real stdlib (executed under CPython) ───────────────────────────


@pytest.fixture(scope="module")
def shim():
    mods = load_shims_for_testing("typing", "copy", "collections", "heapq", "functools", "itertools", "bisect", "abc")
    return type("Shims", (), mods)


def test_deque_matches_stdlib(shim):
    ops = [
        ("append", 1), ("append", 2), ("appendleft", 0), ("extend", [3, 4]), ("extendleft", [-1, -2]),
        ("pop",), ("popleft",), ("rotate", 2), ("rotate", -1), ("append", 9), ("reverse",), ("insert", 1, 7),
        ("remove", 7), ("popleft",), ("pop",),
    ]  # fmt: skip
    for maxlen in (None, 4):
        real, mine = collections.deque(maxlen=maxlen), shim.collections.deque(maxlen=maxlen)
        for name, *args in ops:
            try:
                expected = getattr(real, name)(*args)
            except Exception as e:  # noqa: BLE001
                with pytest.raises(type(e)):
                    getattr(mine, name)(*args)
                continue
            assert getattr(mine, name)(*args) == expected, (maxlen, name, args)
            assert list(mine) == list(real) and len(mine) == len(real)
        assert mine.maxlen == real.maxlen


def test_deque_indexing_and_helpers(shim):
    real, mine = collections.deque([5, 6, 7, 6]), shim.collections.deque([5, 6, 7, 6])
    assert (mine[0], mine[-1], mine[2]) == (real[0], real[-1], real[2])
    assert mine.count(6) == real.count(6) and mine.index(7) == real.index(7)
    assert 7 in mine and 99 not in mine and bool(mine) and not shim.collections.deque()
    mine[1] = 60
    real[1] = 60
    del mine[0]
    del real[0]
    assert list(mine) == list(real) and list(reversed(mine)) == list(reversed(real))
    with pytest.raises(IndexError):
        mine[10]
    with pytest.raises(IndexError):
        shim.collections.deque().popleft()
    assert repr(shim.collections.deque([1], maxlen=3)) == repr(collections.deque([1], maxlen=3))
    assert list(shim.collections.deque([1, 2], 1)) == list(collections.deque([1, 2], 1))


def test_deque_popleft_compaction_keeps_order(shim):
    real, mine = collections.deque(range(200)), shim.collections.deque(range(200))
    for _ in range(150):
        assert mine.popleft() == real.popleft()
    mine.append("x")
    real.append("x")
    mine.appendleft("y")
    real.appendleft("y")
    assert list(mine) == list(real)


def test_defaultdict_matches_stdlib(shim):
    for factory in (list, int, set, lambda: "dflt"):
        real, mine = collections.defaultdict(factory), shim.collections.defaultdict(factory)
        for d in (real, mine):
            _ = d["a"]
            _ = d["b"]
        assert dict(real.items()) == dict(mine.items())
    real, mine = collections.defaultdict(int), shim.collections.defaultdict(int)
    for k in "abracadabra":
        real[k] += 1
        mine[k] += 1
    assert dict(real.items()) == dict(mine.items())
    assert mine.get("zzz") is None and "zzz" not in mine
    nested = shim.collections.defaultdict(lambda: shim.collections.defaultdict(list))
    nested[1][2].append(3)
    assert nested[1][2] == [3]
    with pytest.raises(KeyError):
        shim.collections.defaultdict()[1]
    with pytest.raises(TypeError):
        shim.collections.defaultdict(5)
    assert mine.copy().default_factory is int and dict(mine.copy().items()) == dict(real.items())
    assert repr(shim.collections.defaultdict(list)) == repr(collections.defaultdict(list))


def test_counter_matches_stdlib(shim):
    for source in ("abracadabra", ["x", "y", "x"], {"a": 3, "b": 1}, ()):
        real, mine = collections.Counter(source), shim.collections.Counter(source)
        assert dict(real.items()) == dict(mine.items())
        assert sorted(real.elements()) == sorted(mine.elements())
        assert real.total() == mine.total()
    real, mine = collections.Counter("aabbbc"), shim.collections.Counter("aabbbc")
    assert mine.most_common(2) == real.most_common(2)
    assert mine["missing"] == 0 and "missing" not in mine
    real.update("cc")
    mine.update("cc")
    real.subtract("a")
    mine.subtract("a")
    assert dict(real.items()) == dict(mine.items())
    assert dict((real + collections.Counter("zz")).items()) == dict((mine + shim.collections.Counter("zz")).items())
    assert dict((real - collections.Counter("bb")).items()) == dict((mine - shim.collections.Counter("bb")).items())
    del mine["b"]
    del mine["never-there"]
    assert "b" not in mine
    assert repr(shim.collections.Counter()) == repr(collections.Counter())
    assert repr(shim.collections.Counter("aab")) == repr(collections.Counter("aab"))


def test_copy_matches_stdlib(shim):
    class Node:
        def __init__(self):
            self.items = [1, [2, 3], {"k": {4}}]
            self.name = "n"

    class Slotted:
        __slots__ = ("a", "b")

        def __init__(self):
            self.a = [1]
            self.b = (2, [3])

    original = {"list": [1, [2]], "tuple": (1, [2]), "set": {1, 2}, "node": Node(), "bytes": b"x", "none": None}
    clone = shim.copy.deepcopy(original)
    assert clone == {**copy.deepcopy(original), "node": clone["node"]}
    assert clone["list"][1] is not original["list"][1] and clone["tuple"][1] is not original["tuple"][1]
    assert clone["node"].items == original["node"].items and clone["node"].items is not original["node"].items
    assert clone["node"].items[1] is not original["node"].items[1]

    slotted = shim.copy.deepcopy(Slotted())
    assert slotted.a == [1] and slotted.b == (2, [3])

    cyc = [1]
    cyc.append(cyc)
    cyc_clone = shim.copy.deepcopy(cyc)
    assert cyc_clone[1] is cyc_clone and cyc_clone is not cyc

    shared = [0]
    two = shim.copy.deepcopy([shared, shared])
    assert two[0] is two[1] and two[0] is not shared

    shallow = shim.copy.copy(original["list"])
    assert shallow == original["list"] and shallow is not original["list"] and shallow[1] is original["list"][1]
    assert shim.copy.copy(original["node"]).items is original["node"].items

    dd = shim.collections.defaultdict(list)
    dd["a"].append([1])
    dd_clone = shim.copy.deepcopy(dd)
    assert dd_clone.default_factory is list and dd_clone["a"] == [[1]] and dd_clone["a"] is not dd["a"]

    dq = shim.collections.deque([[1], [2]])
    dq_clone = shim.copy.deepcopy(dq)
    assert list(dq_clone) == [[1], [2]] and dq_clone[0] is not dq[0]


def test_deepcopy_namedtuple_keeps_type(shim):
    Point = collections.namedtuple("Point", "x y")
    clone = shim.copy.deepcopy(Point(1, [2]))
    assert type(clone) is Point and clone == Point(1, [2])


def test_heapq_extras_match_stdlib(shim):
    data = [5, 1, 9, 3, 7, 3]
    assert shim.heapq.nlargest(3, data) == heapq.nlargest(3, data)
    assert shim.heapq.nsmallest(3, data) == heapq.nsmallest(3, data)
    pairs = [("a", 2), ("b", 9), ("c", 2)]
    assert shim.heapq.nlargest(2, pairs, key=lambda p: p[1]) == heapq.nlargest(2, pairs, key=lambda p: p[1])
    assert list(shim.heapq.merge([1, 4], [2, 3])) == list(heapq.merge([1, 4], [2, 3]))
    for name in ("heappushpop", "heapreplace"):
        real_heap, my_heap = [2, 5, 9], [2, 5, 9]
        heapq.heapify(real_heap)
        heapq.heapify(my_heap)
        assert getattr(shim.heapq, name)(my_heap, 4) == getattr(heapq, name)(real_heap, 4)
        assert sorted(my_heap) == sorted(real_heap)
    my_heap = []
    shim.heapq.heappush(my_heap, 3)  # falls through to the real module
    shim.heapq.heappush(my_heap, 1)
    assert shim.heapq.heappop(my_heap) == 1


def test_functools_matches_stdlib(shim):
    assert shim.functools.reduce(lambda a, b: a * b, [1, 2, 3, 4]) == functools.reduce(lambda a, b: a * b, [1, 2, 3, 4])
    assert shim.functools.reduce(lambda a, b: a + b, [], 10) == 10
    with pytest.raises(TypeError):
        shim.functools.reduce(lambda a, b: a + b, [])

    calls = []

    @shim.functools.lru_cache(maxsize=None)
    def fib(n):
        calls.append(n)
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    assert fib(30) == 832040 and len(calls) == 31

    @shim.functools.lru_cache
    def bare(a, b=0):
        calls.append(("bare", a, b))
        return a + b

    assert (bare(1), bare(1), bare(1, b=2), bare(1, b=2)) == (1, 1, 3, 3)
    assert [c for c in calls if isinstance(c, tuple) and c[0] == "bare"] == [("bare", 1, 0), ("bare", 1, 2)]

    @shim.functools.cache
    def sq(x):
        calls.append(("sq", x))
        return x * x

    assert (sq(4), sq(4)) == (16, 16) and calls.count(("sq", 4)) == 1

    p = shim.functools.partial(pow, 2)
    assert p(10) == functools.partial(pow, 2)(10)
    assert shim.functools.partial(lambda a, b, c=0: (a, b, c), 1, c=5)(2) == (1, 2, 5)

    cmp = lambda a, b: (a > b) - (a < b)  # noqa: E731
    assert sorted([3, 1, 2], key=shim.functools.cmp_to_key(cmp)) == sorted([3, 1, 2], key=functools.cmp_to_key(cmp))

    @shim.functools.total_ordering
    class V:
        def __init__(self, v):
            self.v = v

        def __eq__(self, o):
            return self.v == o.v

        def __lt__(self, o):
            return self.v < o.v

    assert V(1) <= V(1) and V(2) > V(1) and V(2) >= V(2) and not V(1) > V(2)

    @shim.functools.wraps(fib)
    def wrapper():
        pass

    assert wrapper() is None


def test_itertools_matches_stdlib(shim):
    s, r = shim.itertools, itertools
    assert list(s.chain([1], (2, 3), "ab")) == list(r.chain([1], (2, 3), "ab"))
    assert list(s.chain.from_iterable([[1, 2], [3]])) == list(r.chain.from_iterable([[1, 2], [3]]))
    assert list(s.islice(s.count(5), 4)) == list(r.islice(r.count(5), 4))
    for args in ((6,), (2, 6), (1, 9, 3), (None, 5, 2)):
        assert list(s.islice(range(20), *args)) == list(r.islice(range(20), *args))
    assert list(s.islice(s.cycle("ab"), 5)) == list(r.islice(r.cycle("ab"), 5))
    assert list(s.repeat("x", 3)) == list(r.repeat("x", 3))
    assert list(s.accumulate([1, 2, 3, 4])) == list(r.accumulate([1, 2, 3, 4]))
    assert list(s.accumulate([1, 2, 3], lambda a, b: a * b)) == list(r.accumulate([1, 2, 3], lambda a, b: a * b))
    assert list(s.accumulate([1, 2], initial=10)) == list(r.accumulate([1, 2], initial=10))
    assert list(s.product("ab", [0, 1])) == list(r.product("ab", [0, 1]))
    assert list(s.product([0, 1], repeat=3)) == list(r.product([0, 1], repeat=3))
    for n in (None, 0, 1, 2, 3, 4):
        assert list(s.permutations("abc", n)) == list(r.permutations("abc", n))
    for n in (0, 1, 2, 3, 4):
        assert list(s.combinations("abcd", n)) == list(r.combinations("abcd", n))
        assert list(s.combinations_with_replacement("abc", n)) == list(r.combinations_with_replacement("abc", n))
    assert list(s.zip_longest("ab", [1, 2, 3], fillvalue="-")) == list(r.zip_longest("ab", [1, 2, 3], fillvalue="-"))
    data = [1, 1, 2, 3, 3, 3, 1]
    assert [(k, list(g)) for k, g in s.groupby(data)] == [(k, list(g)) for k, g in r.groupby(data)]
    assert [(k, list(g)) for k, g in s.groupby("aAbB", key=str.lower)] == [
        (k, list(g)) for k, g in r.groupby("aAbB", key=str.lower)
    ]
    assert list(s.starmap(pow, [(2, 3), (3, 2)])) == list(r.starmap(pow, [(2, 3), (3, 2)]))
    assert list(s.takewhile(lambda x: x < 3, [1, 2, 3, 1])) == list(r.takewhile(lambda x: x < 3, [1, 2, 3, 1]))
    assert list(s.dropwhile(lambda x: x < 3, [1, 2, 3, 1])) == list(r.dropwhile(lambda x: x < 3, [1, 2, 3, 1]))
    assert list(s.filterfalse(lambda x: x % 2, range(6))) == list(r.filterfalse(lambda x: x % 2, range(6)))
    assert list(s.compress("abcd", [1, 0, 1, 0])) == list(r.compress("abcd", [1, 0, 1, 0]))
    assert list(s.pairwise([1, 2, 3, 4])) == list(r.pairwise([1, 2, 3, 4]))
    assert list(s.pairwise([1])) == []


def test_bisect_matches_stdlib(shim):
    data = [1, 3, 3, 5, 8]
    for x in (0, 1, 3, 4, 8, 9):
        assert shim.bisect.bisect_left(data, x) == bisect.bisect_left(data, x)
        assert shim.bisect.bisect_right(data, x) == bisect.bisect_right(data, x)
        assert shim.bisect.bisect(data, x, 1, 4) == bisect.bisect(data, x, 1, 4)
    a, b = list(data), list(data)
    shim.bisect.insort(a, 4)
    bisect.insort(b, 4)
    shim.bisect.insort_left(a, 3)
    bisect.insort_left(b, 3)
    assert a == b
    records = [("a", 1), ("b", 5)]
    assert shim.bisect.bisect_left(records, 3, key=lambda r: r[1]) == bisect.bisect_left(records, 3, key=lambda r: r[1])
    with pytest.raises(ValueError):
        shim.bisect.bisect_left(data, 1, lo=-1)


def test_typing_names_are_permissive(shim):
    t = shim.typing
    for name in ("Any", "Optional", "List", "Dict", "Tuple", "Callable", "Union", "Iterable", "Sequence", "Deque"):
        alias = getattr(t, name)
        assert alias[int] is alias and alias[str, int] is alias
    T = t.TypeVar("T")

    class Box(t.Generic[T]):
        def __init__(self, v):
            self.v = v

    assert Box(3).v == 3
    assert t.cast(int, "x") == "x" and t.TYPE_CHECKING is False

    @t.overload
    def f(x):
        return x

    assert f(1) == 1
    assert t.NewType("UserId", int)(5) == 5

    class Movie(t.TypedDict):
        title: str

    assert Movie(title="x") == {"title": "x"}


def test_abc_shim(shim):
    class A(shim.abc.ABC):
        @shim.abc.abstractmethod
        def go(self):
            raise NotImplementedError

    class B(A):
        def go(self):
            return 1

    assert B().go() == 1


# ── inside the real MicroPython/WASM sandbox ────────────────────────────────────────────────────

SANDBOX_CASES = {
    "typing_annotations": (
        "from typing import Dict, List, Optional, Any, Tuple, TypeVar, Generic\n"
        "T = TypeVar('T')\n"
        "class Box(Generic[T]):\n"
        "    def __init__(self, v: T):\n"
        "        self.v = v\n"
        "def f(x: Dict[str, List[int]]) -> Optional[int]:\n"
        "    return Box(x).v['a'][0]\n",
        ({"a": [7]},),
        7,
    ),
    "copy_deepcopy": (
        "import copy\n"
        "class Store:\n"
        "    def __init__(self):\n"
        "        self.data = {'a': [1, 2]}\n"
        "def f(_):\n"
        "    s = Store()\n"
        "    snap = copy.deepcopy(s)\n"
        "    s.data['a'].append(3)\n"
        "    return [snap.data['a'], s.data['a']]\n",
        (0,),
        [[1, 2], [1, 2, 3]],
    ),
    "defaultdict_graph": (
        "from collections import defaultdict, deque\n"
        "def f(edges):\n"
        "    g = defaultdict(list)\n"
        "    for a, b in edges:\n"
        "        g[a].append(b)\n"
        "    seen, q = [], deque([1])\n"
        "    while q:\n"
        "        n = q.popleft()\n"
        "        seen.append(n)\n"
        "        for m in g[n]:\n"
        "            q.append(m)\n"
        "    return seen\n",
        ([[1, 2], [1, 3], [2, 4]],),
        [1, 2, 3, 4],
    ),
    "counter": (
        "from collections import Counter\ndef f(s):\n    return Counter(s).most_common(1)[0]\n",
        ("hello",),
        ["l", 2],
    ),
    "deque_single_arg_and_maxlen": (
        "from collections import deque\n"
        "def f(_):\n"
        "    d = deque([1, 2, 3])\n"
        "    d.appendleft(0)\n"
        "    d.rotate(1)\n"
        "    w = deque(maxlen=2)\n"
        "    for i in range(5):\n"
        "        w.append(i)\n"
        "    return [list(d), list(w), d.pop()]\n",
        (0,),
        [[3, 0, 1, 2], [3, 4], 2],
    ),
    "heapq_nlargest": (
        "import heapq\nfrom heapq import nlargest\ndef f(xs):\n    return nlargest(2, xs)\n",
        ([4, 9, 1, 7],),
        [9, 7],
    ),
    "functools_cache": (
        "from functools import lru_cache\n"
        "@lru_cache(maxsize=None)\n"
        "def fib(n):\n"
        "    return n if n < 2 else fib(n - 1) + fib(n - 2)\n"
        "def f(n):\n    return fib(n)\n",
        (40,),  # the sandbox allows ~106 stack frames and the cache wrapper uses two per level
        102334155,
    ),
    "itertools_and_bisect": (
        "import itertools, bisect\n"
        "def f(_):\n"
        "    a = [1, 3, 5]\n"
        "    bisect.insort(a, 4)\n"
        "    return [a, list(itertools.combinations([1, 2, 3], 2)), list(itertools.chain([1], [2]))]\n",
        (0,),
        [[1, 3, 4, 5], [[1, 2], [1, 3], [2, 3]], [1, 2]],
    ),
    "abc_abstract": (
        "from abc import ABC, abstractmethod\n"
        "class Base(ABC):\n"
        "    @abstractmethod\n"
        "    def go(self): ...\n"
        "class Impl(Base):\n"
        "    def go(self):\n"
        "        return 'ok'\n"
        "def f(_):\n    return Impl().go()\n",
        (0,),
        "ok",
    ),
    "local_import_inside_function": (
        "def f(xs):\n    from collections import defaultdict\n    d = defaultdict(int)\n"
        "    for x in xs:\n        d[x] += 1\n    return sorted(d.items())\n",
        ([2, 1, 2],),
        [[1, 1], [2, 2]],
    ),
}


@needs_wasm
@pytest.mark.parametrize("name", sorted(SANDBOX_CASES))
def test_solution_runs_in_sandbox(name):
    code, args, expected = SANDBOX_CASES[name]
    ok, result = run_function_in_wasm(code, "f", args)
    assert ok, result
    assert result == expected


@needs_wasm
def test_unshimmed_module_still_reports_import_error():
    ok, result = run_function_in_wasm("import dataclasses\ndef f(_):\n    return 1\n", "f", (0,))
    assert not ok
    assert "dataclasses" in str(result)


@needs_wasm
def test_shim_cost_does_not_shrink_solution_fuel_budget():
    code = "from collections import deque\ndef f(n):\n    s = 0\n    for i in range(n):\n        s += i\n    return s\n"
    plain = "def f(n):\n    s = 0\n    for i in range(n):\n        s += i\n    return s\n"
    n = 12000  # close enough to the 50M budget that an uncompensated prelude (~28M) would trip it
    assert run_function_in_wasm(plain, "f", (n,)) == (True, n * (n - 1) // 2)
    assert run_function_in_wasm(code, "f", (n,)) == (True, n * (n - 1) // 2)


@needs_wasm
def test_infinite_loop_with_shims_is_still_trapped():
    ok, result = run_function_in_wasm(
        "from collections import deque\ndef f(_):\n    while True:\n        pass\n", "f", (0,)
    )
    assert not ok and isinstance(result, TimeoutError)
