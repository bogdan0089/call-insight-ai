"""init

Revision ID: 660a3f30f8ae
Revises: 
Create Date: 2026-08-29 16:02:52.305643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '660a3f30f8ae'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('checklist_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('is_required', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_items_code'), 'checklist_items', ['code'], unique=True)
    op.create_index(op.f('ix_checklist_items_is_active'), 'checklist_items', ['is_active'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('first_name', sa.String(length=64), nullable=False),
    sa.Column('last_name', sa.String(length=64), nullable=False),
    sa.Column('role', sa.Enum('super_admin', 'admin', 'operator', name='user_role'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_table('calls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('external_id', sa.String(length=128), nullable=True),
    sa.Column('operator_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('queued', 'transcribing', 'analyzing', 'done', 'failed', name='call_status'), server_default='queued', nullable=False),
    sa.Column('audio_path', sa.String(length=512), nullable=False),
    sa.Column('duration_sec', sa.Integer(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('total_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calls_created_at'), 'calls', ['created_at'], unique=False)
    op.create_index(op.f('ix_calls_external_id'), 'calls', ['external_id'], unique=True)
    op.create_index(op.f('ix_calls_operator_id'), 'calls', ['operator_id'], unique=False)
    op.create_index(op.f('ix_calls_status'), 'calls', ['status'], unique=False)
    op.create_table('call_scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('call_id', sa.Integer(), nullable=False),
    sa.Column('checklist_item_id', sa.Integer(), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('quote', sa.Text(), nullable=True),
    sa.Column('quote_start_ms', sa.Integer(), nullable=True),
    sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['checklist_item_id'], ['checklist_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('call_id', 'checklist_item_id', name='uq_score_per_item')
    )
    op.create_index(op.f('ix_call_scores_call_id'), 'call_scores', ['call_id'], unique=False)
    op.create_index(op.f('ix_call_scores_checklist_item_id'), 'call_scores', ['checklist_item_id'], unique=False)
    op.create_table('raw_ai_responses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('call_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.Enum('transcription', 'analysis', name='ai_response_kind'), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_ai_responses_call_id'), 'raw_ai_responses', ['call_id'], unique=False)
    op.create_index(op.f('ix_raw_ai_responses_kind'), 'raw_ai_responses', ['kind'], unique=False)
    op.create_table('transcripts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('call_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('language', sa.String(length=8), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcripts_call_id'), 'transcripts', ['call_id'], unique=True)
    op.create_table('transcript_segments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transcript_id', sa.Integer(), nullable=False),
    sa.Column('idx', sa.Integer(), nullable=False),
    sa.Column('speaker', sa.Enum('operator', 'client', 'unknown', name='speaker'), nullable=False),
    sa.Column('start_ms', sa.Integer(), nullable=False),
    sa.Column('end_ms', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('transcript_id', 'idx', name='uq_segment_order')
    )
    op.create_index(op.f('ix_transcript_segments_transcript_id'), 'transcript_segments', ['transcript_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transcript_segments_transcript_id'), table_name='transcript_segments')
    op.drop_table('transcript_segments')
    op.drop_index(op.f('ix_transcripts_call_id'), table_name='transcripts')
    op.drop_table('transcripts')
    op.drop_index(op.f('ix_raw_ai_responses_kind'), table_name='raw_ai_responses')
    op.drop_index(op.f('ix_raw_ai_responses_call_id'), table_name='raw_ai_responses')
    op.drop_table('raw_ai_responses')
    op.drop_index(op.f('ix_call_scores_checklist_item_id'), table_name='call_scores')
    op.drop_index(op.f('ix_call_scores_call_id'), table_name='call_scores')
    op.drop_table('call_scores')
    op.drop_index(op.f('ix_calls_status'), table_name='calls')
    op.drop_index(op.f('ix_calls_operator_id'), table_name='calls')
    op.drop_index(op.f('ix_calls_external_id'), table_name='calls')
    op.drop_index(op.f('ix_calls_created_at'), table_name='calls')
    op.drop_table('calls')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_checklist_items_is_active'), table_name='checklist_items')
    op.drop_index(op.f('ix_checklist_items_code'), table_name='checklist_items')
    op.drop_table('checklist_items')

    sa.Enum(name='call_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='speaker').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='ai_response_kind').drop(op.get_bind(), checkfirst=True)
