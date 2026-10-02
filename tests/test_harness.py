"""Unit and integration tests for benchmark runtime and runners."""

from pathlib import Path

import quickjs

from database import Database
from host_configs import build_hardware_label, detect_system_hardware
from html_report import generate_html_report
from sandboxes import run_function_in_wasm


def test_system_hardware_detection():
    hw = detect_system_hardware()
    assert "system" in hw
    assert "hostname" in hw
    assert "cpu" in hw
    label = build_hardware_label(hw)
    assert len(label) > 0


def test_micropython_wasm_execution():
    code = "def add(a, b):\n    return a + b\n"
    success, res = run_function_in_wasm(code, "add", (19, 23))
    assert success is True
    assert res == 42


def test_quickjs_sandbox_execution():
    ctx = quickjs.Context()
    ctx.eval("var x = 10 * 5;")
    val = ctx.get("x")
    assert val == 50


def test_lua_sandbox_execution():
    from sandboxes import create_lua_sandbox

    rt = create_lua_sandbox()
    res = rt.execute("local a = 15 + 27; return a")
    assert res == 42


def test_lua_sandbox_security_isolation():
    import pytest
    from lupa import LuaError

    from sandboxes import create_lua_sandbox

    rt = create_lua_sandbox()

    # Verify dangerous globals are completely revoked
    assert rt.eval("python == nil") is True
    assert rt.eval("os == nil") is True
    assert rt.eval("io == nil") is True
    assert rt.eval("package == nil") is True
    assert rt.eval("debug == nil") is True
    assert rt.eval("load == nil") is True
    assert rt.eval("loadfile == nil") is True
    assert rt.eval("dofile == nil") is True
    assert rt.eval("require == nil") is True

    # Verify execution of python reflection or dynamic code loading is blocked
    with pytest.raises(LuaError):
        rt.execute("python.eval('1+1')")

    with pytest.raises(LuaError):
        rt.execute("require('os')")

    with pytest.raises(LuaError):
        rt.execute("load('return 1')()")


def test_lua_sandbox_infinite_loop_timeout():
    import pytest
    from lupa import LuaError

    from sandboxes import create_lua_sandbox

    # Create sandbox with small instruction budget to verify rapid timeout
    rt = create_lua_sandbox(max_instructions=100_000)
    with pytest.raises(LuaError, match="instruction limit exceeded"):
        rt.execute("while true do end")


def test_zig_c_compilation_and_wasm(tmp_path):
    from sandboxes import compile_c_to_wasm, load_wasm

    c_code = """
    #define WASM_EXPORT __attribute__((visibility("default")))
    WASM_EXPORT int ringbuf_init(int a, int b) {
        return a * b;
    }
    """
    c_file = tmp_path / "test.c"
    wasm_file = tmp_path / "test.wasm"
    c_file.write_text(c_code, encoding="utf-8")
    ok, err = compile_c_to_wasm(c_file, wasm_file)
    assert ok, f"Zig CC error: {err}"
    assert wasm_file.exists()
    store, exports = load_wasm(wasm_file)
    fn = exports["ringbuf_init"]
    res = fn(store, 6, 7)
    assert res == 42


def test_html_report_generation(tmp_path):
    # Using existing or temp db
    db = Database(Path(__file__).parent.parent / "bench.db")
    out_file = tmp_path / "test_report.html"
    res = generate_html_report(db, output_path=out_file, sync_records=False)
    assert res.exists()
    content = res.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Local LLM Benchmark" in content


def test_mcp_server_functions():
    import mcp_server

    lb = mcp_server.get_leaderboard()
    assert "kv L1" in lb
    cats = mcp_server.list_benchmarks()
    assert "c_framing" in cats
    assert "js_async" in cats
    assert "lua_game_ai" in cats


def test_fresh_database_rebuilt_from_records(tmp_path):
    from sync import import_all

    fresh_db_path = tmp_path / "fresh_bench.db"
    fresh_db = Database(fresh_db_path)
    res = import_all(fresh_db, Path(__file__).parent.parent / "records")
    assert res["runs"] > 0
    assert res["results"] > 0
    assert res["speeds"] > 0
    assert res["hosts"] > 0

    r_count = fresh_db.conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    assert r_count == res["results"]


