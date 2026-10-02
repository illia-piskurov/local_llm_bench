"""JavaScript: Concurrency Pool, Retries & AbortSignal (QuickJS) benchmark.

Tests reliable asynchronous JavaScript (ES2020+) programming capabilities:
- Level 1: Concurrent mapper pMap with worker pool and strict in-order result preservation.
- Level 2: Exponential backoff retries and per-task timeouts.
- Level 3: Early and mid-flight cancellation via AbortSignal and settled mode (Promise.allSettled style).

Code executes inside an isolated QuickJS sandbox with a deterministic virtual timer system.
"""

import json
from collections.abc import Callable
from pathlib import Path

import quickjs

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes.js_quickjs import PRELUDE
from sandboxes.js_quickjs import create_js_context as _create_context
from sandboxes.js_quickjs import drain_js_jobs as _drain

LEVEL1_PROMPT = """\
Implement an asynchronous concurrent mapping function pMap in JavaScript (ES2020+).

Signature:
async function pMap(items, mapper, options)

Parameters:
- items: array of items to process.
- mapper: async function of form async (item, index) => result.
- options: number (e.g. 2) defining concurrency, or options object { concurrency: 2 }. If options is omitted or undefined, default concurrency is 1.

Requirements:
- If items is empty (length 0), return an empty array [].
- Concurrency limit: at most concurrency async calls to mapper may run concurrently. As soon as one finishes, the next task starts.
- Order preservation: the returned array of results must strictly match the initial order of items (indices 0..n-1), regardless of completion order.
- On mapper rejection or uncaught exception, pMap must immediately reject with that error.

Return only the JavaScript code in a single ```javascript ... ``` code block, with no explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your pMap implementation with retries, exponential backoff, and per-task timeouts:

New options in the options object:
- options.retries: number of retry attempts on task failure (default 0).
  For example, retries: 2 means 1 initial attempt + up to 2 retries (up to 3 mapper calls total).
- options.backoffMs: base delay between retries in milliseconds (default 0).
  Delay before 1st retry: backoffMs * (2 ** 0).
  Delay before 2nd retry: backoffMs * (2 ** 1), etc.
  Delay is waited via new Promise(resolve => setTimeout(resolve, delay)).
- options.timeoutMs: maximum execution time for a single mapper attempt in milliseconds (default 0 — no timeout).
  If a mapper attempt exceeds timeoutMs, abort it with new Error("Timeout"), triggering a retry (if attempts remain) or task failure.

Preserve Level 1 behavior (options as number or object, order preservation, concurrency).

Return only the JavaScript code in a single ```javascript ... ``` code block, with no explanations outside the block.
"""

LEVEL3_PROMPT = """\
Extend your pMap implementation with AbortSignal cancellation and settled mode:

New options in the options object:
- options.signal: instance of AbortSignal (from standard AbortController).
  - If signal is already aborted at invocation time (signal.aborted === true), immediately reject pMap with signal.reason (or new Error("Aborted")) without calling mapper.
  - If cancellation occurs mid-flight: do not start remaining tasks in the queue and immediately reject pMap with signal.reason (or new Error("Aborted")).
- options.settled: boolean (default false).
  - Similar to Promise.allSettled: individual task errors do not abort pMap.
  - Instead of raw values, the returned array contains result objects:
    - For fulfilled tasks: { status: 'fulfilled', value: <result> }
    - For failed tasks (after exhausting all retries): { status: 'rejected', reason: <error message or error object> }
  - Important: cancellation via signal still interrupts the entire pMap and rejects it.

Preserve Level 1 and Level 2 behavior.

Return only the JavaScript code in a single ```javascript ... ``` code block, with no explanations outside the block.
"""


# ── LEVEL 1 TEST CASES ──
def test_empty_array(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let result = null;
    pMap([], async x => x * 2).then(r => { result = r; });
    """)
    _drain(ctx)
    res = ctx.eval("JSON.stringify(result)")
    return res == "[]"


def test_order_preservation(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let result = null;
    const delays = [50, 10, 40, 20, 30];
    pMap([0, 1, 2, 3, 4], async (x, i) => {
        await new Promise(r => setTimeout(r, delays[i]));
        return x * 10;
    }, { concurrency: 3 }).then(r => { result = r; });
    """)
    _drain(ctx)
    res = ctx.eval("JSON.stringify(result)")
    return res == "[0,10,20,30,40]"


def test_concurrency_limit(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let maxActive = 0;
    let active = 0;
    let result = null;
    const items = [1, 2, 3, 4, 5, 6, 7, 8];
    pMap(items, async (x) => {
        active++;
        if (active > maxActive) maxActive = active;
        await new Promise(r => setTimeout(r, 20));
        active--;
        return x;
    }, { concurrency: 2 }).then(r => { result = r; });
    """)
    _drain(ctx)
    max_active = ctx.eval("maxActive")
    res = ctx.eval("JSON.stringify(result)")
    return max_active == 2 and res == "[1,2,3,4,5,6,7,8]"


def test_concurrency_as_number(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let maxActive = 0;
    let active = 0;
    pMap([1, 2, 3, 4], async (x) => {
        active++;
        if (active > maxActive) maxActive = active;
        await new Promise(r => setTimeout(r, 15));
        active--;
        return x;
    }, 2);
    """)
    _drain(ctx)
    return ctx.eval("maxActive") == 2


