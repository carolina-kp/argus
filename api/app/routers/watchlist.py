from argus_core.db import get_session
from argus_core.models import Watchlist
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_token
from app.schemas import WatchlistCreate, WatchlistItem, WatchlistUpdate

router = APIRouter(
    prefix="/watchlist", tags=["watchlist"], dependencies=[Depends(require_token)]
)


@router.get("", response_model=list[WatchlistItem])
async def list_items(session: AsyncSession = Depends(get_session)) -> list[Watchlist]:
    result = await session.execute(select(Watchlist).order_by(Watchlist.symbol))
    return list(result.scalars().all())


@router.post("", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: WatchlistCreate, session: AsyncSession = Depends(get_session)
) -> Watchlist:
    item = Watchlist(**payload.model_dump())
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Symbol {payload.symbol} already exists",
        ) from exc
    await session.refresh(item)
    return item


async def _get_or_404(session: AsyncSession, item_id: int) -> Watchlist:
    item = await session.get(Watchlist, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.patch("/{item_id}", response_model=WatchlistItem)
async def update_item(
    item_id: int,
    payload: WatchlistUpdate,
    session: AsyncSession = Depends(get_session),
) -> Watchlist:
    item = await _get_or_404(session, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    item = await _get_or_404(session, item_id)
    await session.delete(item)
    await session.commit()
