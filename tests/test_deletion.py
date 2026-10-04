import json
from pathlib import Path

from benchmarks import REGISTRY
from benchmarks.base import GenerationStats, SpeedSample, StoredResult
from benchmarks.base import TestResult as BenchTestResult
from database import Database
from main import get_recorded_models
from storage import ResultStore, Run, RunStore, SpeedResultStore, result_record_name, speed_record_name


def test_clear_model_isolated_cleanup(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    db.conn.execute("INSERT INTO hosts (id, label, created_at) VALUES ('host1', 'Host 1', '2026-01-01 00:00:00')")
    answers_root = tmp_path / "workspace"
    raw_answers_dir = answers_root / "raw_answers"
    records_dir = answers_root / "records"
    records_results = records_dir / "results"
    records_speeds = records_dir / "speeds"
    records_runs = records_dir / "runs"

    records_results.mkdir(parents=True)
    records_speeds.mkdir(parents=True)
    records_runs.mkdir(parents=True)

    result_store = ResultStore(db, answers_root=answers_root, raw_answers_dir=raw_answers_dir)
    speed_store = SpeedResultStore(db, records_speeds_dir=records_speeds)
    run_store = RunStore(db)

    b = REGISTRY[0]  # e.g. kv
    model_to_delete = "test-vendor/target-model"
    model_to_keep = "test-vendor/target-model-pro"

    # Seed runs
    run_del = Run(id="run_del", host_id="host1", model_key=model_to_delete)
    run_keep = Run(id="run_keep", host_id="host1", model_key=model_to_keep)
    run_store.save(run_del)
    run_store.save(run_keep)

    (records_runs / "host1__run_del.json").write_text(json.dumps(run_del.to_dict()), encoding="utf-8")
    (records_runs / "host1__run_keep.json").write_text(json.dumps(run_keep.to_dict()), encoding="utf-8")

    # Seed results
    res_del = StoredResult(
        model=model_to_delete,
        benchmark=b.id,
        level="level1",
        tested_at="2026-10-04 10:00:00",
        evaluation=BenchTestResult(passed=10, total=10, failures=[]),
    )
    res_keep = StoredResult(
        model=model_to_keep,
        benchmark=b.id,
        level="level1",
        tested_at="2026-10-04 10:00:00",
        evaluation=BenchTestResult(passed=10, total=10, failures=[]),
    )
    result_store.save(b, model_to_delete, "level1", res_del, run_id="run_del")
    result_store.save(b, model_to_keep, "level1", res_keep, run_id="run_keep")

    # Seed speeds
    stats = GenerationStats(
        input_tokens=100,
        total_output_tokens=200,
        reasoning_output_tokens=50,
        tokens_per_second=25.0,
        time_to_first_token_seconds=0.5,
    )
    sample_del = SpeedSample(
        host_id="host1",
        host_label="Host 1",
        model=model_to_delete,
        benchmark=b.id,
        level="level1",
        tested_at="2026-10-04 10:00:00",
        stats=stats,
    )
    sample_keep = SpeedSample(
        host_id="host1",
        host_label="Host 1",
        model=model_to_keep,
        benchmark=b.id,
        level="level1",
        tested_at="2026-10-04 10:00:00",
        stats=stats,
    )
    speed_store.save(sample_del, run_id="run_del")
    speed_store.save(sample_keep, run_id="run_keep")

    # Create dummy answer files
    b_ans_dir = answers_root / b.answers_dir_name
    b_ans_dir.mkdir(parents=True, exist_ok=True)
    raw_answers_dir.mkdir(parents=True, exist_ok=True)

    del_ans = b_ans_dir / f"test-vendor_target-model_{b.id}_level1.{b.file_ext}"
    keep_ans = b_ans_dir / f"test-vendor_target-model-pro_{b.id}_level1.{b.file_ext}"
    del_ans.write_text("deleted solution", encoding="utf-8")
    keep_ans.write_text("kept solution", encoding="utf-8")

    # Verify initial state
    models = get_recorded_models(db)
    assert model_to_delete in models
    assert model_to_keep in models

    # Execute clear_model for target-model
    res_count = result_store.clear_model(model_to_delete, REGISTRY)
    speed_count = speed_store.clear_model(model_to_delete)
    run_count = run_store.clear_model(model_to_delete, records_dir=records_dir)

    assert res_count > 0
    assert speed_count > 0
    assert run_count > 0

    # Target model should be removed from DB
    remaining_results = db.conn.execute("SELECT * FROM results WHERE model = ?", (model_to_delete,)).fetchall()
    assert len(remaining_results) == 0
    remaining_speeds = db.conn.execute("SELECT * FROM speed_results WHERE model = ?", (model_to_delete,)).fetchall()
    assert len(remaining_speeds) == 0
    remaining_runs = db.conn.execute("SELECT * FROM runs WHERE model_key = ?", (model_to_delete,)).fetchall()
    assert len(remaining_runs) == 0

    # Kept model must remain intact in DB
    kept_results = db.conn.execute("SELECT * FROM results WHERE model = ?", (model_to_keep,)).fetchall()
    assert len(kept_results) == 1
    kept_speeds = db.conn.execute("SELECT * FROM speed_results WHERE model = ?", (model_to_keep,)).fetchall()
    assert len(kept_speeds) == 1
    kept_runs = db.conn.execute("SELECT * FROM runs WHERE model_key = ?", (model_to_keep,)).fetchall()
    assert len(kept_runs) == 1

    # Answer files check
    assert not del_ans.exists()
    assert keep_ans.exists()

    # Records check
    del_res_file = records_results / result_record_name("host1", "run_del", model_to_delete, b.id, "level1")
    keep_res_file = records_results / result_record_name("host1", "run_keep", model_to_keep, b.id, "level1")
    assert not del_res_file.exists()
    assert keep_res_file.exists()

    del_speed_file = records_speeds / speed_record_name("host1", "run_del", model_to_delete, b.id, "level1")
    keep_speed_file = records_speeds / speed_record_name("host1", "run_keep", model_to_keep, b.id, "level1")
    assert not del_speed_file.exists()
    assert keep_speed_file.exists()

    assert not (records_runs / "host1__run_del.json").exists()
    assert (records_runs / "host1__run_keep.json").exists()


def test_clear_level_single_test(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    db.conn.execute("INSERT INTO hosts (id, label, created_at) VALUES ('host1', 'Host 1', '2026-01-01 00:00:00')")
    answers_root = tmp_path / "workspace"
    raw_answers_dir = answers_root / "raw_answers"
    records_dir = answers_root / "records"
    records_results = records_dir / "results"
    records_speeds = records_dir / "speeds"
    records_results.mkdir(parents=True)
    records_speeds.mkdir(parents=True)

    result_store = ResultStore(db, answers_root=answers_root, raw_answers_dir=raw_answers_dir)
    speed_store = SpeedResultStore(db, records_speeds_dir=records_speeds)
    run_store = RunStore(db)

    b = REGISTRY[0]
    model = "test-model"

    run = Run(id="run1", host_id="host1", model_key=model)
    run_store.save(run)

    # Seed level 1 and level 2
    r1 = StoredResult(
        model=model,
        benchmark=b.id,
        level="level1",
        tested_at="2026-10-04 10:00:00",
        evaluation=BenchTestResult(passed=5, total=5, failures=[]),
    )
    r2 = StoredResult(
        model=model,
        benchmark=b.id,
        level="level2",
        tested_at="2026-10-04 10:05:00",
        evaluation=BenchTestResult(passed=5, total=5, failures=[]),
    )
    result_store.save(b, model, "level1", r1, run_id="run1")
    result_store.save(b, model, "level2", r2, run_id="run1")

    # Delete only level 1
    result_store.clear(b, model, "level1")
    speed_store.clear_level(model, b.id, "level1")

    assert not result_store.has_result(b, model, "level1")
    assert result_store.has_result(b, model, "level2")


def test_clear_all_wipes_all(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    db.conn.execute("INSERT INTO hosts (id, label, created_at) VALUES ('h1', 'Host 1', '2026-01-01 00:00:00')")
    answers_root = tmp_path / "workspace"
    raw_answers_dir = answers_root / "raw_answers"
    records_dir = answers_root / "records"
    records_results = records_dir / "results"
    records_speeds = records_dir / "speeds"
    records_runs = records_dir / "runs"
    records_results.mkdir(parents=True)
    records_speeds.mkdir(parents=True)
    records_runs.mkdir(parents=True)

    result_store = ResultStore(db, answers_root=answers_root, raw_answers_dir=raw_answers_dir)
    speed_store = SpeedResultStore(db, records_speeds_dir=records_speeds)
    run_store = RunStore(db)

    run = Run(id="r1", host_id="h1", model_key="m1")
    run_store.save(run)
    (records_runs / "h1__r1.json").write_text("{}", encoding="utf-8")

    b = REGISTRY[0]
    r = StoredResult(
        model="m1",
        benchmark=b.id,
        level="level1",
        tested_at="2026-10-04 10:00:00",
        evaluation=BenchTestResult(passed=1, total=1, failures=[]),
    )
    result_store.save(b, "m1", "level1", r, run_id="r1")

    result_store.clear_all(REGISTRY)
    speed_store.clear_all()
    run_store.clear_all(records_dir=records_dir)

    assert len(result_store.all_saved()) == 0
    assert len(speed_store.all_saved()) == 0
    assert len(run_store.list_runs()) == 0
    assert len(list(records_results.glob("*.json"))) == 0
    assert len(list(records_speeds.glob("*.json"))) == 0
    assert len(list(records_runs.glob("*.json"))) == 0
