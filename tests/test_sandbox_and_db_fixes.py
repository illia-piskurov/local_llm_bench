"""Regression tests: JS host APIs, C export selection and non-destructive database upserts."""

import json
import re
from pathlib import Path

import pytest

from database import UPSERT_RUN_SQL, Database
from host_configs import HostConfig, HostConfigStore
from sandboxes.c_wasm import _candidate_exports, _strip_c_noise, compile_c_to_wasm, load_wasm
from sandboxes.js_quickjs import create_js_context, drain_js_jobs
from storage import RunStore
from sync import import_all

ROOT = Path(__file__).resolve().parent.parent


# ── JavaScript host APIs ────────────────────────────────────────────────────────────────────────


def js(source: str, expr: str):
    ctx = create_js_context(source)
    drain_js_jobs(ctx)
    return json.loads(ctx.eval(f"JSON.stringify({expr})"))


def test_date_now_and_performance_follow_virtual_time():
    src = "const t = [Date.now()]; const p = []; setTimeout(() => { t.push(Date.now()); p.push(performance.now()); }, 250);"
    assert js(src, "[t[1] - t[0], p[0]]") == [250, 250]


def test_set_interval_fires_until_cleared():
    src = "const hits = []; const id = setInterval(() => { hits.push(performance.now()); if (hits.length === 3) clearInterval(id); }, 10);"
    assert js(src, "hits") == [10, 20, 30]


def test_clear_interval_before_first_tick_and_set_immediate_order():
    assert js("let n = 0; const id = setInterval(() => n++, 10); clearInterval(id);", "n") == 0
    assert js("const l = []; setTimeout(() => l.push('t'), 0); setImmediate(() => l.push('i'));", "l") == ["t", "i"]


def test_console_and_commonjs_stubs_do_not_crash_solutions():
    src = "console.log('x', 1); console.error(new Error('boom')); function pMap() {} module.exports = { pMap }; exports.y = 1;"
    assert js(src, "[typeof pMap, __consoleLog.length]") == ["function", 2]


def test_solution_may_redeclare_polyfilled_names():
    assert js("class EventTarget { hi() { return 7; } } const r = new EventTarget().hi();", "r") == 7
    assert js("const console = { log() {} }; console.log(1); const z = 2;", "z") == 2
    assert js("class AbortSignal { static x = 1 } const z = AbortSignal.x;", "z") == 1
    assert js("class DOMException extends Error {} const z = new DOMException('m').message;", "z") == "m"


def test_misc_es2022_helpers():
    src = "const r = [[1, 2, 3].at(-1), 'abc'.at(-1), Object.hasOwn({ k: 1 }, 'k'), [1, 2, 3, 4].findLast((x) => x % 2), [3, 1, 2].toSorted()];"
    assert js(src, "r") == [3, "c", True, 3, [1, 2, 3]]
    assert js("let v = 0; queueMicrotask(() => { v = 5; });", "v") == 5
    assert js(
        "const o = { a: [1, { b: 2 }] }; const c = structuredClone(o); c.a[1].b = 9;", "[o.a[1].b, c.a[1].b]"
    ) == [2, 9]


def test_abort_signal_is_standards_conformant():
    src = """
    const ac = new AbortController();
    const log = [];
    ac.signal.addEventListener('abort', (e) => log.push(e.type + ':' + (e.target === ac.signal)));
    ac.signal.onabort = () => log.push('onabort');
    ac.abort();
    const late = [];
    ac.signal.addEventListener('abort', () => late.push('late'));
    let thrown = null;
    try { ac.signal.throwIfAborted(); } catch (e) { thrown = e.name; }
    const once = { n: 0 };
    const c2 = new AbortController();
    c2.signal.addEventListener('abort', () => once.n++, { once: true });
    c2.abort(); c2.abort();
    let illegal = null;
    try { new AbortSignal(); } catch (e) { illegal = e.constructor.name; }
    """
    ctx = create_js_context(src)
    drain_js_jobs(ctx)
    read = lambda expr: json.loads(ctx.eval(f"JSON.stringify({expr})"))  # noqa: E731
    assert read("log") == ["onabort", "abort:true"]
    assert read("late") == []  # no retroactive call for listeners added after the abort
    assert read("thrown") == "AbortError"
    assert read("ac.signal.reason instanceof DOMException && ac.signal.reason instanceof Error") is True
    assert read("once.n") == 1
    assert read("illegal") == "TypeError"


