"""initial schema: watchlist, price/tvl/onchain snapshots, unlock events

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from argus_core.seed import SEED_WATCHLIST

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    watchlist = op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("coingecko_id", sa.String(128)),
        sa.Column("defillama_slug", sa.String(128)),
        sa.Column("is_stablecoin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_watchlist_symbol", "watchlist", ["symbol"])
    op.create_index("ix_watchlist_coingecko_id", "watchlist", ["coingecko_id"])

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("coingecko_id", sa.String(128), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_usd", sa.Numeric(24, 8), nullable=False),
        sa.Column("market_cap_usd", sa.Numeric(28, 2)),
        sa.Column("volume_24h_usd", sa.Numeric(28, 2)),
        sa.UniqueConstraint("coingecko_id", "ts", name="uq_price_asset_ts"),
    )
    op.create_index("ix_price_snapshots_coingecko_id", "price_snapshots", ["coingecko_id"])
    op.create_index("ix_price_snapshots_ts", "price_snapshots", ["ts"])

    op.create_table(
        "tvl_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("defillama_slug", sa.String(128), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tvl_usd", sa.Numeric(28, 2), nullable=False),
        sa.UniqueConstraint("defillama_slug", "ts", name="uq_tvl_slug_ts"),
    )
    op.create_index("ix_tvl_snapshots_defillama_slug", "tvl_snapshots", ["defillama_slug"])
    op.create_index("ix_tvl_snapshots_ts", "tvl_snapshots", ["ts"])

    op.create_table(
        "onchain_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fastest_fee", sa.Integer),
        sa.Column("half_hour_fee", sa.Integer),
        sa.Column("hour_fee", sa.Integer),
        sa.Column("hashrate_ehs", sa.Numeric(20, 4)),
        sa.Column("difficulty", sa.Numeric(30, 2)),
    )
    op.create_index("ix_onchain_snapshots_ts", "onchain_snapshots", ["ts"])

    op.create_table(
        "unlock_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("watchlist_id", sa.Integer, sa.ForeignKey("watchlist.id"), nullable=False),
        sa.Column("unlock_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_tokens", sa.Numeric(28, 4)),
        sa.Column("amount_usd", sa.Numeric(28, 2)),
        sa.Column("description", sa.String(256)),
        sa.UniqueConstraint("watchlist_id", "unlock_date", name="uq_unlock_asset_date"),
    )
    op.create_index("ix_unlock_events_watchlist_id", "unlock_events", ["watchlist_id"])
    op.create_index("ix_unlock_events_unlock_date", "unlock_events", ["unlock_date"])

    op.bulk_insert(watchlist, SEED_WATCHLIST)


def downgrade() -> None:
    op.drop_table("unlock_events")
    op.drop_table("onchain_snapshots")
    op.drop_table("tvl_snapshots")
    op.drop_table("price_snapshots")
    op.drop_table("watchlist")
