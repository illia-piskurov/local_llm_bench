"""Sandbox Engines module for safe and isolated code execution.

Supported runtimes:
- python_wasm: MicroPython WASI with deterministic fuel metering.
- process: Safe AST validation and dispatch to WASM execution.
- c_wasm: Zig CC C99 to WebAssembly compiler + Wasmtime runtime.
- js_quickjs: QuickJS engine with virtual timers and AbortController/Signal polyfills.
- lua_runtime: Lupa Lua sandbox with revoked OS, IO, and package privileges.
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
