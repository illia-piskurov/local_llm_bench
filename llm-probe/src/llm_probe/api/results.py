"""GET /api/results, GET /api/results/{model_id}, GET /api/leaderboard,
DELETE /api/results/{model_id}
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from llm_probe.api.deps import get_db
from llm_probe.db.crud import delete_runs_by_model, get_leaderboard, get_runs
from llm_probe.models.run import RunRead

router = APIRouter(tags=["results"])


@router.get("/results", response_model=list[RunRead])
def read_results(
    model_id: str | None = Query(None),
    bench_id: str | None = Query(None),
    level_id: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    session: Session = Depends(get_db),
) -> list[RunRead]:
    runs = get_runs(session, model_id=model_id, bench_id=bench_id, level_id=level_id, limit=limit)
    return [RunRead.model_validate(r, from_attributes=True) for r in runs]


@router.get("/results/{model_id}", response_model=list[RunRead])
def read_model_results(
    model_id: str,
    session: Session = Depends(get_db),
) -> list[RunRead]:
    runs = get_runs(session, model_id=model_id)
    return [RunRead.model_validate(r, from_attributes=True) for r in runs]


@router.delete("/results/{model_id}")
def delete_model_results(
    model_id: str,
    session: Session = Depends(get_db),
) -> dict:
    count = delete_runs_by_model(session, model_id)
    return {"deleted": count, "model_id": model_id}


@router.get("/leaderboard")
def leaderboard(session: Session = Depends(get_db)) -> list[dict]:
    return get_leaderboard(session)
