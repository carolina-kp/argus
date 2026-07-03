from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchlistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    coingecko_id: str | None
    defillama_slug: str | None
    is_stablecoin: bool


class WatchlistCreate(BaseModel):
    symbol: str
    name: str
    coingecko_id: str | None = None
    defillama_slug: str | None = None
    is_stablecoin: bool = False


class WatchlistUpdate(BaseModel):
    name: str | None = None
    coingecko_id: str | None = None
    defillama_slug: str | None = None
    is_stablecoin: bool | None = None


class PricePoint(BaseModel):
    ts: datetime
    price_usd: float
    market_cap_usd: float | None = None
    volume_24h_usd: float | None = None


class TvlPoint(BaseModel):
    ts: datetime
    tvl_usd: float


class ResearchAsk(BaseModel):
    question: str
    jurisdiction: str | None = None  # EU | CH | GLOBAL


class Citation(BaseModel):
    n: int
    document: str
    ref: str
    url: str
    score: float


class ResearchAnswer(BaseModel):
    answered: bool
    answer: str | None = None
    citations: list[Citation] = []
    max_score: float | None = None
    message: str | None = None


class OnchainPoint(BaseModel):
    ts: datetime
    fastest_fee: int | None
    half_hour_fee: int | None
    hour_fee: int | None
    hashrate_ehs: float | None
    difficulty: float | None
