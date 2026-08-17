"""Async HTTP client for LM Studio REST API.

Key design decisions:
- connect timeout = 10s (fast fail if LM Studio not running)
- read timeout = None (generation can take minutes on weak hardware)
- Retry with exponential backoff on ConnectError (model reloading)
"""

import asyncio
import logging

import httpx

from llm_probe.lmstudio.types import (
    ChatRequest,
    ChatResponse,
    ModelInfo,
    ModelsResponse,
)

logger = logging.getLogger(__name__)

# read=None: never timeout on generation — weak hardware can be slow
_TIMEOUTS = httpx.Timeout(connect=10.0, read=None, write=30.0, pool=5.0)

DEFAULT_BASE_URL = "http://localhost:1234"


class LMStudioClient:
    """Async client for LM Studio local API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=_TIMEOUTS,
            headers={"Content-Type": "application/json"},
        )

    async def __aenter__(self) -> "LMStudioClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_models(self) -> list[ModelInfo]:
        """Return available models from LM Studio."""
        resp = await self._client.get("/v1/models")
        resp.raise_for_status()
        return ModelsResponse.model_validate(resp.json()).data

    async def generate(
        self,
        request: ChatRequest,
        *,
        max_retries: int = 3,
        retry_backoff: float = 5.0,
    ) -> ChatResponse:
        """Send chat completion request. Retries on connection errors."""
        return await _generate_with_retry(
            self._client, request, max_retries=max_retries, retry_backoff=retry_backoff
        )

    async def unload_model(self) -> None:
        """Best-effort model unload (not all LM Studio versions support it)."""
        try:
            await self._client.post("/v1/models/unload")
        except Exception as exc:
            logger.debug("unload_model failed (non-critical): %s", exc)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


async def _generate_with_retry(
    client: httpx.AsyncClient,
    request: ChatRequest,
    *,
    max_retries: int,
    retry_backoff: float,
) -> ChatResponse:
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = await client.post(
                "/v1/chat/completions",
                content=request.model_dump_json(),
            )
            resp.raise_for_status()
            return ChatResponse.model_validate(resp.json())
        except httpx.ConnectError as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                wait = retry_backoff * (attempt + 1)
                logger.warning(
                    "LM Studio unreachable (attempt %d/%d), retrying in %.0fs…",
                    attempt + 1,
                    max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
        except httpx.HTTPStatusError:
            raise
        except Exception:
            raise

    raise last_exc or RuntimeError("generate: all retries exhausted")
