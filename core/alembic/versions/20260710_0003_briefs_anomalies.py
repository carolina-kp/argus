"""briefs and anomalies tables for the agent layer

Revision ID: 0003_briefs_anomalies
Revises: 0002_rag_queries
Create Date: 2026-07-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_briefs_anomalies"
down_revision: str | None = "0002_rag_queries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "briefs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("brief_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sections", sa.JSON, nullable=False),
        sa.Column("body_markdown", sa.Text, nullable=False),
        sa.Column("emailed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_briefs_brief_date", "briefs", ["brief_date"], unique=True)

    op.create_table(
        "anomalies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("metric", sa.String(16), nullable=False),
        sa.Column("zscore", sa.Float),
        sa.Column("value", sa.Float),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detail", sa.JSON, nullable=False),
        sa.Column("dedupe_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dedupe_key", name="uq_anomaly_dedupe"),
    )
    op.create_index("ix_anomalies_kind", "anomalies", ["kind"])
    op.create_index("ix_anomalies_symbol", "anomalies", ["symbol"])
    op.create_index("ix_anomalies_ts", "anomalies", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_anomalies_ts", table_name="anomalies")
    op.drop_index("ix_anomalies_symbol", table_name="anomalies")
    op.drop_index("ix_anomalies_kind", table_name="anomalies")
    op.drop_table("anomalies")
    op.drop_index("ix_briefs_brief_date", table_name="briefs")
    op.drop_table("briefs")
