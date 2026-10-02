"""Unit and integration tests for Run entity, RunStore, migration, and multi-host aggregation."""

import json
import re

from benchmarks.base import GenerationStats, SpeedSample, StoredResult
from benchmarks.base import TestResult as BenchTestResult
from benchmarks.c_framing import CFramingBenchmark
from benchmarks.vm import VMBenchmark
from database import Database
from lmstudio import GenerationConfig, ModelArtifactInfo, _render_transcript
from storage import (
    ResultStore,
    Run,
    RunStore,
    SpeedResultStore,
    compute_suite_hash,
    detect_backend,
    detect_quantization,
    get_suite_version,
)
from sync import export_all, import_all


def _add_test_host(db: Database, host_id: str, label: str) -> None:
    db.conn.execute(
        "INSERT OR REPLACE INTO hosts (id, label, created_at) VALUES (?, ?, ?)",
        (host_id, label, "2026-01-01 00:00:00"),
    )
    db.conn.commit()


def test_detect_quantization():
    assert detect_quantization("qwen2.5-coder-7b-instruct-q4_k_m.gguf") == "Q4_K_M"
    assert detect_quantization("meta-llama-3-8b-instruct-q8_0") == "Q8_0"
    assert detect_quantization("model-fp16") == "FP16"
    assert detect_quantization("deepseek-coder-qat") == "QAT"
    assert detect_quantization("plain-model-name") is None


def test_detect_backend():
    assert "Ollama" in detect_backend("http://localhost:11434/v1")
    assert "llama.cpp" in detect_backend("http://127.0.0.1:8080")
    assert "vLLM" in detect_backend("http://localhost:8000/v1")
    assert "LM Studio" in detect_backend("http://localhost:1234/v1")


def test_run_dataclass():
    run = Run.create(
        host_id="test_host",
        model_key="test-model-q4_k_m",
        generation_params={"temperature": 0.2, "seed": 42},
    )
    assert run.id.startswith("run_")
    assert run.host_id == "test_host"
    assert run.quantization == "Q4_K_M"
    assert run.status == "in_progress"
    assert run.generation_params["temperature"] == 0.2

    d = run.to_dict()
    restored = Run.from_dict(d)
    assert restored.id == run.id
    assert restored.generation_params == run.generation_params


def test_run_store_lifecycle(tmp_path):
    db = Database(tmp_path / "test.db")
    _add_test_host(db, "host_1", "Host One")

    store = RunStore(db)

    # 1. Create run
    run = store.create(
        host_id="host_1",
        model_key="model_alpha",
        model_name="Model Alpha",
        quantization="Q4_K_M",
        backend="LM Studio",
        generation_params={"temperature": 0.0, "max_tokens": 1024},
    )
    assert run.status == "in_progress"

    # 2. Get active run
    active_id = store.get_active_run_id("model_alpha")
    assert active_id == run.id

    # 3. Retrieve run
    fetched = store.get(run.id)
    assert fetched is not None
    assert fetched.model_key == "model_alpha"
    assert fetched.quantization == "Q4_K_M"
    assert fetched.generation_params["max_tokens"] == 1024

    # 4. Complete run
    store.complete(run.id, status="completed")
    updated = store.get(run.id)
    assert updated.status == "completed"
    assert updated.completed_at is not None

    # Active run should now be None
    assert store.get_active_run_id("model_alpha") is None

    # 5. List runs
    runs = store.list_runs(model_key="model_alpha")
    assert len(runs) == 1
    assert runs[0].id == run.id


def test_result_and_speed_stores_link_to_run(tmp_path):
    db = Database(tmp_path / "test.db")
    _add_test_host(db, "host_1", "Host One")

    run_store = RunStore(db)
    result_store = ResultStore(db, tmp_path / "answers", tmp_path / "raw")
    speed_store = SpeedResultStore(db, records_speeds_dir=tmp_path / "speeds")

    bench = VMBenchmark()
    run = run_store.create(host_id="host_1", model_key="model_beta")

    # Store test result with run_id
    tr = BenchTestResult(
        passed=1,
        total=1,
        failures=[],
    )
    sr = StoredResult(
        model="model_beta",
        benchmark="vm",
        level="1",
        tested_at="2026-01-01 00:00:00",
        evaluation=tr,
    )
    result_store.save(bench, "model_beta", "1", sr, run_id=run.id)

    # Store speed result with run_id
    stats = GenerationStats(
        input_tokens=100,
        total_output_tokens=50,
        reasoning_output_tokens=10,
        tokens_per_second=45.5,
        time_to_first_token_seconds=0.3,
        model_load_time_seconds=1.2,
    )
    sample = SpeedSample(
        host_id="host_1",
        host_label="Host One",
        model="model_beta",
        benchmark="vm",
        level="1",
        tested_at="2026-01-01 00:00:00",
        stats=stats,
    )
    speed_store.save(sample, run_id=run.id)

    # Verify rows in database have run_id
    r_row = db.conn.execute("SELECT run_id, model, benchmark, level, passed FROM results").fetchone()
    assert r_row["run_id"] == run.id
    assert r_row["model"] == "model_beta"
    assert r_row["passed"] == 1

    s_row = db.conn.execute("SELECT run_id, host_id, model, tokens_per_second FROM speed_results").fetchone()
    assert s_row["run_id"] == run.id
    assert s_row["host_id"] == "host_1"
    assert s_row["tokens_per_second"] == 45.5


