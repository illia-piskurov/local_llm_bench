"""C99 to WebAssembly Sandbox (Zig CC + Wasmtime/WASI).

Compiles C code on the fly with minimal WASI flags and executes inside Wasmtime sandbox:
- Zero disk or socket access to host.
- Isolated WebAssembly linear memory with configurable bounds.
- Fuel consumption limits to terminate infinite loops.
"""

import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from wasmtime import Config, Engine, Linker, Module, Store, WasiConfig

DEFAULT_WASM_FUEL = 50_000_000  # 50 million fuel instructions
DEFAULT_WASM_MEMORY_LIMIT = (
    64 * 1024 * 1024
)  # 64 MB max linear memory (Zig wasm32-wasi default initial is 257 pages ~16.8MB)
DEFAULT_MAX_STACK = 1024 * 1024  # 1 MB max stack
COMPILE_TIMEOUT_SECONDS = 120  # generous: the very first build has to populate zig's wasi libc cache
MAX_EXPORT_RETRIES = 3

# Functions the benchmark harness may call. Only names the solution really defines get exported.
DEFAULT_EXPORTS: tuple[str, ...] = (
    "ringbuf_init",
    "ringbuf_push",
    "ringbuf_pop",
    "ringbuf_available",
    "ringbuf_free_space",
    "decode_packet",
    "feed_bytes",
    "get_next_packet",
)

_MISSING_EXPORT_RE = re.compile(
    r"(?:symbol exported via --export not found|undefined symbol|unknown symbol):\s*(\w+)",
    re.IGNORECASE,
)
_C_NOISE_RE = re.compile(
    r"""/\*.*?\*/            # block comments
      | //[^\n]*              # line comments
      | "(?:\\.|[^"\\\n])*"  # string literals
      | '(?:\\.|[^'\\\n])*'  # character literals
    """,
    re.DOTALL | re.VERBOSE,
)


def _strip_c_noise(source: str) -> str:
    """Removes comments and string/char literals so identifiers inside them are not mistaken for code."""
    return _C_NOISE_RE.sub(" ", source)


def _candidate_exports(source: str, exports: Sequence[str]) -> list[str]:
    """Wanted functions that appear as identifiers followed by '(' in the code proper.

    This is only a cheap pre-filter. The linker is the source of truth: names that still fail to
    link (prototype without body, ``static`` function, ...) are dropped by the retry loop.
    """
    code = _strip_c_noise(source)
    return [name for name in exports if re.search(rf"\b{re.escape(name)}\s*\(", code)]


def compile_c_to_wasm(
    c_path: Path,
    wasm_output_path: Path,
    exports: Sequence[str] = DEFAULT_EXPORTS,
) -> tuple[bool, str]:
    """Compiles C file to WebAssembly via embedded ziglang compiler.

    Args:
        c_path: C99 source file.
        wasm_output_path: Where the linked module is written.
        exports: Function names to export when the solution defines them. Undefined names are skipped
            instead of failing the build, so a partial solution can still be tested.
    """
    c_source = c_path.read_text(encoding="utf-8", errors="replace") if c_path.exists() else ""
    wanted = _candidate_exports(c_source, exports)

    base_cmd = [
        sys.executable,
        "-m",
        "ziglang",
        "cc",
        "-target",
        "wasm32-wasi",
        "-O2",
        "-nostartfiles",
        "-Wl,--no-entry",
    ]

    last_error = ""
    max_retries = max(len(wanted), MAX_EXPORT_RETRIES)
    for _ in range(max_retries + 1):
        cmd = base_cmd + [f"-Wl,--export={name}" for name in wanted] + [str(c_path), "-o", str(wasm_output_path)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECONDS)
        except Exception as e:
            return False, str(e)
        if proc.returncode == 0:
            return True, ""

        last_error = proc.stderr or proc.stdout
        missing = set(_MISSING_EXPORT_RE.findall(last_error))
        remaining = [name for name in wanted if name not in missing]
        if not missing or len(remaining) == len(wanted):
            break  # a genuine compile/link error, not a missing export
        wanted = remaining
    return False, last_error


def load_wasm(
    wasm_path: Path,
    fuel: int = DEFAULT_WASM_FUEL,
    memory_limit_bytes: int = DEFAULT_WASM_MEMORY_LIMIT,
) -> tuple[Store, Any]:
    """Loads compiled WASM module into an isolated Wasmtime runtime with fuel & memory bounds."""
    cfg = Config()
    cfg.consume_fuel = True
    cfg.max_wasm_stack = DEFAULT_MAX_STACK
    engine = Engine(cfg)
    store = Store(engine)
    if fuel > 0:
        store.set_fuel(fuel)
    if memory_limit_bytes > 0:
        store.set_limits(memory_size=memory_limit_bytes)

    linker = Linker(engine)
    linker.define_wasi()

    wasi = WasiConfig()
    store.set_wasi(wasi)

    module = Module.from_file(engine, str(wasm_path))
    instance = linker.instantiate(store, module)
    return store, instance.exports(store)
