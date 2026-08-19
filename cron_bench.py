"""
Бенчмарк для локальных LLM: парсер cron-выражений и планировщик дат.

Использование:
    python cron_bench.py path/to/solution.py

Файл solution.py должен содержать функцию:
    next_runs(cron: str, from_time: str, count: int) -> list[str]
где:
    cron: 5-позиционная строка ("минута час день_месяца месяц день_недели") или алиас
    from_time: ISO 8601 UTC строка (например "2026-08-18T10:00:00.000Z")
    count: количество следующих дат строго после from_time
возвращает:
    список из count ISO 8601 UTC строк ("YYYY-MM-DDTHH:MM:SS.000Z")
"""

import importlib.util
import sys
import traceback

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from timeout_utils import call_with_timeout


def load_next_runs(path: str):
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "next_runs"):
        raise AttributeError("В решении не найдена функция next_runs(cron: str, from_time: str, count: int) -> list[str]")
    return module.next_runs


# Каждый тест: (имя, cron, from_time, count, expected_iso_list)

LEVEL1_TESTS = [
    (
        "hourly_zero_minute",
        "0 * * * *",
        "2026-08-18T10:15:00.000Z",
        2,
        ["2026-08-18T11:00:00.000Z", "2026-08-18T12:00:00.000Z"],
    ),
    (
        "exact_daily_time",
        "30 8 * * *",
        "2026-08-18T08:00:00.000Z",
        2,
        ["2026-08-18T08:30:00.000Z", "2026-08-19T08:30:00.000Z"],
    ),
    (
        "minute_list",
        "0,15,30,45 12 * * *",
        "2026-08-18T12:10:00.000Z",
        3,
        ["2026-08-18T12:15:00.000Z", "2026-08-18T12:30:00.000Z", "2026-08-18T12:45:00.000Z"],
    ),
    (
        "hour_range",
        "0 9-11 * * *",
        "2026-08-18T08:00:00.000Z",
        3,
        ["2026-08-18T09:00:00.000Z", "2026-08-18T10:00:00.000Z", "2026-08-18T11:00:00.000Z"],
    ),
    (
        "first_of_month",
        "0 0 1 * *",
        "2026-08-18T00:00:00.000Z",
        2,
        ["2026-09-01T00:00:00.000Z", "2026-10-01T00:00:00.000Z"],
    ),
    (
        "specific_day_of_week",
        "0 12 * * 1",
        "2026-08-18T00:00:00.000Z",
        2,
        ["2026-08-24T12:00:00.000Z", "2026-08-31T12:00:00.000Z"],
    ),
    (
        "strictly_after_exact_match",
        "0 10 * * *",
        "2026-08-18T10:00:00.000Z",
        1,
        ["2026-08-19T10:00:00.000Z"],
    ),
]

LEVEL2_TESTS = [
    (
        "every_15_minutes_in_work_hours",
        "*/15 9-17 * * 1-5",
        "2026-08-18T10:00:00.000Z",
        3,
        ["2026-08-18T10:15:00.000Z", "2026-08-18T10:30:00.000Z", "2026-08-18T10:45:00.000Z"],
    ),
    (
        "step_with_range",
        "10-20/5 8 * * *",
        "2026-08-18T08:00:00.000Z",
        3,
        ["2026-08-18T08:10:00.000Z", "2026-08-18T08:15:00.000Z", "2026-08-18T08:20:00.000Z"],
    ),
    (
        "dom_and_dow_or_rule",
        "0 0 1,15 * 5",
        "2026-08-01T00:00:00.000Z",
        4,
        ["2026-08-07T00:00:00.000Z", "2026-08-14T00:00:00.000Z", "2026-08-15T00:00:00.000Z", "2026-08-21T00:00:00.000Z"],
    ),
    (
        "every_two_months",
        "0 0 1 */2 *",
        "2026-01-01T00:00:00.000Z",
        3,
        ["2026-03-01T00:00:00.000Z", "2026-05-01T00:00:00.000Z", "2026-07-01T00:00:00.000Z"],
    ),
    (
        "cross_year_boundary",
        "0 0 1 1 *",
        "2026-08-01T00:00:00.000Z",
        2,
        ["2027-01-01T00:00:00.000Z", "2028-01-01T00:00:00.000Z"],
    ),
]

