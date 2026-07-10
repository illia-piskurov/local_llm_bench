from pathlib import Path

import bench
import kv_bench
from benchmarks.base import Benchmark, Level, TestResult

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


class KVBenchmark(Benchmark):
    id = "kv"
    name = "KV-хранилище с транзакциями (SET/GET/BEGIN/COMMIT/ROLLBACK)"
    short = "KV"
    levels = [
        Level(id="level1", name="Level 1 (SET/GET/DELETE + транзакции)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (COUNT/WATCH)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        tests = kv_bench.LEVEL1_TESTS if level_id == "level1" else kv_bench.LEVEL1_TESTS + kv_bench.LEVEL2_TESTS
        name = self.level_by_id(level_id).name
        try:
            run_fn = bench.load_run(str(answer_path))
        except Exception as e:
            return TestResult(0, len(tests), [f"не удалось загрузить решение: {e}"])
        passed, total, failures = bench.run_suite(name, tests, run_fn)
        return TestResult(passed, total, failures)
