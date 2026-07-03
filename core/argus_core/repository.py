"""Idempotent upserts for snapshot data. Postgres ON CONFLICT DO NOTHING."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from argus_core.models import (
    OnchainSnapshot,
    PriceSnapshot,
    TvlSnapshot,
    Watchlist,
)


async def list_watchlist(session: AsyncSession) -> list[Watchlist]:
    result = await session.execute(select(Watchlist).order_by(Watchlist.symbol))
    return list(result.scalars().all())


async def upsert_price(
    session: AsyncSession,
    coingecko_id: str,
    ts: datetime,
    price_usd: float,
    market_cap_usd: float | None = None,
    volume_24h_usd: float | None = None,
) -> None:
    stmt = insert(PriceSnapshot).values(
        coingecko_id=coingecko_id,
        ts=ts,
        price_usd=price_usd,
        market_cap_usd=market_cap_usd,
        volume_24h_usd=volume_24h_usd,
    )
    await session.execute(stmt.on_conflict_do_nothing(constraint="uq_price_asset_ts"))


async def upsert_tvl(
    session: AsyncSession, defillama_slug: str, ts: datetime, tvl_usd: float
) -> None:
    stmt = insert(TvlSnapshot).values(defillama_slug=defillama_slug, ts=ts, tvl_usd=tvl_usd)
    await session.execute(stmt.on_conflict_do_nothing(constraint="uq_tvl_slug_ts"))


async def insert_onchain(
    session: AsyncSession,
    ts: datetime,
    fastest_fee: int | None,
    half_hour_fee: int | None,
    hour_fee: int | None,
    hashrate_ehs: float | None,
    difficulty: float | None,
) -> None:
    session.add(
        OnchainSnapshot(
            ts=ts,
            fastest_fee=fastest_fee,
            half_hour_fee=half_hour_fee,
            hour_fee=hour_fee,
            hashrate_ehs=hashrate_ehs,
            difficulty=difficulty,
        )
    )
