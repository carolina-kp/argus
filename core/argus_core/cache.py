import json
from typing import Any

import redis.asyncio as redis

from argus_core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def cache_get(key: str) -> Any | None:
    raw = await get_redis().get(key)
    return json.loads(raw) if raw is not None else None


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    await get_redis().set(key, json.dumps(value), ex=ttl_seconds)


# Manual regulatory-ingestion trigger. The API sets this key; the worker
# polls and clears it (see api /admin/ingest and worker check_ingest_request).
INGEST_REQUEST_KEY = "argus:ingest:requested"


async def request_ingest(requested_at: str) -> None:
    await get_redis().set(INGEST_REQUEST_KEY, requested_at)


async def pop_ingest_request() -> str | None:
    """Atomically read and clear the trigger; returns the timestamp if set."""
    value = await get_redis().getdel(INGEST_REQUEST_KEY)
    return value if value is None else str(value)
