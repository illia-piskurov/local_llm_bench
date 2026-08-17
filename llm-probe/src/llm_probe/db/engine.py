"""Database engine and session management."""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from llm_probe.models.run import Run  # noqa: F401 — register table

_DB_PATH = Path.home() / ".llm-probe" / "results.db"

_engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db(db_path: Path | None = None) -> None:
    """Create tables if they don't exist. Call once at startup."""
    global _engine
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if db_path is not None:
        _engine = create_engine(
            f"sqlite:///{path}",
            connect_args={"check_same_thread": False},
            echo=False,
        )
    SQLModel.metadata.create_all(_engine)


def get_session() -> Session:
    """Return a new SQLModel session. Use as context manager: `with get_session() as s:`"""
    return Session(_engine)
