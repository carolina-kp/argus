"""Async snapshot collectors shared by scheduled jobs and the backfill script."""
import logging
from datetime import UTC, datetime

from argus_core.clients.coingecko import CoinGeckoClient
from argus_core.clients.defillama import DefiLlamaClient
from argus_core.clients.mempool import MempoolClient
from argus_core.db import SessionLocal
from argus_core.repository import (
    insert_onchain,
    list_watchlist,
    upsert_price,
    upsert_tvl,
)

logger = logging.getLogger("argus.worker")


async def collect_market() -> None:
    """Current prices/market caps/volumes for every watchlist asset."""
    async with SessionLocal() as session:
        assets = await list_watchlist(session)
        ids = [a.coingecko_id for a in assets if a.coingecko_id]
        if not ids:
            return
        prices = await CoinGeckoClient().simple_price(ids)
        ts = datetime.now(tz=UTC)
        for coin_id, data in prices.items():
            await upsert_price(
                session,
                coingecko_id=coin_id,
                ts=ts,
                price_usd=data["usd"],
                market_cap_usd=data.get("usd_market_cap"),
                volume_24h_usd=data.get("usd_24h_vol"),
            )
        await session.commit()
    logger.info('{"job":"market_snapshot","assets":%d}', len(ids))


async def collect_tvl() -> None:
    """Current TVL for every watchlist asset that has a DeFiLlama slug."""
    client = DefiLlamaClient()
    async with SessionLocal() as session:
        assets = await list_watchlist(session)
        slugs = [a.defillama_slug for a in assets if a.defillama_slug]
        ts = datetime.now(tz=UTC)
        for slug in slugs:
            tvl = await client.current_tvl(slug)
            await upsert_tvl(session, defillama_slug=slug, ts=ts, tvl_usd=tvl)
        await session.commit()
    logger.info('{"job":"tvl_snapshot","protocols":%d}', len(slugs))


async def collect_onchain() -> None:
    """BTC mempool fees, hashrate and difficulty."""
    client = MempoolClient()
    fees = await client.recommended_fees()
    hashrate = await client.hashrate()
    current_hashrate = hashrate.get("currentHashrate")
    async with SessionLocal() as session:
        await insert_onchain(
            session,
            ts=datetime.now(tz=UTC),
            fastest_fee=fees.get("fastestFee"),
            half_hour_fee=fees.get("halfHourFee"),
            hour_fee=fees.get("hourFee"),
            hashrate_ehs=current_hashrate / 1e18 if current_hashrate else None,
            difficulty=hashrate.get("currentDifficulty"),
        )
        await session.commit()
    logger.info('{"job":"onchain_snapshot","status":"ok"}')
