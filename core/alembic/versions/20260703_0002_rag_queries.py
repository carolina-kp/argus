"""rag_queries audit log for the regulatory RAG

Revision ID: 0002_rag_queries
Revises: 0001_initial
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_rag_queries"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rag_queries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("rewritten_query", sa.Text),
        sa.Column("jurisdiction", sa.String(8)),
        sa.Column("retrieved", sa.JSON, nullable=False),
        sa.Column("answer", sa.Text),
        sa.Column("max_score", sa.Float),
        sa.Column("refused", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rag_queries_created_at", "rag_queries", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_rag_queries_created_at", table_name="rag_queries")
    op.drop_table("rag_queries")
