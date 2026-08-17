"""POST /api/run — start benchmark chain
GET  /api/run/{run_id}/stream — SSE progress stream
"""

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from llm_probe.api.deps import get_lm_client
from llm_probe.benchmarks.registry import all_bench_ids, get_benchmark
from llm_probe.lmstudio.client import LMStudioClient
from llm_probe.runner.runner import ChainSummary, build_jobs, run_chain, stream_jobs

router = APIRouter(tags=["runs"])

# In-memory store of active/completed chain summaries (keyed by chain_id)
# In production this would be Redis/DB — fine for a local tool
_chains: dict[str, ChainSummary | None] = {}


class RunRequest(BaseModel):
    model_id: str
    bench_ids: list[str] = Field(default_factory=all_bench_ids)
    levels: list[str] = Field(default=["l1", "l2", "l3"])
    k: int = Field(default=3, ge=1, le=10)
    eval_timeout: float = Field(default=5.0, ge=1.0, le=60.0)


@router.post("/run")
async def start_run(
    req: RunRequest,
    background_tasks: BackgroundTasks,
    client: LMStudioClient = Depends(get_lm_client),
) -> dict:
    # Validate bench_ids
    for bid in req.bench_ids:
        try:
            get_benchmark(bid)
        except KeyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    chain_id = str(uuid.uuid4())
    _chains[chain_id] = None  # pending

    jobs = build_jobs(req.model_id, req.bench_ids, req.levels, req.k)

    async def _run() -> None:
        summary = await run_chain(jobs, client, eval_timeout=req.eval_timeout)
        _chains[chain_id] = summary

    background_tasks.add_task(_run)

    return {
        "chain_id": chain_id,
        "total_jobs": len(jobs),
        "stream_url": f"/api/run/{chain_id}/stream",
    }


@router.get("/run/{chain_id}/stream")
async def stream_run(
    chain_id: str,
    model_id: Annotated[str, Query()],
    bench_ids: Annotated[list[str], Query()] = None,  # type: ignore[assignment]
    levels: Annotated[list[str], Query()] = None,  # type: ignore[assignment]
    k: Annotated[int, Query(ge=1, le=10)] = 3,
    eval_timeout: Annotated[float, Query(ge=1.0, le=60.0)] = 5.0,
    client: LMStudioClient = Depends(get_lm_client),
) -> StreamingResponse:
    """SSE endpoint — streams job results as they complete."""
    _bench_ids = bench_ids or all_bench_ids()
    _levels = levels or ["l1", "l2", "l3"]
    jobs = build_jobs(model_id, _bench_ids, _levels, k)

    async def event_generator() -> AsyncIterator:  # type: ignore[type-arg]
        async for event in stream_jobs(jobs, client, eval_timeout=eval_timeout):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0)  # yield control
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Fix missing import
from collections.abc import AsyncIterator  # noqa: E402
