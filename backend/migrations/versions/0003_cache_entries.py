"""Add cache_entries table for persistent cache

Revision ID: 0003_cache_entries
Revises: 0002_seed_idempotency_indexes
Create Date: 2026-04-10

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_cache_entries"
down_revision = "0002_seed_idempotency_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cache_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("namespace", sa.String(length=64), nullable=False),
        sa.Column("cache_key", sa.String(length=512), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("namespace", "cache_key", name="uq_cache_namespace_key"),
    )
    op.create_index("ix_cache_expires_at", "cache_entries", ["expires_at"])
    op.create_index("ix_cache_namespace", "cache_entries", ["namespace"])


def downgrade() -> None:
    op.drop_index("ix_cache_namespace", table_name="cache_entries")
    op.drop_index("ix_cache_expires_at", table_name="cache_entries")
    op.drop_table("cache_entries")
