"""FastAPI dependency injection."""

from llm_probe.db.engine import get_session
from llm_probe.lmstudio.client import DEFAULT_BASE_URL, LMStudioClient
from sqlmodel import Session

# Re-export for router use
__all__ = ["get_db", "get_lm_client"]


def get_db() -> Session:
    """Yield a DB session, auto-close after request."""
    with get_session() as session:
        yield session  # type: ignore[misc]


def get_lm_client() -> LMStudioClient:
    """Return shared LM Studio client (base URL from env or default)."""
    import os
    base_url = os.getenv("LM_STUDIO_URL", DEFAULT_BASE_URL)
    return LMStudioClient(base_url)
