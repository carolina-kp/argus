from typing import Any

from argus_core.clients.base import BaseClient
from argus_core.config import settings

_TTL = 60


class MempoolClient(BaseClient):
    """BTC on-chain metrics from mempool.space."""

    def __init__(self) -> None:
        super().__init__(settings.mempool_base_url, source="mempool")

    async def recommended_fees(self) -> dict[str, int]:
        data: dict[str, int] = await self.get(
            "/v1/fees/recommended",
            cache_key="mempool:fees",
            ttl_seconds=_TTL,
        )
        return data

    async def hashrate(self) -> dict[str, Any]:
        """Current hashrate/difficulty (`currentHashrate` in H/s, `currentDifficulty`)."""
        data: dict[str, Any] = await self.get(
            "/v1/mining/hashrate/3d",
            cache_key="mempool:hashrate",
            ttl_seconds=_TTL,
        )
        return data
