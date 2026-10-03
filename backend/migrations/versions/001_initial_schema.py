"""Initial database schema for task_runs and agent_events.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-02 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create task_runs table
    op.create_table(
        'task_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('final_result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_task_runs_status', 'task_runs', ['status'])
    op.create_index('ix_task_runs_created_at', 'task_runs', ['created_at'])

    # 2. Create agent_events audit table
    op.create_table(
        'agent_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_run_id', sa.String(length=36), sa.ForeignKey('task_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_agent_events_task_run_id', 'agent_events', ['task_run_id'])
    op.create_index('ix_agent_events_agent_name', 'agent_events', ['agent_name'])
    op.create_index('ix_agent_events_event_type', 'agent_events', ['event_type'])
    op.create_index('ix_agent_events_timestamp', 'agent_events', ['timestamp'])
    op.create_index('idx_task_timestamp', 'agent_events', ['task_run_id', 'timestamp'])


def downgrade() -> None:
    op.drop_table('agent_events')
    op.drop_table('task_runs')
