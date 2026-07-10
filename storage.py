import json
import re
from pathlib import Path

from benchmarks.base import Benchmark, StoredResult


def safe_filename(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


class ResultStore:
    def __init__(self, answers_root: Path, raw_answers_dir: Path, results_dir: Path):
        self.answers_root = answers_root
        self.raw_answers_dir = raw_answers_dir
        self.results_dir = results_dir

    def ensure_dirs(self, benchmarks: list[Benchmark]) -> None:
        self.raw_answers_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        for benchmark in benchmarks:
            (self.answers_root / benchmark.answers_dir_name).mkdir(parents=True, exist_ok=True)

    def paths_for(self, benchmark: Benchmark, model_key: str, level_id: str) -> tuple[Path, Path, Path]:
        key = safe_filename(model_key)
        answers_dir = self.answers_root / benchmark.answers_dir_name
        answer_path = answers_dir / f"{key}_{benchmark.id}_{level_id}.{benchmark.file_ext}"
        raw_path = self.raw_answers_dir / f"{key}_{benchmark.id}_{level_id}.txt"
        result_path = self.results_dir / f"{key}_{benchmark.id}_{level_id}.json"
        return answer_path, raw_path, result_path

    def load(self, benchmark: Benchmark, model_key: str, level_id: str) -> StoredResult | None:
        _, _, result_path = self.paths_for(benchmark, model_key, level_id)
        return self._load_path(result_path)

    def _load_path(self, result_path: Path) -> StoredResult | None:
        if not result_path.exists():
            return None
        data = json.loads(result_path.read_text(encoding="utf-8"))
        return StoredResult.from_dict(data)

    def save(self, benchmark: Benchmark, model_key: str, level_id: str, result: StoredResult) -> None:
        _, _, result_path = self.paths_for(benchmark, model_key, level_id)
        result_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self, benchmark: Benchmark, model_key: str, level_id: str) -> None:
        for path in self.paths_for(benchmark, model_key, level_id):
            path.unlink(missing_ok=True)

    def all_saved(self) -> list[StoredResult]:
        results = []
        for path in sorted(self.results_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                results.append(StoredResult.from_dict(data))
            except (json.JSONDecodeError, OSError, KeyError):
                continue
        return results
