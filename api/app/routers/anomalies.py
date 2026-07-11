from datetime import UTC, datetime, timedelta

from argus_core.db import get_session
from argus_core.models import Anomaly
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_token
from app.schemas import AnomalyItem

router = APIRouter(prefix="/anomalies", tags=["anomalies"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[AnomalyItem])
async def list_anomalies(
    kind: str | None = Query(default=None, description="zscore | depeg"),
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[Anomaly]:
    since = datetime.now(tz=UTC) - timedelta(days=days)
    stmt = select(Anomaly).where(Anomaly.ts >= since)
    if kind:
        stmt = stmt.where(Anomaly.kind == kind)
    stmt = stmt.order_by(Anomaly.ts.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())
