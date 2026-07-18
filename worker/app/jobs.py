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


def daily_brief() -> None:
    from app.brief import run_daily_brief  # local import: heavy (embedding model)

    asyncio.run(run_daily_brief())


def anomaly_scan() -> None:
    from app.anomaly import run_anomaly_scan

    asyncio.run(run_anomaly_scan())


def ingest_regulatory() -> None:
    from app.ingest import run_ingestion  # local import: heavy (embedding model)

    asyncio.run(run_ingestion())


def check_ingest_request() -> None:
    """Run ingestion if the API set the manual-trigger flag in Redis."""
    from argus_core.cache import pop_ingest_request

    from app.ingest import run_ingestion

    async def _run() -> None:
        requested_at = await pop_ingest_request()
        if requested_at is None:
            return
        logger.info('{"job":"check_ingest_request","triggered_at":"%s"}', requested_at)
        await run_ingestion()

    asyncio.run(_run())
