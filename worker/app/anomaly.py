"""Anomaly scan: rolling 30-day z-scores on returns, volume and TVL deltas
(|z| > 3), plus a stablecoin depeg rule (|price - 1| > 0.005 sustained across
3 consecutive snapshots). Events are deduped per asset/metric/day and stored.

The 30-day series is pulled with portable SQL and the z-score computed in
Python so the logic is unit-testable on SQLite (see DECISIONS.md).
"""
import logging
import statistics
from datetime import UTC, datetime, timedelta
from typing import Any

from argus_core.db import SessionLocal
from argus_core.models import Anomaly, PriceSnapshot, TvlSnapshot, Watchlist
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("argus.worker")

WINDOW = timedelta(days=30)
Z_THRESHOLD = 3.0
MIN_SAMPLES = 10
DEPEG_BAND = 0.005
DEPEG_STREAK = 3


def _zscore(series: list[float]) -> float | None:
    """z-score of the last value against the distribution of the series."""
    if len(series) < MIN_SAMPLES:
        return None
    std = statistics.pstdev(series)
    if std == 0:
        return None
    return (series[-1] - statistics.mean(series)) / std


def _returns(prices: list[float]) -> list[float]:
    return [
        (prices[i] - prices[i - 1]) / prices[i - 1]
        for i in range(1, len(prices))
        if prices[i - 1]
    ]


def _flag(
    kind: str, symbol: str, metric: str, ts: datetime, zscore: float | None,
    value: float, detail: dict[str, Any],
) -> Anomaly:
    dedupe_key = f"{kind}:{symbol}:{metric}:{ts.date().isoformat()}"
    return Anomaly(
        kind=kind, symbol=symbol, metric=metric, zscore=zscore, value=value,
        ts=ts, detail=detail, dedupe_key=dedupe_key,
    )


async def _price_rows(
    session: AsyncSession, coingecko_id: str, since: datetime
) -> list[PriceSnapshot]:
    return list(
        (
            await session.execute(
                select(PriceSnapshot)
                .where(PriceSnapshot.coingecko_id == coingecko_id, PriceSnapshot.ts >= since)
                .order_by(PriceSnapshot.ts)
            )
        ).scalars().all()
    )


async def _tvl_rows(session: AsyncSession, slug: str, since: datetime) -> list[TvlSnapshot]:
    return list(
        (
            await session.execute(
                select(TvlSnapshot)
                .where(TvlSnapshot.defillama_slug == slug, TvlSnapshot.ts >= since)
                .order_by(TvlSnapshot.ts)
            )
        ).scalars().all()
    )


def _detect_for_asset(
    asset: Watchlist, prices: list[PriceSnapshot], tvls: list[TvlSnapshot]
) -> list[Anomaly]:
    found: list[Anomaly] = []

    # Returns z-score.
    price_vals = [float(p.price_usd) for p in prices]
    ret = _returns(price_vals)
    z = _zscore(ret)
    if z is not None and abs(z) > Z_THRESHOLD:
        found.append(
            _flag("zscore", asset.symbol, "return", prices[-1].ts, z, ret[-1],
                  {"n": len(ret), "latest_return": ret[-1]})
        )

    # Volume z-score.
    vols = [float(p.volume_24h_usd) for p in prices if p.volume_24h_usd is not None]
    z = _zscore(vols)
    if z is not None and abs(z) > Z_THRESHOLD:
        found.append(
            _flag("zscore", asset.symbol, "volume", prices[-1].ts, z, vols[-1],
                  {"n": len(vols), "latest_volume": vols[-1]})
        )

    # TVL delta z-score.
    tvl_vals = [float(t.tvl_usd) for t in tvls]
    tvl_deltas = _returns(tvl_vals)
    z = _zscore(tvl_deltas)
    if z is not None and abs(z) > Z_THRESHOLD:
        found.append(
            _flag("zscore", asset.symbol, "tvl", tvls[-1].ts, z, tvl_deltas[-1],
                  {"n": len(tvl_deltas), "latest_delta": tvl_deltas[-1]})
        )

    # Stablecoin depeg: |price - 1| > band across the last DEPEG_STREAK snapshots.
    if asset.is_stablecoin and len(prices) >= DEPEG_STREAK:
        recent = prices[-DEPEG_STREAK:]
        if all(abs(float(p.price_usd) - 1.0) > DEPEG_BAND for p in recent):
            latest_dev = float(prices[-1].price_usd) - 1.0
            found.append(
                _flag("depeg", asset.symbol, "price", prices[-1].ts, None, latest_dev,
                      {"prices": [float(p.price_usd) for p in recent], "band": DEPEG_BAND})
            )

    return found


async def scan(session: AsyncSession) -> int:
    """Run the scan, store newly-flagged anomalies, return how many were stored."""
    since = datetime.now(tz=UTC) - WINDOW
    assets = list((await session.execute(select(Watchlist))).scalars().all())

    candidates: list[Anomaly] = []
    for asset in assets:
        prices = await _price_rows(session, asset.coingecko_id, since) if asset.coingecko_id else []
        tvls = await _tvl_rows(session, asset.defillama_slug, since) if asset.defillama_slug else []
        candidates.extend(_detect_for_asset(asset, prices, tvls))

    if not candidates:
        logger.info('{"job":"anomaly_scan","flagged":0}')
        return 0

    keys = {c.dedupe_key for c in candidates}
    existing = set(
        (
            await session.execute(
                select(Anomaly.dedupe_key).where(Anomaly.dedupe_key.in_(keys))
            )
        ).scalars().all()
    )
    fresh = [c for c in candidates if c.dedupe_key not in existing]
    seen: set[str] = set()
    for anomaly in fresh:
        if anomaly.dedupe_key in seen:
            continue
        seen.add(anomaly.dedupe_key)
        session.add(anomaly)
    await session.commit()
    logger.info('{"job":"anomaly_scan","flagged":%d}', len(seen))
    return len(seen)


async def run_anomaly_scan() -> None:
    async with SessionLocal() as session:
        await scan(session)
