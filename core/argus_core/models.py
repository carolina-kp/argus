from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Watchlist(Base):
    """A tracked asset. `coingecko_id` and `defillama_slug` map to external sources."""

    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    coingecko_id: Mapped[str | None] = mapped_column(String(128), index=True)
    defillama_slug: Mapped[str | None] = mapped_column(String(128))
    is_stablecoin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (UniqueConstraint("coingecko_id", "ts", name="uq_price_asset_ts"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    coingecko_id: Mapped[str] = mapped_column(String(128), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price_usd: Mapped[float] = mapped_column(Numeric(24, 8))
    market_cap_usd: Mapped[float | None] = mapped_column(Numeric(28, 2))
    volume_24h_usd: Mapped[float | None] = mapped_column(Numeric(28, 2))


class TvlSnapshot(Base):
    __tablename__ = "tvl_snapshots"
    __table_args__ = (UniqueConstraint("defillama_slug", "ts", name="uq_tvl_slug_ts"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    defillama_slug: Mapped[str] = mapped_column(String(128), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    tvl_usd: Mapped[float] = mapped_column(Numeric(28, 2))


class OnchainSnapshot(Base):
    """BTC on-chain metrics from mempool.space."""

    __tablename__ = "onchain_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fastest_fee: Mapped[int | None] = mapped_column()
    half_hour_fee: Mapped[int | None] = mapped_column()
    hour_fee: Mapped[int | None] = mapped_column()
    hashrate_ehs: Mapped[float | None] = mapped_column(Numeric(20, 4))
    difficulty: Mapped[float | None] = mapped_column(Numeric(30, 2))


class UnlockEvent(Base):
    __tablename__ = "unlock_events"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "unlock_date", name="uq_unlock_asset_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlist.id"), index=True)
    unlock_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    amount_tokens: Mapped[float | None] = mapped_column(Numeric(28, 4))
    amount_usd: Mapped[float | None] = mapped_column(Numeric(28, 2))
    description: Mapped[str | None] = mapped_column(String(256))


class Brief(Base):
    """A generated daily brief. One per calendar date (CET)."""

    __tablename__ = "briefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    brief_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), unique=True, index=True
    )
    sections: Mapped[dict[str, Any]] = mapped_column(JSON)
    body_markdown: Mapped[str] = mapped_column(Text)
    emailed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Anomaly(Base):
    """A flagged anomaly. `dedupe_key` prevents the same event refiring."""

    __tablename__ = "anomalies"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_anomaly_dedupe"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)  # zscore | depeg
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    metric: Mapped[str] = mapped_column(String(16))  # return | volume | tvl | price
    zscore: Mapped[float | None] = mapped_column(Float)
    value: Mapped[float | None] = mapped_column(Float)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON)
    dedupe_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RagQuery(Base):
    """Audit log for the regulatory RAG: every question, retrieved set, and answer."""

    __tablename__ = "rag_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    rewritten_query: Mapped[str | None] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(String(8))
    retrieved: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    answer: Mapped[str | None] = mapped_column(Text)
    max_score: Mapped[float | None] = mapped_column(Float)
    refused: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
