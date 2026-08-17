"""pass@k chain runner — resilient, never crashes, saves all results.

Design principles:
- Every Job is atomic: failure of one never stops the chain
- 4 guarded stages per job: LLM → extract → eval → save
- Progress emitted via async callback (SSE / CLI rich)
- KeyboardInterrupt / CancelledError = graceful stop, keep saved results
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from llm_probe.benchmarks.base import BenchmarkTask
from llm_probe.benchmarks.registry import get_benchmark
from llm_probe.db.crud import save_run
from llm_probe.db.engine import get_session
from llm_probe.lmstudio.client import LMStudioClient
from llm_probe.lmstudio.types import ChatRequest, Message
from llm_probe.models.run import JobStatus, Run
from llm_probe.runner.extractor import extract_code
from llm_probe.runner.sandbox import SandboxResult, evaluate

logger = logging.getLogger(__name__)

# Temperature schedule for pass@k attempts
_TEMPERATURES = [0.2, 0.5, 0.8, 0.4, 0.6]

ProgressCallback = Callable[["JobResult"], Coroutine[Any, Any, None]]


@dataclass
class Job:
    """One atomic unit of work."""
    bench_id: str
    level_id: str
    task: BenchmarkTask
    attempt: int           # 1-indexed
    temperature: float
    model_id: str


@dataclass
class JobResult:
    job: Job
    run_id: UUID | None
    status: JobStatus
    passed: int = 0
    total: int = 0
    tok_per_sec: float | None = None
    ttft_ms: float | None = None
    error: str | None = None

    @property
    def label(self) -> str:
        return f"{self.job.bench_id}/{self.job.level_id} attempt {self.job.attempt}"


@dataclass
class ChainSummary:
    total: int = 0
    ok: int = 0
    llm_errors: int = 0
    eval_errors: int = 0
    save_errors: int = 0
    duration_sec: float = 0.0
    results: list[JobResult] = field(default_factory=list)


def build_jobs(
    model_id: str,
    bench_ids: list[str],
    levels: list[str],
    k: int,
) -> list[Job]:
    """Expand benchmark selection into a flat list of Jobs."""
    jobs: list[Job] = []
    temps = (_TEMPERATURES * k)[:k]  # cycle through temperatures

    for bench_id in bench_ids:
        bench = get_benchmark(bench_id)
        for level in levels:
            tasks = bench.load_tasks(level)
            for task in tasks:
                for attempt_idx in range(k):
                    jobs.append(Job(
                        bench_id=bench_id,
                        level_id=level,
                        task=task,
                        attempt=attempt_idx + 1,
                        temperature=temps[attempt_idx],
                        model_id=model_id,
                    ))
    return jobs


async def run_chain(
    jobs: list[Job],
    lm_client: LMStudioClient,
    *,
    on_progress: ProgressCallback | None = None,
    eval_timeout: float = 5.0,
) -> ChainSummary:
    """Run all jobs sequentially, never crashing on individual failures."""
    summary = ChainSummary(total=len(jobs))
    t_start = time.monotonic()

    try:
        for i, job in enumerate(jobs):
            logger.info(
                "[%d/%d] %s/%s task=%s attempt=%d",
                i + 1, len(jobs), job.bench_id, job.level_id, job.task.id, job.attempt,
            )
            result = await _run_job_safe(job, lm_client, eval_timeout=eval_timeout)
            summary.results.append(result)

            # Tally
            match result.status:
                case "ok" | "no_code":
                    summary.ok += 1
                case "llm_error":
                    summary.llm_errors += 1
                case "eval_error":
                    summary.eval_errors += 1
                case "save_error":
                    summary.save_errors += 1

            if on_progress:
                await on_progress(result)

    except (asyncio.CancelledError, KeyboardInterrupt):
        completed = len(summary.results)
        logger.warning(
            "Chain interrupted after %d/%d jobs — %d results saved to DB",
            completed, len(jobs), sum(1 for r in summary.results if r.run_id),
        )

    summary.duration_sec = time.monotonic() - t_start
    return summary


# ------------------------------------------------------------------
# Internal: single job execution with full error isolation
# ------------------------------------------------------------------

async def _run_job_safe(
    job: Job,
    lm_client: LMStudioClient,
    *,
    eval_timeout: float,
) -> JobResult:
    """Run one job through all 4 stages. Never raises."""

    # ── Stage 1: LLM generation ────────────────────────────────────
    t0 = time.monotonic()
    try:
        request = ChatRequest(
            model=job.model_id,
            messages=[Message(role="user", content=job.task.prompt)],
            temperature=job.temperature,
        )
        response = await lm_client.generate(request)
        raw_response = response.content
        elapsed_ms = (time.monotonic() - t0) * 1000

        # Derive speed metrics from usage
        output_tokens = response.usage.completion_tokens
        tok_per_sec = (
            output_tokens / ((time.monotonic() - t0)) if output_tokens > 0 else None
        )
        input_tokens = response.usage.prompt_tokens

    except Exception as exc:
        error_msg = _classify_llm_error(exc)
        logger.warning("[%s] LLM error: %s", job.task.id, error_msg)
        return JobResult(job=job, run_id=None, status="llm_error", error=error_msg)

    # ── Stage 2: code extraction ────────────────────────────────────
    extracted = extract_code(raw_response)
    if not extracted:
        logger.warning("[%s] No code block found in response", job.task.id)
        result = _save_run(job, raw_response, extracted, SandboxResult(0, len(job.task.tests), ["No code extracted"]), tok_per_sec, None, input_tokens, output_tokens)
        return JobResult(
            job=job, run_id=result, status="no_code",
            total=len(job.task.tests), error="No code block in response",
        )

    # ── Stage 3: sandbox eval ───────────────────────────────────────
    tests = [{"code": t.code} for t in job.task.tests]
    try:
        sandbox = await asyncio.get_event_loop().run_in_executor(
            None, lambda: evaluate(extracted, tests, timeout=eval_timeout)
        )
    except Exception as exc:
        logger.error("[%s] Sandbox error: %s", job.task.id, exc)
        sandbox = SandboxResult(0, len(tests), [str(exc)])

    # ── Stage 4: save to SQLite ─────────────────────────────────────
    run_id = _save_run(
        job, raw_response, extracted, sandbox,
        tok_per_sec, elapsed_ms, input_tokens, output_tokens,
    )
    if run_id is None:
        return JobResult(
            job=job, run_id=None, status="save_error",
            passed=sandbox.passed, total=sandbox.total,
            tok_per_sec=tok_per_sec,
        )

    logger.info(
        "[%s] ✓ %d/%d passed (%.1f tok/s)",
        job.task.id, sandbox.passed, sandbox.total, tok_per_sec or 0,
    )
    return JobResult(
        job=job, run_id=run_id, status="ok",
        passed=sandbox.passed, total=sandbox.total,
        tok_per_sec=tok_per_sec, ttft_ms=elapsed_ms,
    )


def _save_run(
    job: Job,
    raw_response: str,
    extracted_code: str,
    sandbox: SandboxResult,
    tok_per_sec: float | None,
    ttft_ms: float | None,
    input_tokens: int,
    output_tokens: int,
) -> UUID | None:
    """Persist run to SQLite. Returns run_id or None on error."""
    try:
        run = Run(
            model_id=job.model_id,
            bench_id=job.bench_id,
            level_id=job.level_id,
            attempt=job.attempt,
            temperature=job.temperature,
            tok_per_sec=tok_per_sec,
            ttft_ms=ttft_ms,
            input_tokens=input_tokens or None,
            output_tokens=output_tokens or None,
            passed=sandbox.passed,
            total=sandbox.total,
            error_log="\n".join(sandbox.errors) or None,
            raw_response=raw_response,
            extracted_code=extracted_code,
            status="ok" if extracted_code else "no_code",
        )
        with get_session() as session:
            return save_run(session, run).id
    except Exception as exc:
        logger.error("Failed to save run for %s: %s", job.task.id, exc)
        return None


def _classify_llm_error(exc: Exception) -> str:
    import httpx
    if isinstance(exc, httpx.ConnectError):
        return "LM Studio unreachable — is it running?"
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
    return f"{type(exc).__name__}: {exc}"


# ------------------------------------------------------------------
# SSE streaming helper
# ------------------------------------------------------------------

async def stream_jobs(
    jobs: list[Job],
    lm_client: LMStudioClient,
    eval_timeout: float = 5.0,
) -> AsyncIterator[dict]:
    """Yield progress events for SSE. Same resilience as run_chain."""
    for i, job in enumerate(jobs):
        result = await _run_job_safe(job, lm_client, eval_timeout=eval_timeout)
        yield {
            "index": i + 1,
            "total": len(jobs),
            "label": result.label,
            "status": result.status,
            "passed": result.passed,
            "total_tests": result.total,
            "tok_per_sec": result.tok_per_sec,
            "error": result.error,
        }