def test_concurrency_default_one(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let maxActive = 0;
    let active = 0;
    pMap([1, 2, 3], async (x) => {
        active++;
        if (active > maxActive) maxActive = active;
        await new Promise(r => setTimeout(r, 10));
        active--;
        return x;
    });
    """)
    _drain(ctx)
    return ctx.eval("maxActive") == 1


def test_index_passed(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let result = null;
    pMap(['a', 'b', 'c'], async (item, index) => {
        return item + index;
    }, 2).then(r => { result = r; });
    """)
    _drain(ctx)
    return ctx.eval("JSON.stringify(result)") == '["a0","b1","c2"]'


def test_mapper_rejection(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let errorCaught = null;
    pMap([1, 2, 3], async (x) => {
        if (x === 2) throw new Error("Item2Failed");
        return x;
    }, 2).catch(err => { errorCaught = (err && err.message) || String(err); });
    """)
    _drain(ctx)
    err = ctx.eval("errorCaught")
    return err is not None and "Item2Failed" in str(err)


LEVEL1_CASES: list[tuple[str, Callable[[str], bool]]] = [
    ("empty_array", test_empty_array),
    ("order_preservation", test_order_preservation),
    ("concurrency_limit", test_concurrency_limit),
    ("concurrency_as_number", test_concurrency_as_number),
    ("concurrency_default_one", test_concurrency_default_one),
    ("index_passed", test_index_passed),
    ("mapper_rejection", test_mapper_rejection),
]


# ── LEVEL 2 TEST CASES: Retries & Timeout ──
def test_retry_transient_failure(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let attempts = 0;
    let result = null;
    pMap(['item'], async (x) => {
        attempts++;
        if (attempts === 1) throw new Error("Transient");
        return 'success';
    }, { retries: 2 }).then(r => { result = r; });
    """)
    _drain(ctx)
    return ctx.eval("attempts") == 2 and ctx.eval("JSON.stringify(result)") == '["success"]'


def test_retry_exhausted(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let attempts = 0;
    let errorCaught = null;
    pMap(['item'], async (x) => {
        attempts++;
        throw new Error("Permanent");
    }, { retries: 2 }).catch(err => { errorCaught = (err && err.message) || String(err); });
    """)
    _drain(ctx)
    return ctx.eval("attempts") == 3 and "Permanent" in str(ctx.eval("errorCaught"))


def test_exponential_backoff(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let timestamps = [];
    let result = null;
    pMap(['item'], async (x) => {
        timestamps.push(__currentTime);
        if (timestamps.length < 3) throw new Error("RetryMe");
        return 'done';
    }, { retries: 2, backoffMs: 100 }).then(r => { result = r; });
    """)
    _drain(ctx)
    times = json.loads(ctx.eval("JSON.stringify(timestamps)"))
    if len(times) != 3:
        return False
    return times[0] == 0 and times[1] == 100 and times[2] == 300 and ctx.eval("JSON.stringify(result)") == '["done"]'


def test_task_timeout(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let errorCaught = null;
    pMap(['slow'], async () => {
        await new Promise(r => setTimeout(r, 100));
        return 'done';
    }, { timeoutMs: 30 }).catch(err => { errorCaught = (err && err.message) || String(err); });
    """)
    _drain(ctx)
    err = str(ctx.eval("errorCaught"))
    return "Timeout" in err or "timeout" in err.lower()


def test_timeout_triggers_retry(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let attempts = 0;
    let result = null;
    pMap(['item'], async () => {
        attempts++;
        if (attempts === 1) {
            await new Promise(r => setTimeout(r, 100));
            return 'late';
        }
        return 'fast';
    }, { retries: 1, timeoutMs: 30 }).then(r => { result = r; });
    """)
    _drain(ctx)
    return ctx.eval("attempts") == 2 and ctx.eval("JSON.stringify(result)") == '["fast"]'


LEVEL2_CASES: list[tuple[str, Callable[[str], bool]]] = [
    ("retry_transient_failure", test_retry_transient_failure),
    ("retry_exhausted", test_retry_exhausted),
    ("exponential_backoff", test_exponential_backoff),
    ("task_timeout", test_task_timeout),
    ("timeout_triggers_retry", test_timeout_triggers_retry),
]


