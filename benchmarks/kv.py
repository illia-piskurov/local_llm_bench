"""In-memory Key-Value хранилище с транзакциями бенчмарк.

Тестирует способность модели реализовать базу данных в памяти:
- Level 1: SET, GET, DELETE, вложенные транзакции (BEGIN, COMMIT, ROLLBACK).
- Level 2: Агрегации (COUNT) и реактивные слушатели (WATCH key).
- Level 3: Полные снимки состояния и восстановление (SNAPSHOT / RESTORE).
"""

from pathlib import Path
from typing import Any

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Реализуй in-memory key-value хранилище с вложенными транзакциями в одном Python файле.

Поддерживаемые команды (одна на строку, аргументы через пробел):
SET <key> <value>  — установить значение ключа
GET <key>          — вывести текущее значение ключа, или "NULL", если ключ не установлен
DELETE <key>       — удалить ключ (если ключа нет — ничего не делать, без ошибки)
BEGIN              — начать новую (возможно вложенную) транзакцию
COMMIT             — зафиксировать самую внутреннюю открытую транзакцию, слив её изменения
                     в родительскую транзакцию (а не сразу в глобальное хранилище, если
                     это вложенная транзакция). Если открытых транзакций нет — вывести
                     "NO TRANSACTION"
ROLLBACK           — откатить самую внутреннюю открытую транзакцию, отменив все изменения,
                     сделанные внутри неё. Если открытых транзакций нет — вывести
                     "NO TRANSACTION"

Пустые строки — игнорировать.

Требования:
- Один файл, без внешних зависимостей.
- Транзакции можно вкладывать друг в друга произвольно глубоко.
- Изменения внутри транзакции должны быть видны через GET сразу же (даже до COMMIT),
  но должны полностью отменяться при ROLLBACK.
- Добавь функцию run(program: str) -> list[str], возвращающую список строк вывода —
  по одной строке для каждой команды GET, а также для COMMIT/ROLLBACK, если они вывели
  "NO TRANSACTION" (остальные команды вывода не производят).

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию двумя новыми командами:

COUNT <value>  — вывести количество ключей, чьё текущее значение (с учётом открытых
                транзакций) равно <value>
WATCH <key>    — начать наблюдение за ключом. С этого момента при любом SET или DELETE,
                которые меняют видимое в данный момент значение этого ключа (включая
                изменения внутри ещё не зафиксированных транзакций), сразу вывести строку:
                "WATCH <key> <старое_значение> -> <новое_значение>"
                где вместо отсутствующего значения используется "NULL".
                Если SET устанавливает то же значение, что было — уведомление не выводится.
                Уведомления о WATCH выводятся сразу в момент выполнения SET/DELETE, а не
                при COMMIT/ROLLBACK.

