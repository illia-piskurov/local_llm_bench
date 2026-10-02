"""C99 to WebAssembly Sandbox (Zig CC + Wasmtime/WASI).

Compiles C code on the fly with minimal WASI flags and executes inside Wasmtime sandbox:
- Zero disk or socket access to host.
- Isolated WebAssembly linear memory with configurable bounds.
- Fuel consumption limits to terminate infinite loops.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

from wasmtime import Config, Engine, Linker, Module, Store, WasiConfig

DEFAULT_WASM_FUEL = 50_000_000  # 50 million fuel instructions
DEFAULT_WASM_MEMORY_LIMIT = (
    64 * 1024 * 1024
)  # 64 MB max linear memory (Zig wasm32-wasi default initial is 257 pages ~16.8MB)
DEFAULT_MAX_STACK = 1024 * 1024  # 1 MB max stack


def compile_c_to_wasm(c_path: Path, wasm_output_path: Path) -> tuple[bool, str]:
    """Compiles C file to WebAssembly via embedded ziglang compiler."""
    exports = [
        "ringbuf_init",
        "ringbuf_push",
        "ringbuf_pop",
        "ringbuf_available",
        "ringbuf_free_space",
        "decode_packet",
        "feed_bytes",
        "get_next_packet",
    ]
    c_source = c_path.read_text(encoding="utf-8", errors="replace") if c_path.exists() else ""
    export_flags = [f"-Wl,--export={e}" for e in exports if e in c_source]

    cmd = (
        [
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
        + export_flags
        + [str(c_path), "-o", str(wasm_output_path)]
    )

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode != 0:
            return False, proc.stderr or proc.stdout
        return True, ""
    except Exception as e:
        return False, str(e)


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
