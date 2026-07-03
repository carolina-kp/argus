from datetime import UTC, datetime
from typing import Any

from argus_core.clients.base import BaseClient
from argus_core.config import settings

# DeFiLlama is generous and free; TVL moves slowly so cache for an hour.
_TVL_TTL = 3600


class DefiLlamaClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(settings.defillama_base_url, source="defillama")

    async def current_tvl(self, slug: str) -> float:
        """Current protocol TVL in USD."""
        data: float = await self.get(
            f"/tvl/{slug}",
            cache_key=f"llama:tvl:{slug}",
            ttl_seconds=_TVL_TTL,
        )
        return float(data)

    async def protocol_tvl_history(
        self, slug: str, days: int
    ) -> list[tuple[datetime, float]]:
        """Daily (timestamp, tvl_usd) points, trimmed to the trailing `days` window."""
        raw: dict[str, Any] = await self.get(
            f"/protocol/{slug}",
            cache_key=f"llama:hist:{slug}",
            ttl_seconds=_TVL_TTL,
        )
        cutoff = datetime.now(tz=UTC).timestamp() - days * 86400
        points: list[tuple[datetime, float]] = []
        for entry in raw.get("tvl", []):
            secs = entry.get("date")
            value = entry.get("totalLiquidityUSD")
            if secs is None or value is None or secs < cutoff:
                continue
            points.append((datetime.fromtimestamp(secs, tz=UTC), float(value)))
        return points