LEVEL3_TESTS = [
    (
        "alias_hourly",
        "@hourly",
        "2026-08-18T10:15:00.000Z",
        2,
        ["2026-08-18T11:00:00.000Z", "2026-08-18T12:00:00.000Z"],
    ),
    (
        "alias_daily",
        "@daily",
        "2026-08-18T10:00:00.000Z",
        2,
        ["2026-08-19T00:00:00.000Z", "2026-08-20T00:00:00.000Z"],
    ),
    (
        "alias_monthly",
        "@monthly",
        "2026-08-18T00:00:00.000Z",
        2,
        ["2026-09-01T00:00:00.000Z", "2026-10-01T00:00:00.000Z"],
    ),
    (
        "alias_weekly",
        "@weekly",
        "2026-08-18T00:00:00.000Z",
        2,
        ["2026-08-23T00:00:00.000Z", "2026-08-30T00:00:00.000Z"],
    ),
    (
        "leap_year_feb_29",
        "0 12 29 2 *",
        "2026-01-01T00:00:00.000Z",
        1,
        ["2028-02-29T12:00:00.000Z"],
    ),
    (
        "leap_year_next",
        "0 12 29 2 *",
        "2028-03-01T00:00:00.000Z",
        1,
        ["2032-02-29T12:00:00.000Z"],
    ),
    (
        "end_of_year_minute_transition",
        "59 23 31 12 *",
        "2026-12-31T23:58:00.000Z",
        2,
        ["2026-12-31T23:59:00.000Z", "2027-12-31T23:59:00.000Z"],
    ),
]


def norm_iso(iso_str: str) -> str:
    """Приводит ISO дату к стандартному YYYY-MM-DDTHH:MM:SS.000Z виду."""
    s = str(iso_str).strip()
    if s.endswith("+00:00"):
        s = s[:-6] + "Z"
    if not s.endswith("Z"):
        s += "Z"
    if ".000Z" not in s and "Z" in s:
        s = s.replace("Z", ".000Z")
    return s


def run_suite(name: str, tests: list, path: str):
    passed = 0
    failed = []
    for test_name, cron_str, from_time, count, expected in tests:
        success, result = call_with_timeout(path, "next_runs", (cron_str, from_time, count))
        if not success:
            failed.append((test_name, f"исключение/таймаут: {result}"))
            continue

        if not isinstance(result, list):
            failed.append((test_name, f"ожидался list, получено {type(result).__name__}"))
            continue

        norm_result = [norm_iso(x) for x in result]
        norm_expected = [norm_iso(x) for x in expected]

        if norm_result == norm_expected:
            passed += 1
        else:
            failed.append((test_name, f"ожидалось {norm_expected}, получено {norm_result}"))

    total = len(tests)
    print(f"\n=== {name}: {passed}/{total} ===")
    for test_name, reason in failed:
        print(f"  [FAIL] {test_name}: {reason}")
    failures = [f"{test_name}: {reason}" for test_name, reason in failed]
    return passed, total, failures


def main():
    if len(sys.argv) != 2:
        print("Использование: python cron_bench.py path/to/solution.py")
        sys.exit(1)

    path = sys.argv[1]
    try:
        load_next_runs(path)
    except Exception as e:
        print(f"Не удалось загрузить решение: {e}")
        traceback.print_exc()
        sys.exit(1)

    p1, t1, _ = run_suite("LEVEL 1", LEVEL1_TESTS, path)
    p2, t2, _ = run_suite("LEVEL 2", LEVEL2_TESTS, path)
    p3, t3, _ = run_suite("LEVEL 3", LEVEL3_TESTS, path)

    print("\n=== ИТОГО ===")
    print(f"Level 1: {p1}/{t1}")
    print(f"Level 2: {p2}/{t2}")
    print(f"Level 3: {p3}/{t3}")
    print(f"Всего:   {p1 + p2 + p3}/{t1 + t2 + t3}")


if __name__ == "__main__":
    main()
