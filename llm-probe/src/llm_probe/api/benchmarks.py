"""GET /api/benchmarks — list available benchmarks."""

from fastapi import APIRouter

from llm_probe.benchmarks.registry import list_benchmarks

router = APIRouter(tags=["benchmarks"])


@router.get("/benchmarks")
def list_benches() -> list[dict]:
    return list_benchmarks()
