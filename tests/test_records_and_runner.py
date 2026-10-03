"""Tests for records file naming, error-handler robustness, JS timer ids and runner skip/force semantics."""

import json
from pathlib import Path

import pytest
from rich.console import Console

import lmstudio
import runner
from benchmarks.base import Benchmark, GenerationStats, Level, SpeedSample, StoredResult
from benchmarks.base import TestResult as BenchTestResult
from database import Database
from host_configs import HostConfig, HostConfigStore
from lmstudio import GenerationConfig, Model, ModelResponse
from sandboxes.js_quickjs import create_js_context, drain_js_jobs
from storage import (
    GENERATION_FAILED_PREFIX,
    TRUNCATED_PREFIX,
    ResultStore,
    RunStore,
    SpeedResultStore,
    result_record_name,
)
from sync import export_all, import_all


class DummyBenchmark(Benchmark):
    id = "dummy"
    name = "Dummy"
    short = "Dummy"
    levels = [
        Level(id="level1", name="L1", prompt="prompt 1"),
        Level(id="level2", name="L2", prompt="prompt 2", requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> BenchTestResult:
        return BenchTestResult(1, 1, [])


def _add_host(db: Database, host_id: str, label: str = "Host") -> HostConfig:
    db.conn.execute(
        "INSERT OR REPLACE INTO hosts (id, label, created_at) VALUES (?, ?, ?)",
        (host_id, label, "2026-01-01 00:00:00"),
    )
    db.conn.commit()
    return HostConfig(id=host_id, label=label, created_at="2026-01-01 00:00:00")


def _stored(model: str, level: str, passed: int = 1, total: int = 1, failures: list[str] | None = None):
    return StoredResult(
        model=model,
        benchmark="dummy",
        level=level,
        tested_at="2026-01-01 00:00:00",
        evaluation=BenchTestResult(passed, total, failures or []),
    )


class Env:
    def __init__(self, tmp_path: Path):
        self.db = Database(tmp_path / "t.db")
        self.host = _add_host(self.db, "hostaaaa1111")
        self.run_store = RunStore(self.db)
        self.store = ResultStore(self.db, tmp_path / "answers", tmp_path / "raw")
        self.speed_store = SpeedResultStore(self.db, records_speeds_dir=tmp_path / "speeds")
        self.bench = DummyBenchmark()
        self.model = Model(type="llm", key="m-1")
        self.console = Console(quiet=True)
        self.store.ensure_dirs([self.bench])

    def new_run(self):
        return self.run_store.create(host_id=self.host.id, model_key=self.model.key)

    def seed_scored(self, level: str) -> None:
        """Simulates a previous run that fully completed the level (result + answer + raw)."""
        run = self.new_run()
        self.store.save(self.bench, self.model.key, level, _stored(self.model.key, level), run_id=run.id)
        answer_path, raw_path = self.store.paths_for(self.bench, self.model.key, level)
        answer_path.write_text("old answer\n", encoding="utf-8")
        raw_path.write_text("old raw\n", encoding="utf-8")

    def execute(self, level: str, run_id: str, force: bool) -> bool:
        return runner.execute_test(
            self.model,
            self.bench,
            level,
            self.host,
            run_id=run_id,
            force=force,
            gen_config=GenerationConfig(),
            store=self.store,
            speed_store=self.speed_store,
            db=self.db,
            console=self.console,
        )


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


@pytest.fixture
def ask_calls(monkeypatch):
    calls: list[list[dict]] = []

    def fake_ask(model_key, messages, temperature=None, config=None):
        calls.append(messages)
        return ModelResponse(
            content="```python\nx = 1\n```",
            stats={"tokens_per_second": 10.0, "time_to_first_token_seconds": 0.1},
            raw={},
        )

    monkeypatch.setattr(lmstudio, "ask_model", fake_ask)
    return calls


# ── runner skip / force ─────────────────────────────────────────────────────────


def test_scored_level_from_earlier_run_is_skipped(env, ask_calls):
    env.seed_scored("level1")
    run = env.new_run()

    assert env.execute("level1", run.id, force=False) is True
    assert ask_calls == []


def test_force_regenerates_only_requested_level(env, ask_calls):
    env.seed_scored("level1")
    env.seed_scored("level2")
    run = env.new_run()

    env.execute("level2", run.id, force=True)

    assert len(ask_calls) == 1  # level 1 was reused as context, not regenerated
    assert [m["content"] for m in ask_calls[0]] == ["prompt 1", "old raw\n", "prompt 2"]
    assert env.store.load(env.bench, env.model.key, "level2", run_id=run.id) is not None


def test_missing_level_does_not_regenerate_scored_prerequisite(env, ask_calls):
    env.seed_scored("level1")
    run = env.new_run()

    env.execute("level2", run.id, force=False)

    assert len(ask_calls) == 1
    assert ask_calls[0][-1]["content"] == "prompt 2"
    assert env.store.paths_for(env.bench, env.model.key, "level1")[0].read_text(encoding="utf-8") == "old answer\n"


def test_unscored_prerequisite_is_generated_first(env, ask_calls):
    run = env.new_run()

    env.execute("level2", run.id, force=False)

    assert len(ask_calls) == 2
    assert ask_calls[0][-1]["content"] == "prompt 1"
    assert ask_calls[1][-1]["content"] == "prompt 2"
    # Current run only executed level2, so only level2 must have a speed sample in this run
    speeds = env.speed_store.all_saved(run_id=run.id)
    assert len(speeds) == 1
    assert speeds[0].level == "level2"


def test_prerequisite_with_raw_on_disk_is_reused_without_regeneration(env, ask_calls):
    # Prerequisite raw file exists on disk, but has NO DB record in results
    _, raw_path = env.store.paths_for(env.bench, env.model.key, "level1")
    raw_path.write_text("existing raw answer\n", encoding="utf-8")
    run = env.new_run()

    env.execute("level2", run.id, force=False)

    assert len(ask_calls) == 1
    assert ask_calls[0][-1]["content"] == "prompt 2"
    assert ask_calls[0][-2]["content"] == "existing raw answer\n"


def test_skip_with_none_load_does_not_crash(env, monkeypatch):
    run = env.new_run()
    monkeypatch.setattr(env.store, "has_scored_result", lambda *args, **kwargs: True)
    monkeypatch.setattr(env.store, "load", lambda *args, **kwargs: None)

    assert env.execute("level1", run.id, force=False) is True


@pytest.mark.parametrize("marker", [TRUNCATED_PREFIX, GENERATION_FAILED_PREFIX, "Model generation failed or timed out"])
def test_infrastructure_failures_are_not_treated_as_done(env, ask_calls, marker):
    old = env.new_run()
    env.store.save(env.bench, env.model.key, "level1", _stored(env.model.key, "level1", 0, 1, [f"{marker} x"]), old.id)
    assert env.store.has_result(env.bench, env.model.key, "level1")
    assert not env.store.has_scored_result(env.bench, env.model.key, "level1")

    run = env.new_run()
    env.execute("level1", run.id, force=False)
    assert len(ask_calls) == 1


def test_real_zero_score_counts_as_scored(env):
    run = env.new_run()
    env.store.save(env.bench, env.model.key, "level1", _stored(env.model.key, "level1", 0, 5, ["wrong"]), run.id)
    assert env.store.has_scored_result(env.bench, env.model.key, "level1")


# ── error handlers must not raise UnboundLocalError ─────────────────────────────


def test_result_save_survives_unwritable_records_dir(tmp_path):
    db = Database(tmp_path / "t.db")
    _add_host(db, "h1")
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "records").write_text("not a directory", encoding="utf-8")  # mkdir will fail
    store = ResultStore(db, answers, tmp_path / "raw")
    run = RunStore(db).create(host_id="h1", model_key="m")

    store.save(DummyBenchmark(), "m", "level1", _stored("m", "level1"), run_id=run.id)

    assert store.has_result(DummyBenchmark(), "m", "level1", run_id=run.id)


def test_speed_save_survives_unwritable_records_dir(tmp_path):
    db = Database(tmp_path / "t.db")
    _add_host(db, "h1")
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    store = SpeedResultStore(db, records_speeds_dir=blocker / "speeds")
    run = RunStore(db).create(host_id="h1", model_key="m")
    sample = SpeedSample(
        "h1", "Host", "m", "dummy", "level1", "2026-01-01 00:00:00", GenerationStats(tokens_per_second=5.0)
    )

    store.save(sample, run_id=run.id)

    assert len(store.all_saved(run_id=run.id)) == 1


def test_host_add_survives_unwritable_records_dir(tmp_path, monkeypatch):
    db = Database(tmp_path / "t.db")

    def boom(self, *args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(Path, "mkdir", boom)
    host = HostConfig.create("Some Host")

    store = HostConfigStore(db, records_dir=tmp_path / "records" / "hosts")
    store.add(host)

    assert store.get(host.id) is not None


# ── JS virtual timers ───────────────────────────────────────────────────────────


def test_js_timer_ids_stay_unique_after_timers_fire():
    solution = """
    const log = [];
    setTimeout(() => {
        log.push('a');
        const c = setTimeout(() => log.push('c'), 20);
        clearTimeout(c);               // must cancel c, never b
    }, 0);
    setTimeout(() => log.push('b'), 10);
    """
    ctx = create_js_context(solution)
    drain_js_jobs(ctx)
    assert json.loads(ctx.eval("JSON.stringify(log)")) == ["a", "b"]


def test_js_timer_ids_are_monotonic():
    ctx = create_js_context("const ids = [setTimeout(() => {}, 0), setTimeout(() => {}, 0)];")
    drain_js_jobs(ctx)
    ctx.eval("ids.push(setTimeout(() => {}, 0))")
    assert json.loads(ctx.eval("JSON.stringify(ids)")) == [1, 2, 3]


# ── records file names ──────────────────────────────────────────────────────────


def test_result_records_include_host_and_run_ids(tmp_path):
    db = Database(tmp_path / "t.db")
    _add_host(db, "hostaaaa1111")
    _add_host(db, "hostbbbb2222")
    store = ResultStore(db, tmp_path / "answers", tmp_path / "raw")
    run_store = RunStore(db)
    bench = DummyBenchmark()

    run_a = run_store.create(host_id="hostaaaa1111", model_key="vendor/m-1")
    run_b = run_store.create(host_id="hostbbbb2222", model_key="vendor/m-1")
    store.save(bench, "vendor/m-1", "level1", _stored("vendor/m-1", "level1"), run_id=run_a.id)
    store.save(bench, "vendor/m-1", "level1", _stored("vendor/m-1", "level1", 0, 1, ["x"]), run_id=run_b.id)

    results_dir = tmp_path / "answers" / "records" / "results"
    files = sorted(p.name for p in results_dir.glob("*.json"))
    assert files == sorted(
        [
            result_record_name("hostaaaa1111", run_a.id, "vendor/m-1", "dummy", "level1"),
            result_record_name("hostbbbb2222", run_b.id, "vendor/m-1", "dummy", "level1"),
        ]
    )
    data = json.loads((results_dir / files[0]).read_text(encoding="utf-8"))
    assert {"run_id", "host_id", "model", "benchmark", "level"} <= data.keys()
    assert files[0].startswith(data["host_id"]) and data["run_id"] in files[0]


def test_speed_records_include_host_and_run_ids(tmp_path):
    db = Database(tmp_path / "t.db")
    _add_host(db, "hostaaaa1111")
    store = SpeedResultStore(db, records_speeds_dir=tmp_path / "speeds")
    run = RunStore(db).create(host_id="hostaaaa1111", model_key="m")
    sample = SpeedSample(
        "hostaaaa1111", "Host", "m", "dummy", "level1", "2026-01-01 00:00:00", GenerationStats(tokens_per_second=5.0)
    )

    store.save(sample, run_id=run.id)

    (path,) = list((tmp_path / "speeds").glob("*.json"))
    assert path.name.startswith("hostaaaa1111__") and run.id in path.name
    assert json.loads(path.read_text(encoding="utf-8"))["run_id"] == run.id


def test_export_skips_snapshots_for_legacy_runs(tmp_path):
    db = Database(tmp_path / "src.db")
    _add_host(db, "hostaaaa1111")
    store = ResultStore(db, tmp_path / "answers", tmp_path / "raw")
    legacy = RunStore(db).create(host_id="hostaaaa1111", model_key="m")
    db.conn.execute("UPDATE runs SET id = 'legacy_h_m' WHERE id = ?", (legacy.id,))
    db.conn.commit()
    store.save(DummyBenchmark(), "m", "level1", _stored("m", "level1"), run_id="legacy_h_m")

    records = tmp_path / "records"
    counts = export_all(db, records)

    assert counts["runs"] == 1  # the run file still carries the data
    assert counts["results"] == 0
    assert list((records / "results").glob("*.json")) == []


def test_export_writes_distinct_snapshot_files_per_run_and_roundtrips(tmp_path):
    src = Database(tmp_path / "src.db")
    _add_host(src, "hostaaaa1111")
    _add_host(src, "hostbbbb2222")
    store = ResultStore(src, tmp_path / "answers", tmp_path / "raw")
    run_store = RunStore(src)
    bench = DummyBenchmark()
    run_a = run_store.create(host_id="hostaaaa1111", model_key="m")
    run_b = run_store.create(host_id="hostbbbb2222", model_key="m")
    store.save(bench, "m", "level1", _stored("m", "level1", 1, 2), run_id=run_a.id)
    store.save(bench, "m", "level1", _stored("m", "level1", 2, 2), run_id=run_b.id)

    records = tmp_path / "records"
    counts = export_all(src, records)
    assert counts["results"] == 2
    assert len(list((records / "results").glob("*.json"))) == 2

    # Snapshot-only import (no runs/ directory) must attribute each result to its own run.
    for f in (records / "runs").glob("*.json"):
        f.unlink()
    dst = Database(tmp_path / "dst.db")
    imported = import_all(dst, records)
    assert imported["results"] == 2
    rows = dst.conn.execute("SELECT run_id, passed FROM results ORDER BY run_id").fetchall()
    assert {(r["run_id"], r["passed"]) for r in rows} == {(run_a.id, 1), (run_b.id, 2)}


def test_infra_failures_not_penalized_in_leaderboard_and_analytics(tmp_path):
    import analytics
    import report_data

    db = Database(tmp_path / "t.db")
    _add_host(db, "host1")
    store = ResultStore(db, tmp_path / "answers", tmp_path / "raw")
    run_store = RunStore(db)
    bench = DummyBenchmark()
    run = run_store.create(host_id="host1", model_key="test-model")

    # Scored success
    res1 = _stored("test-model", "level1", passed=5, total=5)
    # Infra failures (timeout/error and truncation)
    res2 = _stored(
        "test-model",
        "level2",
        passed=0,
        total=0,
        failures=[f"{GENERATION_FAILED_PREFIX} Model generation failed or timed out"],
    )
    res3 = _stored("test-model", "level3", passed=0, total=0, failures=[f"{TRUNCATED_PREFIX} Output truncated"])

    store.save(bench, "test-model", "level1", res1, run_id=run.id)
    store.save(bench, "test-model", "level2", res2, run_id=run.id)
    store.save(bench, "test-model", "level3", res3, run_id=run.id)

    assert store.has_scored_result(bench, "test-model", "level1") is True
    assert store.has_scored_result(bench, "test-model", "level2") is False
    assert store.has_scored_result(bench, "test-model", "level3") is False

    assert store.has_result(bench, "test-model", "level1", only_scored=True) is True
    assert store.has_result(bench, "test-model", "level2", only_scored=True) is False

    # Check analytics helper behavior
    rows = db.conn.execute("SELECT * FROM results WHERE model = 'test-model' ORDER BY level").fetchall()
    assert analytics._pct(rows[0]) == 100.0
    assert analytics._pct(rows[1]) is None
    assert analytics._pct(rows[2]) is None

    assert analytics._score_text(rows[0]) == "5/5"
    assert analytics._score_text(rows[1]) == "⚠️ INFRA"
    assert analytics._score_text(rows[2]) == "✂️ TRUNC"

    # Leaderboard should average only genuinely scored tests (100%, not 33.3%)
    leaderboard = analytics.get_leaderboard(db.conn)
    assert "100%" in leaderboard
    assert "33%" not in leaderboard

    # list_models should show 100.0% average quality
    models_summary = analytics.list_models(db.conn)
    assert "100.0%" in models_summary

    # report_data should also exclude infra failures from totals and averages
    l_data, _ = report_data.load_leaderboard_data(db.conn)
    assert len(l_data) == 1
    assert l_data[0]["avg_pct"] == 100.0
    assert l_data[0]["passed"] == 5
    assert l_data[0]["total"] == 5


def test_runner_records_zero_total_on_generation_failure(env, monkeypatch):
    run = env.new_run()
    monkeypatch.setattr(runner, "ensure_level_answer", lambda *a, **kw: None)

    ret = env.execute("level1", run_id=run.id, force=True)
    assert ret is False

    res = env.store.load(env.bench, env.model.key, "level1", run_id=run.id)
    assert res is not None
    assert res.evaluation.passed == 0
    assert res.evaluation.total == 0
    assert res.evaluation.failures[0].startswith(GENERATION_FAILED_PREFIX)
    assert env.store.has_scored_result(env.bench, env.model.key, "level1", run_id=run.id) is False


def test_js_global_const_and_class_redeclaration():
    # User solution declaring its own class AbortController or const __timers must not fail with SyntaxError
    code = """
    class AbortController {
        constructor() { this.custom = true; }
    }
    class AbortSignal {
        constructor() { this.custom = true; }
    }
    const __timers = [1, 2, 3];
    const setTimeout = () => 42;
    const clearInterval = () => true;
    let __currentTime = 999;
    const result = {
        ac: new AbortController().custom,
        as: new AbortSignal().custom,
        timers: __timers,
        st: setTimeout(),
    };
    """
    ctx = create_js_context(code)
    drain_js_jobs(ctx)
    res = json.loads(ctx.eval("JSON.stringify(result)"))
    assert res == {"ac": True, "as": True, "timers": [1, 2, 3], "st": 42}


def test_js_virtual_clock_date_and_performance():
    code = """
    const pStart = performance.now();
    const dStart = Date.now();
    const objStart = new Date().getTime();
    let pEnd = 0;
    let dEnd = 0;
    let objEnd = 0;

    setTimeout(() => {
        pEnd = performance.now();
        dEnd = Date.now();
        objEnd = new Date().getTime();
    }, 150);
    """
    ctx = create_js_context(code)
    drain_js_jobs(ctx)
    assert ctx.eval("pStart") == 0
    assert ctx.eval("pEnd") == 150
    assert ctx.eval("dEnd - dStart") == 150
    assert ctx.eval("objEnd - objStart") == 150


def test_js_set_interval_and_clear_interval():
    code = """
    const ticks = [];
    const id = setInterval(() => {
        ticks.push(performance.now());
        if (ticks.length === 3) {
            clearInterval(id);
        }
    }, 20);
    """
    ctx = create_js_context(code)
    drain_js_jobs(ctx)
    ticks = json.loads(ctx.eval("JSON.stringify(ticks)"))
    assert ticks == [20, 40, 60]


def test_js_queue_microtask():
    code = """
    const order = [];
    setTimeout(() => order.push("timer"), 0);
    queueMicrotask(() => order.push("microtask"));
    """
    ctx = create_js_context(code)
    drain_js_jobs(ctx)
    assert json.loads(ctx.eval("JSON.stringify(order)")) == ["microtask", "timer"]


def test_js_abort_signal_features():
    code = """
    const c = new AbortController();
    const sig = c.signal;

    let onabortCalled = false;
    let listenerCalled = false;
    let eventType = null;
    let eventTargetIsSig = false;

    sig.onabort = (e) => {
        onabortCalled = true;
        eventType = e.type;
        eventTargetIsSig = (e.target === sig);
    };
    sig.addEventListener('abort', (e) => {
        listenerCalled = true;
    });

    c.abort();

    let threwAbort = false;
    try {
        sig.throwIfAborted();
    } catch (err) {
        threwAbort = (err.name === 'AbortError' && err.message === 'This operation was aborted');
    }

    const staticAborted = AbortSignal.abort();
    let staticTimeoutAborted = false;
    let timeoutReasonName = null;
    const timeoutSig = AbortSignal.timeout(10);
    timeoutSig.addEventListener('abort', (e) => {
        staticTimeoutAborted = true;
        timeoutReasonName = timeoutSig.reason.name;
    });
    """
    ctx = create_js_context(code)
    drain_js_jobs(ctx)
    assert ctx.eval("onabortCalled") is True
    assert ctx.eval("listenerCalled") is True
    assert ctx.eval("eventType") == "abort"
    assert ctx.eval("eventTargetIsSig") is True
    assert ctx.eval("threwAbort") is True
    assert ctx.eval("staticAborted.aborted") is True
    assert ctx.eval("staticAborted.reason.name") == "AbortError"
    assert ctx.eval("staticTimeoutAborted") is True
    assert ctx.eval("timeoutReasonName") == "TimeoutError"


def test_js_exception_inside_timer_does_not_break_drain_js_jobs():
    code = """
    const log = [];
    setTimeout(() => {
        log.push(1);
        throw new Error("Failure inside timer");
    }, 10);
    setTimeout(() => {
        log.push(2);
    }, 20);
    """
    ctx = create_js_context(code)
    drain_js_jobs(ctx)
    assert json.loads(ctx.eval("JSON.stringify(log)")) == [1, 2]
