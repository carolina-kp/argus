from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from argus_core.models import Anomaly, Base, PriceSnapshot, Watchlist
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import anomaly


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_zscore_needs_min_samples() -> None:
    assert anomaly._zscore([1.0, 2.0, 3.0]) is None  # too few
    assert anomaly._zscore([1.0] * 20) is None  # zero variance


def test_zscore_flags_spike() -> None:
    series = [0.0] * 30 + [100.0]
    z = anomaly._zscore(series)
    assert z is not None and z > anomaly.Z_THRESHOLD


async def _seed_flat_then_spike(session: AsyncSession) -> Watchlist:
    now = datetime.now(tz=UTC)
    asset = Watchlist(symbol="AAVE", name="Aave", coingecko_id="aave", defillama_slug="aave")
    session.add(asset)
    # 30 flat price points, then a large jump -> a return-series outlier.
    for i in range(30):
        session.add(
            PriceSnapshot(
                coingecko_id="aave", ts=now - timedelta(hours=30 - i),
                price_usd=100.0, volume_24h_usd=1000.0,
            )
        )
    session.add(PriceSnapshot(coingecko_id="aave", ts=now, price_usd=140.0, volume_24h_usd=50000.0))
    await session.commit()
    return asset


@pytest.mark.asyncio
async def test_scan_flags_and_dedupes(session: AsyncSession) -> None:
    await _seed_flat_then_spike(session)

    stored = await anomaly.scan(session)
    assert stored >= 1
    metrics = set(
        (await session.execute(select(Anomaly.metric).where(Anomaly.kind == "zscore"))).scalars()
    )
    assert "return" in metrics

    # Re-running the same scan must not create duplicates (dedupe by day).
    stored_again = await anomaly.scan(session)
    assert stored_again == 0
    total = (await session.execute(select(func.count()).select_from(Anomaly))).scalar_one()
    assert total == len(metrics)


@pytest.mark.asyncio
async def test_depeg_rule(session: AsyncSession) -> None:
    now = datetime.now(tz=UTC)
    asset = Watchlist(symbol="USDC", name="USD Coin", coingecko_id="usd-coin", is_stablecoin=True)
    session.add(asset)
    # Last three snapshots all more than 0.5% off peg.
    for i, price in enumerate([1.0, 0.99, 0.988, 0.985]):
        session.add(
            PriceSnapshot(
                coingecko_id="usd-coin",
                ts=now - timedelta(minutes=30 * (3 - i)),
                price_usd=price,
            )
        )
    await session.commit()

    await anomaly.scan(session)
    depegs = list(
        (await session.execute(select(Anomaly).where(Anomaly.kind == "depeg"))).scalars()
    )
    assert len(depegs) == 1
    assert depegs[0].symbol == "USDC"


@pytest.mark.asyncio
async def test_no_flag_when_stable(session: AsyncSession) -> None:
    now = datetime.now(tz=UTC)
    session.add(Watchlist(symbol="ETH", name="Ethereum", coingecko_id="ethereum"))
    for i in range(31):
        session.add(
            PriceSnapshot(coingecko_id="ethereum", ts=now - timedelta(hours=31 - i),
                          price_usd=2000.0, volume_24h_usd=1000.0)
        )
    await session.commit()
    assert await anomaly.scan(session) == 0
