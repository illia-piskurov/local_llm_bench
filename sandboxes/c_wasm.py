"""C99 to WebAssembly Sandbox (Zig CC + Wasmtime/WASI).

Компилирует C код на лету с минимальными флагами WASI и запускает в песочнице Wasmtime:
- Нулевой доступ к диску хоста и сокетам.
- Изолированная линейная память WebAssembly.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

from wasmtime import Engine, Linker, Module, Store, WasiConfig


def compile_c_to_wasm(c_path: Path, wasm_output_path: Path) -> tuple[bool, str]:
    """Компилирует C файл в WebAssembly через встроенный ziglang."""
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


def load_wasm(wasm_path: Path) -> tuple[Store, Any]:
    """Загружает скомпилированный WASM модуль в изолированный рантайм Wasmtime."""
    engine = Engine()
    store = Store(engine)
    linker = Linker(engine)
    linker.define_wasi()

    wasi = WasiConfig()
    store.set_wasi(wasi)

    module = Module.from_file(engine, str(wasm_path))
    instance = linker.instantiate(store, module)
    return store, instance.exports(store)