def test_strip_reasoning_blocks():
    from benchmarks.base import strip_reasoning_blocks

    raw = "<think>Let me ponder this problem...\nMaybe approach A?</think>\n\nHere is the answer: 42"
    cleaned, reasoning = strip_reasoning_blocks(raw)
    assert cleaned == "Here is the answer: 42"
    assert "Let me ponder" in reasoning


def test_reasoning_code_extraction_shields_drafts():
    from benchmarks.vm import VMBenchmark

    bench = VMBenchmark()
    # A model drafts wrong code inside <think> with backticks, but provides correct code outside
    raw = """
    <think>
    What if I do:
    ```python
    def run_vm():
        return 'wrong_draft'
    ```
    No, that's not right.
    </think>

    Here is the final solution:
    ```python
    def run_vm():
        return 'correct_final'
    ```
    """
    code = bench.extract_code(raw)
    assert "correct_final" in code
    assert "wrong_draft" not in code


def test_wasm_fuel_infinite_loop_trap(tmp_path):
    import pytest
    from wasmtime import Trap

    from sandboxes.c_wasm import compile_c_to_wasm, load_wasm

    loop_c = """
    #define WASM_EXPORT __attribute__((visibility("default")))
    WASM_EXPORT int ringbuf_push(int x) {
        volatile int val = x;
        while (1) {
            val++;
        }
        return val;
    }
    """
    c_file = tmp_path / "loop.c"
    wasm_file = tmp_path / "loop.wasm"
    c_file.write_text(loop_c, encoding="utf-8")
    ok, err = compile_c_to_wasm(c_file, wasm_file)
    assert ok, f"Compilation error: {err}"

    # Load with small fuel allocation to trigger fast trap
    store, exports = load_wasm(wasm_file, fuel=10_000)
    with pytest.raises(Trap, match="all fuel consumed"):
        exports["ringbuf_push"](store, 1)


def test_report_script_tag_sanitization(tmp_path):
    from database import Database
    from report_data import load_report_data

    db = Database(tmp_path / "test_sec.db")
    # Insert run and result containing </script> and <!-- in model and failure messages
    run_id = "test_sec_run"
    db.conn.execute("INSERT INTO hosts (id, label, created_at, is_active) VALUES ('h1', 'Host 1', '2026-01-01', 1)")
    db.conn.execute(
        "INSERT INTO runs (id, host_id, model_key, model_name, quantization, backend, generation_params, started_at, status) "
        "VALUES (?, 'h1', 'model_xss', 'Model XSS', 'Q4', 'test', '{}', '2026-01-01', 'completed')",
        (run_id,),
    )
    db.conn.execute(
        "INSERT INTO results (run_id, model, benchmark, level, tested_at, passed, total, failures) "
        "VALUES (?, 'model_xss', 'js_async', 'level1', '2026-01-01', 0, 1, ?)",
        (run_id, '["Malicious </script><script>alert(1)</script><!-- comment -->"]'),
    )
    db.conn.commit()

    report_data = load_report_data(db)
    # The JSON string must have < replaced by \\u003c
    assert "</script>" not in report_data.client_json
    assert "<!--" not in report_data.client_json
    assert "\\u003c/script>" in report_data.client_json or "\\u003c" in report_data.client_json


def test_report_model_name_with_single_quote(tmp_path):
    from database import Database
    from html_report import generate_html_report

    db = Database(tmp_path / "test_quote.db")
    run_id = "test_quote_run"
    quote_model = "test'model/with\"quotes"
    db.conn.execute("INSERT INTO hosts (id, label, created_at, is_active) VALUES ('h1', 'Host 1', '2026-01-01', 1)")
    db.conn.execute(
        "INSERT INTO runs (id, host_id, model_key, model_name, quantization, backend, generation_params, started_at, status) "
        "VALUES (?, 'h1', ?, 'Model Quote', 'Q4', 'test', '{}', '2026-01-01', 'completed')",
        (run_id, quote_model),
    )
    db.conn.execute(
        "INSERT INTO results (run_id, model, benchmark, level, tested_at, passed, total, failures) "
        "VALUES (?, ?, 'vm', 'level1', '2026-01-01', 1, 1, '[]')",
        (run_id, quote_model),
    )
    db.conn.commit()

    out_file = tmp_path / "report.html"
    generate_html_report(db, out_file, sync_records=False)
    content = out_file.read_text(encoding="utf-8")
    assert 'data-model="test&#x27;model/with&quot;quotes"' in content
    assert 'onclick="selectModel(this.dataset.model)"' in content
