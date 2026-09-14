"""add is_verified to call_scores

Revision ID: 053f93439d98
Revises: 274f2534813d
Create Date: 2026-09-07 20:38:07.705523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '053f93439d98'
down_revision: Union[str, None] = '274f2534813d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'call_scores',
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('call_scores', 'is_verified')
