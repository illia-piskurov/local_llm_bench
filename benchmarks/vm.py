from pathlib import Path

import bench
from benchmarks.base import Benchmark, Level, TestResult

LEVEL1_PROMPT = """\
Реализуй интерпретатор простого стекового языка в одном Python файле.

Поддерживаемые инструкции (одна на строку, аргументы через пробел):
PUSH <n>  — положить число n на стек
POP       — снять значение со стека
ADD       — снять два значения, положить их сумму
SUB       — снять два значения (b, затем a), положить a - b
MUL       — снять два значения, положить произведение
DIV       — снять два значения (b, затем a), положить a / b (целочисленное деление)
DUP       — продублировать значение на вершине стека
SWAP      — поменять местами два верхних значения стека
PRINT     — вывести значение на вершине стека (не снимая его)

Программа передаётся как многострочный текст. Пустые строки и строки, начинающиеся с "#", — комментарии, их нужно игнорировать.

Требования:
- Один файл, без внешних зависимостей.
- Если стека не хватает для операции — кинуть понятную ошибку с номером строки.
- Деление на ноль — понятная ошибка с номером строки.
- Добавь функцию run(program: str) -> list[str], возвращающую список выведенных строк (то, что напечатал PRINT).

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию поддержкой меток и условных переходов:

LABEL <name>   — определяет метку в текущей позиции (ничего не делает при выполнении)
JMP <name>     — безусловный переход к метке
JZ <name>      — снять значение со стека, перейти к метке, если оно == 0
JNZ <name>     — снять значение со стека, перейти к метке, если оно != 0

Не меняй поведение уже реализованных инструкций и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


class VMBenchmark(Benchmark):
    id = "vm"
    name = "Стековая VM (PUSH/ADD/.../LABEL/JMP)"
    short = "VM"
    levels = [
        Level(id="level1", name="Level 1 (базовые инструкции)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (LABEL/JMP/JZ/JNZ)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        tests = bench.LEVEL1_TESTS if level_id == "level1" else bench.LEVEL1_TESTS + bench.LEVEL2_TESTS
        name = self.level_by_id(level_id).name
        try:
            bench.load_run(str(answer_path))
        except Exception as e:
            return TestResult(0, len(tests), [f"не удалось загрузить решение: {e}"])
        passed, total, failures = bench.run_suite(name, tests, str(answer_path))
        return TestResult(passed, total, failures)
