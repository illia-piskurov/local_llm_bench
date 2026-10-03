"""Stack Virtual Machine (VM) benchmark.

Tests the model's ability to implement an interpreter for a simple bytecode/stack language:
- Level 1: Basic stack operations (PUSH, POP, ADD, SUB, MUL, DIV, DUP, SWAP, PRINT).
- Level 2: Control flow (LABEL, JMP, JZ, JNZ, loops).
- Level 3: Subroutines and functions (CALL, RET, EQ, GT, LT, STORE, LOAD).
"""

from pathlib import Path
from typing import Any

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Implement an interpreter for a simple stack-based language in a single Python file.

Supported instructions (one per line, arguments separated by space):
PUSH <n>  — push number n onto the stack
POP       — pop value from the stack
ADD       — pop two values, push their sum
SUB       — pop two values (b, then a), push a - b
MUL       — pop two values, push their product
DIV       — pop two values (b, then a), push a // b (integer division)
DUP       — duplicate the value on top of the stack
SWAP      — swap the top two values on the stack
PRINT     — print the value on top of the stack (without popping it)

The program is passed as multi-line text. Empty lines and lines starting with "#" are comments and must be ignored.

Requirements:
- Single file, no external dependencies.
- If the stack does not have enough values for an operation — raise a clear error with the line number.
- Division by zero — raise a clear error with the line number.
- Add a function run(program: str) -> list[str], returning a list of printed strings (output from PRINT).

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your implementation with support for labels and conditional jumps:

LABEL <name>   — define a label at the current position (does nothing during execution)
JMP <name>     — unconditional jump to label
JZ <name>      — pop value from stack, jump to label if value == 0
JNZ <name>     — pop value from stack, jump to label if value != 0

Do not change the behavior of previously implemented instructions and preserve the run(program: str) -> list[str] signature.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL3_PROMPT = """\
Extend your implementation with support for subroutines, comparison operations, and named variables:

1. Subroutines (call stack):
   CALL <name>  — push return address onto call stack and jump to label <name>
   RET          — pop return address from call stack and jump to it (the instruction immediately following CALL).
                  If call stack is empty — raise a clear error.

2. Comparison operations:
   EQ           — pop two values (b, then a), push 1 if a == b else 0
   GT           — pop two values (b, then a), push 1 if a > b else 0
   LT           — pop two values (b, then a), push 1 if a < b else 0

3. Named variables (memory):
   STORE <var>  — pop value from stack and store into variable <var>
   LOAD <var>   — push value of variable <var> onto stack. If variable <var> has not been stored yet — raise a clear error.

Requirements:
- Support nested and recursive subroutine calls via CALL/RET.
- Do not change the behavior of previously implemented instructions and preserve the run(program: str) -> list[str] signature.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

# Each test: (name, program, expected output or "ERROR")
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
    ("comments_and_blank_lines", "# this is a comment\n\nPUSH 3\n\n# another comment\nPUSH 4\nADD\nPRINT", ["7"]),
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
    """Normalizes solution output to a list of strings for uniform comparison."""
    if not isinstance(values, (list, tuple)):
        return [str(values)]
    return [str(v) for v in values]


def run_vm_suite(tests: list[tuple[str, str, Any]], solution_path: str | Path) -> tuple[int, int, list[str]]:
    """Runs VM test suite and returns (passed, total, failures)."""
    passed = 0
    failures: list[str] = []

    for test_name, program, expected in tests:
        success, result = call_with_timeout(str(solution_path), "run", (program,))
        if not success:
            if expected == "ERROR":
                passed += 1
            else:
                failures.append(f"{test_name}: unexpected exception/timeout: {result}")
            continue

        if expected == "ERROR":
            failures.append(f"{test_name}: expected error, but execution succeeded ({result})")
            continue

        result_norm = _norm(result)
        if result_norm == expected:
            passed += 1
        else:
            failures.append(f"{test_name}: expected {expected}, got {result_norm}")

    return passed, len(tests), failures


class VMBenchmark(Benchmark):
    id = "vm"
    name = "Stack VM (PUSH/ADD/.../LABEL/JMP/CALL/RET)"
    short = "VM"
    levels = [
        Level(id="level1", name="Level 1 (basic instructions)", prompt=LEVEL1_PROMPT, requires=None),
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
            return TestResult(0, len(tests), [f"failed to load solution: {e}"])

        passed, total, failures = run_vm_suite(tests, answer_path)
        return TestResult(passed, total, failures)
