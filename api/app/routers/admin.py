from datetime import UTC, datetime

from argus_core.cache import request_ingest
from fastapi import APIRouter, Depends, status

from app.auth import require_token
from app.schemas import IngestTriggerResponse

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_token)])


@router.post("/ingest", response_model=IngestTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingest() -> IngestTriggerResponse:
    """Request a regulatory re-ingestion. The worker picks this up within a minute.

    Ingestion runs in the worker (it owns the embedding model), so the API only
    sets a Redis flag rather than embedding inline.
    """
    now = datetime.now(tz=UTC)
    await request_ingest(now.isoformat())
    return IngestTriggerResponse(status="accepted", requested_at=now)