def test_multi_host_join_no_cartesian_multiplication(tmp_path):
    """Verifies that joining results and speed_results on run_id prevents

    multiplication of passed/total counts across multiple hosts.
    """
    db = Database(tmp_path / "test.db")
    _add_test_host(db, "host_mac", "MacBook Pro")
    _add_test_host(db, "host_pc", "Desktop PC")

    run_store = RunStore(db)
    result_store = ResultStore(db, tmp_path / "answers", tmp_path / "raw")
    speed_store = SpeedResultStore(db, records_speeds_dir=tmp_path / "speeds")

    bench = CFramingBenchmark()

    # Host 1 run
    run1 = run_store.create(host_id="host_mac", model_key="shared_model")
    sr1 = StoredResult(
        model="shared_model",
        benchmark="c_framing",
        level="1",
        tested_at="2026-01-01 00:00:00",
        evaluation=BenchTestResult(passed=5, total=5, failures=[]),
    )
    result_store.save(bench, "shared_model", "1", sr1, run_id=run1.id)
    speed_store.save(
        SpeedSample(
            host_id="host_mac",
            host_label="MacBook Pro",
            model="shared_model",
            benchmark="c_framing",
            level="1",
            tested_at="2026-01-01 00:00:00",
            stats=GenerationStats(
                input_tokens=10,
                total_output_tokens=20,
                reasoning_output_tokens=0,
                tokens_per_second=30.0,
                time_to_first_token_seconds=0.2,
                model_load_time_seconds=0.5,
            ),
        ),
        run_id=run1.id,
    )
    run_store.complete(run1.id)

    # Host 2 run
    run2 = run_store.create(host_id="host_pc", model_key="shared_model")
    sr2 = StoredResult(
        model="shared_model",
        benchmark="c_framing",
        level="1",
        tested_at="2026-01-01 00:00:00",
        evaluation=BenchTestResult(passed=5, total=5, failures=[]),
    )
    result_store.save(bench, "shared_model", "1", sr2, run_id=run2.id)
    speed_store.save(
        SpeedSample(
            host_id="host_pc",
            host_label="Desktop PC",
            model="shared_model",
            benchmark="c_framing",
            level="1",
            tested_at="2026-01-01 00:00:00",
            stats=GenerationStats(
                input_tokens=10,
                total_output_tokens=20,
                reasoning_output_tokens=0,
                tokens_per_second=60.0,
                time_to_first_token_seconds=0.1,
                model_load_time_seconds=0.2,
            ),
        ),
        run_id=run2.id,
    )
    run_store.complete(run2.id)

    # Query with strict run_id join (the fixed architecture)
    fixed_query = """
        SELECT
            r.model,
            COUNT(r.benchmark) as entries,
            SUM(r.passed) as total_passed,
            SUM(r.total) as total_tests
        FROM results r
        LEFT JOIN speed_results s
            ON r.run_id = s.run_id
            AND r.benchmark = s.benchmark
            AND r.level = s.level
        WHERE r.model = 'shared_model'
        GROUP BY r.model
    """
    row = db.conn.execute(fixed_query).fetchone()
    # 2 runs * 5 tests = 10 total tests (not 20!)
    assert row["entries"] == 2
    assert row["total_passed"] == 10
    assert row["total_tests"] == 10

    # For a single run, tests count is exactly 5
    single_run_query = """
        SELECT SUM(r.passed) as passed, SUM(r.total) as total
        FROM results r
        LEFT JOIN speed_results s
            ON r.run_id = s.run_id
            AND r.benchmark = s.benchmark
            AND r.level = s.level
        WHERE r.run_id = ?
    """
    s_row = db.conn.execute(single_run_query, (run1.id,)).fetchone()
    assert s_row["passed"] == 5
    assert s_row["total"] == 5


