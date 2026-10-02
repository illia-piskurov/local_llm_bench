"""Планировщик задач с зависимостями бенчмарк.

Тестирует способность модели работать с графами задач и зависимостями:
- Level 1: Топологическая сортировка графа (topo_sort) и обнаружение циклов (возврат None).
- Level 2: Расчёт критического пути (critical_path - самая длинная зависимая цепочка).
"""

from pathlib import Path
from typing import Any

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Реализуй планировщик задач с зависимостями в одном Python файле.

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None

tasks — словарь, где ключ — имя задачи (строка), а значение — список имён задач,
от которых она зависит (эти задачи должны быть выполнены раньше).

Функция должна вернуть список имён всех задач в порядке, при котором каждая задача
идёт строго после всех своих зависимостей (топологическая сортировка).
Если в графе зависимостей есть цикл — верни None.

Требования:
- Один файл, без внешних зависимостей (никаких networkx и т.п.).
- Порядок среди задач, не зависящих друг от друга, может быть любым — важно только,
  чтобы зависимости шли раньше зависимых от них задач.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию функцией расчёта критического пути:

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None

tasks — словарь, где значение — кортеж (длительность_задачи, список_зависимостей).
Функция должна вернуть длину критического пути — суммарную длительность самой долгой
по времени цепочки зависимых друг от друга задач (classic critical path method).
Если в графе зависимостей есть цикл — верни None.

Не меняй сигнатуру и поведение topo_sort.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
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
            failures.append(f"{name}: неожиданное исключение/таймаут: {result}")
            continue

        if expected is None:
            if result is None:
                passed += 1
            else:
                failures.append(f"{name}: ожидался None (цикл), получено {result}")
        else:
            if is_valid_topo_order(tasks, result):
                passed += 1
            else:
                failures.append(f"{name}: невалидный топологический порядок: {result}")

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
                failures.append(f"{name}: неожиданное исключение/таймаут: {result}")
            continue

        if result == expected:
            passed += 1
        else:
            failures.append(f"{name}: ожидалось {expected}, получено {result}")

    return passed, len(LEVEL2_TESTS), failures


class SchedulerBenchmark(Benchmark):
    id = "scheduler"
    name = "Планировщик задач (topo sort + critical path)"
    short = "Scheduler"
    levels = [
        Level(id="level1", name="Level 1 (topo_sort + циклы)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (critical_path)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        func_name = "topo_sort" if level_id == "level1" else "critical_path"
        tests_count = len(LEVEL1_TESTS) if level_id == "level1" else len(LEVEL2_TESTS)

        try:
            verify_function_exists(answer_path, func_name)
        except Exception as e:
            return TestResult(0, tests_count, [f"не удалось загрузить решение: {e}"])

        if level_id == "level1":
            passed, total, failures = run_scheduler_level1(answer_path)
        else:
            passed, total, failures = run_scheduler_level2(answer_path)

        return TestResult(passed, total, failures)
