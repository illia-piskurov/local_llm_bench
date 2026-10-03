"""Safe validation and WASM-only execution of Python solutions.

Model-generated code is never imported or executed by the host native Python process.
Solutions incompatible with MicroPython/WASM receive an execution error rather than
an unsafe fallback.
"""

import ast
from pathlib import Path

from sandboxes.python_wasm import WASM_AVAILABLE, run_function_in_wasm


def verify_function_exists(path: str | Path, func_name: str) -> None:
    """Verifies syntax and function presence via AST without code execution."""
    content = Path(path).read_text(encoding="utf-8")
    try:
        tree = ast.parse(content)
    except SyntaxError as error:
        raise SyntaxError(f"Syntax error in solution: {error}") from error

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            return

    raise AttributeError(f"Function {func_name}(...) not found in solution")


def call_with_timeout(path: str | Path, func_name: str, args: tuple) -> tuple[bool, object]:
    """Runs ``func_name(*args)`` exclusively inside isolated WASM sandbox."""
    if not WASM_AVAILABLE:
        return False, RuntimeError("WASM runtime unavailable; native execution is disabled")

    return run_function_in_wasm(str(path), func_name, args)
