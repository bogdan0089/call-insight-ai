"""add organizations and tenant columns

Revision ID: d5a71f62c9e4
Revises: c4f8a1d36b52
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d5a71f62c9e4"
down_revision: str | None = "c4f8a1d36b52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_ORG = "Перша організація"
DEFAULT_SLUG = "default"


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'owner'")

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"])

    for table in ("users", "calls", "checklist_items"):
        op.add_column(
            table, sa.Column("organization_id", sa.Integer(), nullable=True)
        )
        op.create_foreign_key(
            f"fk_{table}_organization_id",
            table,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index(
        "ix_checklist_items_organization_id", "checklist_items", ["organization_id"]
    )
    op.create_index(
        "ix_calls_org_created", "calls", ["organization_id", "created_at", "id"]
    )

    op.execute(
        sa.text(
            "INSERT INTO organizations (name, slug) VALUES (:name, :slug)"
        ).bindparams(name=DEFAULT_ORG, slug=DEFAULT_SLUG)
    )
    op.execute(
        "UPDATE users SET organization_id = (SELECT id FROM organizations "
        f"WHERE slug = '{DEFAULT_SLUG}') WHERE organization_id IS NULL"
    )
    op.execute(
        "UPDATE calls SET organization_id = (SELECT id FROM organizations "
        f"WHERE slug = '{DEFAULT_SLUG}') WHERE organization_id IS NULL"
    )
    op.execute(
        "UPDATE checklist_items SET organization_id = (SELECT id FROM organizations "
        f"WHERE slug = '{DEFAULT_SLUG}') WHERE organization_id IS NULL"
    )

    op.drop_index("ix_checklist_items_code", table_name="checklist_items")
    op.create_index("ix_checklist_items_code", "checklist_items", ["code"])
    op.create_unique_constraint(
        "uq_checklist_code_per_org", "checklist_items", ["organization_id", "code"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_checklist_code_per_org", "checklist_items", type_="unique"
    )
    op.drop_index("ix_checklist_items_code", table_name="checklist_items")
    op.create_index(
        "ix_checklist_items_code", "checklist_items", ["code"], unique=True
    )

    op.drop_index("ix_calls_org_created", table_name="calls")
    op.drop_index(
        "ix_checklist_items_organization_id", table_name="checklist_items"
    )
    op.drop_index("ix_users_organization_id", table_name="users")

    for table in ("checklist_items", "calls", "users"):
        op.drop_constraint(f"fk_{table}_organization_id", table, type_="foreignkey")
        op.drop_column(table, "organization_id")

    op.drop_index("ix_organizations_is_active", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
