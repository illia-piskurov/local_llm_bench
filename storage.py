import hashlib
import json
import logging
import re
import secrets
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from benchmarks.base import Benchmark, GenerationStats, ManualResult, SpeedSample, StoredResult, TestResult
from database import Database

logger = logging.getLogger(__name__)


def safe_filename(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def detect_quantization(model_key: str) -> str | None:
    match = re.search(
        r"(?i)\b(q[0-9]_[a-z0-9_]+|qat|awq|gptq|exl2|fp16|bf16|int8|int4|f32|fp32)\b",
        model_key,
    )
    if match:
        return match.group(1).upper()
    if "-qat" in model_key.lower():
        return "QAT"
    return None


def detect_backend(url: str | None = None) -> str:
    try:
        from lmstudio import get_base_url

        u = (url or get_base_url()).lower()
    except Exception:
        u = (url or "").lower()

    if ":11434" in u or "ollama" in u:
        try:
            import requests

            r = requests.get(f"{url or 'http://localhost:11434'}/api/version", timeout=1)
            if r.status_code == 200 and "version" in r.json():
                return f"Ollama v{r.json()['version']}"
        except Exception:
            pass
        return "Ollama"

    if ":8080" in u:
        return "llama.cpp"

    if ":8000" in u or "vllm" in u:
        try:
            import requests

            r = requests.get(f"{url or 'http://localhost:8000'}/version", timeout=1)
            if r.status_code == 200 and "version" in r.json():
                return f"vLLM v{r.json()['version']}"
        except Exception:
            pass
        return "vLLM"

    # LM Studio default
    try:
        res = subprocess.run(
            ["lms", "--version"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            ver = res.stdout.strip()
            match = re.search(r"([a-f0-9]{7,})", ver)
            if match:
                return f"LM Studio ({match.group(1)[:7]})"
            return f"LM Studio ({ver[:20]})"
    except Exception:
        pass
    return "LM Studio"


def compute_suite_hash() -> str:
    hasher = hashlib.sha256()
    benchmarks_dir = Path(__file__).parent / "benchmarks"
    if benchmarks_dir.exists():
        for py_file in sorted(benchmarks_dir.glob("*.py")):
            hasher.update(py_file.name.encode("utf-8"))
            hasher.update(py_file.read_bytes())
    return hasher.hexdigest()[:12]


def get_suite_version() -> str:
    git_sha = "1.0.0"
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            git_sha = res.stdout.strip()
    except Exception:
        pass
    suite_h = compute_suite_hash()
    return f"{git_sha} ({suite_h})"


@dataclass
class Run:
    id: str
    host_id: str
    model_key: str
    model_name: str | None = None
    quantization: str | None = None
    backend: str | None = None
    generation_params: dict = field(default_factory=dict)
    suite_version: str | None = None
    started_at: str = ""
    completed_at: str | None = None
    status: str = "in_progress"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "host_id": self.host_id,
            "model_key": self.model_key,
            "model_name": self.model_name or self.model_key,
            "quantization": self.quantization,
            "backend": self.backend,
            "generation_params": self.generation_params,
            "suite_version": self.suite_version,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Run":
        params = d.get("generation_params")
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                params = {}
        return cls(
            id=d["id"],
            host_id=d["host_id"],
            model_key=d["model_key"],
            model_name=d.get("model_name"),
            quantization=d.get("quantization"),
            backend=d.get("backend"),
            generation_params=params or {},
            suite_version=d.get("suite_version"),
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at"),
            status=d.get("status", "completed"),
        )

    @classmethod
    def create(
        cls,
        host_id: str,
        model_key: str,
        model_name: str | None = None,
        quantization: str | None = None,
        backend: str | None = None,
        generation_params: dict | None = None,
        suite_version: str | None = None,
    ) -> "Run":
        now = datetime.now()
        ts = now.strftime("%Y%m%d_%H%M%S")
        rand = secrets.token_hex(3)
        run_id = f"run_{ts}_{rand}"
        return cls(
            id=run_id,
            host_id=host_id,
            model_key=model_key,
            model_name=model_name or model_key,
            quantization=quantization or detect_quantization(model_key),
            backend=backend or detect_backend(),
            generation_params=generation_params or {},
            suite_version=suite_version or get_suite_version(),
            started_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            status="in_progress",
        )


class RunStore:
    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        host_id: str,
        model_key: str,
        model_name: str | None = None,
        quantization: str | None = None,
        backend: str | None = None,
        generation_params: dict | None = None,
        suite_version: str | None = None,
    ) -> Run:
        run = Run.create(
            host_id=host_id,
            model_key=model_key,
            model_name=model_name,
            quantization=quantization,
            backend=backend,
            generation_params=generation_params,
            suite_version=suite_version,
        )
        self.save(run)
        return run

    def save(self, run: Run) -> None:
        params_json = json.dumps(run.generation_params, ensure_ascii=False)
        self.db.conn.execute(
            """INSERT OR REPLACE INTO runs
               (id, host_id, model_key, model_name, quantization, backend,
                generation_params, suite_version, started_at, completed_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.id,
                run.host_id,
                run.model_key,
                run.model_name or run.model_key,
                run.quantization,
                run.backend,
                params_json,
                run.suite_version,
                run.started_at,
                run.completed_at,
                run.status,
            ),
        )
        self.db.conn.commit()

    def get(self, run_id: str) -> Run | None:
        row = self.db.conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return Run.from_dict(dict(row)) if row else None

    def get_active_run_id(self, model_key: str, host_id: str | None = None) -> str | None:
        query = "SELECT id FROM runs WHERE model_key = ? AND status = 'in_progress'"
        params = [model_key]
        if host_id:
            query += " AND host_id = ?"
            params.append(host_id)
        query += " ORDER BY started_at DESC LIMIT 1"
        row = self.db.conn.execute(query, params).fetchone()
        return row[0] if row else None

    def get_latest(self, model_key: str, host_id: str | None = None) -> Run | None:
        if host_id:
            row = self.db.conn.execute(
                "SELECT * FROM runs WHERE model_key = ? AND host_id = ? ORDER BY started_at DESC LIMIT 1",
                (model_key, host_id),
            ).fetchone()
        else:
            row = self.db.conn.execute(
                "SELECT * FROM runs WHERE model_key = ? ORDER BY started_at DESC LIMIT 1",
                (model_key,),
            ).fetchone()
        return Run.from_dict(dict(row)) if row else None

    def list_runs(self, model_key: str | None = None, host_id: str | None = None, limit: int = 100) -> list[Run]:
        query = "SELECT * FROM runs"
        conditions = []
        params: list[str] = []
        if model_key:
            conditions.append("model_key = ?")
            params.append(model_key)
        if host_id:
            conditions.append("host_id = ?")
            params.append(host_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(str(limit))
        rows = self.db.conn.execute(query, params).fetchall()
        return [Run.from_dict(dict(r)) for r in rows]

    def complete(self, run_id: str, status: str = "completed") -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.conn.execute(
            "UPDATE runs SET completed_at = ?, status = ? WHERE id = ?",
            (now, status, run_id),
        )
        self.db.conn.commit()

    def delete(self, run_id: str) -> bool:
        cur = self.db.conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        self.db.conn.commit()
        return cur.rowcount > 0


class ResultStore:
    def __init__(self, db: Database, answers_root: Path, raw_answers_dir: Path):
        self.db = db
        self.answers_root = answers_root
        self.raw_answers_dir = raw_answers_dir
        self.run_store = RunStore(db)

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

    def load(
        self,
        benchmark: Benchmark,
        model_key: str,
        level_id: str,
        run_id: str | None = None,
    ) -> StoredResult | None:
        if run_id:
            row = self.db.conn.execute(
                "SELECT * FROM results WHERE run_id = ? AND benchmark = ? AND level = ?",
                (run_id, benchmark.id, level_id),
            ).fetchone()
        else:
            row = self.db.conn.execute(
                "SELECT * FROM results WHERE model = ? AND benchmark = ? AND level = ? ORDER BY tested_at DESC LIMIT 1",
                (model_key, benchmark.id, level_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_result(row)

    def has_result(
        self,
        benchmark: Benchmark,
        model_key: str,
        level_id: str,
        run_id: str | None = None,
    ) -> bool:
        if run_id:
            row = self.db.conn.execute(
                "SELECT 1 FROM results WHERE run_id = ? AND benchmark = ? AND level = ?",
                (run_id, benchmark.id, level_id),
            ).fetchone()
        else:
            row = self.db.conn.execute(
                "SELECT 1 FROM results WHERE model = ? AND benchmark = ? AND level = ?",
                (model_key, benchmark.id, level_id),
            ).fetchone()
        return row is not None

    def _ensure_active_run_id(self, model_key: str) -> str:
        active = self.run_store.get_active_run_id(model_key)
        if active:
            return active
        latest = self.run_store.get_latest(model_key)
        if latest:
            return latest.id
        # Fallback host
        host_row = self.db.conn.execute("SELECT id FROM hosts WHERE is_active = 1 LIMIT 1").fetchone()
        if not host_row:
            host_row = self.db.conn.execute("SELECT id FROM hosts LIMIT 1").fetchone()
        host_id = host_row[0] if host_row else "default"
        run = self.run_store.create(host_id=host_id, model_key=model_key)
        return run.id

    def save(
        self,
        benchmark: Benchmark,
        model_key: str,
        level_id: str,
        result: StoredResult,
        run_id: str | None = None,
    ) -> None:
        target_run_id = run_id or self._ensure_active_run_id(model_key)

        if isinstance(result.evaluation, ManualResult):
            self.db.conn.execute(
                """INSERT OR REPLACE INTO results
                   (run_id, model, benchmark, level, tested_at, manual_score, comment)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    target_run_id,
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
                   (run_id, model, benchmark, level, tested_at, passed, total, failures)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    target_run_id,
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

        # Persist legacy format to records/results for Git versioning compatibility
        try:
            records_dir = self.answers_root / "records" / "results"
            records_dir.mkdir(parents=True, exist_ok=True)
            m_slug = safe_filename(result.model)
            path = records_dir / f"{m_slug}_{result.benchmark}_{result.level}.json"
            path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to persist legacy result record to %s: %s", path, e)

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

    def all_saved(self, run_id: str | None = None) -> list[StoredResult]:
        if run_id:
            rows = self.db.conn.execute(
                "SELECT * FROM results WHERE run_id = ? ORDER BY model, benchmark, level",
                (run_id,),
            ).fetchall()
        else:
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
    def __init__(self, db: Database, records_speeds_dir: Path | None = None):
        self.db = db
        self.run_store = RunStore(db)
        self.records_speeds_dir = records_speeds_dir or (Path(__file__).parent / "records" / "speeds")

    def ensure_dir(self) -> None:
        pass

    def _ensure_active_run_id(self, model_key: str, host_id: str) -> str:
        active = self.run_store.get_active_run_id(model_key, host_id)
        if active:
            return active
        latest = self.run_store.get_latest(model_key, host_id)
        if latest:
            return latest.id
        run = self.run_store.create(host_id=host_id, model_key=model_key)
        return run.id

    def save(self, sample: SpeedSample, run_id: str | None = None) -> None:
        target_run_id = run_id or self._ensure_active_run_id(sample.model, sample.host_id)
        stats = sample.stats
        self.db.conn.execute(
            """INSERT OR REPLACE INTO speed_results
               (run_id, host_id, model, benchmark, level, tested_at,
                input_tokens, total_output_tokens, reasoning_output_tokens,
                tokens_per_second, time_to_first_token_seconds, model_load_time_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                target_run_id,
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

        # Persist to records/speeds for Git versioning compatibility
        try:
            records_dir = self.records_speeds_dir
            records_dir.mkdir(parents=True, exist_ok=True)
            m_slug = safe_filename(sample.model)
            path = records_dir / f"{sample.host_id}_{m_slug}_{sample.benchmark}_{sample.level}.json"
            path.write_text(json.dumps(sample.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to persist speed record to %s: %s", path, e)

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

    def all_saved(self, run_id: str | None = None) -> list[SpeedSample]:
        if run_id:
            rows = self.db.conn.execute(
                """
                SELECT sr.*, h.label AS host_label
                FROM speed_results sr
                LEFT JOIN hosts h ON sr.host_id = h.id
                WHERE sr.run_id = ?
                ORDER BY sr.model, sr.benchmark, sr.level
            """,
                (run_id,),
            ).fetchall()
        else:
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
