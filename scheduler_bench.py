"""
Тесты для бенчмарка "планировщик задач с зависимостями".

Level 1: topo_sort(tasks: dict[str, list[str]]) -> list[str] | None
Level 2: critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None
"""

import importlib.util


def load_function(path, func_name):
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, func_name):
        raise AttributeError(f"В решении не найдена функция {func_name}(...)")
    return getattr(module, func_name)


def is_valid_topo_order(tasks, order):
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


# Каждый тест: (имя, tasks, expected)
# expected == "VALID_ORDER" -> проверяем корректность порядка (не точное совпадение)
# expected == None -> ожидаем цикл (функция должна вернуть None)

LEVEL1_TESTS = [
    (
        "no_dependencies",
        {"a": [], "b": [], "c": []},
        "VALID_ORDER",
    ),
    (
        "simple_chain",
        {"a": [], "b": ["a"], "c": ["b"]},
        "VALID_ORDER",
    ),
    (
        "diamond",
        # a -> b, a -> c, b,c -> d
        {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]},
        "VALID_ORDER",
    ),
    (
        "multiple_roots",
        {"a": [], "b": [], "c": ["a", "b"], "d": ["c"]},
        "VALID_ORDER",
    ),
    (
        "single_task",
        {"a": []},
        "VALID_ORDER",
    ),
    (
        "self_cycle",
        {"a": ["a"]},
        None,
    ),
    (
        "two_node_cycle",
        {"a": ["b"], "b": ["a"]},
        None,
    ),
    (
        "long_cycle",
        {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["a"]},
        None,
    ),
    (
        "cycle_with_extra_nodes",
        {"a": [], "b": ["a"], "c": ["b", "d"], "d": ["c"]},
        None,
    ),
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

# Каждый тест: (имя, weighted_tasks, expected_length_or_None)
LEVEL2_TESTS = [
    (
        "single_task",
        {"a": (5, [])},
        5,
    ),
    (
        "simple_chain",
        # a(2) -> b(3) -> c(4): критический путь = 2+3+4 = 9
        {"a": (2, []), "b": (3, ["a"]), "c": (4, ["b"])},
        9,
    ),
    (
        "diamond_pick_longer_branch",
        # a(1) -> b(10) -> d(1)
        # a(1) -> c(1) -> d(1)
        # критический путь идёт через b: 1+10+1 = 12
        {
            "a": (1, []),
            "b": (10, ["a"]),
            "c": (1, ["a"]),
            "d": (1, ["b", "c"]),
        },
        12,
    ),
    (
        "independent_tasks",
        # нет зависимостей — критический путь = самая длинная одиночная задача
        {"a": (3, []), "b": (7, []), "c": (2, [])},
        7,
    ),
    (
        "wide_graph",
        {
            "compile": (10, []),
            "lint": (2, []),
            "test": (5, ["compile"]),
            "package": (3, ["test", "lint"]),
            "deploy": (1, ["package"]),
        },
        # compile(10) -> test(5) -> package(3) -> deploy(1) = 19
        19,
    ),
    (
        "cycle_returns_none",
        {"a": (1, ["b"]), "b": (1, ["a"])},
        None,
    ),
]


def run_level1_suite(topo_sort_fn):
    passed = 0
    failed = []
    for name, tasks, expected in LEVEL1_TESTS:
        try:
            result = topo_sort_fn(tasks)
        except Exception as e:
            failed.append((name, f"неожиданное исключение: {e}"))
            continue

        if expected is None:
            if result is None:
                passed += 1
            else:
                failed.append((name, f"ожидался None (цикл), получено {result}"))
        else:  # "VALID_ORDER"
            if is_valid_topo_order(tasks, result):
                passed += 1
            else:
                failed.append((name, f"невалидный топологический порядок: {result}"))

    total = len(LEVEL1_TESTS)
    print(f"\n=== LEVEL 1 (topo_sort): {passed}/{total} ===")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    return passed, total


def run_level2_suite(critical_path_fn):
    passed = 0
    failed = []
    for name, tasks, expected in LEVEL2_TESTS:
        try:
            result = critical_path_fn(tasks)
        except Exception as e:
            if expected is None:
                passed += 1
            else:
                failed.append((name, f"неожиданное исключение: {e}"))
            continue

        if result == expected:
            passed += 1
        else:
            failed.append((name, f"ожидалось {expected}, получено {result}"))

    total = len(LEVEL2_TESTS)
    print(f"\n=== LEVEL 2 (critical_path): {passed}/{total} ===")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    return passed, total
