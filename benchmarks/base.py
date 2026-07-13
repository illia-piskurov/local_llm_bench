import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Level:
    id: str
    name: str
    prompt: str
    requires: str | None = None


@dataclass
class TestResult:
    passed: int
    total: int
    failures: list[str]

    def percent(self) -> float:
        return self.passed / self.total * 100 if self.total else 0.0

    def format(self) -> str:
        return f"{self.passed}/{self.total}"

    def to_dict(self) -> dict:
        return {"passed": self.passed, "total": self.total, "failures": self.failures}


@dataclass
class ManualResult:
    score: int
    comment: str

    def percent(self) -> float:
        return self.score / 10 * 100

    def format(self) -> str:
        return f"{self.score}/10"

    def to_dict(self) -> dict:
        return {"manual_score": self.score, "comment": self.comment}


@dataclass
class GenerationStats:
    input_tokens: int | None = None
    total_output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    tokens_per_second: float | None = None
    time_to_first_token_seconds: float | None = None
    model_load_time_seconds: float | None = None

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "reasoning_output_tokens": self.reasoning_output_tokens,
            "tokens_per_second": self.tokens_per_second,
            "time_to_first_token_seconds": self.time_to_first_token_seconds,
            "model_load_time_seconds": self.model_load_time_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "GenerationStats | None":
        if not data:
            return None
        return cls(
            input_tokens=data.get("input_tokens"),
            total_output_tokens=data.get("total_output_tokens"),
            reasoning_output_tokens=data.get("reasoning_output_tokens"),
            tokens_per_second=data.get("tokens_per_second"),
            time_to_first_token_seconds=data.get("time_to_first_token_seconds"),
            model_load_time_seconds=data.get("model_load_time_seconds"),
        )


@dataclass
class SpeedSample:
    host_id: str
    host_label: str
    model: str
    benchmark: str
    level: str
    tested_at: str
    stats: GenerationStats

    def to_dict(self) -> dict:
        return {
            "host_id": self.host_id,
            "host_label": self.host_label,
            "model": self.model,
            "benchmark": self.benchmark,
            "level": self.level,
            "tested_at": self.tested_at,
            "stats": self.stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpeedSample":
        return cls(
            host_id=data["host_id"],
            host_label=data.get("host_label", ""),
            model=data["model"],
            benchmark=data["benchmark"],
            level=data["level"],
            tested_at=data["tested_at"],
            stats=GenerationStats.from_dict(data.get("stats")) or GenerationStats(),
        )


@dataclass
class StoredResult:
    model: str
    benchmark: str
    level: str
    tested_at: str
    evaluation: TestResult | ManualResult

    def percent(self) -> float:
        return self.evaluation.percent()

    def format(self) -> str:
        return self.evaluation.format()

    @property
    def failures(self) -> list[str]:
        return self.evaluation.failures if isinstance(self.evaluation, TestResult) else []

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "benchmark": self.benchmark,
            "level": self.level,
            "tested_at": self.tested_at,
            **self.evaluation.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StoredResult":
        if "manual_score" in data:
            evaluation = ManualResult(score=data["manual_score"], comment=data.get("comment", ""))
        else:
            evaluation = TestResult(
                passed=data["passed"], total=data["total"], failures=data.get("failures", [])
            )
        return cls(
            model=data["model"],
            benchmark=data["benchmark"],
            level=data["level"],
            tested_at=data["tested_at"],
            evaluation=evaluation,
        )


class Benchmark(ABC):
    id: str
    name: str
    short: str
    levels: list[Level]
    file_ext: str = "py"
    code_lang: str = "python"
    answers_dir_name: str = "models_answers"
    manual_levels: frozenset[str] = frozenset()

    @property
    def level_order(self) -> list[str]:
        return [level.id for level in self.levels]

    def level_by_id(self, level_id: str) -> Level:
        for level in self.levels:
            if level.id == level_id:
                return level
        raise KeyError(f"Unknown level '{level_id}' for benchmark '{self.id}'")

    def extract_code(self, raw_text: str) -> str:
        """Достаёт код из ```<code_lang> ... ``` блока (последнего, если их несколько —
        модель могла сначала показать черновик/другой язык, а затем финальный вариант).
        Если явного блока с этой меткой языка нет — берёт последний блок без метки языка.
        Если открывающий блок есть, а закрывающего нет (генерация оборвалась) — берёт всё
        после открывающего маркера, отбрасывая сам маркер.
        Если блоков нет вообще — возвращает текст как есть."""
        lang_blocks = re.findall(rf"```{re.escape(self.code_lang)}\s*\n(.*?)```", raw_text, re.DOTALL)
        if lang_blocks:
            return lang_blocks[-1].strip() + "\n"

        any_blocks = re.findall(r"```(?:\w*)\s*\n(.*?)```", raw_text, re.DOTALL)
        if any_blocks:
            return any_blocks[-1].strip() + "\n"

        unclosed = re.search(rf"```{re.escape(self.code_lang)}\s*\n(.*)", raw_text, re.DOTALL)
        if unclosed:
            return unclosed.group(1).strip() + "\n"

        unclosed_any = re.search(r"```(?:\w*)\s*\n(.*)", raw_text, re.DOTALL)
        if unclosed_any:
            return unclosed_any.group(1).strip() + "\n"

        return raw_text.strip() + "\n"

    @abstractmethod
    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        """Прогоняет тесты для данного уровня. Вызывается фреймворком только когда
        level_id NOT IN self.manual_levels — реализация для manual-уровней не нужна."""
        raise NotImplementedError
