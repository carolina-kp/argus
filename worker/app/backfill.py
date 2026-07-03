"""One-time 30-day history backfill so the API serves real history immediately.

Idempotent: reruns skip rows that already exist. Run with `python -m app.backfill`.
"""
import asyncio
import logging

from argus_core.clients.coingecko import CoinGeckoClient
from argus_core.clients.defillama import DefiLlamaClient
from argus_core.db import SessionLocal
from argus_core.repository import list_watchlist, upsert_price, upsert_tvl

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("argus.worker")

DAYS = 30


async def backfill(days: int = DAYS) -> None:
    cg = CoinGeckoClient()
    llama = DefiLlamaClient()
    async with SessionLocal() as session:
        assets = await list_watchlist(session)
        for asset in assets:
            if asset.coingecko_id:
                for ts, price in await cg.market_chart(asset.coingecko_id, days):
                    await upsert_price(session, asset.coingecko_id, ts, price)
                logger.info('{"backfill":"price","asset":"%s"}', asset.symbol)
            if asset.defillama_slug:
                for ts, tvl in await llama.protocol_tvl_history(asset.defillama_slug, days):
                    await upsert_tvl(session, asset.defillama_slug, ts, tvl)
                logger.info('{"backfill":"tvl","asset":"%s"}', asset.symbol)
        await session.commit()
    logger.info('{"backfill":"done"}')


if __name__ == "__main__":
    asyncio.run(backfill())
