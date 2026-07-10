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
        Если блоков нет вообще — возвращает текст как есть."""
        lang_blocks = re.findall(rf"```{re.escape(self.code_lang)}\s*\n(.*?)```", raw_text, re.DOTALL)
        if lang_blocks:
            return lang_blocks[-1].strip() + "\n"

        any_blocks = re.findall(r"```(?:\w*)\s*\n(.*?)```", raw_text, re.DOTALL)
        if any_blocks:
            return any_blocks[-1].strip() + "\n"

        return raw_text.strip() + "\n"

    @abstractmethod
    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        """Прогоняет тесты для данного уровня. Вызывается фреймворком только когда
        level_id NOT IN self.manual_levels — реализация для manual-уровней не нужна."""
        raise NotImplementedError
