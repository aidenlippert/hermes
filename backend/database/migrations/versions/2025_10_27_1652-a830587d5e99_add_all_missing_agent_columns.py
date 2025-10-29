"""add_all_missing_agent_columns

Revision ID: a830587d5e99
Revises: mesh_protocol_v1
Create Date: 2025-10-27 16:52:54.286115

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a830587d5e99'
down_revision = 'mesh_protocol_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add all missing columns to agents table to match the Agent model
    # Ensure enum type exists and matches SQLAlchemy Enum values (lowercase strings)
    # 1) Create type if missing with lowercase values
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agentstatus') THEN
            CREATE TYPE agentstatus AS ENUM ('active', 'inactive', 'pending_review', 'rejected');
        END IF;
    END$$;
    """)

    # 2) If enum exists with uppercase values from older migrations, rename them to lowercase
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'agentstatus' AND e.enumlabel = 'ACTIVE'
        ) THEN
            ALTER TYPE agentstatus RENAME VALUE 'ACTIVE' TO 'active';
        END IF;
        IF EXISTS (
            SELECT 1 FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'agentstatus' AND e.enumlabel = 'INACTIVE'
        ) THEN
            ALTER TYPE agentstatus RENAME VALUE 'INACTIVE' TO 'inactive';
        END IF;
        IF EXISTS (
            SELECT 1 FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'agentstatus' AND e.enumlabel = 'PENDING_REVIEW'
        ) THEN
            ALTER TYPE agentstatus RENAME VALUE 'PENDING_REVIEW' TO 'pending_review';
        END IF;
        IF EXISTS (
            SELECT 1 FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'agentstatus' AND e.enumlabel = 'REJECTED'
        ) THEN
            ALTER TYPE agentstatus RENAME VALUE 'REJECTED' TO 'rejected';
        END IF;
    END$$;
    """)

    # Add columns idempotently (will skip if they already exist)
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS version VARCHAR DEFAULT '1.0.0'")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS description_embedding JSONB")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS successful_calls INTEGER DEFAULT 0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS failed_calls INTEGER DEFAULT 0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS average_duration DOUBLE PRECISION DEFAULT 0.0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS status agentstatus DEFAULT 'pending_review'")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_card JSONB")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS creator_id VARCHAR")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_called TIMESTAMPTZ")

    # Migrate/rename legacy columns safely
    # Move owner_id -> creator_id then drop owner_id if it exists
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='agents' AND column_name='owner_id'
        ) THEN
            EXECUTE 'UPDATE agents SET creator_id = COALESCE(creator_id, owner_id)';
            EXECUTE 'ALTER TABLE agents DROP COLUMN owner_id';
        END IF;
    END$$;
    """)

    # Move average_response_time -> average_duration then drop average_response_time if it exists
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='agents' AND column_name='average_response_time'
        ) THEN
            EXECUTE 'UPDATE agents SET average_duration = COALESCE(average_duration, average_response_time)';
            EXECUTE 'ALTER TABLE agents DROP COLUMN average_response_time';
        END IF;
    END$$;
    """)

    # Clean up deprecated columns if they exist
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS api_key")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS is_active")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS last_active")


def downgrade() -> None:
    # This is complex, leaving as no-op for now
    pass
