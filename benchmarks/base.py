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
            evaluation = TestResult(passed=data["passed"], total=data["total"], failures=data.get("failures", []))
        return cls(
            model=data["model"],
            benchmark=data["benchmark"],
            level=data["level"],
            tested_at=data["tested_at"],
            evaluation=evaluation,
        )


def strip_reasoning_blocks(raw_text: str) -> tuple[str, str | None]:
    """Strips reasoning tags (<think>, <thought>, <reasoning>, <reflection>) from text.

    Returns:
        (cleaned_text, extracted_reasoning_text)
    """
    if not raw_text:
        return "", None

    reasoning_parts = []
    cleaned = raw_text

    tags = ["think", "thought", "reasoning", "reflection"]
    for tag in tags:
        pat = rf"<{tag}>(.*?)</{tag}>"
        for match in re.finditer(pat, cleaned, re.DOTALL | re.IGNORECASE):
            text = match.group(1).strip()
            if text:
                reasoning_parts.append(text)
        cleaned = re.sub(pat, "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # If opening tag remains unclosed (generation truncated mid-thought)
    tag_union = "|".join(tags)
    unclosed_pat = rf"<(?:{tag_union})>(.*)"
    unclosed = re.search(unclosed_pat, cleaned, re.DOTALL | re.IGNORECASE)
    if unclosed:
        text = unclosed.group(1).strip()
        if text:
            reasoning_parts.append(text)
        cleaned = re.sub(unclosed_pat, "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    reasoning_str = "\n\n".join(reasoning_parts) if reasoning_parts else None
    return cleaned.strip(), reasoning_str


class Benchmark(ABC):
    id: str
    name: str
    short: str
    levels: list[Level]
    file_ext: str = "py"
    code_lang: str = "python"
    code_lang_aliases: tuple[str, ...] = ()
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
        """Extracts source code from ```<code_lang> ... ``` block (takes the last block if
        multiple are present, as the model may output drafts or preamble before final code).
        If no block with matching language label is found, falls back to the last generic block.
        If an opening block is present without a closing fence, captures all content after the marker.
        If no fences exist, returns the text as is."""
        # 1. First strip reasoning blocks (<think>...</think>) to avoid extracting drafts from thought chains
        cleaned, _ = strip_reasoning_blocks(raw_text)
        if not cleaned:
            return ""

        text_to_parse = cleaned

        langs = [self.code_lang] + list(self.code_lang_aliases)
        pattern = "|".join(re.escape(language) for language in langs)
        lang_blocks = re.findall(rf"```(?:{pattern})\s*\n(.*?)```", text_to_parse, re.DOTALL | re.IGNORECASE)
        if lang_blocks:
            return lang_blocks[-1].strip() + "\n"

        any_blocks = re.findall(r"```(?:\w*)\s*\n(.*?)```", text_to_parse, re.DOTALL)
        if any_blocks:
            return any_blocks[-1].strip() + "\n"

        unclosed = re.search(rf"```(?:{pattern})\s*\n(.*)", text_to_parse, re.DOTALL | re.IGNORECASE)
        if unclosed:
            return unclosed.group(1).strip() + "\n"

        unclosed_any = re.search(r"```(?:\w*)\s*\n(.*)", text_to_parse, re.DOTALL)
        if unclosed_any:
            return unclosed_any.group(1).strip() + "\n"

        return text_to_parse.strip() + "\n"

    @abstractmethod
    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        """Runs test suite for given level. Invoked only when level_id is not manual."""
        raise NotImplementedError