def test_abort_signal_static_helpers():
    src = """
    const pre = AbortSignal.abort(new Error('X'));
    const any = AbortSignal.any([new AbortController().signal, pre]);
    const timeout = AbortSignal.timeout(100);
    let name = null;
    timeout.addEventListener('abort', () => { name = timeout.reason.name; });
    """
    assert js(src, "[pre.aborted, pre.reason.message, any.aborted, any.reason.message, name]") == [
        True,
        "X",
        True,
        "X",
        "TimeoutError",
    ]


def test_explicit_abort_reason_is_preserved():
    assert (
        js("const ac = new AbortController(); const e = new Error('mine'); ac.abort(e);", "ac.signal.reason === e")
        is True
    )
    assert js("const ac = new AbortController(); ac.abort('str');", "ac.signal.reason") == "str"


# ── C export selection ──────────────────────────────────────────────────────────────────────────

C_WITH_NOISE = """\
#include <stdint.h>
/* decode_packet and ringbuf_pop(...) are only mentioned in this comment */
// feed_bytes( is mentioned here too
static const char *doc = "get_next_packet(";
static int ringbuf_free_space(void) { return 1; }   /* static: must not be exported */
int ringbuf_init(void) { return 1; }
int ringbuf_push(int x) { return ringbuf_free_space() + x; }
"""


def _compile(tmp_path: Path, source: str, **kwargs):
    c_file = tmp_path / "sol.c"
    c_file.write_text(source, encoding="utf-8")
    wasm = tmp_path / "sol.wasm"
    ok, err = compile_c_to_wasm(c_file, wasm, **kwargs)
    return ok, err, wasm


def test_strip_c_noise_removes_comments_and_strings():
    stripped = _strip_c_noise(
        "int a; /* decode_packet( */ // feed_bytes(\nchar *s = \"get_next_packet(\"; char c = 'x';"
    )
    assert "decode_packet" not in stripped and "feed_bytes" not in stripped and "get_next_packet" not in stripped
    assert "int a;" in stripped


def test_candidate_exports_ignore_comments_and_strings():
    names = ("ringbuf_init", "ringbuf_pop", "decode_packet", "feed_bytes", "get_next_packet", "ringbuf_push")
    assert _candidate_exports(C_WITH_NOISE, names) == ["ringbuf_init", "ringbuf_push"]


def test_names_in_comments_and_static_functions_do_not_break_the_build(tmp_path):
    ok, err, wasm = _compile(tmp_path, C_WITH_NOISE)
    assert ok, err
    _, exports = load_wasm(wasm)
    names = {e.name for e in exports._exports} if hasattr(exports, "_exports") else set(exports)
    assert "ringbuf_init" in names and "ringbuf_push" in names
    assert "ringbuf_free_space" not in names  # static
    assert "decode_packet" not in names


def test_prototype_without_definition_is_dropped_instead_of_failing_the_link(tmp_path):
    source = "int decode_packet(int x);\nint ringbuf_init(void) { return 3; }\n"
    ok, err, _ = _compile(tmp_path, source)
    assert ok, err


def test_exports_are_configurable_and_generic(tmp_path):
    source = "int answer(void) { return 42; }\nint other(void) { return 1; }\n"
    ok, err, wasm = _compile(tmp_path, source, exports=("answer",))
    assert ok, err
    store, exports = load_wasm(wasm)
    assert exports["answer"](store) == 42
    assert "other" not in exports


def test_real_compile_errors_are_still_reported(tmp_path):
    ok, err, _ = _compile(tmp_path, "int ringbuf_init(void) { return undefined_symbol_xyz; }\n")
    assert not ok and "undefined_symbol_xyz" in err


