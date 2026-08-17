"""SQLModel table for benchmark runs."""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Run(SQLModel, table=True):
    """A single benchmark attempt (one job in pass@k chain)."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: str = Field(index=True)
    bench_id: str = Field(index=True)   # 'bug_hunt', 'algorithm', ...
    level_id: str                        # 'l1', 'l2', 'l3'
    attempt: int                         # 1..k
    temperature: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Speed metrics
    tok_per_sec: float | None = None
    ttft_ms: float | None = None
    load_time_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    # Eval result
    passed: int | None = None
    total: int | None = None
    error_log: str | None = None

    # Raw data
    raw_response: str | None = None
    extracted_code: str | None = None

    # Job status — не путать с eval результатом
    status: str = "ok"  # 'ok' | 'llm_error' | 'eval_error' | 'save_error' | 'no_code'


class RunRead(SQLModel):
    """Read-only DTO для API."""

    id: UUID
    model_id: str
    bench_id: str
    level_id: str
    attempt: int
    temperature: float
    created_at: datetime
    tok_per_sec: float | None
    ttft_ms: float | None
    input_tokens: int | None
    output_tokens: int | None
    passed: int | None
    total: int | None
    error_log: str | None
    status: str

    @property
    def pass_rate(self) -> float | None:
        if self.passed is None or self.total is None or self.total == 0:
            return None
        return self.passed / self.total


JobStatus = Literal["ok", "llm_error", "eval_error", "save_error", "no_code"]
