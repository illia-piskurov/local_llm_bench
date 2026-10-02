"""JavaScript: Concurrency Pool, Retries & AbortSignal (QuickJS) бенчмарк.

Тестирует написание надежного асинхронного JavaScript-кода (ES2020+):
- Level 1: Конкурентный маппер pMap с пулом воркеров и сохранением исходного порядка элементов.
- Level 2: Повторные попытки с экспоненциальной задержкой (exponential backoff) и таймаут на задачу.
- Level 3: Отмена пула через AbortSignal и режим settled (Promise.allSettled стиль).

Код исполняется в изолированной песочнице QuickJS с детерминированным таймером без задержек ОС.
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
Реализуй асинхронную функцию конкурентного маппинга pMap на JavaScript (ES2020+).

Сигнатура:
async function pMap(items, mapper, options)

Параметры:
- items: массив элементов для обработки.
- mapper: асинхронная функция вида async (item, index) => result.
- options: число (например, 2), задающее concurrency, либо объект { concurrency: 2 }. Если options не передан или опущен, concurrency по умолчанию равен 1.

Требования:
- Если items пуст (длина 0), возвращается пустой массив [].
- Ограничение конкурентности: в любой момент времени выполняется не более concurrency асинхронных вызовов mapper. Как только один завершается, сразу запускается следующий.
- Сохранение порядка: итоговый массив результатов должен строго соответствовать исходному порядку элементов items (индексы 0..n-1), вне зависимости от того, в каком порядке завершались промисы.
- При возникновении ошибки в mapper (исключение или rejection), pMap должен сразу реджектиться с этой ошибкой.

В ответе верни только JavaScript код одним блоком ```javascript ... ```, без пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию pMap поддержкой повторных попыток (retries), экспоненциальной задержки (exponential backoff) и таймаута на задачу:

Новые опции в объекте options:
- options.retries: число повторных попыток при ошибке задачи (по умолчанию 0).
  Например, retries: 2 означает: 1 исходная попытка + до 2 повторных попыток (всего до 3 вызовов mapper).
- options.backoffMs: базовая задержка между попытками в миллисекундах (по умолчанию 0).
  Задержка перед 1-й повторной попыткой: backoffMs * (2 ** 0).
  Задержка перед 2-й повторной попыткой: backoffMs * (2 ** 1) и т.д.
  Ожидание осуществляется через new Promise(resolve => setTimeout(resolve, delay)).
- options.timeoutMs: максимальное время выполнения одной попытки mapper в миллисекундах (по умолчанию 0 — без таймаута).
  Если попытка mapper длится дольше timeoutMs, она прерывается ошибкой new Error("Timeout"), что приводит к retry (если остались попытки) или провалу задачи.

Сохрани поведение Level 1 (поддержка options как числа или объекта, сохранение порядка, concurrency).

В ответе верни только JavaScript код одним блоком ```javascript ... ```, без пояснений вне блока.
"""

LEVEL3_PROMPT = """\
Дополни свою реализацию pMap поддержкой отмены через AbortSignal и режима settled:

Новые опции в объекте options:
- options.signal: экземпляр AbortSignal (из стандартного AbortController).
  - Если signal уже отменён на момент вызова (signal.aborted === true), pMap должен немедленно реджектиться с ошибкой signal.reason (или new Error("Aborted")), не запуская mapper.
  - Если отмена происходит во время работы: не запускать оставшиеся задачи в очереди и немедленно реджектить pMap с signal.reason (или new Error("Aborted")).
- options.settled: boolean (по умолчанию false).
  - По аналогии с Promise.allSettled: ошибки отдельных задач не приводят к прерыванию pMap.
  - Вместо исходных значений элементов, возвращаемый массив содержит объекты результатов:
    - Для успешных задач: { status: 'fulfilled', value: <результат> }
    - Для задач, завершившихся ошибкой (после исчерпания всех retries): { status: 'rejected', reason: <сообщение или объект ошибки> }
  - Важно: отмена через signal всё равно прерывает весь pMap и реджектит его.

Сохрани поведение Level 1 и Level 2.

В ответе верни только JavaScript код одним блоком ```javascript ... ```, без пояснений вне блока.
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
        return 0, len(cases), [f"Файл {js_path} не найден"]

    try:
        solution_js = js_path.read_text(encoding="utf-8")
    except Exception as e:
        return 0, len(cases), [f"Ошибка чтения файла {js_path}: {e}"]

    # Проверка синтаксиса
    try:
        test_ctx = quickjs.Context()
        test_ctx.set_time_limit(2)
        test_ctx.eval(PRELUDE)
        test_ctx.eval(solution_js)
    except Exception as e:
        return 0, len(cases), [f"Синтаксическая ошибка JavaScript: {e}"]

    passed = 0
    failures: list[str] = []
    for test_name, test_fn in cases:
        try:
            ok = test_fn(solution_js)
            if ok:
                passed += 1
            else:
                failures.append(f"{test_name}: проверка вернула False")
        except Exception as e:
            failures.append(f"{test_name}: исключение {e}")

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
