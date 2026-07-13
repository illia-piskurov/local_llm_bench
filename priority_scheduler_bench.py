"""
Тесты для бенчмарка "планировщик с приоритетами и ресурсами".

Level 1: plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None
Level 2: critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None
         makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None
"""

import heapq

from timeout_utils import call_with_timeout, load_function

_call_function_in_subprocess = call_with_timeout


def _ready_key(name: str, task: tuple[int, list[str], int]) -> tuple[int, int, str]:
    duration, _deps, priority = task
    return (-priority, duration, name)


def simulate_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    if workers <= 0:
        return None

    durations = {name: spec[0] for name, spec in tasks.items()}
    deps = {name: list(spec[1]) for name, spec in tasks.items()}
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


def critical_path_value(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    state: dict[str, int] = {}

    def dfs(name: str) -> int | None:
        if name not in tasks:
            return None
        marker = state.get(name, 0)
        if marker == 1:
            return None
        if marker == 2:
            return memo[name]

        state[name] = 1
        duration, deps, _priority = tasks[name]
        best = 0
        for dep in deps:
            value = dfs(dep)
            if value is None:
                return None
            if value > best:
                best = value
        state[name] = 2
        memo[name] = duration + best
        return memo[name]

    memo: dict[str, int] = {}
    best = 0
    for name in tasks:
        value = dfs(name)
        if value is None:
            return None
        if value > best:
            best = value
    return best


def makespan_value(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    order = simulate_order(tasks, workers)
    if order is None:
        return None

    # Re-simulate to compute the finish time deterministically.
    durations = {name: spec[0] for name, spec in tasks.items()}
    indeg = {name: len(spec[1]) for name, spec in tasks.items()}
    dependents: dict[str, list[str]] = {name: [] for name in tasks}
    for name, spec in tasks.items():
        for dep in spec[1]:
            dependents.setdefault(dep, []).append(name)

    ready = [name for name, degree in indeg.items() if degree == 0]
    ready.sort(key=lambda name: _ready_key(name, tasks[name]))
    time = 0
    running: list[tuple[int, str]] = []
    started: set[str] = set()
    finished_count = 0

    while finished_count < len(tasks):
        while ready and len(running) < workers:
            name = ready.pop(0)
            started.add(name)
            heapq.heappush(running, (time + durations[name], name))

        if not running:
            return None

        time = running[0][0]
        finished = []
        while running and running[0][0] == time:
            _finish_time, name = heapq.heappop(running)
            finished.append(name)
            finished_count += 1

        for name in finished:
            for nxt in dependents.get(name, []):
                indeg[nxt] -= 1
                if indeg[nxt] == 0 and nxt not in started:
                    ready.append(nxt)
        ready.sort(key=lambda name: _ready_key(name, tasks[name]))

    return time


LEVEL1_TESTS = [
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
        {
            "a": (5, [], 1),
        },
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


def run_level1_suite(solution_path: str):
    passed = 0
    failed = []
    for name, tasks, workers, expected in LEVEL1_TESTS:
        success, payload = _call_function_in_subprocess(solution_path, "plan_order", (tasks, workers))
        if not success:
            failed.append((name, f"неожиданное исключение: {payload}"))
            continue
        result = payload

        if expected is None:
            if result is None:
                passed += 1
            else:
                failed.append((name, f"ожидался None (цикл), получено {result}"))
        else:
            if result == expected:
                passed += 1
            else:
                failed.append((name, f"ожидалось {expected}, получено {result}"))

    total = len(LEVEL1_TESTS)
    print(f"\n=== LEVEL 1 (plan_order): {passed}/{total} ===")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    failures = [f"{name}: {reason}" for name, reason in failed]
    return passed, total, failures


def run_level2_suite(solution_path: str):
    passed = 0
    failed = []
    for name, tasks, workers, expected_order, expected_makespan, expected_cp in LEVEL2_TESTS:
        success_cp, cp = _call_function_in_subprocess(solution_path, "critical_path", (tasks,))
        success_ms, ms = _call_function_in_subprocess(solution_path, "makespan", (tasks, workers))
        if not success_cp or not success_ms:
            if expected_order is None:
                passed += 1
            else:
                reason = cp if not success_cp else ms
                failed.append((name, f"неожиданное исключение: {reason}"))
            continue

        order = simulate_order(tasks, workers)

        if expected_order is None:
            if cp is None and ms is None and order is None:
                passed += 1
            else:
                failed.append((name, f"ожидались None, получено order={order}, ms={ms}, cp={cp}"))
            continue

        if order == expected_order and ms == expected_makespan and cp == expected_cp:
            passed += 1
        else:
            failed.append((name, f"ожидалось order={expected_order}, ms={expected_makespan}, cp={expected_cp}; получено order={order}, ms={ms}, cp={cp}"))

    total = len(LEVEL2_TESTS)
    print(f"\n=== LEVEL 2 (critical_path/makespan): {passed}/{total} ===")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    failures = [f"{name}: {reason}" for name, reason in failed]
    return passed, total, failures