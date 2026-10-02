"""Модуль песочниц (Sandbox Engines) для безопасного и изолированного запуска решений.

Поддерживаемые рантаймы:
- python_wasm: MicroPython WASI с детерминированным учетом инструкций (fuel metering).
- process: безопасная AST-проверка и запуск Python-кода только в WASM.
- c_wasm: Zig CC компилятор C99 в WebAssembly + Wasmtime рантайм.
- js_quickjs: QuickJS с виртуальным таймером и полифиллами AbortController/Signal.
- lua_runtime: Lupa песочница с отключенным доступом к ОС, диску и пакетам.
"""

from sandboxes.c_wasm import compile_c_to_wasm, load_wasm
from sandboxes.js_quickjs import create_js_context, drain_js_jobs
from sandboxes.lua_runtime import create_lua_sandbox
from sandboxes.process import call_with_timeout, verify_function_exists
from sandboxes.python_wasm import WASM_AVAILABLE, run_function_in_wasm

__all__ = [
    "WASM_AVAILABLE",
    "call_with_timeout",
    "compile_c_to_wasm",
    "create_js_context",
    "create_lua_sandbox",
    "drain_js_jobs",
    "load_wasm",
    "run_function_in_wasm",
    "verify_function_exists",
]
