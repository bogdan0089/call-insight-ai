"""add embedding and embedding_model to transcripts

Revision ID: 274f2534813d
Revises: 660a3f30f8ae
Create Date: 2026-08-30 16:30:09.843459

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '274f2534813d'
down_revision: Union[str, None] = '660a3f30f8ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        'transcripts',
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    )
    op.add_column(
        'transcripts',
        sa.Column('embedding_model', sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('transcripts', 'embedding_model')
    op.drop_column('transcripts', 'embedding')