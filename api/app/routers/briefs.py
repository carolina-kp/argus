from datetime import UTC, date, datetime, timedelta

from argus_core.db import get_session
from argus_core.models import Brief
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_token
from app.schemas import BriefDetail, BriefSummary

router = APIRouter(prefix="/briefs", tags=["briefs"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[BriefSummary])
async def list_briefs(
    limit: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> list[Brief]:
    result = await session.execute(
        select(Brief).order_by(Brief.brief_date.desc()).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{brief_date}", response_model=BriefDetail)
async def get_brief(
    brief_date: date,
    session: AsyncSession = Depends(get_session),
) -> Brief:
    start = datetime.combine(brief_date, datetime.min.time(), tzinfo=UTC)
    result = await session.execute(
        select(Brief).where(
            Brief.brief_date >= start, Brief.brief_date < start + timedelta(days=1)
        )
    )
    brief = result.scalar_one_or_none()
    if brief is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No brief for that date")
    return brief
