"""WASM Sandbox Runner for secure execution of local LLM-generated code.

Uses WebAssembly (WASI) via MicroPython/Wasmtime:
1. Strict isolation: guest code has zero access to host disk, network, or OS processes.
2. Deterministic fuel metering: instruction counting instead of OS process killing.
3. Sub-millisecond startup (<1ms) without virtualization overhead.
"""

import json
from pathlib import Path

try:
    import micropython_wasm

    WASM_AVAILABLE = True
except ImportError:
    WASM_AVAILABLE = False


DEFAULT_FUEL = 50_000_000  # 50M instructions per test case


def _indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line if line.strip() else line for line in text.splitlines())


def run_function_in_wasm(
    code_or_path: str | Path,
    func_name: str,
    args: tuple,
    fuel: int = DEFAULT_FUEL,
) -> tuple[bool, object]:
    """Executes function func_name(*args) from solution in isolated WASM sandbox.

    Returns:
        (True, result) on successful execution
        (False, exception) on runtime error, syntax failure, or fuel exhaustion
    """
    if not WASM_AVAILABLE:
        return False, RuntimeError("micropython_wasm is not installed")

    if isinstance(code_or_path, (str, Path)) and Path(code_or_path).exists():
        code = Path(code_or_path).read_text(encoding="utf-8")
    else:
        code = str(code_or_path)

    args_json = json.dumps(list(args), ensure_ascii=False)

    driver = (
        "import json\n"
        f"_WASM_ARGS = {args_json}\n"
        "try:\n" + _indent(code) + "\n"
        f"    _WASM_RESULT = {func_name}(*_WASM_ARGS)\n"
        "    print('__WASM_RES__:' + json.dumps(_WASM_RESULT))\n"
        "except Exception as _e:\n"
        "    print('__WASM_EXC__:' + json.dumps(f'{type(_e).__name__}: {_e}'))\n"
    )

    try:
        res = micropython_wasm.run(driver, fuel=fuel)
    except Exception as e:
        err_str = str(e).lower()
        if "fuel consumed" in err_str or "out of fuel" in err_str:
            return False, TimeoutError("WASM computation fuel limit exceeded (infinite loop)")
        return False, RuntimeError(f"WASM trap: {e}")

    for line in res.stdout.splitlines():
        if line.startswith("__WASM_RES__:"):
            try:
                val = json.loads(line[len("__WASM_RES__:") :])
                return True, val
            except json.JSONDecodeError as je:
                return False, RuntimeError(f"Error decoding WASM response: {je}")
        elif line.startswith("__WASM_EXC__:"):
            try:
                exc_msg = json.loads(line[len("__WASM_EXC__:") :])
                return False, RuntimeError(exc_msg)
            except Exception:
                return False, RuntimeError(line)

    if res.stderr and res.stderr.strip():
        err_clean = res.stderr.strip().splitlines()[-1]
        return False, RuntimeError(f"Syntax error: {err_clean}")

    return False, RuntimeError("WASM sandbox exited without returning a result")
