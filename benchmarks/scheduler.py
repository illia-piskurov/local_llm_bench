"""Task Scheduler with Dependencies benchmark.

Tests task dependency graph analysis and ordering:
- Level 1: Directed acyclic graph topological sorting (topo_sort) and cycle detection (return None).
- Level 2: Critical path method analysis (critical_path - longest dependent task chain).
"""

from pathlib import Path
from typing import Any

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Implement a task dependency scheduler in a single Python file.

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None

tasks is a dictionary where the key is the task name (str), and the value is a list of
dependency task names that must complete prior to this task.

The function must return a list of all task names in an order where every task appears
strictly after all of its dependencies (topological sort).
If the dependency graph contains a cycle, return None.

Requirements:
- Single file, no external dependencies (no networkx, etc.).
- The relative order between independent tasks is arbitrary — only the dependency
  ordering guarantee is required.

Return only the Python code in a single ```python ... ``` code block, with no explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your implementation with a critical path calculation function:

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None

tasks is a dictionary where each value is a tuple of (duration, dependencies_list).
The function must return the length of the critical path — the total duration of the
longest dependent sequence of tasks (classic critical path method).
If the dependency graph contains a cycle, return None.

Preserve the signature and behavior of topo_sort.

Return only the Python code in a single ```python ... ``` code block, with no explanations outside the block.
"""


def is_valid_topo_order(tasks: dict[str, list[str]], order: list[str] | None) -> bool:
    if order is None:
        return False
    if set(order) != set(tasks.keys()):
        return False
    position = {name: i for i, name in enumerate(order)}
    for name, deps in tasks.items():
        for dep in deps:
            if dep not in position or position[dep] >= position[name]:
                return False
    return True


LEVEL1_TESTS: list[tuple[str, dict[str, list[str]], Any]] = [
    ("no_dependencies", {"a": [], "b": [], "c": []}, "VALID_ORDER"),
    ("simple_chain", {"a": [], "b": ["a"], "c": ["b"]}, "VALID_ORDER"),
    ("diamond", {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}, "VALID_ORDER"),
    ("multiple_roots", {"a": [], "b": [], "c": ["a", "b"], "d": ["c"]}, "VALID_ORDER"),
    ("single_task", {"a": []}, "VALID_ORDER"),
    ("self_cycle", {"a": ["a"]}, None),
    ("two_node_cycle", {"a": ["b"], "b": ["a"]}, None),
    ("long_cycle", {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["a"]}, None),
    ("cycle_with_extra_nodes", {"a": [], "b": ["a"], "c": ["b", "d"], "d": ["c"]}, None),
    (
        "wide_graph",
        {
            "compile": [],
            "lint": [],
            "test": ["compile"],
            "package": ["test", "lint"],
            "deploy": ["package"],
        },
        "VALID_ORDER",
    ),
]

LEVEL2_TESTS: list[tuple[str, dict[str, tuple[int, list[str]]], Any]] = [
    ("single_task", {"a": (5, [])}, 5),
    ("simple_chain", {"a": (2, []), "b": (3, ["a"]), "c": (4, ["b"])}, 9),
    (
        "diamond_pick_longer_branch",
        {
            "a": (1, []),
            "b": (10, ["a"]),
            "c": (1, ["a"]),
            "d": (1, ["b", "c"]),
        },
        12,
    ),
    ("independent_tasks", {"a": (3, []), "b": (7, []), "c": (2, [])}, 7),
    (
        "wide_graph",
        {
            "compile": (10, []),
            "lint": (2, []),
            "test": (5, ["compile"]),
            "package": (3, ["test", "lint"]),
            "deploy": (1, ["package"]),
        },
        19,
    ),
    ("cycle_returns_none", {"a": (1, ["b"]), "b": (1, ["a"])}, None),
]


def run_scheduler_level1(solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for name, tasks, expected in LEVEL1_TESTS:
        success, result = call_with_timeout(str(solution_path), "topo_sort", (tasks,))
        if not success:
            failures.append(f"{name}: unexpected exception/timeout: {result}")
            continue

        if expected is None:
            if result is None:
                passed += 1
            else:
                failures.append(f"{name}: expected None (cycle), got {result}")
        else:
            if is_valid_topo_order(tasks, result):
                passed += 1
            else:
                failures.append(f"{name}: invalid topological order: {result}")

    return passed, len(LEVEL1_TESTS), failures


def run_scheduler_level2(solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for name, tasks, expected in LEVEL2_TESTS:
        success, result = call_with_timeout(str(solution_path), "critical_path", (tasks,))
        if not success:
            if expected is None:
                passed += 1
            else:
                failures.append(f"{name}: unexpected exception/timeout: {result}")
            continue

        if result == expected:
            passed += 1
        else:
            failures.append(f"{name}: expected {expected}, got {result}")

    return passed, len(LEVEL2_TESTS), failures


class SchedulerBenchmark(Benchmark):
    id = "scheduler"
    name = "Task Scheduler (topo sort + critical path)"
    short = "Scheduler"
    levels = [
        Level(id="level1", name="Level 1 (topo_sort + cycles)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (critical_path)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        func_name = "topo_sort" if level_id == "level1" else "critical_path"
        tests_count = len(LEVEL1_TESTS) if level_id == "level1" else len(LEVEL2_TESTS)

        try:
            verify_function_exists(answer_path, func_name)
        except Exception as e:
            return TestResult(0, tests_count, [f"failed to load solution: {e}"])

        if level_id == "level1":
            passed, total, failures = run_scheduler_level1(answer_path)
        else:
            passed, total, failures = run_scheduler_level2(answer_path)

        return TestResult(passed, total, failures)
