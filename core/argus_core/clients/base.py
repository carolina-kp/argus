import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from argus_core.cache import cache_get, cache_set

logger = logging.getLogger("argus.clients")

_RETRYABLE = (httpx.TransportError, httpx.HTTPStatusError)


class BaseClient:
    """Async HTTP client with exponential-backoff retry and Redis-backed caching."""

    def __init__(self, base_url: str, source: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.source = source

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        reraise=True,
    )
    async def _fetch(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                logger.warning('{"source":"%s","event":"rate_limited"}', self.source)
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        cache_key: str | None = None,
        ttl_seconds: int = 0,
    ) -> Any:
        """GET with optional caching. When `cache_key` is set, serve/store from Redis."""
        if cache_key and ttl_seconds > 0:
            cached = await cache_get(cache_key)
            if cached is not None:
                return cached
        data = await self._fetch(path, params)
        if cache_key and ttl_seconds > 0:
            await cache_set(cache_key, data, ttl_seconds)
        return data
