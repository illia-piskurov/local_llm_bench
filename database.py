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

            CREATE TABLE IF NOT EXISTS results (
                model TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                level TEXT NOT NULL,
                tested_at TEXT NOT NULL,
                passed INTEGER,
                total INTEGER,
                failures TEXT,
                manual_score INTEGER,
                comment TEXT,
                PRIMARY KEY (model, benchmark, level)
            );

            CREATE TABLE IF NOT EXISTS speed_results (
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
                PRIMARY KEY (host_id, model, benchmark, level)
            );
        """)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