def test_multiple_missing_exports_drop_cleanly(tmp_path):
    # Only ringbuf_init is implemented; 4 other names are declared as prototypes without definitions
    source = """
    int decode_packet(int x);
    int feed_bytes(const void *p, int len);
    int get_next_packet(void *p);
    int ringbuf_pop(void);
    int ringbuf_init(void) { return 42; }
    """
    ok, err, wasm = _compile(tmp_path, source)
    assert ok, err
    store, exports = load_wasm(wasm)
    assert exports["ringbuf_init"](store) == 42
    names = {e.name for e in exports._exports} if hasattr(exports, "_exports") else set(exports)
    for missing in ("decode_packet", "feed_bytes", "get_next_packet", "ringbuf_pop"):
        assert missing not in names


# ── non-destructive database upserts ────────────────────────────────────────────────────────────


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "t.db")
    database.conn.execute(
        "INSERT INTO hosts (id, label, created_at, is_active) VALUES ('h1', 'Host', '2026-01-01 00:00:00', 1)"
    )
    database.conn.commit()
    return database


def _seed_run(db: Database, status: str = "in_progress") -> None:
    c = db.conn
    c.execute(
        "INSERT INTO runs (id, host_id, model_key, started_at, status) VALUES ('r1', 'h1', 'm', '2026-01-01 00:00:00', ?)",
        (status,),
    )
    c.execute(
        "INSERT INTO results (run_id, model, benchmark, level, tested_at, passed, total, failures) "
        "VALUES ('r1', 'm', 'kv', 'level1', '2026-02-01 00:00:00', 3, 3, '[]')"
    )
    c.execute(
        "INSERT INTO speed_results (run_id, host_id, model, benchmark, level, tested_at, tokens_per_second) "
        "VALUES ('r1', 'h1', 'm', 'kv', 'level1', '2026-02-01 00:00:00', 12.5)"
    )
    c.commit()


def _counts(db: Database) -> tuple[int, int]:
    c = db.conn
    return (
        c.execute("SELECT COUNT(*) FROM results").fetchone()[0],
        c.execute("SELECT COUNT(*) FROM speed_results").fetchone()[0],
    )


def _write_run_file(records: Path, results: list[dict], status: str = "completed", completed_at: str | None = "x"):
    (records / "runs").mkdir(parents=True, exist_ok=True)
    (records / "hosts").mkdir(parents=True, exist_ok=True)
    (records / "hosts" / "h1.json").write_text(
        json.dumps({"id": "h1", "label": "Renamed Host", "created_at": "2026-01-01 00:00:00"}), encoding="utf-8"
    )
    data = {
        "id": "r1", "host_id": "h1", "model_key": "m", "model_name": "M", "started_at": "2026-01-01 00:00:00",
        "completed_at": completed_at, "status": status, "generation_params": {}, "results": results, "speeds": [],
    }  # fmt: skip
    (records / "runs" / "r1.json").write_text(json.dumps(data), encoding="utf-8")


def test_importing_an_existing_run_keeps_its_results_and_speeds(db, tmp_path):
    _seed_run(db)
    _write_run_file(tmp_path / "records", results=[])  # file knows nothing about the local rows

    import_all(db, tmp_path / "records")

    assert _counts(db) == (1, 1)  # INSERT OR REPLACE used to cascade-delete both
    assert db.conn.execute("SELECT status FROM runs WHERE id = 'r1'").fetchone()[0] == "completed"


def test_run_upsert_does_not_cascade_delete(db):
    _seed_run(db)
    RunStore(db).save(RunStore(db).get("r1"))
    assert _counts(db) == (1, 1)


def test_stale_in_progress_copy_cannot_reopen_a_finished_run(db, tmp_path):
    _seed_run(db, status="completed")
    db.conn.execute("UPDATE runs SET completed_at = '2026-03-03 00:00:00' WHERE id = 'r1'")
    db.conn.commit()
    _write_run_file(tmp_path / "records", results=[], status="in_progress", completed_at=None)

    import_all(db, tmp_path / "records")

    status, completed_at = db.conn.execute("SELECT status, completed_at FROM runs WHERE id = 'r1'").fetchone()
    assert status == "completed" and completed_at == "2026-03-03 00:00:00"


