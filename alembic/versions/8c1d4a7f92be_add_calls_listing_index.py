"""add composite index for call listing and stats

Revision ID: 8c1d4a7f92be
Revises: 053f93439d98
Create Date: 2026-09-12

"""

from collections.abc import Sequence

from alembic import op

revision: str = "8c1d4a7f92be"
down_revision: str | None = "053f93439d98"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX_NAME = "ix_calls_operator_created"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        "calls",
        ["operator_id", "created_at", "id"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="calls")
