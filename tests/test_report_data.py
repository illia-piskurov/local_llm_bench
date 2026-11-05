import json

import pytest

import report_data
from database import Database
from storage import GENERATION_FAILED_PREFIX, INFRA_FAILURE_PREFIX, TRUNCATED_PREFIX, failure_kind


def _db_with_hosts(tmp_path, *hosts):
    db = Database(tmp_path / "t.db")
    for h in hosts:
        db.conn.execute("INSERT INTO hosts (id, label, created_at, is_active) VALUES (?, ?, '2026-01-01', 1)", (h, h))
    return db


def _add_run(db, run_id, host, model, backend="LM Studio (abc)", quant="Q4_K_M", params=None):
    db.conn.execute(
        "INSERT INTO runs (id, host_id, model_key, model_name, quantization, backend, generation_params, "
        "started_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, '2026-01-01', 'completed')",
        (run_id, host, model, model, quant, backend, json.dumps(params or {})),
    )


def _add_result(db, run_id, model, bench, level, passed, total, failures=None, tested_at="2026-01-01", tps=None):
    db.conn.execute(
        "INSERT INTO results (run_id, model, benchmark, level, tested_at, passed, total, failures) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (run_id, model, bench, level, tested_at, passed, total, json.dumps(failures or [])),
    )
    if tps is not None:
        host = db.conn.execute("SELECT host_id FROM runs WHERE id = ?", (run_id,)).fetchone()[0]
        db.conn.execute(
            "INSERT INTO speed_results (run_id, host_id, model, benchmark, level, tested_at, total_output_tokens, "
            "tokens_per_second) VALUES (?, ?, ?, ?, ?, ?, 100, ?)",
            (run_id, host, model, bench, level, tested_at, tps),
        )


def test_failure_kind_classification():
    assert failure_kind([]) is None
    assert failure_kind(["assertion failed"]) is None
    assert failure_kind([f"{TRUNCATED_PREFIX} cut"]) == "truncated"
    assert failure_kind([f"{GENERATION_FAILED_PREFIX} boom"]) == "failed"
    assert failure_kind(["Model generation failed or timed out"]) == "failed"
    assert failure_kind([f"{INFRA_FAILURE_PREFIX} server down"]) == "infra"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Ollama v0.40.14", "Ollama"),
        ("LM Studio (69d945a)", "LM Studio"),
        ("vLLM v0.5.1", "vLLM"),
        ("llama.cpp", "llama.cpp"),
        (None, "unknown"),
    ],
)
def test_backend_family(raw, expected):
    assert report_data.backend_family(raw) == expected


def test_truncated_generations_never_raise_the_score(tmp_path):
    db = _db_with_hosts(tmp_path, "h1")
    _add_run(db, "r1", "h1", "m")
    _add_result(db, "r1", "m", "vm", "level1", 10, 10)
    _add_result(db, "r1", "m", "vm", "level2", 0, 0, [f"{TRUNCATED_PREFIX} cut"])
    _add_result(db, "r1", "m", "vm", "level3", 0, 0, [f"{INFRA_FAILURE_PREFIX} down"])

    (entry,) = report_data.build_leaderboard(report_data.load_result_rows(db.conn))
    # truncated counts as 0%, the harness failure is excluded: (100 + 0) / 2
    assert entry["avg_pct"] == 50.0
    assert (entry["tests_count"], entry["truncated"], entry["infra"]) == (2, 1, 1)


def test_partial_coverage_models_are_not_ranked_above_full_ones(tmp_path, monkeypatch):
    monkeypatch.setattr(report_data, "TOTAL_TASKS", 4)
    db = _db_with_hosts(tmp_path, "h1")
    _add_run(db, "r1", "h1", "tiny-sample")
    _add_run(db, "r2", "h1", "full")
    _add_result(db, "r1", "tiny-sample", "vm", "level1", 5, 5)
    for i in range(1, 5):
        _add_result(db, "r2", "full", "vm", f"level{i}", 9, 10)

    board = report_data.build_leaderboard(report_data.load_result_rows(db.conn))
    assert [e["model"] for e in board] == ["full", "tiny-sample"]
    assert [e["ranked"] for e in board] == [True, False]


