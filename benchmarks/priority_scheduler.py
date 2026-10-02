"""Priority and Resource Task Scheduler benchmark.

Tests task scheduling with constraints and resource limits:
- Level 1: Deterministic execution order (plan_order) with task priorities, durations, and worker pools.
- Level 2: Critical path analysis (critical_path) and total completion makespan calculation (makespan).
"""

import heapq
from pathlib import Path

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Implement a task scheduler with dependencies, priorities, and a limited worker pool in a single Python file.

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None

Each task is defined by a tuple (duration, deps, priority):
- duration: task duration in integer time units;
- deps: list of task names that must finish before this task can start;
- priority: task priority; higher priority tasks must start earlier.

Execution rules:
- Tasks run non-preemptively;
- At most workers tasks can run simultaneously;
- When multiple tasks are ready to run, select first by highest priority,
  then shortest duration, then alphabetical task name;
- If multiple tasks start at the exact same timestamp, append them to the returned list[str]
  following the same priority tie-breaking rule;
- If there is a cyclic dependency in tasks, return None.

Return only the Python code in a single ```python ... ``` code block, with no explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your implementation with two functions:

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None

Return the length of the longest dependency path by sum of durations, ignoring priority.
If there is a cycle in the dependency graph, return None.

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None

Return the total completion time of all tasks using the same scheduling rules as plan_order.
Use the same deterministic tie-breaking for ready tasks:
descending priority, ascending duration, alphabetical name.
If there is a cycle in the dependency graph, return None.

Do not alter the signature or behavior of plan_order.

Return only the Python code in a single ```python ... ``` code block, with no explanations outside the block.
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
        8,
        8,
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
            failures.append(f"{name}: unexpected exception: {payload}")
            continue

        result = payload
        if expected is None:
            if result is None:
                passed += 1
            else:
                failures.append(f"{name}: expected None (cycle), got {result}")
        else:
            if result == expected:
                passed += 1
            else:
                failures.append(f"{name}: expected {expected}, got {result}")

    return passed, len(LEVEL1_TESTS), failures


def run_priority_level2(solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for name, tasks, workers, expected_order, expected_makespan, expected_cp in LEVEL2_TESTS:
        success_order, order = call_with_timeout(str(solution_path), "plan_order", (tasks, workers))
        success_cp, cp = call_with_timeout(str(solution_path), "critical_path", (tasks,))
        success_ms, ms = call_with_timeout(str(solution_path), "makespan", (tasks, workers))
        if not success_order or not success_cp or not success_ms:
            failed_result = next(
                result
                for success, result in ((success_order, order), (success_cp, cp), (success_ms, ms))
                if not success
            )
            failures.append(f"{name}: unexpected exception: {failed_result}")
            continue

        if expected_order is None:
            if cp is None and ms is None and order is None:
                passed += 1
            else:
                failures.append(f"{name}: expected None, got order={order}, ms={ms}, cp={cp}")
            continue

        if order == expected_order and ms == expected_makespan and cp == expected_cp:
            passed += 1
        else:
            failures.append(
                f"{name}: expected order={expected_order}, ms={expected_makespan}, cp={expected_cp}; "
                f"got order={order}, ms={ms}, cp={cp}"
            )

    return passed, len(LEVEL2_TESTS), failures


class PrioritySchedulerBenchmark(Benchmark):
    id = "priority_scheduler"
    name = "Priority & Resource Task Scheduler"
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
            return TestResult(0, tests_count, [f"failed to load solution: {e}"])

        if level_id == "level1":
            passed, total, failures = run_priority_level1(answer_path)
        else:
            passed, total, failures = run_priority_level2(answer_path)

        return TestResult(passed, total, failures)
