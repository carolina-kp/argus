from datetime import UTC, datetime
from typing import Any

import pytest

from argus_core.clients.coingecko import CoinGeckoClient
from argus_core.clients.defillama import DefiLlamaClient
from argus_core.clients.mempool import MempoolClient


class _Canned:
    """Patches BaseClient.get to return canned payloads without HTTP or Redis."""

    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    async def __call__(
        self, path: str, params: dict[str, Any] | None = None, **_: Any
    ) -> Any:
        self.calls.append((path, params))
        return self.payload


@pytest.mark.asyncio
async def test_coingecko_market_chart_parses_daily_points(monkeypatch: pytest.MonkeyPatch) -> None:
    canned = _Canned({"prices": [[1_700_000_000_000, 42000.5], [1_700_086_400_000, 43000.0]]})
    monkeypatch.setattr(CoinGeckoClient, "get", canned)
    points = await CoinGeckoClient().market_chart("bitcoin", 30)
    assert len(points) == 2
    assert isinstance(points[0][0], datetime)
    assert points[0][1] == 42000.5


@pytest.mark.asyncio
async def test_coingecko_simple_price(monkeypatch: pytest.MonkeyPatch) -> None:
    canned = _Canned({"ethereum": {"usd": 3000.0, "usd_market_cap": 1.0, "usd_24h_vol": 2.0}})
    monkeypatch.setattr(CoinGeckoClient, "get", canned)
    data = await CoinGeckoClient().simple_price(["ethereum"])
    assert data["ethereum"]["usd"] == 3000.0


@pytest.mark.asyncio
async def test_defillama_history_trims_to_window(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(tz=UTC).timestamp()
    canned = _Canned(
        {
            "tvl": [
                {"date": now - 100 * 86400, "totalLiquidityUSD": 1.0},  # too old
                {"date": now - 5 * 86400, "totalLiquidityUSD": 2.0},
            ]
        }
    )
    monkeypatch.setattr(DefiLlamaClient, "get", canned)
    points = await DefiLlamaClient().protocol_tvl_history("aave", 30)
    assert len(points) == 1
    assert points[0][1] == 2.0


@pytest.mark.asyncio
async def test_mempool_fees(monkeypatch: pytest.MonkeyPatch) -> None:
    canned = _Canned({"fastestFee": 20, "halfHourFee": 15, "hourFee": 10})
    monkeypatch.setattr(MempoolClient, "get", canned)
    fees = await MempoolClient().recommended_fees()
    assert fees["fastestFee"] == 20
