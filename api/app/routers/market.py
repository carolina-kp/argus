from datetime import UTC, datetime, timedelta

from argus_core.db import get_session
from argus_core.models import (
    OnchainSnapshot,
    PriceSnapshot,
    TvlSnapshot,
    UnlockEvent,
    Watchlist,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_token
from app.schemas import OnchainPoint, PricePoint, TvlPoint, UnlockPoint

router = APIRouter(tags=["market"], dependencies=[Depends(require_token)])


def _since(days: int) -> datetime:
    return datetime.now(tz=UTC) - timedelta(days=days)


def _until(days: int) -> datetime:
    return datetime.now(tz=UTC) + timedelta(days=days)


@router.get("/market/prices/{coingecko_id}", response_model=list[PricePoint])
async def price_history(
    coingecko_id: str,
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> list[PriceSnapshot]:
    result = await session.execute(
        select(PriceSnapshot)
        .where(
            PriceSnapshot.coingecko_id == coingecko_id,
            PriceSnapshot.ts >= _since(days),
        )
        .order_by(PriceSnapshot.ts)
    )
    return list(result.scalars().all())


@router.get("/market/tvl/{defillama_slug}", response_model=list[TvlPoint])
async def tvl_history(
    defillama_slug: str,
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> list[TvlSnapshot]:
    result = await session.execute(
        select(TvlSnapshot)
        .where(
            TvlSnapshot.defillama_slug == defillama_slug,
            TvlSnapshot.ts >= _since(days),
        )
        .order_by(TvlSnapshot.ts)
    )
    return list(result.scalars().all())


@router.get("/onchain/btc/latest", response_model=OnchainPoint)
async def onchain_latest(
    session: AsyncSession = Depends(get_session),
) -> OnchainSnapshot:
    result = await session.execute(
        select(OnchainSnapshot).order_by(OnchainSnapshot.ts.desc()).limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No on-chain data yet"
        )
    return snapshot


@router.get("/onchain/btc/history", response_model=list[OnchainPoint])
async def onchain_history(
    days: int = Query(default=7, ge=1, le=90),
    session: AsyncSession = Depends(get_session),
) -> list[OnchainSnapshot]:
    result = await session.execute(
        select(OnchainSnapshot)
        .where(OnchainSnapshot.ts >= _since(days))
        .order_by(OnchainSnapshot.ts)
    )
    return list(result.scalars().all())


@router.get("/market/unlocks", response_model=list[UnlockPoint])
async def upcoming_unlocks(
    days: int = Query(default=7, ge=1, le=90),
    session: AsyncSession = Depends(get_session),
) -> list[UnlockPoint]:
    """Upcoming token unlocks for watchlist assets within the next N days.

    Curated data (see README): unlock coverage is maintained for watchlist
    tokens rather than sourced live for the whole market.
    """
    rows = (
        await session.execute(
            select(UnlockEvent, Watchlist.symbol, Watchlist.name)
            .join(Watchlist, UnlockEvent.watchlist_id == Watchlist.id)
            .where(
                UnlockEvent.unlock_date >= datetime.now(tz=UTC),
                UnlockEvent.unlock_date <= _until(days),
            )
            .order_by(UnlockEvent.unlock_date)
        )
    ).all()
    return [
        UnlockPoint(
            symbol=symbol,
            name=name,
            unlock_date=event.unlock_date,
            amount_tokens=(
                float(event.amount_tokens)
                if event.amount_tokens is not None
                else None
            ),
            amount_usd=(
                float(event.amount_usd) if event.amount_usd is not None else None
            ),
            description=event.description,
        )
        for event, symbol, name in rows
    ]
