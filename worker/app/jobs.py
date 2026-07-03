import asyncio
import logging

from app.snapshots import collect_market, collect_onchain, collect_tvl

logger = logging.getLogger("argus.worker")


def heartbeat() -> None:
    logger.info('{"job":"heartbeat","status":"alive"}')


def market_snapshot() -> None:
    asyncio.run(collect_market())


def tvl_snapshot() -> None:
    asyncio.run(collect_tvl())


def onchain_snapshot() -> None:
    asyncio.run(collect_onchain())


def ingest_regulatory() -> None:
    from app.ingest import run_ingestion  # local import: heavy (embedding model)

    asyncio.run(run_ingestion())
