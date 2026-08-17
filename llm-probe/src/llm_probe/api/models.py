"""GET /api/models — list models from LM Studio."""

from fastapi import APIRouter, Depends, HTTPException

from llm_probe.api.deps import get_lm_client
from llm_probe.lmstudio.client import LMStudioClient
from llm_probe.lmstudio.types import ModelInfo

router = APIRouter(tags=["models"])


@router.get("/models", response_model=list[ModelInfo])
async def list_models(client: LMStudioClient = Depends(get_lm_client)) -> list[ModelInfo]:
    try:
        return await client.list_models()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio unreachable: {exc}") from exc
