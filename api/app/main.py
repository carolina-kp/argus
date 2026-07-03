import logging

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger("argus.api")

app = FastAPI(title="Argus API", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    environment: str


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