def test_runs_git_sync(tmp_path):
    records_dir = tmp_path / "records"
    db_source = Database(tmp_path / "source.db")
    _add_test_host(db_source, "host_main", "Main Host")

    run_store = RunStore(db_source)
    result_store = ResultStore(db_source, tmp_path / "answers", tmp_path / "raw")
    speed_store = SpeedResultStore(db_source, records_speeds_dir=tmp_path / "records" / "speeds")

    bench = VMBenchmark()

    run = run_store.create(
        host_id="host_main",
        model_key="model_sync_test",
        generation_params={"seed": 123},
    )
    sr = StoredResult(
        model="model_sync_test",
        benchmark="vm",
        level="1",
        tested_at="2026-01-01 00:00:00",
        evaluation=BenchTestResult(passed=3, total=3, failures=[]),
    )
    result_store.save(bench, "model_sync_test", "1", sr, run_id=run.id)
    speed_store.save(
        SpeedSample(
            host_id="host_main",
            host_label="Main Host",
            model="model_sync_test",
            benchmark="vm",
            level="1",
            tested_at="2026-01-01 00:00:00",
            stats=GenerationStats(
                input_tokens=10,
                total_output_tokens=15,
                reasoning_output_tokens=0,
                tokens_per_second=25.0,
                time_to_first_token_seconds=0.5,
                model_load_time_seconds=1.0,
            ),
        ),
        run_id=run.id,
    )
    run_store.complete(run.id)

    # Export to records
    counts = export_all(db_source, records_dir)
    assert counts["runs"] == 1
    assert counts["results"] == 1
    assert counts["speeds"] == 1
    assert counts["hosts"] == 1

    run_file = records_dir / "runs" / f"{run.id}.json"
    assert run_file.exists()
    run_data = json.loads(run_file.read_text(encoding="utf-8"))
    assert run_data["id"] == run.id
    assert len(run_data["results"]) == 1
    assert len(run_data["speeds"]) == 1

    # Import into fresh database
    db_target = Database(tmp_path / "target.db")
    imported = import_all(db_target, records_dir)
    assert imported["runs"] == 1
    assert imported["results"] == 1
    assert imported["speeds"] == 1
    assert imported["hosts"] == 1

    target_run = RunStore(db_target).get(run.id)
    assert target_run is not None
    assert target_run.model_key == "model_sync_test"
    assert target_run.generation_params["seed"] == 123


def test_mcp_runs_tools():
    import mcp_server

    runs_res = mcp_server.list_runs(limit=10)
    assert isinstance(runs_res, str)
    assert "Benchmark Runs" in runs_res
    assert "Run ID" in runs_res

    # Extract first run ID from table
    match = re.search(r"`([a-zA-Z0-9_-]+)`", runs_res)
    assert match is not None
    rid = match.group(1)

    details = mcp_server.get_run_details(rid)
    assert isinstance(details, str)
    assert f"Run: `{rid}`" in details or "Model" in details
    assert "Generation Params" in details or "Hyperparameters" in details


def test_generation_config():
    cfg = GenerationConfig()
    assert cfg.temperature == 0.0
    assert cfg.seed == 42
    assert cfg.top_p == 1.0
    assert cfg.max_tokens == 16384
    assert cfg.timeout_seconds == 600.0

    d = cfg.to_dict()
    assert d["temperature"] == 0.0
    assert d["seed"] == 42
    assert d["max_tokens"] == 16384

    restored = GenerationConfig.from_dict(d)
    assert restored.seed == 42
    assert restored.temperature == 0.0


def test_model_artifact_info():
    art = ModelArtifactInfo(
        key="nvidia/nemotron-3-nano-4b",
        display_name="Nemotron 3 Nano 4B",
        architecture="nemotron_h",
        quantization="Q4_K_M",
        quantization_bits=4,
        size_bytes=2837173509,
        params_string="4.0B",
        format="gguf",
    )
    d = art.to_dict()
    assert d["architecture"] == "nemotron_h"
    assert d["quantization"] == "Q4_K_M"
    assert d["size_bytes"] == 2837173509

    restored = ModelArtifactInfo.from_dict(d)
    assert restored.architecture == "nemotron_h"
    assert restored.size_bytes == 2837173509


def test_compute_suite_hash():
    h = compute_suite_hash()
    assert isinstance(h, str)
    assert len(h) == 12

    # Determinism test
    h2 = compute_suite_hash()
    assert h == h2

    ver = get_suite_version()
    assert h in ver


def test_render_transcript_single_and_multi_turn():
    # Single user turn should NOT prepend 'User:\n'
    sys_p, content = _render_transcript([{"role": "user", "content": "Write a function"}])
    assert sys_p is None
    assert content == "Write a function"

    # Multi turn should cleanly separate
    messages = [
        {"role": "system", "content": "You are an assistant"},
        {"role": "user", "content": "Level 1 prompt"},
        {"role": "assistant", "content": "Level 1 code"},
        {"role": "user", "content": "Level 2 prompt"},
    ]
    sys_p, content = _render_transcript(messages)
    assert sys_p == "You are an assistant"
    assert "User:\nLevel 1 prompt" in content
    assert "Assistant:\nLevel 1 code" in content
    assert "User:\nLevel 2 prompt" in content
