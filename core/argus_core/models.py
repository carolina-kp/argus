from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
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
