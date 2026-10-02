import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS hosts (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                host_id TEXT NOT NULL REFERENCES hosts(id),
                model_key TEXT NOT NULL,
                model_name TEXT,
                quantization TEXT,
                backend TEXT,
                generation_params TEXT,
                suite_version TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'completed'
            );
        """)

        # Check if legacy results needs migration to include run_id
        has_results = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='results'"
        ).fetchone()
        if has_results:
            cols = [c[1] for c in self.conn.execute("PRAGMA table_info(results)").fetchall()]
            if "run_id" not in cols:
                self._migrate_legacy_schema()

        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS results (
                run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                model TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                level TEXT NOT NULL,
                tested_at TEXT NOT NULL,
                passed INTEGER,
                total INTEGER,
                failures TEXT,
                manual_score INTEGER,
                comment TEXT,
                PRIMARY KEY (run_id, benchmark, level)
            );

            CREATE TABLE IF NOT EXISTS speed_results (
                run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                host_id TEXT NOT NULL REFERENCES hosts(id),
                model TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                level TEXT NOT NULL,
                tested_at TEXT NOT NULL,
                input_tokens INTEGER,
                total_output_tokens INTEGER,
                reasoning_output_tokens INTEGER,
                tokens_per_second REAL,
                time_to_first_token_seconds REAL,
                model_load_time_seconds REAL,
                PRIMARY KEY (run_id, benchmark, level)
            );

            CREATE INDEX IF NOT EXISTS idx_results_model ON results(model);
            CREATE INDEX IF NOT EXISTS idx_speed_model ON speed_results(model);
            CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model_key);
            CREATE INDEX IF NOT EXISTS idx_runs_host ON runs(host_id);
            CREATE INDEX IF NOT EXISTS idx_results_run ON results(run_id);
            CREATE INDEX IF NOT EXISTS idx_speed_run ON speed_results(run_id);
        """)
        self.conn.commit()

    def _migrate_legacy_schema(self) -> None:
        import re

        self.conn.execute("PRAGMA foreign_keys=OFF")

        def safe_slug(key: str) -> str:
            return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)

        def detect_quant(model_key: str) -> str | None:
            match = re.search(
                r"(?i)\b(q[0-9]_[a-z0-9_]+|qat|awq|gptq|exl2|fp16|bf16|int8|int4|f32|fp32)\b",
                model_key,
            )
            if match:
                return match.group(1).upper()
            if "-qat" in model_key.lower():
                return "QAT"
            return None

        self.conn.execute("DROP TABLE IF EXISTS _new_results")
        self.conn.execute("DROP TABLE IF EXISTS _new_speed_results")

        self.conn.execute("""
            CREATE TABLE _new_results (
                run_id TEXT NOT NULL,
                model TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                level TEXT NOT NULL,
                tested_at TEXT NOT NULL,
                passed INTEGER,
                total INTEGER,
                failures TEXT,
                manual_score INTEGER,
                comment TEXT,
                PRIMARY KEY (run_id, benchmark, level)
            )
        """)
        self.conn.execute("""
            CREATE TABLE _new_speed_results (
                run_id TEXT NOT NULL,
                host_id TEXT NOT NULL,
                model TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                level TEXT NOT NULL,
                tested_at TEXT NOT NULL,
                input_tokens INTEGER,
                total_output_tokens INTEGER,
                reasoning_output_tokens INTEGER,
                tokens_per_second REAL,
                time_to_first_token_seconds REAL,
                model_load_time_seconds REAL,
                PRIMARY KEY (run_id, benchmark, level)
            )
        """)

        speeds_by_test = {}
        for s in self.conn.execute("SELECT * FROM speed_results").fetchall():
            key = (s["model"], s["benchmark"], s["level"])
            speeds_by_test.setdefault(key, []).append(s)

        model_hosts = {}
        for s in self.conn.execute("SELECT DISTINCT model, host_id FROM speed_results").fetchall():
            model_hosts.setdefault(s["model"], []).append(s["host_id"])

        host_row = self.conn.execute("SELECT id FROM hosts LIMIT 1").fetchone()
        default_host = host_row[0] if host_row else "default"

        runs_to_insert = {}
        for model, hosts in model_hosts.items():
            for hid in hosts:
                rid = f"legacy_{hid}_{safe_slug(model)}"
                runs_to_insert[rid] = {
                    "id": rid,
                    "host_id": hid,
                    "model_key": model,
                    "model_name": model,
                    "quantization": detect_quant(model),
                    "backend": "LM Studio",
                    "generation_params": "{}",
                    "suite_version": "legacy",
                    "started_at": "2026-01-01 00:00:00",
                    "completed_at": "2026-01-01 00:00:00",
                    "status": "completed",
                }

        results = self.conn.execute("SELECT * FROM results").fetchall()
        for r in results:
            key = (r["model"], r["benchmark"], r["level"])
            m_slug = safe_slug(r["model"])
            if key in speeds_by_test:
                for s in speeds_by_test[key]:
                    hid = s["host_id"]
                    rid = f"legacy_{hid}_{m_slug}"
                    self.conn.execute(
                        """
                        INSERT OR REPLACE INTO _new_results
                        (run_id, model, benchmark, level, tested_at, passed, total, failures, manual_score, comment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            rid,
                            r["model"],
                            r["benchmark"],
                            r["level"],
                            r["tested_at"],
                            r["passed"],
                            r["total"],
                            r["failures"],
                            r["manual_score"],
                            r["comment"],
                        ),
                    )
            else:
                hosts = model_hosts.get(r["model"], [default_host])
                hid = hosts[0]
                rid = f"legacy_{hid}_{m_slug}"
                if rid not in runs_to_insert:
                    runs_to_insert[rid] = {
                        "id": rid,
                        "host_id": hid,
                        "model_key": r["model"],
                        "model_name": r["model"],
                        "quantization": detect_quant(r["model"]),
                        "backend": "LM Studio",
                        "generation_params": "{}",
                        "suite_version": "legacy",
                        "started_at": r["tested_at"],
                        "completed_at": r["tested_at"],
                        "status": "completed",
                    }
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO _new_results
                    (run_id, model, benchmark, level, tested_at, passed, total, failures, manual_score, comment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        rid,
                        r["model"],
                        r["benchmark"],
                        r["level"],
                        r["tested_at"],
                        r["passed"],
                        r["total"],
                        r["failures"],
                        r["manual_score"],
                        r["comment"],
                    ),
                )

        for s in self.conn.execute("SELECT * FROM speed_results").fetchall():
            m_slug = safe_slug(s["model"])
            hid = s["host_id"]
            rid = f"legacy_{hid}_{m_slug}"
            self.conn.execute(
                """
                INSERT OR REPLACE INTO _new_speed_results
                (run_id, host_id, model, benchmark, level, tested_at,
                 input_tokens, total_output_tokens, reasoning_output_tokens,
                 tokens_per_second, time_to_first_token_seconds, model_load_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    rid,
                    hid,
                    s["model"],
                    s["benchmark"],
                    s["level"],
                    s["tested_at"],
                    s["input_tokens"],
                    s["total_output_tokens"],
                    s["reasoning_output_tokens"],
                    s["tokens_per_second"],
                    s["time_to_first_token_seconds"],
                    s["model_load_time_seconds"],
                ),
            )

        for r_dict in runs_to_insert.values():
            self.conn.execute(
                """
                INSERT OR REPLACE INTO runs
                (id, host_id, model_key, model_name, quantization, backend, generation_params, suite_version, started_at, completed_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    r_dict["id"],
                    r_dict["host_id"],
                    r_dict["model_key"],
                    r_dict["model_name"],
                    r_dict["quantization"],
                    r_dict["backend"],
                    r_dict["generation_params"],
                    r_dict["suite_version"],
                    r_dict["started_at"],
                    r_dict["completed_at"],
                    r_dict["status"],
                ),
            )

        self.conn.execute("DROP TABLE results")
        self.conn.execute("DROP TABLE speed_results")
        self.conn.execute("ALTER TABLE _new_results RENAME TO results")
        self.conn.execute("ALTER TABLE _new_speed_results RENAME TO speed_results")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
