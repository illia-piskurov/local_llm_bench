"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from llm_probe.api.benchmarks import router as benchmarks_router
from llm_probe.api.models import router as models_router
from llm_probe.api.results import router as results_router
from llm_probe.api.runs import router as runs_router
from llm_probe.db.engine import init_db

_WEB_DIR = Path(__file__).parent.parent.parent.parent / "web"


def create_app() -> FastAPI:
    app = FastAPI(
        title="llm-probe",
        description="Local LLM benchmark tool",
        version="0.1.0",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    app.include_router(models_router, prefix="/api")
    app.include_router(benchmarks_router, prefix="/api")
    app.include_router(runs_router, prefix="/api")
    app.include_router(results_router, prefix="/api")

    # Serve frontend static files if they exist
    if _WEB_DIR.exists():
        app.mount("/", StaticFiles(directory=_WEB_DIR, html=True), name="static")

    return app


app = create_app()