Не меняй поведение уже реализованных команд и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL3_PROMPT = """\
Дополни свою реализацию командами snapshot/restore:

SNAPSHOT <name>  — сохранить полное текущее состояние хранилища под именем <name>.
                                     Сохраняется всё: глобальные значения, все открытые транзакции,
                                     watched keys, а также любые внутренние структуры, если они нужны
                                     для корректной работы run().
RESTORE <name>   — восстановить полное состояние из ранее сохранённого snapshot.
                                     После RESTORE хранилище должно вести себя так, будто программа
                                     продолжила выполнение из момента SNAPSHOT. RESTORE не печатает
                                     ничего и сам по себе не должен вызывать WATCH-уведомления.

Требования:
- SNAPSHOT может быть вызван внутри вложенных транзакций, и RESTORE должен вернуть
    именно то состояние, которое было сохранено, включая глубину стека транзакций.
- Если snapshot с таким именем уже существует, перезапиши его.
- RESTORE к неизвестному snapshot можно считать ошибкой или нештатной ситуацией,
    но в тестах этот случай не используется.
- Не меняй поведение уже реализованных команд и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL1_TESTS: list[tuple[str, str, list[str]]] = [
    ("basic_set_get", "SET a 10\nGET a", ["10"]),
    ("get_missing", "GET x", ["NULL"]),
    ("delete_then_get", "SET a 10\nDELETE a\nGET a", ["NULL"]),
    ("delete_missing_key_noop", "DELETE x\nGET x", ["NULL"]),
    ("overwrite_set", "SET a 1\nSET a 2\nGET a", ["2"]),
    ("commit_no_transaction", "COMMIT", ["NO TRANSACTION"]),
    ("rollback_no_transaction", "ROLLBACK", ["NO TRANSACTION"]),
    ("simple_transaction_commit", "BEGIN\nSET a 10\nCOMMIT\nGET a", ["10"]),
    ("simple_transaction_rollback", "SET a 5\nBEGIN\nSET a 10\nROLLBACK\nGET a", ["5"]),
    ("rollback_restores_delete", "SET a 5\nBEGIN\nDELETE a\nGET a\nROLLBACK\nGET a", ["NULL", "5"]),
    (
        "nested_transactions",
        "BEGIN\nSET a 10\nBEGIN\nSET a 20\nGET a\nROLLBACK\nGET a\nROLLBACK\nGET a",
        ["20", "10", "NULL"],
    ),
    (
        "nested_commit_propagates_to_outer_only",
        "BEGIN\nSET a 1\nBEGIN\nSET a 2\nCOMMIT\nGET a\nCOMMIT\nGET a",
        ["2", "2"],
    ),
    ("rollback_after_commit_is_no_transaction", "BEGIN\nSET a 1\nCOMMIT\nROLLBACK", ["NO TRANSACTION"]),
    ("multiple_keys_independent", "SET a 1\nSET b 2\nBEGIN\nSET a 99\nGET b\nROLLBACK\nGET a\nGET b", ["2", "1", "2"]),
    ("set_new_key_inside_transaction", "BEGIN\nSET x 100\nGET x\nCOMMIT\nGET x", ["100", "100"]),
]

LEVEL2_TESTS: list[tuple[str, str, list[str]]] = [
    ("count_basic", "SET a 1\nSET b 1\nSET c 2\nCOUNT 1", ["2"]),
    ("count_zero", "COUNT 5", ["0"]),
    ("count_respects_transaction", "SET a 1\nBEGIN\nSET b 1\nCOUNT 1\nROLLBACK\nCOUNT 1", ["2", "1"]),
    ("count_after_delete", "SET a 1\nSET b 1\nDELETE a\nCOUNT 1", ["1"]),
    ("watch_set_new_key", "WATCH a\nSET a 10", ["WATCH a NULL -> 10"]),
    ("watch_set_change", "SET a 5\nWATCH a\nSET a 10", ["WATCH a 5 -> 10"]),
    ("watch_no_change_no_notification", "SET a 5\nWATCH a\nSET a 5", []),
    ("watch_delete", "SET a 5\nWATCH a\nDELETE a", ["WATCH a 5 -> NULL"]),
    ("watch_unrelated_key_silent", "WATCH a\nSET b 1", []),
    ("watch_inside_transaction_fires", "WATCH a\nBEGIN\nSET a 1", ["WATCH a NULL -> 1"]),
]

LEVEL3_TESTS: list[tuple[str, str, list[str]]] = [
    (
        "snapshot_restores_full_state",
        "SET a 1\nBEGIN\nSET a 2\nSNAPSHOT s\nSET a 3\nRESTORE s\nGET a\nCOMMIT\nGET a",
        ["2", "2"],
    ),
    (
        "snapshot_is_deep_copied",
        "SET a 1\nSNAPSHOT s1\nSET a 2\nSNAPSHOT s2\nSET a 3\nRESTORE s1\nGET a\nRESTORE s2\nGET a",
        ["1", "2"],
    ),
    (
        "restore_preserves_open_transactions",
        "BEGIN\nSET a 1\nSNAPSHOT s\nSET a 2\nROLLBACK\nRESTORE s\nCOMMIT\nGET a",
        ["1"],
    ),
    (
        "restore_keeps_watch_registrations",
        "WATCH a\nSET a 1\nSNAPSHOT s\nSET a 2\nRESTORE s\nSET a 3",
        ["WATCH a NULL -> 1", "WATCH a 1 -> 2", "WATCH a 1 -> 3"],
    ),
    (
        "snapshot_inside_nested_transactions",
        "BEGIN\nSET a 1\nBEGIN\nSET b 2\nSNAPSHOT s\nSET a 3\nROLLBACK\nRESTORE s\nGET a\nGET b\nCOMMIT\nGET a\nGET b",
        ["1", "2", "1", "2"],
    ),
]


def _norm(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return [str(values)]
    return [str(v) for v in values]


def run_kv_suite(tests: list[tuple[str, str, list[str]]], solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for test_name, program, expected in tests:
        success, result = call_with_timeout(str(solution_path), "run", (program,))
        if not success:
            failures.append(f"{test_name}: неожиданное исключение/таймаут: {result}")
            continue

        result_norm = _norm(result)
        if result_norm == expected:
            passed += 1
        else:
            failures.append(f"{test_name}: ожидали {expected}, получили {result_norm}")

    return passed, len(tests), failures


class KVBenchmark(Benchmark):
    id = "kv"
    name = "KV-хранилище с транзакциями (SET/GET/BEGIN/COMMIT/ROLLBACK/SNAPSHOT)"
    short = "KV"
    levels = [
        Level(id="level1", name="Level 1 (SET/GET/DELETE + транзакции)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (COUNT/WATCH)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (SNAPSHOT/RESTORE)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            tests = LEVEL1_TESTS
        elif level_id == "level2":
            tests = LEVEL1_TESTS + LEVEL2_TESTS
        else:
            tests = LEVEL1_TESTS + LEVEL2_TESTS + LEVEL3_TESTS

        try:
            verify_function_exists(answer_path, "run")
        except Exception as e:
            return TestResult(0, len(tests), [f"не удалось загрузить решение: {e}"])

        passed, total, failures = run_kv_suite(tests, answer_path)
        return TestResult(passed, total, failures)
