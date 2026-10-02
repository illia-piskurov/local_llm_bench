"""Планировщик с приоритетами и ресурсами бенчмарк.

Тестирует способность модели реализовать планировщик задач с учетом ограничений:
- Level 1: Порядок выполнения задач (plan_order) с учетом приоритетов, длительности, имен и пула воркеров.
- Level 2: Расчет критического пути (critical_path) и общего времени выполнения (makespan).
"""

import heapq
from pathlib import Path

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Реализуй планировщик задач с зависимостями, приоритетами и ограниченным числом исполнителей в одном Python файле.

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None

Каждая задача задаётся кортежем (duration, deps, priority):
- duration — длительность задачи в целых единицах времени;
- deps — список имён задач, которые должны завершиться раньше;
- priority — приоритет задачи, чем больше, тем раньше она должна стартовать.

Правила выполнения:
- задачи выполняются не прерываясь;
- одновременно могут идти не более workers задач;
- когда несколько задач готовы к запуску, выбирай сначала с большим priority,
  затем с меньшей duration, затем по имени по возрастанию;
- если несколько задач стартуют в один и тот же момент, возвращай их в list[str]
  в порядке этого же правила;
- если в зависимостях есть цикл, верни None.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию двумя функциями:

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None

Верни длину самого длинного зависимого пути по сумме duration, игнорируя priority.
Если в графе зависимостей есть цикл — верни None.

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None

Верни общее время завершения всех задач при тех же правилах выбора задач, что и в plan_order.
Используй тот же детерминированный порядок выбора готовых задач:
priority по убыванию, duration по возрастанию, name по возрастанию.
Если в графе зависимостей есть цикл — верни None.

Не меняй сигнатуру plan_order.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


def _ready_key(name: str, task: tuple[int, list[str], int]) -> tuple[int, int, str]:
    duration, _deps, priority = task
    return (-priority, duration, name)


def simulate_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    if workers <= 0:
        return None

    durations = {name: spec[0] for name, spec in tasks.items()}
    dependents: dict[str, list[str]] = {name: [] for name in tasks}
    indeg = {name: len(spec[1]) for name, spec in tasks.items()}

    for name, spec in tasks.items():
        for dep in spec[1]:
            if dep not in tasks:
                return None
            dependents.setdefault(dep, []).append(name)

    ready = [name for name, degree in indeg.items() if degree == 0]
    order: list[str] = []
    time = 0
    running: list[tuple[int, str]] = []
    started: set[str] = set()

    def push_ready() -> None:
        nonlocal ready
        ready.sort(key=lambda name: _ready_key(name, tasks[name]))

    push_ready()

    while len(order) < len(tasks):
        while ready and len(running) < workers:
            push_ready()
            name = ready.pop(0)
            started.add(name)
            order.append(name)
            heapq.heappush(running, (time + durations[name], name))

        if not running:
            if len(order) == len(tasks):
                break
            return None

        time = running[0][0]
        finished = []
        while running and running[0][0] == time:
            _finish_time, name = heapq.heappop(running)
            finished.append(name)

        for name in finished:
            for nxt in dependents.get(name, []):
                indeg[nxt] -= 1
                if indeg[nxt] == 0 and nxt not in started:
                    ready.append(nxt)
        push_ready()

    return order


LEVEL1_TESTS: list[tuple[str, dict[str, tuple[int, list[str], int]], int, list[str] | None]] = [
    (
        "priority_beats_name_order",
        {
            "a": (3, [], 1),
            "b": (1, [], 5),
            "c": (2, [], 3),
        },
        2,
        ["b", "c", "a"],
    ),
    (
        "dependency_unlocks_later",
        {
            "a": (2, [], 1),
            "b": (1, ["a"], 10),
            "c": (1, ["a"], 5),
        },
        2,
        ["a", "b", "c"],
    ),
    (
        "single_worker_duration_tiebreak",
        {
            "a": (3, [], 1),
            "b": (1, [], 1),
            "c": (2, [], 1),
        },
        1,
        ["b", "c", "a"],
    ),
    (
        "resource_limit_and_priority",
        {
            "compile": (5, [], 5),
            "lint": (1, [], 3),
            "test": (2, ["compile"], 10),
            "package": (1, ["test", "lint"], 8),
            "deploy": (1, ["package"], 1),
        },
        2,
        ["compile", "lint", "test", "package", "deploy"],
    ),
    (
        "simultaneous_unlocks",
        {
            "root": (1, [], 1),
            "b": (1, ["root"], 1),
            "c": (1, ["root"], 5),
            "d": (1, ["root"], 3),
        },
        2,
        ["root", "c", "d", "b"],
    ),
    (
        "cycle_returns_none",
        {
            "a": (1, ["b"], 1),
            "b": (1, ["a"], 1),
        },
        2,
        None,
    ),
]

