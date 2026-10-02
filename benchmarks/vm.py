"""Стековая виртуальная машина (VM) бенчмарк.

Тестирует способность модели реализовать интерпретатор простого байткод/стекового языка:
- Level 1: Базовые стек-операции (PUSH, POP, ADD, SUB, MUL, DIV, DUP, SWAP, PRINT).
- Level 2: Управление потоком (LABEL, JMP, JZ, JNZ, циклы).
- Level 3: Подпрограммы и функции (CALL, RET, EQ, GT, LT, STORE, LOAD).
"""

from pathlib import Path
from typing import Any

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

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

LEVEL3_PROMPT = """\
Дополни свою реализацию поддержкой подпрограмм, операций сравнения и именованных переменных:

1. Подпрограммы (стек вызовов):
   CALL <name>  — сохранить адрес возврата в стек вызовов и перейти к метке <name>
   RET          — снять адрес возврата со стека вызовов и перейти к нему (к инструкции, следующей сразу за CALL).
                  Если стек вызовов пуст — кинуть понятную ошибку.

2. Операции сравнения:
   EQ           — снять два значения (b, затем a), положить 1, если a == b, иначе 0
   GT           — снять два значения (b, затем a), положить 1, если a > b, иначе 0
   LT           — снять два значения (b, затем a), положить 1, если a < b, иначе 0

3. Именованные переменные (память):
   STORE <var>  — снять значение со стека и сохранить в переменную <var>
   LOAD <var>   — положить значение переменной <var> на стек. Если переменная <var> ещё не была сохранена — кинуть понятную ошибку.

Требования:
- Поддержка вложенных и рекурсивных вызовов подпрограмм через CALL/RET.
- Не меняй поведение уже реализованных инструкций и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

# Каждый тест: (имя, программа, ожидаемый вывод или "ERROR")
LEVEL1_TESTS: list[tuple[str, str, Any]] = [
    ("push_print", "PUSH 5\nPRINT", ["5"]),
    ("add", "PUSH 2\nPUSH 3\nADD\nPRINT", ["5"]),
    ("sub_order", "PUSH 10\nPUSH 3\nSUB\nPRINT", ["7"]),
    ("mul", "PUSH 4\nPUSH 6\nMUL\nPRINT", ["24"]),
    ("div_order", "PUSH 20\nPUSH 4\nDIV\nPRINT", ["5"]),
    ("div_truncate", "PUSH 7\nPUSH 2\nDIV\nPRINT", ["3"]),
    ("div_by_zero", "PUSH 5\nPUSH 0\nDIV\nPRINT", "ERROR"),
    ("dup", "PUSH 9\nDUP\nADD\nPRINT", ["18"]),
    ("swap", "PUSH 1\nPUSH 2\nSWAP\nSUB\nPRINT", ["1"]),
    ("pop", "PUSH 1\nPUSH 2\nPOP\nPRINT", ["1"]),
    ("comments_and_blank_lines", "# это комментарий\n\nPUSH 3\n\n# ещё комментарий\nPUSH 4\nADD\nPRINT", ["7"]),
    ("multiple_prints", "PUSH 1\nPRINT\nPUSH 2\nPRINT\nADD\nPRINT", ["1", "2", "3"]),
    ("print_does_not_pop", "PUSH 5\nPRINT\nPRINT", ["5", "5"]),
    ("negative_numbers", "PUSH -3\nPUSH 5\nADD\nPRINT", ["2"]),
    ("stack_underflow_add", "PUSH 1\nADD\nPRINT", "ERROR"),
    ("stack_underflow_pop", "POP", "ERROR"),
    ("empty_program", "", []),
    ("complex_chain", "PUSH 2\nPUSH 3\nADD\nPUSH 10\nPUSH 6\nSUB\nMUL\nPUSH 2\nDIV\nPRINT", ["10"]),
]

LEVEL2_TESTS: list[tuple[str, str, Any]] = [
    ("unconditional_jump_skips_code", "PUSH 1\nJMP skip\nPUSH 999\nLABEL skip\nPUSH 2\nADD\nPRINT", ["3"]),
    ("jz_taken_when_zero", "PUSH 0\nJZ zero\nPUSH 1\nPRINT\nJMP end\nLABEL zero\nPUSH 0\nPRINT\nLABEL end", ["0"]),
    (
        "jz_not_taken_when_nonzero",
        "PUSH 5\nJZ zero\nPUSH 1\nPRINT\nJMP end\nLABEL zero\nPUSH 0\nPRINT\nLABEL end",
        ["1"],
    ),
    ("jnz_taken_when_nonzero", "PUSH 5\nJNZ nz\nPUSH 0\nPRINT\nJMP end\nLABEL nz\nPUSH 1\nPRINT\nLABEL end", ["1"]),
    ("jnz_not_taken_when_zero", "PUSH 0\nJNZ nz\nPUSH 0\nPRINT\nJMP end\nLABEL nz\nPUSH 1\nPRINT\nLABEL end", ["0"]),
    (
        "countdown_loop",
        "PUSH 5\nLABEL loop\nDUP\nPRINT\nPUSH 1\nSUB\nDUP\nJNZ loop\nPOP\n",
        ["5", "4", "3", "2", "1"],
    ),
    (
        "count_up_loop",
        "PUSH 0\nLABEL loop\nPUSH 1\nADD\nDUP\nPRINT\nDUP\nPUSH 5\nSUB\nJNZ loop\n",
        ["1", "2", "3", "4", "5"],
    ),
    ("jump_to_undefined_label", "PUSH 1\nJMP nowhere\nPRINT", "ERROR"),
    ("label_does_nothing_on_its_own", "LABEL start\nPUSH 42\nPRINT", ["42"]),
]

LEVEL3_TESTS: list[tuple[str, str, Any]] = [
    ("call_ret_basic", "PUSH 5\nCALL double\nPRINT\nJMP end\nLABEL double\nPUSH 2\nMUL\nRET\nLABEL end", ["10"]),
    (
        "call_ret_nested",
        "CALL func_a\nPRINT\nJMP end\nLABEL func_b\nPUSH 10\nRET\nLABEL func_a\nCALL func_b\nPUSH 2\nMUL\nRET\nLABEL end",
        ["20"],
    ),
    (
        "comparison_eq_gt_lt",
        "PUSH 5\nPUSH 5\nEQ\nPRINT\nPUSH 5\nPUSH 10\nEQ\nPRINT\nPUSH 10\nPUSH 5\nGT\nPRINT\nPUSH 5\nPUSH 10\nGT\nPRINT\nPUSH 3\nPUSH 7\nLT\nPRINT\nPUSH 7\nPUSH 3\nLT\nPRINT",
        ["1", "0", "1", "0", "1", "0"],
    ),
    ("store_and_load", "PUSH 42\nSTORE x\nPUSH 100\nSTORE y\nLOAD x\nLOAD y\nADD\nPRINT", ["142"]),
    ("store_overwrite", "PUSH 10\nSTORE val\nPUSH 99\nSTORE val\nLOAD val\nPRINT", ["99"]),
    (
        "recursive_factorial",
        "PUSH 4\nCALL fact\nPRINT\nJMP end\nLABEL fact\nDUP\nPUSH 1\nGT\nJZ base_case\nDUP\nPUSH 1\nSUB\nCALL fact\nMUL\nRET\nLABEL base_case\nPOP\nPUSH 1\nRET\nLABEL end",
        ["24"],
    ),
    (
        "recursive_fibonacci",
        "PUSH 6\nCALL fib\nPRINT\nJMP end\nLABEL fib\nDUP\nPUSH 2\nLT\nJZ fib_rec\nRET\nLABEL fib_rec\nDUP\nPUSH 1\nSUB\nCALL fib\nSWAP\nPUSH 2\nSUB\nCALL fib\nADD\nRET\nLABEL end",
        ["8"],
    ),
    ("ret_without_call_error", "RET", "ERROR"),
    ("load_undefined_variable_error", "LOAD undefined_var", "ERROR"),
    ("call_undefined_label_error", "CALL missing_label", "ERROR"),
]


def _norm(values: Any) -> list[str]:
    """Приводит вывод решения к списку строк для единообразного сравнения."""
    if not isinstance(values, (list, tuple)):
        return [str(values)]
    return [str(v) for v in values]


def run_vm_suite(tests: list[tuple[str, str, Any]], solution_path: str | Path) -> tuple[int, int, list[str]]:
    """Выполняет тестовый набор VM и возвращает (passed, total, failures)."""
    passed = 0
    failures: list[str] = []

    for test_name, program, expected in tests:
        success, result = call_with_timeout(str(solution_path), "run", (program,))
        if not success:
            if expected == "ERROR":
                passed += 1
            else:
                failures.append(f"{test_name}: неожиданное исключение/таймаут: {result}")
            continue

        if expected == "ERROR":
            failures.append(f"{test_name}: ожидалась ошибка, но выполнение прошло успешно ({result})")
            continue

        result_norm = _norm(result)
        if result_norm == expected:
            passed += 1
        else:
            failures.append(f"{test_name}: ожидалось {expected}, получено {result_norm}")

    return passed, len(tests), failures


class VMBenchmark(Benchmark):
    id = "vm"
    name = "Стековая VM (PUSH/ADD/.../LABEL/JMP/CALL/RET)"
    short = "VM"
    levels = [
        Level(id="level1", name="Level 1 (базовые инструкции)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (LABEL/JMP/JZ/JNZ)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (CALL/RET/EQ/GT/LT/STORE/LOAD)", prompt=LEVEL3_PROMPT, requires="level2"),
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

        passed, total, failures = run_vm_suite(tests, answer_path)
        return TestResult(passed, total, failures)
