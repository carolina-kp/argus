from datetime import UTC, datetime
from typing import Any

from argus_core.clients.base import BaseClient
from argus_core.config import settings

# CoinGecko free tier: ~30 calls/min. Cache hard: current prices for 60s,
# historical market charts (which change slowly) for 1 hour.
_PRICE_TTL = 60
_HISTORY_TTL = 3600


class CoinGeckoClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(settings.coingecko_base_url, source="coingecko")

    async def simple_price(self, ids: list[str]) -> dict[str, dict[str, float]]:
        """Current price, market cap and 24h volume for the given CoinGecko ids."""
        joined = ",".join(sorted(ids))
        data: dict[str, dict[str, float]] = await self.get(
            "/simple/price",
            params={
                "ids": joined,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
            },
            cache_key=f"cg:price:{joined}",
            ttl_seconds=_PRICE_TTL,
        )
        return data

    async def market_chart(self, coin_id: str, days: int) -> list[tuple[datetime, float]]:
        """Daily (timestamp, price_usd) points over the trailing `days` window."""
        raw: dict[str, Any] = await self.get(
            f"/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": str(days), "interval": "daily"},
            cache_key=f"cg:chart:{coin_id}:{days}",
            ttl_seconds=_HISTORY_TTL,
        )
        points: list[tuple[datetime, float]] = []
        for ms, price in raw.get("prices", []):
            ts = datetime.fromtimestamp(ms / 1000, tz=UTC)
            points.append((ts, float(price)))
        return points
