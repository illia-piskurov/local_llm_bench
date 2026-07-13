"""
Тесты для бенчмарка "скобки: баланс + глубина + позиции ошибок".

Level 1: is_balanced(s: str) -> bool
Level 2: max_depth(s: str) -> int, find_unmatched(s: str) -> list[int]
"""

from timeout_utils import call_with_timeout, load_function


# Каждый тест: (имя, строка, ожидаемый bool)
LEVEL1_TESTS = [
    ("empty", "", True),
    ("simple_pairs", "()[]{}", True),
    ("nested", "{[()]}", True),
    ("wrong_order", "([)]", False),
    ("unclosed", "(()", False),
    ("extra_closing", "())", False),
    ("mismatched_types", "(]", False),
    ("ignore_non_bracket", "foo(bar[baz]{qux})", True),
    ("only_text_no_brackets", "hello world", True),
    ("stray_closing_only", ")", False),
    ("deep_nesting", "((((()))))", True),
    ("mixed_fail", "(a[b)c]", False),
]

# Каждый тест: (имя, строка, ожидаемая глубина)
MAX_DEPTH_TESTS = [
    ("empty", "", 0),
    ("flat", "()()()", 1),
    ("nested3", "((()))", 3),
    ("mixed_types_nested", "{[()]}", 3),
    ("unclosed_counts", "(((", 3),
    ("stray_closing_ignored", ")))(((", 3),
    ("mismatched_type_not_popped", "(]", 1),
]

# Каждый тест: (имя, строка, ожидаемый отсортированный список индексов)
UNMATCHED_TESTS = [
    ("all_matched", "()", []),
    ("single_unclosed_open", "(", [0]),
    ("single_stray_close", ")", [0]),
    ("mismatch_and_unclosed", "(]", [0, 1]),
    ("stray_close_after_valid_pair", "())", [2]),
    ("wrong_order_classic", "([)]", [0, 2]),
    ("mixed_with_text", "foo(bar]baz", [3, 7]),
    ("fully_balanced_nested", "{[()]}", []),
]


def run_level1_suite(path):
    passed = 0
    failed = []
    for name, s, expected in LEVEL1_TESTS:
        success, result = call_with_timeout(path, "is_balanced", (s,))
        if not success:
            failed.append((name, f"неожиданное исключение: {result}"))
            continue
        if bool(result) == expected:
            passed += 1
        else:
            failed.append((name, f"ожидалось {expected}, получено {result}"))

    total = len(LEVEL1_TESTS)
    print(f"\n=== LEVEL 1 (is_balanced): {passed}/{total} ===")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    failures = [f"{name}: {reason}" for name, reason in failed]
    return passed, total, failures


def run_level2_suite(path):
    passed = 0
    failed = []

    for name, s, expected in MAX_DEPTH_TESTS:
        success, result = call_with_timeout(path, "max_depth", (s,))
        if not success:
            failed.append((f"max_depth/{name}", f"неожиданное исключение: {result}"))
            continue
        if result == expected:
            passed += 1
        else:
            failed.append((f"max_depth/{name}", f"ожидалось {expected}, получено {result}"))

    for name, s, expected in UNMATCHED_TESTS:
        success, result = call_with_timeout(path, "find_unmatched", (s,))
        if not success:
            failed.append((f"find_unmatched/{name}", f"неожиданное исключение: {result}"))
            continue
        if sorted(result) == expected:
            passed += 1
        else:
            failed.append((f"find_unmatched/{name}", f"ожидалось {expected}, получено {result}"))

    total = len(MAX_DEPTH_TESTS) + len(UNMATCHED_TESTS)
    print(f"\n=== LEVEL 2 (max_depth + find_unmatched): {passed}/{total} ===")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    failures = [f"{name}: {reason}" for name, reason in failed]
    return passed, total, failures
