"""add_callback_engine_tables

Revision ID: 070d0612c9a2
Revises: 2b4af3f5ef05
Create Date: 2026-07-16 23:30:46.338662

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = 'add_callback_engine_tables'
down_revision: Union[str, Sequence[str], None] = '2b4af3f5ef05' # Points to the latest revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('callback_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', 'EXHAUSTED', name='callbackstatus'), nullable=False),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_callback_jobs_id'), 'callback_jobs', ['id'], unique=False)
    
    op.create_table('callback_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['callback_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_callback_attempts_id'), 'callback_attempts', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_callback_attempts_id'), table_name='callback_attempts')
    op.drop_table('callback_attempts')
    op.drop_index(op.f('ix_callback_jobs_id'), table_name='callback_jobs')
    op.drop_table('callback_jobs')
    op.execute('DROP TYPE callbackstatus')