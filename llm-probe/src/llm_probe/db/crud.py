"""CRUD operations and leaderboard aggregations."""

from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, col, select

from llm_probe.models.run import Run


def save_run(session: Session, run: Run) -> Run:
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: UUID) -> Run | None:
    return session.get(Run, run_id)


def get_runs(
    session: Session,
    *,
    model_id: str | None = None,
    bench_id: str | None = None,
    level_id: str | None = None,
    limit: int = 200,
) -> list[Run]:
    stmt = select(Run)
    if model_id:
        stmt = stmt.where(Run.model_id == model_id)
    if bench_id:
        stmt = stmt.where(Run.bench_id == bench_id)
    if level_id:
        stmt = stmt.where(Run.level_id == level_id)
    stmt = stmt.order_by(Run.created_at.desc()).limit(limit)  # type: ignore[attr-defined]
    return list(session.exec(stmt).all())


def delete_runs_by_model(session: Session, model_id: str) -> int:
    runs = list(session.exec(select(Run).where(Run.model_id == model_id)).all())
    for run in runs:
        session.delete(run)
    session.commit()
    return len(runs)


def get_leaderboard(session: Session) -> list[dict]:
    """Aggregate pass@1, avg accuracy per model/bench/level."""
    from sqlalchemy import Integer, Float, case

    stmt = (
        select(
            Run.model_id,
            Run.bench_id,
            Run.level_id,
            func.count(Run.id).label("attempts"),
            func.max(
                case((col(Run.passed) == col(Run.total), 1), else_=0)
            ).label("pass_at_1"),
            func.avg(
                col(Run.passed).cast(Float) / col(Run.total).cast(Float)
            ).label("avg_accuracy"),
            func.avg(col(Run.tok_per_sec)).label("avg_tok_per_sec"),
            func.avg(col(Run.ttft_ms)).label("avg_ttft_ms"),
        )
        .where(col(Run.total) > 0)
        .where(Run.status == "ok")
        .group_by(Run.model_id, Run.bench_id, Run.level_id)
        .order_by(Run.model_id, Run.bench_id, Run.level_id)
    )
    rows = session.exec(stmt).all()  # type: ignore[arg-type]
    return [dict(r._mapping) for r in rows]

