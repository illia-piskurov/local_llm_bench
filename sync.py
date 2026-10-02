"""Synchronization of benchmark results between SQLite (bench.db) and JSON records (records/).

Enables conflict-free Git commits from multiple devices (Mac, ThinkPad, Linux workstation):
1. Git tracks only text JSON files under records/ (eliminates SQLite binary merge conflicts).
2. On runner launch or report generation, bench.db automatically imports new files from records/.
3. Test runs persist to both bench.db and records/ concurrently.
4. If bench.db is absent (e.g. after fresh git clone), it is rebuilt from records/ instantly.
"""

import json
import logging
import re
from pathlib import Path

from database import Database
from storage import result_record_name, speed_record_name

logger = logging.getLogger(__name__)

LEGACY_RUN_PREFIX = "legacy_"

ROOT = Path(__file__).parent
RECORDS_DIR = ROOT / "records"


def safe_filename(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def ensure_records_dirs(records_dir: Path = RECORDS_DIR) -> tuple[Path, Path, Path, Path]:
    hosts_dir = records_dir / "hosts"
    runs_dir = records_dir / "runs"
    results_dir = records_dir / "results"
    speeds_dir = records_dir / "speeds"
    hosts_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    speeds_dir.mkdir(parents=True, exist_ok=True)
    return hosts_dir, runs_dir, results_dir, speeds_dir


def export_all(db: Database, records_dir: Path = RECORDS_DIR) -> dict[str, int]:
    """Exports all tables from SQLite to JSON files in records/."""
    hosts_dir, runs_dir, results_dir, speeds_dir = ensure_records_dirs(records_dir)
    conn = db.conn

    # 1. Hosts
    hosts_count = 0
    for row in conn.execute("SELECT id, label, created_at FROM hosts").fetchall():
        data = {
            "id": row["id"],
            "label": row["label"],
            "created_at": row["created_at"],
        }
        path = hosts_dir / f"{row['id']}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        hosts_count += 1

    # 2. Runs (with embedded results and speeds)
    runs_count = 0
    for row in conn.execute("SELECT * FROM runs").fetchall():
        run_id = row["id"]
        results_in_run = []
        for r in conn.execute("SELECT * FROM results WHERE run_id = ?", (run_id,)).fetchall():
            failures = json.loads(r["failures"]) if r["failures"] else []
            results_in_run.append(
                {
                    "benchmark": r["benchmark"],
                    "level": r["level"],
                    "tested_at": r["tested_at"],
                    "passed": r["passed"],
                    "total": r["total"],
                    "failures": failures,
                    "manual_score": r["manual_score"],
                    "comment": r["comment"] or "",
                }
            )

        speeds_in_run = []
        for s in conn.execute("SELECT * FROM speed_results WHERE run_id = ?", (run_id,)).fetchall():
            speeds_in_run.append(
                {
                    "benchmark": s["benchmark"],
                    "level": s["level"],
                    "tested_at": s["tested_at"],
                    "stats": {
                        "input_tokens": s["input_tokens"],
                        "total_output_tokens": s["total_output_tokens"],
                        "reasoning_output_tokens": s["reasoning_output_tokens"],
                        "tokens_per_second": s["tokens_per_second"],
                        "time_to_first_token_seconds": s["time_to_first_token_seconds"],
                        "model_load_time_seconds": s["model_load_time_seconds"],
                    },
                }
            )

        params = json.loads(row["generation_params"]) if row["generation_params"] else {}
        run_data = {
            "id": row["id"],
            "host_id": row["host_id"],
            "model_key": row["model_key"],
            "model_name": row["model_name"] or row["model_key"],
            "quantization": row["quantization"],
            "backend": row["backend"],
            "generation_params": params,
            "suite_version": row["suite_version"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "status": row["status"],
            "results": results_in_run,
            "speeds": speeds_in_run,
        }
        path = runs_dir / f"{row['id']}.json"
        path.write_text(json.dumps(run_data, ensure_ascii=False, indent=2), encoding="utf-8")
        runs_count += 1

    # 3. Per-result snapshots: results/ (one file per host + run + test, so machines never share a file)
    results_count = 0
    run_hosts = {r["id"]: r["host_id"] for r in conn.execute("SELECT id, host_id FROM runs").fetchall()}
    for row in conn.execute("SELECT * FROM results ORDER BY tested_at ASC").fetchall():
        if row["run_id"].startswith(LEGACY_RUN_PREFIX):
            continue  # pre-runs data lives only in runs/; a snapshot would just duplicate it
        failures = json.loads(row["failures"]) if row["failures"] else []
        host_id = run_hosts.get(row["run_id"], "unknown")
        data = {
            "run_id": row["run_id"],
            "host_id": host_id,
            "model": row["model"],
            "benchmark": row["benchmark"],
            "level": row["level"],
            "tested_at": row["tested_at"],
            "passed": row["passed"],
            "total": row["total"],
            "failures": failures,
            "manual_score": row["manual_score"],
            "comment": row["comment"] or "",
        }
        path = results_dir / result_record_name(host_id, row["run_id"], row["model"], row["benchmark"], row["level"])
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        results_count += 1

    # 4. Per-sample snapshots: speeds/
    speeds_count = 0
    for row in conn.execute("SELECT * FROM speed_results ORDER BY tested_at ASC").fetchall():
        if row["run_id"].startswith(LEGACY_RUN_PREFIX):
            continue
        data = {
            "run_id": row["run_id"],
            "host_id": row["host_id"],
            "model": row["model"],
            "benchmark": row["benchmark"],
            "level": row["level"],
            "tested_at": row["tested_at"],
            "stats": {
                "input_tokens": row["input_tokens"],
                "total_output_tokens": row["total_output_tokens"],
                "reasoning_output_tokens": row["reasoning_output_tokens"],
                "tokens_per_second": row["tokens_per_second"],
                "time_to_first_token_seconds": row["time_to_first_token_seconds"],
                "model_load_time_seconds": row["model_load_time_seconds"],
            },
        }
        path = speeds_dir / speed_record_name(
            row["host_id"], row["run_id"], row["model"], row["benchmark"], row["level"]
        )
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        speeds_count += 1

    return {"hosts": hosts_count, "runs": runs_count, "results": results_count, "speeds": speeds_count}


def import_all(db: Database, records_dir: Path = RECORDS_DIR) -> dict[str, int]:
    """Imports JSON files from records/ into SQLite database."""
    if not records_dir.exists():
        return {"hosts": 0, "runs": 0, "results": 0, "speeds": 0}

    hosts_dir, runs_dir, results_dir, speeds_dir = ensure_records_dirs(records_dir)
    conn = db.conn

    # 1. Hosts
    hosts_count = 0
    for path in hosts_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR REPLACE INTO hosts (id, label, created_at) VALUES (?, ?, ?)",
                (data["id"], data["label"], data["created_at"]),
            )
            hosts_count += 1
        except Exception as e:
            logger.warning("Failed to import host record from %s: %s", path, e)
            continue

    # 2. Runs (if available)
    runs_count = 0
    results_count = 0
    speeds_count = 0

    run_files = list(runs_dir.glob("*.json"))
    if run_files:
        for path in run_files:
            try:
                run_data = json.loads(path.read_text(encoding="utf-8"))
                run_id = run_data["id"]
                gen_params_str = (
                    json.dumps(run_data.get("generation_params", {}), ensure_ascii=False)
                    if isinstance(run_data.get("generation_params"), dict)
                    else str(run_data.get("generation_params", "{}"))
                )
                conn.execute(
                    """INSERT OR REPLACE INTO runs
                       (id, host_id, model_key, model_name, quantization, backend,
                        generation_params, suite_version, started_at, completed_at, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        run_data["host_id"],
                        run_data["model_key"],
                        run_data.get("model_name") or run_data["model_key"],
                        run_data.get("quantization"),
                        run_data.get("backend"),
                        gen_params_str,
                        run_data.get("suite_version"),
                        run_data.get("started_at", ""),
                        run_data.get("completed_at"),
                        run_data.get("status", "completed"),
                    ),
                )
                runs_count += 1

                for r in run_data.get("results", []):
                    failures_json = json.dumps(r.get("failures", []), ensure_ascii=False)
                    conn.execute(
                        """INSERT OR REPLACE INTO results
                           (run_id, model, benchmark, level, tested_at, passed, total, failures, manual_score, comment)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            run_id,
                            run_data["model_key"],
                            r["benchmark"],
                            r["level"],
                            r["tested_at"],
                            r.get("passed", 0),
                            r.get("total", 0),
                            failures_json,
                            r.get("manual_score"),
                            r.get("comment", ""),
                        ),
                    )
                    results_count += 1

                for s in run_data.get("speeds", []):
                    stats = s.get("stats", {})
                    conn.execute(
                        """INSERT OR REPLACE INTO speed_results
                           (run_id, host_id, model, benchmark, level, tested_at,
                            input_tokens, total_output_tokens, reasoning_output_tokens,
                            tokens_per_second, time_to_first_token_seconds, model_load_time_seconds)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            run_id,
                            run_data["host_id"],
                            run_data["model_key"],
                            s["benchmark"],
                            s["level"],
                            s["tested_at"],
                            stats.get("input_tokens"),
                            stats.get("total_output_tokens"),
                            stats.get("reasoning_output_tokens"),
                            stats.get("tokens_per_second"),
                            stats.get("time_to_first_token_seconds"),
                            stats.get("model_load_time_seconds"),
                        ),
                    )
                    speeds_count += 1
            except Exception as e:
                logger.warning("Failed to import run record from %s: %s", path, e)
                continue

    # 3. Fallback: If no runs existed, import legacy results and speeds
    if runs_count == 0:
        # Build legacy runs for legacy files
        default_host_row = conn.execute("SELECT id FROM hosts LIMIT 1").fetchone()
        default_host = default_host_row[0] if default_host_row else "default"

        # Speed files
        speed_records = []
        for path in speeds_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                speed_records.append(data)
            except Exception as e:
                logger.warning("Failed to read speed record from %s: %s", path, e)
                continue

        result_records = []
        for path in results_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                result_records.append(data)
            except Exception as e:
                logger.warning("Failed to read result record from %s: %s", path, e)
                continue

        # Create runs for each (model, host_id)
        known_hosts = {row[0] for row in conn.execute("SELECT id FROM hosts").fetchall()}

        def ensure_stub_run(rid: str, hid: str | None, model: str, ts: str) -> None:
            # INSERT OR IGNORE: never replace an existing run (REPLACE would cascade-delete its results).
            host = hid if hid in known_hosts else default_host
            conn.execute(
                """INSERT OR IGNORE INTO runs
                   (id, host_id, model_key, model_name, started_at, completed_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (rid, host, model, model, ts, ts, "completed"),
            )

        legacy_runs = {}
        for s in speed_records:
            hid = s["host_id"]
            m = s["model"]
            if s.get("run_id"):
                ensure_stub_run(s["run_id"], hid, m, s["tested_at"])
                continue
            rid = f"legacy_{hid}_{safe_filename(m)}"
            if rid not in legacy_runs:
                legacy_runs[rid] = (hid, m)
                conn.execute(
                    """INSERT OR REPLACE INTO runs
                       (id, host_id, model_key, model_name, started_at, completed_at, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (rid, hid, m, m, s["tested_at"], s["tested_at"], "completed"),
                )
                runs_count += 1

        for r in result_records:
            m = r["model"]
            if r.get("run_id"):
                # New-format snapshot: it names its own run, so attribute it exactly.
                ensure_stub_run(r["run_id"], r.get("host_id"), m, r["tested_at"])
                matching_rids = [r["run_id"]]
            else:
                # Old-format snapshot without run info: match by model.
                matching_rids = [rid for rid, (hid, m_key) in legacy_runs.items() if m_key == m]
            if not matching_rids:
                rid = f"legacy_{default_host}_{safe_filename(m)}"
                legacy_runs[rid] = (default_host, m)
                conn.execute(
                    """INSERT OR REPLACE INTO runs
                       (id, host_id, model_key, model_name, started_at, completed_at, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (rid, default_host, m, m, r["tested_at"], r["tested_at"], "completed"),
                )
                runs_count += 1
                matching_rids = [rid]

            failures_json = json.dumps(r.get("failures", []), ensure_ascii=False)
            for rid in matching_rids:
                conn.execute(
                    """INSERT OR REPLACE INTO results
                       (run_id, model, benchmark, level, tested_at, passed, total, failures, manual_score, comment)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        rid,
                        m,
                        r["benchmark"],
                        r["level"],
                        r["tested_at"],
                        r.get("passed", 0),
                        r.get("total", 0),
                        failures_json,
                        r.get("manual_score"),
                        r.get("comment", ""),
                    ),
                )
                results_count += 1

        for s in speed_records:
            hid = s["host_id"]
            m = s["model"]
            rid = s.get("run_id") or f"legacy_{hid}_{safe_filename(m)}"
            stats = s.get("stats", {})
            conn.execute(
                """INSERT OR REPLACE INTO speed_results
                   (run_id, host_id, model, benchmark, level, tested_at,
                    input_tokens, total_output_tokens, reasoning_output_tokens,
                    tokens_per_second, time_to_first_token_seconds, model_load_time_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rid,
                    hid,
                    m,
                    s["benchmark"],
                    s["level"],
                    s["tested_at"],
                    stats.get("input_tokens"),
                    stats.get("total_output_tokens"),
                    stats.get("reasoning_output_tokens"),
                    stats.get("tokens_per_second"),
                    stats.get("time_to_first_token_seconds"),
                    stats.get("model_load_time_seconds"),
                ),
            )
            speeds_count += 1

    conn.commit()
    return {"hosts": hosts_count, "runs": runs_count, "results": results_count, "speeds": speeds_count}


def sync_db_and_records(db: Database, records_dir: Path = RECORDS_DIR) -> dict[str, dict[str, int]]:
    """Synchronizes records/ and bench.db: imports files and exports missing records."""
    # First import incoming changes from Git records
    imp = import_all(db, records_dir)
    # Then ensure local additions are pushed to records/
    exp = export_all(db, records_dir)
    return {"imported": imp, "exported": exp}
