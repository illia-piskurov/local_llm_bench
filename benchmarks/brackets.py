from pathlib import Path

import bracket_bench
from benchmarks.base import Benchmark, Level, TestResult

LEVEL1_PROMPT = """\
Реализуй проверку сбалансированности скобок в одном Python файле.

def is_balanced(s: str) -> bool

Скобки: () [] {}. Строка может содержать любые другие символы — их нужно игнорировать,
учитывать только скобки.

Строка считается сбалансированной, если:
- каждая открывающая скобка имеет соответствующую закрывающую скобку того же типа;
- скобки закрываются в правильном порядке (последняя открытая — первая закрытая);
- нет лишних закрывающих скобок и нет незакрытых открывающих скобок.

Требования:
- Один файл, без внешних зависимостей.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию двумя функциями:

def max_depth(s: str) -> int

Верни максимальную глубину вложенности скобок при сканировании строки слева направо.
Глубина увеличивается на 1 при каждой открывающей скобке (независимо от того, будет ли
она в итоге закрыта правильно) и уменьшается на 1 только когда встречается закрывающая
скобка, которая корректно закрывает скобку на вершине стека открытых скобок (совпадает
тип). Если закрывающая скобка не совпадает с вершиной стека (или стек пуст) — она не
влияет на глубину и не снимает ничего со стека.

def find_unmatched(s: str) -> list[int]

Верни отсортированный по возрастанию список индексов (0-based) всех "несовпавших"
скобок в строке:
- индексы закрывающих скобок, которые не смогли закрыть ничего на вершине стека
  (стек пуст или тип не совпадает);
- индексы открывающих скобок, которые остались на стеке незакрытыми после
  прохода всей строки.

Не меняй поведение is_balanced и сохрани её сигнатуру.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


class BracketsBenchmark(Benchmark):
    id = "brackets"
    name = "Скобки: баланс + глубина + позиции ошибок"
    short = "Brackets"
    levels = [
        Level(id="level1", name="Level 1 (is_balanced)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (max_depth/find_unmatched)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            try:
                bracket_bench.load_function(str(answer_path), "is_balanced")
            except Exception as e:
                return TestResult(0, len(bracket_bench.LEVEL1_TESTS), [f"не удалось загрузить решение: {e}"])
            passed, total, failures = bracket_bench.run_level1_suite(str(answer_path))
        else:
            total = len(bracket_bench.MAX_DEPTH_TESTS) + len(bracket_bench.UNMATCHED_TESTS)
            try:
                bracket_bench.load_function(str(answer_path), "max_depth")
                bracket_bench.load_function(str(answer_path), "find_unmatched")
            except Exception as e:
                return TestResult(0, total, [f"не удалось загрузить решение: {e}"])
            passed, total, failures = bracket_bench.run_level2_suite(str(answer_path))
        return TestResult(passed, total, failures)