def test_host_filter_limits_scores_and_speed(tmp_path):
    db = _db_with_hosts(tmp_path, "fast", "slow")
    _add_run(db, "r1", "fast", "m")
    _add_run(db, "r2", "slow", "m")
    _add_result(db, "r1", "m", "vm", "level1", 10, 10, tested_at="2026-01-01", tps=80.0)
    _add_result(db, "r2", "m", "vm", "level2", 0, 10, tested_at="2026-01-02", tps=20.0)
    rows = report_data.load_result_rows(db.conn)

    (everything,) = report_data.build_leaderboard(rows)
    assert everything["avg_pct"] == 50.0
    assert everything["avg_speed"] == pytest.approx(50.0)  # median of the per-host speeds
    assert everything["speed_by_host"] == {"fast": pytest.approx(80.0), "slow": pytest.approx(20.0)}

    (only_fast,) = report_data.build_leaderboard(rows, host="fast")
    assert only_fast["avg_pct"] == 100.0
    assert only_fast["avg_speed"] == pytest.approx(80.0)
    assert report_data.build_leaderboard(rows, host="slow", backend="Ollama") == []


def test_matrix_keeps_backends_and_quantizations_apart_and_builds_speed_index(tmp_path):
    db = _db_with_hosts(tmp_path, "a", "b")
    for host, backend, quant, tps in [
        ("a", "LM Studio (x)", "Q4_K_M", 100.0),
        ("b", "LM Studio (x)", "Q4_K_M", 50.0),
        ("a", "Ollama v0.1", "Q4_K_M", 10.0),
    ]:
        run_id = f"{host}-{backend[:3]}"
        _add_run(db, run_id, host, "m", backend=backend, quant=quant)
        for i in range(report_data.MIN_SPEED_SAMPLES):
            _add_result(db, run_id, "m", "vm", f"level{i}", 1, 1, tps=tps)

    stats, matrix, hosts = report_data.load_hardware_matrix(db.conn)
    assert [v["backend"] for v in matrix] == ["LM Studio", "Ollama"]
    lm = matrix[0]
    assert lm["cells"]["a"]["tps"] == pytest.approx(100.0)
    assert lm["fastest_host"] == "a"
    assert matrix[1]["fastest_host"] is None  # a single host cannot be "fastest"
    # relative to the mean (75): a is 4/3, b is 2/3
    assert stats["a"]["index"] == pytest.approx(100 / 75)
    assert stats["b"]["index"] == pytest.approx(50 / 75)
    assert {h["id"] for h in hosts} == {"a", "b"}


def test_run_history_score_matches_leaderboard_formula_and_none_when_empty(tmp_path):
    db = _db_with_hosts(tmp_path, "h1")
    _add_run(db, "r1", "h1", "m")
    _add_run(db, "empty", "h1", "m2")
    _add_result(db, "r1", "m", "vm", "level1", 10, 10)
    _add_result(db, "r1", "m", "vm", "level2", 0, 0, [f"{TRUNCATED_PREFIX} cut"])

    runs, rows_html = report_data.load_runs_history(db.conn)
    by_id = {r["id"]: r for r in runs}
    assert by_id["r1"]["avg_score"] == 50.0
    assert by_id["r1"]["tests_truncated"] == 1
    assert by_id["empty"]["avg_score"] is None  # shown as "—", not a misleading 0%
    assert "✂ 1" in rows_html


def test_client_payload_carries_task_status(tmp_path):
    db = _db_with_hosts(tmp_path, "h1")
    _add_run(db, "r1", "h1", "m")
    _add_result(db, "r1", "m", "vm", "level1", 0, 0, [f"{TRUNCATED_PREFIX} cut"])

    payload = json.loads(report_data.load_report_data(db).client_json)
    assert payload["models"]["m"]["results"]["vm/level1"]["status"] == "truncated"
    assert payload["models"]["m"]["results"]["vm/level1"]["percent"] == 0.0