def test_import_does_not_overwrite_newer_local_result_but_accepts_newer_remote(db, tmp_path):
    _seed_run(db)
    older = {
        "benchmark": "kv",
        "level": "level1",
        "tested_at": "2026-01-15 00:00:00",
        "passed": 0,
        "total": 3,
        "failures": ["x"],
    }
    _write_run_file(tmp_path / "records", results=[older])
    import_all(db, tmp_path / "records")
    assert db.conn.execute("SELECT passed FROM results").fetchone()[0] == 3  # local is newer: kept

    newer = {**older, "tested_at": "2026-04-01 00:00:00", "passed": 2}
    _write_run_file(tmp_path / "records", results=[newer])
    import_all(db, tmp_path / "records")
    assert db.conn.execute("SELECT passed FROM results").fetchone()[0] == 2  # remote is newer: applied


def test_host_upsert_preserves_is_active(db, tmp_path):
    _write_run_file(tmp_path / "records", results=[])
    import_all(db, tmp_path / "records")
    label, active = db.conn.execute("SELECT label, is_active FROM hosts WHERE id = 'h1'").fetchone()
    assert label == "Renamed Host" and active == 1

    store = HostConfigStore(db, records_dir=tmp_path / "host_records")
    store.add(HostConfig(id="h1", label="Again", created_at="2026-01-01 00:00:00"))
    assert db.conn.execute("SELECT is_active FROM hosts WHERE id = 'h1'").fetchone()[0] == 1
    assert (tmp_path / "host_records" / "h1.json").exists()


def test_upsert_sql_is_not_a_replace():
    assert "ON CONFLICT" in UPSERT_RUN_SQL and "REPLACE" not in UPSERT_RUN_SQL.upper()


def test_no_insert_or_replace_into_parent_tables_left_in_source():
    """REPLACE on `runs`/`hosts` cascades into child rows; guard against it creeping back in."""
    pattern = re.compile(r"INSERT\s+OR\s+REPLACE\s+INTO\s+(runs|hosts)\b", re.IGNORECASE)
    offenders = []
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & {".venv", "tests", "models_answers", "llm-probe", ".agents"}:
            continue
        # database.py's one-off legacy-schema migration builds fresh tables and is exempt.
        if path.name == "database.py":
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_export_all_write_if_changed_preserves_mtime(db, tmp_path):
    from sync import export_all

    records_dir = tmp_path / "rec"
    export_all(db, records_dir)
    host_file = records_dir / "hosts" / "h1.json"
    assert host_file.exists()
    mtime_before = host_file.stat().st_mtime_ns

    # Second export with identical data should not rewrite the file
    export_all(db, records_dir)
    mtime_after = host_file.stat().st_mtime_ns
    assert mtime_before == mtime_after


def test_upsert_run_preserves_newer_completed_at(db):
    db.conn.execute(
        UPSERT_RUN_SQL,
        (
            "run_test",
            "h1",
            "model_x",
            "model_x",
            "Q4",
            "LM Studio",
            "{}",
            "1.0",
            "2026-01-01 00:00:00",
            "2026-01-01 02:00:00",
            "completed",
        ),
    )
    db.conn.commit()

    # Attempt to upsert with older completed_at should keep the newer completed_at
    db.conn.execute(
        UPSERT_RUN_SQL,
        (
            "run_test",
            "h1",
            "model_x",
            "model_x",
            "Q4",
            "LM Studio",
            "{}",
            "1.0",
            "2026-01-01 00:00:00",
            "2026-01-01 01:00:00",
            "completed",
        ),
    )
    db.conn.commit()
    row = db.conn.execute("SELECT completed_at FROM runs WHERE id = 'run_test'").fetchone()
    assert row[0] == "2026-01-01 02:00:00"


