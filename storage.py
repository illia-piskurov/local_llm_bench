import json
import re
from pathlib import Path

from benchmarks.base import Benchmark, GenerationStats, ManualResult, SpeedSample, StoredResult, TestResult
from database import Database


def safe_filename(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


class ResultStore:
    def __init__(self, db: Database, answers_root: Path, raw_answers_dir: Path):
        self.db = db
        self.answers_root = answers_root
        self.raw_answers_dir = raw_answers_dir

    def ensure_dirs(self, benchmarks: list[Benchmark]) -> None:
        self.raw_answers_dir.mkdir(exist_ok=True)
        for benchmark in benchmarks:
            (self.answers_root / benchmark.answers_dir_name).mkdir(parents=True, exist_ok=True)

    def paths_for(self, benchmark: Benchmark, model_key: str, level_id: str) -> tuple[Path, Path]:
        key = safe_filename(model_key)
        answers_dir = self.answers_root / benchmark.answers_dir_name
        answer_path = answers_dir / f"{key}_{benchmark.id}_{level_id}.{benchmark.file_ext}"
        raw_path = self.raw_answers_dir / f"{key}_{benchmark.id}_{level_id}.txt"
        return answer_path, raw_path

    def load(self, benchmark: Benchmark, model_key: str, level_id: str) -> StoredResult | None:
        row = self.db.conn.execute(
            "SELECT * FROM results WHERE model = ? AND benchmark = ? AND level = ?",
            (model_key, benchmark.id, level_id),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_result(row)

    def has_result(self, benchmark: Benchmark, model_key: str, level_id: str) -> bool:
        row = self.db.conn.execute(
            "SELECT 1 FROM results WHERE model = ? AND benchmark = ? AND level = ?",
            (model_key, benchmark.id, level_id),
        ).fetchone()
        return row is not None

    def save(self, benchmark: Benchmark, model_key: str, level_id: str, result: StoredResult) -> None:
        if isinstance(result.evaluation, ManualResult):
            self.db.conn.execute(
                """INSERT OR REPLACE INTO results
                   (model, benchmark, level, tested_at, manual_score, comment)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    result.model,
                    result.benchmark,
                    result.level,
                    result.tested_at,
                    result.evaluation.score,
                    result.evaluation.comment,
                ),
            )
        else:
            failures_json = json.dumps(result.evaluation.failures, ensure_ascii=False)
            self.db.conn.execute(
                """INSERT OR REPLACE INTO results
                   (model, benchmark, level, tested_at, passed, total, failures)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.model,
                    result.benchmark,
                    result.level,
                    result.tested_at,
                    result.evaluation.passed,
                    result.evaluation.total,
                    failures_json,
                ),
            )
        self.db.conn.commit()

        # Сохранение в records/ для версионирования в Git
        try:
            records_dir = self.answers_root / "records" / "results"
            records_dir.mkdir(parents=True, exist_ok=True)
            m_slug = safe_filename(result.model)
            path = records_dir / f"{m_slug}_{result.benchmark}_{result.level}.json"
            path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def clear(self, benchmark: Benchmark, model_key: str, level_id: str) -> int:
        count = 0
        cursor = self.db.conn.execute(
            "DELETE FROM results WHERE model = ? AND benchmark = ? AND level = ?",
            (model_key, benchmark.id, level_id),
        )
        count += cursor.rowcount
        self.db.conn.commit()

        answer_path, raw_path = self.paths_for(benchmark, model_key, level_id)
        for path in [answer_path, raw_path, raw_path.with_suffix(".api.json")]:
            if path.exists():
                path.unlink(missing_ok=True)
                count += 1
        return count

    def clear_model(self, model_key: str, benchmarks: list[Benchmark]) -> int:
        count = 0
        for benchmark in benchmarks:
            for level_id in benchmark.level_order:
                answer_path, raw_path = self.paths_for(benchmark, model_key, level_id)
                for path in [answer_path, raw_path, raw_path.with_suffix(".api.json")]:
                    if path.exists():
                        path.unlink(missing_ok=True)
                        count += 1
        cursor = self.db.conn.execute("DELETE FROM results WHERE model = ?", (model_key,))
        count += cursor.rowcount
        self.db.conn.commit()
        return count

    def clear_all(self, benchmarks: list[Benchmark]) -> int:
        count = 0
        for result in self.all_saved():
            for benchmark in benchmarks:
                if benchmark.id == result.benchmark:
                    answer_path, raw_path = self.paths_for(benchmark, result.model, result.level)
                    for path in [answer_path, raw_path, raw_path.with_suffix(".api.json")]:
                        if path.exists():
                            path.unlink(missing_ok=True)
                            count += 1
        cursor = self.db.conn.execute("DELETE FROM results")
        count += cursor.rowcount
        self.db.conn.commit()
        return count

    def all_saved(self) -> list[StoredResult]:
        rows = self.db.conn.execute("SELECT * FROM results ORDER BY model, benchmark, level").fetchall()
        return [self._row_to_result(row) for row in rows]

    @staticmethod
    def _row_to_result(row) -> StoredResult:
        if row["manual_score"] is not None:
            evaluation = ManualResult(score=row["manual_score"], comment=row["comment"] or "")
        else:
            failures = json.loads(row["failures"]) if row["failures"] else []
            evaluation = TestResult(passed=row["passed"], total=row["total"], failures=failures)
        return StoredResult(
            model=row["model"],
            benchmark=row["benchmark"],
            level=row["level"],
            tested_at=row["tested_at"],
            evaluation=evaluation,
        )


class SpeedResultStore:
    def __init__(self, db: Database):
        self.db = db

    def ensure_dir(self) -> None:
        pass  # SQLite — директория не нужна

    def save(self, sample: SpeedSample) -> None:
        stats = sample.stats
        self.db.conn.execute(
            """INSERT OR REPLACE INTO speed_results
               (host_id, model, benchmark, level, tested_at,
                input_tokens, total_output_tokens, reasoning_output_tokens,
                tokens_per_second, time_to_first_token_seconds, model_load_time_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sample.host_id,
                sample.model,
                sample.benchmark,
                sample.level,
                sample.tested_at,
                stats.input_tokens,
                stats.total_output_tokens,
                stats.reasoning_output_tokens,
                stats.tokens_per_second,
                stats.time_to_first_token_seconds,
                stats.model_load_time_seconds,
            ),
        )
        self.db.conn.commit()

        # Сохранение в records/ для версионирования в Git
        try:
            records_dir = Path(__file__).parent / "records" / "speeds"
            records_dir.mkdir(parents=True, exist_ok=True)
            m_slug = safe_filename(sample.model)
            path = records_dir / f"{sample.host_id}_{m_slug}_{sample.benchmark}_{sample.level}.json"
            path.write_text(json.dumps(sample.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def clear_level(self, model_key: str, benchmark_id: str, level_id: str) -> int:
        cursor = self.db.conn.execute(
            "DELETE FROM speed_results WHERE model = ? AND benchmark = ? AND level = ?",
            (model_key, benchmark_id, level_id),
        )
        self.db.conn.commit()
        return cursor.rowcount

    def clear_model(self, model_key: str) -> int:
        cursor = self.db.conn.execute("DELETE FROM speed_results WHERE model = ?", (model_key,))
        self.db.conn.commit()
        return cursor.rowcount

    def clear_all(self) -> int:
        cursor = self.db.conn.execute("DELETE FROM speed_results")
        self.db.conn.commit()
        return cursor.rowcount

    def all_saved(self) -> list[SpeedSample]:
        rows = self.db.conn.execute("""
            SELECT sr.*, h.label AS host_label
            FROM speed_results sr
            LEFT JOIN hosts h ON sr.host_id = h.id
            ORDER BY sr.model, sr.benchmark, sr.level
        """).fetchall()
        return [self._row_to_sample(row) for row in rows]

    @staticmethod
    def _row_to_sample(row) -> SpeedSample:
        return SpeedSample(
            host_id=row["host_id"],
            host_label=row["host_label"] or "",
            model=row["model"],
            benchmark=row["benchmark"],
            level=row["level"],
            tested_at=row["tested_at"],
            stats=GenerationStats(
                input_tokens=row["input_tokens"],
                total_output_tokens=row["total_output_tokens"],
                reasoning_output_tokens=row["reasoning_output_tokens"],
                tokens_per_second=row["tokens_per_second"],
                time_to_first_token_seconds=row["time_to_first_token_seconds"],
                model_load_time_seconds=row["model_load_time_seconds"],
            ),
        )
