"""add email verification

Revision ID: b7e2c9f41a08
Revises: 8c1d4a7f92be
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e2c9f41a08"
down_revision: str | None = "8c1d4a7f92be"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "email_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_verifications_user_id", "email_verifications", ["user_id"]
    )
    op.create_index(
        "ix_email_verifications_token_hash",
        "email_verifications",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_email_verifications_token_hash", table_name="email_verifications")
    op.drop_index("ix_email_verifications_user_id", table_name="email_verifications")
    op.drop_table("email_verifications")
    op.drop_column("users", "email_verified_at")
