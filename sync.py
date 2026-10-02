"""Синхронизация результатов тестов между SQLite (bench.db) и текстовыми JSON (records/).

Позволяет безопасно коммитить результаты в Git с разных устройств (Mac, ThinkPad и т.д.):
1. В Git коммитятся только текстовые файлы из records/ (нет бинарных конфликтов слияния SQLite).
2. При запуске main.py / отчётов bench.db автоматически подтягивает новые файлы из records/.
3. При сохранении любого теста данные пишутся одновременно в bench.db и records/.
4. Если bench.db отсутствует (первый запуск после git clone) — база мгновенно восстанавливается из records/.
"""

import json
import re
from pathlib import Path

from database import Database

ROOT = Path(__file__).parent
RECORDS_DIR = ROOT / "records"


def safe_filename(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def ensure_records_dirs(records_dir: Path = RECORDS_DIR) -> tuple[Path, Path, Path]:
    hosts_dir = records_dir / "hosts"
    results_dir = records_dir / "results"
    speeds_dir = records_dir / "speeds"
    hosts_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    speeds_dir.mkdir(parents=True, exist_ok=True)
    return hosts_dir, results_dir, speeds_dir


def export_all(db: Database, records_dir: Path = RECORDS_DIR) -> dict[str, int]:
    """Экспортирует все таблицы из SQLite в текстовые JSON-файлы в records/."""
    hosts_dir, results_dir, speeds_dir = ensure_records_dirs(records_dir)
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

    # 2. Results
    results_count = 0
    for row in conn.execute("SELECT * FROM results").fetchall():
        failures = json.loads(row["failures"]) if row["failures"] else []
        data = {
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
        m_slug = safe_filename(row["model"])
        path = results_dir / f"{m_slug}_{row['benchmark']}_{row['level']}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        results_count += 1

    # 3. Speeds
    speeds_count = 0
    for row in conn.execute("SELECT * FROM speed_results").fetchall():
        data = {
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
        m_slug = safe_filename(row["model"])
        path = speeds_dir / f"{row['host_id']}_{m_slug}_{row['benchmark']}_{row['level']}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        speeds_count += 1

    return {"hosts": hosts_count, "results": results_count, "speeds": speeds_count}


def import_all(db: Database, records_dir: Path = RECORDS_DIR) -> dict[str, int]:
    """Импортирует все текстовые JSON-файлы из records/ в SQLite базу."""
    if not records_dir.exists():
        return {"hosts": 0, "results": 0, "speeds": 0}

    hosts_dir, results_dir, speeds_dir = ensure_records_dirs(records_dir)
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
        except Exception:
            continue

    # 2. Results
    results_count = 0
    for path in results_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            failures_json = json.dumps(data.get("failures", []), ensure_ascii=False)
            conn.execute(
                """INSERT OR REPLACE INTO results
                   (model, benchmark, level, tested_at, passed, total, failures, manual_score, comment)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["model"],
                    data["benchmark"],
                    data["level"],
                    data["tested_at"],
                    data.get("passed", 0),
                    data.get("total", 0),
                    failures_json,
                    data.get("manual_score"),
                    data.get("comment", ""),
                ),
            )
            results_count += 1
        except Exception:
            continue

    # 3. Speeds
    speeds_count = 0
    for path in speeds_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            stats = data.get("stats", {})
            conn.execute(
                """INSERT OR REPLACE INTO speed_results
                   (host_id, model, benchmark, level, tested_at,
                    input_tokens, total_output_tokens, reasoning_output_tokens,
                    tokens_per_second, time_to_first_token_seconds, model_load_time_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["host_id"],
                    data["model"],
                    data["benchmark"],
                    data["level"],
                    data["tested_at"],
                    stats.get("input_tokens"),
                    stats.get("total_output_tokens"),
                    stats.get("reasoning_output_tokens"),
                    stats.get("tokens_per_second"),
                    stats.get("time_to_first_token_seconds"),
                    stats.get("model_load_time_seconds"),
                ),
            )
            speeds_count += 1
        except Exception:
            continue

    conn.commit()
    return {"hosts": hosts_count, "results": results_count, "speeds": speeds_count}


def sync_db_and_records(db: Database, records_dir: Path = RECORDS_DIR) -> dict[str, int]:
    """Синхронизирует records/ и bench.db: импортирует файлы и экспортирует недостающие."""
    # Сначала импортируем всё, что пришло из Git
    imp = import_all(db, records_dir)
    # Затем гарантируем, что локальные записи попали в records/
    exp = export_all(db, records_dir)
    return {"imported": imp, "exported": exp}