LEVEL2_TESTS = [
    (
        "single_task",
        {"a": (5, [], 1)},
        2,
        ["a"],
        5,
        5,
    ),
    (
        "parallel_tasks_reduce_makespan",
        {
            "a": (3, [], 1),
            "b": (2, [], 2),
            "c": (1, [], 3),
        },
        2,
        ["c", "b", "a"],
        4,
        3,
    ),
    (
        "dependencies_and_workers",
        {
            "a": (2, [], 1),
            "b": (5, ["a"], 1),
            "c": (1, ["a"], 10),
            "d": (4, ["b", "c"], 1),
        },
        2,
        ["a", "c", "b", "d"],
        11,
        11,
    ),
    (
        "critical_path_longer_than_worker_parallelism",
        {
            "a": (4, [], 1),
            "b": (4, [], 1),
            "c": (4, [], 1),
            "d": (4, [], 1),
        },
        1,
        ["a", "b", "c", "d"],
        16,
        4,
    ),
    (
        "wide_graph_with_unlocks",
        {
            "fetch": (2, [], 3),
            "compile": (4, [], 5),
            "test": (3, ["compile", "fetch"], 10),
            "package": (1, ["test"], 1),
        },
        2,
        ["compile", "fetch", "test", "package"],
        7,
        9,
    ),
    (
        "cycle_returns_none",
        {
            "a": (1, ["b"], 1),
            "b": (1, ["a"], 1),
        },
        2,
        None,
        None,
        None,
    ),
]


def run_priority_level1(solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for name, tasks, workers, expected in LEVEL1_TESTS:
        success, payload = call_with_timeout(str(solution_path), "plan_order", (tasks, workers))
        if not success:
            failures.append(f"{name}: неожиданное исключение: {payload}")
            continue

        result = payload
        if expected is None:
            if result is None:
                passed += 1
            else:
                failures.append(f"{name}: ожидался None (цикл), получено {result}")
        else:
            if result == expected:
                passed += 1
            else:
                failures.append(f"{name}: ожидалось {expected}, получено {result}")

    return passed, len(LEVEL1_TESTS), failures


def run_priority_level2(solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for name, tasks, workers, expected_order, expected_makespan, expected_cp in LEVEL2_TESTS:
        success_cp, cp = call_with_timeout(str(solution_path), "critical_path", (tasks,))
        success_ms, ms = call_with_timeout(str(solution_path), "makespan", (tasks, workers))
        if not success_cp or not success_ms:
            if expected_order is None:
                passed += 1
            else:
                reason = cp if not success_cp else ms
                failures.append(f"{name}: неожиданное исключение: {reason}")
            continue

        order = simulate_order(tasks, workers)

        if expected_order is None:
            if cp is None and ms is None and order is None:
                passed += 1
            else:
                failures.append(f"{name}: ожидались None, получено order={order}, ms={ms}, cp={cp}")
            continue

        if order == expected_order and ms == expected_makespan and cp == expected_cp:
            passed += 1
        else:
            failures.append(
                f"{name}: ожидалось order={expected_order}, ms={expected_makespan}, cp={expected_cp}; "
                f"получено order={order}, ms={ms}, cp={cp}"
            )

    return passed, len(LEVEL2_TESTS), failures


class PrioritySchedulerBenchmark(Benchmark):
    id = "priority_scheduler"
    name = "Планировщик с приоритетами и ресурсами"
    short = "PrioSched"
    levels = [
        Level(id="level1", name="Level 1 (plan_order)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (critical_path + makespan)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        func_name = "plan_order" if level_id == "level1" else "critical_path"
        tests_count = len(LEVEL1_TESTS) if level_id == "level1" else len(LEVEL2_TESTS)

        try:
            verify_function_exists(answer_path, func_name)
        except Exception as e:
            return TestResult(0, tests_count, [f"не удалось загрузить решение: {e}"])

        if level_id == "level1":
            passed, total, failures = run_priority_level1(answer_path)
        else:
            passed, total, failures = run_priority_level2(answer_path)

        return TestResult(passed, total, failures)