def test_legacy_import_does_not_duplicate_results_across_hosts(db, tmp_path):
    # Setup two hosts in DB
    db.conn.execute(
        "INSERT OR REPLACE INTO hosts (id, label, created_at, is_active) VALUES ('h2', 'Host2', '2026-01-01', 0)"
    )
    db.conn.commit()

    rec_dir = tmp_path / "rec_legacy"
    res_dir = rec_dir / "results"
    res_dir.mkdir(parents=True)

    # Legacy result file without run_id or host_id
    legacy_res = {
        "model": "model_shared",
        "benchmark": "bench_test",
        "level": "level1",
        "tested_at": "2026-01-01 00:00:00",
        "passed": 1,
        "total": 1,
        "failures": [],
    }
    (res_dir / "model_shared_bench_test_level1.json").write_text(json.dumps(legacy_res), encoding="utf-8")

    import_all(db, rec_dir)

    # Should only create 1 result row attached to 1 run (default_host h1), NOT duplicated to h2!
    rows = db.conn.execute("SELECT run_id, model FROM results WHERE model = 'model_shared'").fetchall()
    assert len(rows) == 1
    assert "h1" in rows[0][0]


def test_paths_for_supports_quantization_and_avoids_collisions(tmp_path):
    from benchmarks.base import Benchmark, Level
    from storage import ResultStore

    class DummyB(Benchmark):
        id = "dummy_b"
        name = "Dummy"
        short = "DB"
        answers_dir_name = "models_answers"
        file_ext = "py"
        levels = [Level(id="l1", name="L1", prompt="")]

        def run_tests(self, level_id, answer_path):
            return None

    bench = DummyB()
    store = ResultStore(Database(tmp_path / "test.db"), answers_root=tmp_path, raw_answers_dir=tmp_path / "raw")

    ans_q4, _ = store.paths_for(bench, "my_model", "l1", quantization="Q4_K_M")
    ans_fp16, _ = store.paths_for(bench, "my_model", "l1", quantization="FP16")

    assert "Q4_K_M" in ans_q4.name
    assert "FP16" in ans_fp16.name
    assert ans_q4.name != ans_fp16.name

    # Backwards compatibility: existing unquantized answer is returned when quantized file doesn't exist
    legacy_file = tmp_path / "models_answers" / "my_model_dummy_b_l1.py"
    legacy_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_file.write_text("print('legacy')", encoding="utf-8")

    ans_resolved, _ = store.paths_for(bench, "my_model", "l1", quantization="Q8_0")
    assert ans_resolved == legacy_file


def test_detect_backend_respects_custom_url(monkeypatch):
    import requests

    from storage import detect_backend

    called_urls = []

    def mock_get(url, *args, **kwargs):
        called_urls.append(url)

        class MockResp:
            status_code = 200

            def json(self):
                return {"version": "0.1.30"}

        return MockResp()

    monkeypatch.setattr(requests, "get", mock_get)

    res = detect_backend("http://custom-host:11434/v1")
    assert res == "Ollama v0.1.30"
    assert any("custom-host:11434/api/version" in u for u in called_urls)
    assert not any("localhost:11434" in u for u in called_urls)


def test_ensure_active_run_id_handles_stale_and_completed_runs(db, tmp_path):
    from storage import ResultStore

    store = ResultStore(db, answers_root=tmp_path, raw_answers_dir=tmp_path / "raw")

    # 1. Stale in_progress run (started in past)
    old_time = "2026-01-01 00:00:00"
    run_store = RunStore(db)
    stale_run = run_store.create(host_id="h1", model_key="stale_model")
    db.conn.execute("UPDATE runs SET started_at = ? WHERE id = ?", (old_time, stale_run.id))
    db.conn.commit()

    new_run_id = store._ensure_active_run_id("stale_model", host_id="h1")
    assert new_run_id != stale_run.id
    # Stale run must be marked failed
    stale_status = db.conn.execute("SELECT status FROM runs WHERE id = ?", (stale_run.id,)).fetchone()[0]
    assert stale_status == "failed"

    # 2. Completed run must not be hitched onto
    completed_run = run_store.create(host_id="h1", model_key="completed_model")
    run_store.complete(completed_run.id, status="completed")

    fresh_run_id = store._ensure_active_run_id("completed_model", host_id="h1")
    assert fresh_run_id != completed_run.id
