"""add_all_missing_agent_columns

Revision ID: a830587d5e99
Revises: effd783ff13e
Create Date: 2025-10-27 16:52:54.286115

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a830587d5e99'
down_revision = 'effd783ff13e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add all missing columns to agents table to match the Agent model
    op.execute("DO $$ BEGIN CREATE TYPE agentstatus AS ENUM ('pending_review', 'active', 'suspended', 'deprecated'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    op.add_column('agents', sa.Column('version', sa.String(), server_default='1.0.0', nullable=True))
    op.add_column('agents', sa.Column('tags', postgresql.JSON(), server_default='[]', nullable=True))
    op.add_column('agents', sa.Column('description_embedding', postgresql.JSON(), nullable=True))
    op.add_column('agents', sa.Column('successful_calls', sa.Integer(), server_default='0', nullable=True))
    op.add_column('agents', sa.Column('failed_calls', sa.Integer(), server_default='0', nullable=True))
    op.add_column('agents', sa.Column('average_duration', sa.Float(), server_default='0.0', nullable=True))
    op.add_column('agents', sa.Column('status', postgresql.ENUM('pending_review', 'active', 'suspended', 'deprecated', name='agentstatus', create_type=False), server_default='pending_review', nullable=True))
    op.add_column('agents', sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('agents', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('agents', sa.Column('agent_card', postgresql.JSON(), nullable=True))
    op.add_column('agents', sa.Column('creator_id', sa.String(), nullable=True))
    op.add_column('agents', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agents', sa.Column('last_called', sa.DateTime(timezone=True), nullable=True))
    
    # Rename columns to match model
    op.execute("ALTER TABLE agents RENAME COLUMN owner_id TO creator_id_temp")
    op.execute("UPDATE agents SET creator_id = creator_id_temp")
    op.execute("ALTER TABLE agents DROP COLUMN creator_id_temp")
    op.execute("ALTER TABLE agents RENAME COLUMN average_response_time TO average_duration_temp")
    op.execute("UPDATE agents SET average_duration = average_duration_temp")
    op.execute("ALTER TABLE agents DROP COLUMN average_duration_temp")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS api_key")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS is_active")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS last_active")


def downgrade() -> None:
    # This is complex, leaving as no-op for now
    pass