# ── LEVEL 3 TEST CASES: AbortSignal & Settled ──
def test_already_aborted_signal(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    const ac = new AbortController();
    ac.abort(new Error("PreAborted"));
    let called = false;
    let errorCaught = null;
    pMap([1, 2], async (x) => {
        called = true;
        return x;
    }, { signal: ac.signal }).catch(err => { errorCaught = (err && err.message) || String(err); });
    """)
    _drain(ctx)
    return not ctx.eval("called") and "PreAborted" in str(ctx.eval("errorCaught"))


def test_mid_flight_abort(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    const ac = new AbortController();
    let started = [];
    let errorCaught = null;
    pMap([1, 2, 3, 4], async (x) => {
        started.push(x);
        await new Promise(r => setTimeout(r, 50));
        return x;
    }, { concurrency: 2, signal: ac.signal }).catch(err => {
        errorCaught = (err && err.message) || String(err);
    });
    setTimeout(() => ac.abort(new Error("StoppedMidway")), 20);
    """)
    _drain(ctx)
    started = json.loads(ctx.eval("JSON.stringify(started)"))
    err = str(ctx.eval("errorCaught"))
    return len(started) <= 2 and "StoppedMidway" in err


def test_settled_all_success(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let result = null;
    pMap(['a', 'b'], async (x) => x.toUpperCase(), { settled: true }).then(r => { result = r; });
    """)
    _drain(ctx)
    res = json.loads(ctx.eval("JSON.stringify(result)"))
    if len(res) != 2:
        return False
    return (
        res[0].get("status") == "fulfilled"
        and res[0].get("value") == "A"
        and res[1].get("status") == "fulfilled"
        and res[1].get("value") == "B"
    )


def test_settled_mixed_failures(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let result = null;
    pMap(['good', 'bad', 'great'], async (x) => {
        if (x === 'bad') throw new Error("BadItem");
        return x.toUpperCase();
    }, { settled: true }).then(r => { result = r; });
    """)
    _drain(ctx)
    res = json.loads(ctx.eval("JSON.stringify(result)"))
    if len(res) != 3:
        return False
    r0, r1, r2 = res[0], res[1], res[2]
    return (
        r0.get("status") == "fulfilled"
        and r0.get("value") == "GOOD"
        and r1.get("status") == "rejected"
        and "BadItem" in str(r1.get("reason"))
        and r2.get("status") == "fulfilled"
        and r2.get("value") == "GREAT"
    )


def test_settled_with_retries(solution_js: str) -> bool:
    ctx = _create_context(solution_js)
    ctx.eval("""
    let attempts = 0;
    let result = null;
    pMap(['fail'], async () => {
        attempts++;
        throw new Error("WillFail");
    }, { settled: true, retries: 2 }).then(r => { result = r; });
    """)
    _drain(ctx)
    attempts = ctx.eval("attempts")
    res = json.loads(ctx.eval("JSON.stringify(result)"))
    return attempts == 3 and len(res) == 1 and res[0].get("status") == "rejected"


LEVEL3_CASES: list[tuple[str, Callable[[str], bool]]] = [
    ("already_aborted_signal", test_already_aborted_signal),
    ("mid_flight_abort", test_mid_flight_abort),
    ("settled_all_success", test_settled_all_success),
    ("settled_mixed_failures", test_settled_mixed_failures),
    ("settled_with_retries", test_settled_with_retries),
]


def run_js_suite(cases: list[tuple[str, Callable[[str], bool]]], js_path: Path) -> tuple[int, int, list[str]]:
    if not js_path.exists():
        return 0, len(cases), [f"File {js_path} not found"]

    try:
        solution_js = js_path.read_text(encoding="utf-8")
    except Exception as e:
        return 0, len(cases), [f"Error reading file {js_path}: {e}"]

    # Syntax check
    try:
        test_ctx = quickjs.Context()
        test_ctx.set_time_limit(2)
        test_ctx.eval(PRELUDE)
        test_ctx.eval(solution_js)
    except Exception as e:
        return 0, len(cases), [f"JavaScript syntax error: {e}"]

    passed = 0
    failures: list[str] = []
    for test_name, test_fn in cases:
        try:
            ok = test_fn(solution_js)
            if ok:
                passed += 1
            else:
                failures.append(f"{test_name}: assertion returned False")
        except Exception as e:
            failures.append(f"{test_name}: exception {e}")

    return passed, len(cases), failures


class JSAsyncBenchmark(Benchmark):
    id = "js_async"
    name = "JavaScript: Concurrency Pool, Retries & AbortSignal (QuickJS)"
    short = "JS Async"
    file_ext = "js"
    code_lang = "javascript"
    code_lang_aliases = ("js",)
    levels = [
        Level(id="level1", name="Level 1 (ConcurrentMap & In-Order)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (Exponential Backoff & Timeout)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (AbortSignal & Settled Mode)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            cases = LEVEL1_CASES
        elif level_id == "level2":
            cases = LEVEL1_CASES + LEVEL2_CASES
        else:
            cases = LEVEL1_CASES + LEVEL2_CASES + LEVEL3_CASES

        passed, total, failures = run_js_suite(cases, answer_path)
        return TestResult(passed, total, failures)
