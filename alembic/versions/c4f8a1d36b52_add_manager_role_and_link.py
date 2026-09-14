"""add manager role and operator to manager link

Revision ID: c4f8a1d36b52
Revises: b7e2c9f41a08
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4f8a1d36b52"
down_revision: str | None = "b7e2c9f41a08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'manager'")

    op.add_column("users", sa.Column("manager_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_manager_id", "users", ["manager_id"])
    op.create_foreign_key(
        "fk_users_manager_id",
        "users",
        "users",
        ["manager_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_manager_id", "users", type_="foreignkey")
    op.drop_index("ix_users_manager_id", table_name="users")
    op.drop_column("users", "manager_id")
