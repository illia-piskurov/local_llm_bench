"""Безопасная проверка и WASM-only запуск Python-решений.

Код, сгенерированный моделью, никогда не импортируется и не исполняется
нативным Python-процессом. Несовместимые с MicroPython/WASM решения получают
ошибку выполнения, а не небезопасный fallback.
"""

import ast
from pathlib import Path

from sandboxes.python_wasm import WASM_AVAILABLE, run_function_in_wasm


def verify_function_exists(path: str | Path, func_name: str) -> None:
    """Проверяет синтаксис и наличие функции через AST, без выполнения кода."""
    content = Path(path).read_text(encoding="utf-8")
    try:
        tree = ast.parse(content)
    except SyntaxError as error:
        raise SyntaxError(f"Синтаксическая ошибка в решении: {error}") from error

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            return

    raise AttributeError(f"В решении не найдена функция {func_name}(...)")


def call_with_timeout(path: str | Path, func_name: str, args: tuple) -> tuple[bool, object]:
    """Запускает ``func_name(*args)`` только в изолированной WASM-песочнице."""
    if not WASM_AVAILABLE:
        return False, RuntimeError("WASM-рантайм недоступен; нативное исполнение отключено")

    return run_function_in_wasm(str(path), func_name, args)
