"""
Бенчмарк для локальных LLM: тестирует реализацию стековой VM (см. vm.md).

Использование:
    python bench.py path/to/solution.py

Файл solution.py (код, сгенерированный моделью) должен содержать функцию
    run(program: str) -> list[str]
где каждый элемент списка — то, что напечатала инструкция PRINT (как строка).

Скрипт прогоняет:
  - LEVEL 1 тесты: PUSH/POP/ADD/SUB/MUL/DIV/DUP/SWAP/PRINT, комментарии/пустые строки, ошибки
  - LEVEL 2 тесты: LABEL/JMP/JZ/JNZ, включая циклы
  - LEVEL 3 тесты: CALL/RET (подпрограммы и рекурсия), EQ/GT/LT, STORE/LOAD (переменные)

и печатает отчёт + итоговый счёт по каждому уровню.
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


def load_run(path):
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run"):
        raise AttributeError("В решении не найдена функция run(program: str) -> list[str]")
    return module.run


def norm(values):
    """Приводим вывод к списку строк для сравнения (допускаем int/str в PRINT)."""
    return [str(v) for v in values]


# Каждый тест: (имя, программа, ожидаемый вывод) либо (имя, программа, "ERROR")
# "ERROR" означает: ожидаем, что run() кинет исключение (некорректная программа).

LEVEL1_TESTS = [
    (
        "push_print",
        "PUSH 5\nPRINT",
        ["5"],
    ),
    (
        "add",
        "PUSH 2\nPUSH 3\nADD\nPRINT",
        ["5"],
    ),
    (
        "sub_order",
        # a=10, b=3 -> a - b = 7 (порядок важен!)
        "PUSH 10\nPUSH 3\nSUB\nPRINT",
        ["7"],
    ),
    (
        "mul",
        "PUSH 4\nPUSH 6\nMUL\nPRINT",
        ["24"],
    ),
    (
        "div_order",
        # a=20, b=4 -> a / b = 5 (порядок важен!)
        "PUSH 20\nPUSH 4\nDIV\nPRINT",
        ["5"],
    ),
    (
        "div_truncate",
        "PUSH 7\nPUSH 2\nDIV\nPRINT",
        ["3"],
    ),
    (
        "div_by_zero",
        "PUSH 5\nPUSH 0\nDIV\nPRINT",
        "ERROR",
    ),
    (
        "dup",
        "PUSH 9\nDUP\nADD\nPRINT",
        ["18"],
    ),
    (
        "swap",
        "PUSH 1\nPUSH 2\nSWAP\nSUB\nPRINT",
        # stack after swap: [2, 1] (top=1) -> SUB: a=2,b=1 -> 1
        ["1"],
    ),
    (
        "pop",
        "PUSH 1\nPUSH 2\nPOP\nPRINT",
        ["1"],
    ),
    (
        "comments_and_blank_lines",
        "# это комментарий\n\nPUSH 3\n\n# ещё комментарий\nPUSH 4\nADD\nPRINT",
        ["7"],
    ),
    (
        "multiple_prints",
        "PUSH 1\nPRINT\nPUSH 2\nPRINT\nADD\nPRINT",
        ["1", "2", "3"],
    ),
    (
        "print_does_not_pop",
        "PUSH 5\nPRINT\nPRINT",
        ["5", "5"],
    ),
    (
        "negative_numbers",
        "PUSH -3\nPUSH 5\nADD\nPRINT",
        ["2"],
    ),
    (
        "stack_underflow_add",
        "PUSH 1\nADD\nPRINT",
        "ERROR",
    ),
    (
        "stack_underflow_pop",
        "POP",
        "ERROR",
    ),
    (
        "empty_program",
        "",
        [],
    ),
    (
        "complex_chain",
        # (2+3) * (10-6) / 2 = 5*4/2 = 10
        "PUSH 2\nPUSH 3\nADD\nPUSH 10\nPUSH 6\nSUB\nMUL\nPUSH 2\nDIV\nPRINT",
        ["10"],
    ),
]

LEVEL2_TESTS = [
    (
        "unconditional_jump_skips_code",
        "PUSH 1\nJMP skip\nPUSH 999\nLABEL skip\nPUSH 2\nADD\nPRINT",
        ["3"],
    ),
    (
        "jz_taken_when_zero",
        "PUSH 0\nJZ zero\nPUSH 1\nPRINT\nJMP end\nLABEL zero\nPUSH 0\nPRINT\nLABEL end",
        ["0"],
    ),
    (
        "jz_not_taken_when_nonzero",
        "PUSH 5\nJZ zero\nPUSH 1\nPRINT\nJMP end\nLABEL zero\nPUSH 0\nPRINT\nLABEL end",
        ["1"],
    ),
    (
        "jnz_taken_when_nonzero",
        "PUSH 5\nJNZ nz\nPUSH 0\nPRINT\nJMP end\nLABEL nz\nPUSH 1\nPRINT\nLABEL end",
        ["1"],
    ),
    (
        "jnz_not_taken_when_zero",
        "PUSH 0\nJNZ nz\nPUSH 0\nPRINT\nJMP end\nLABEL nz\nPUSH 1\nPRINT\nLABEL end",
        ["0"],
    ),
    (
        "countdown_loop",
        # печатает 5 4 3 2 1, используя JNZ для цикла
        "PUSH 5\n"
        "LABEL loop\n"
        "DUP\n"
        "PRINT\n"
        "PUSH 1\n"
        "SUB\n"
        "DUP\n"
        "JNZ loop\n"
        "POP\n",
        ["5", "4", "3", "2", "1"],
    ),
    (
        "count_up_loop",
        # печатает 1 2 3 4 5
        "PUSH 0\n"
        "LABEL loop\n"
        "PUSH 1\n"
        "ADD\n"
        "DUP\n"
        "PRINT\n"
        "DUP\n"
        "PUSH 5\n"
        "SUB\n"
        "JNZ loop\n",
        ["1", "2", "3", "4", "5"],
    ),
    (
        "jump_to_undefined_label",
        "PUSH 1\nJMP nowhere\nPRINT",
        "ERROR",
    ),
    (
        "label_does_nothing_on_its_own",
        "LABEL start\nPUSH 42\nPRINT",
        ["42"],
    ),
]

LEVEL3_TESTS = [
    (
        "call_ret_basic",
        "PUSH 5\nCALL double\nPRINT\nJMP end\nLABEL double\nPUSH 2\nMUL\nRET\nLABEL end",
        ["10"],
    ),
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
    (
        "store_and_load",
        "PUSH 42\nSTORE x\nPUSH 100\nSTORE y\nLOAD x\nLOAD y\nADD\nPRINT",
        ["142"],
    ),
    (
        "store_overwrite",
        "PUSH 10\nSTORE val\nPUSH 99\nSTORE val\nLOAD val\nPRINT",
        ["99"],
    ),
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
    (
        "ret_without_call_error",
        "RET",
        "ERROR",
    ),
    (
        "load_undefined_variable_error",
        "LOAD undefined_var",
        "ERROR",
    ),
    (
        "call_undefined_label_error",
        "CALL missing_label",
        "ERROR",
    ),
]


def run_suite(name, tests, path):
    passed = 0
    failed = []
    for test_name, program, expected in tests:
        success, result = call_with_timeout(path, "run", (program,))
        if not success:
            if expected == "ERROR":
                passed += 1
            else:
                failed.append((test_name, f"неожиданное исключение: {result}", None))
            continue

        if expected == "ERROR":
            failed.append((test_name, "ожидалась ошибка, но выполнение прошло успешно", result))
            continue
        result_norm = norm(result)
        if result_norm == expected:
            passed += 1
        else:
            failed.append((test_name, f"ожидалось {expected}, получено {result_norm}", None))

    total = len(tests)
    print(f"\n=== {name}: {passed}/{total} ===")
    for test_name, reason, _ in failed:
        print(f"  [FAIL] {test_name}: {reason}")
    failures = [f"{test_name}: {reason}" for test_name, reason, _ in failed]
    return passed, total, failures


def main():
    if len(sys.argv) != 2:
        print("Использование: python bench.py path/to/solution.py")
        sys.exit(1)

    path = sys.argv[1]
    try:
        load_run(path)
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
