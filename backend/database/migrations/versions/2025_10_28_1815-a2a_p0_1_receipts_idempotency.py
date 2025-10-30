"""a2a_p0_1_receipts_idempotency

Revision ID: a2a_p0_1
Revises: orgs_acl_v1
Create Date: 2025-10-28 18:15:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a2a_p0_1'
down_revision = 'orgs_acl_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add idempotency_key to a2a_messages
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='a2a_messages' AND column_name='idempotency_key'
            ) THEN
                ALTER TABLE a2a_messages ADD COLUMN idempotency_key VARCHAR;
                CREATE INDEX IF NOT EXISTS ix_a2a_messages_idem ON a2a_messages(idempotency_key);
            END IF;
        END$$;
        """
    )

    # Create receipts table
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='a2a_message_receipts'
            ) THEN
                CREATE TABLE a2a_message_receipts (
                    id VARCHAR PRIMARY KEY,
                    message_id VARCHAR NOT NULL REFERENCES a2a_messages(id) ON DELETE CASCADE,
                    agent_id VARCHAR NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    delivered_at TIMESTAMPTZ,
                    acked_at TIMESTAMPTZ,
                    delivery_attempts INTEGER DEFAULT 0,
                    last_attempt_at TIMESTAMPTZ,
                    CONSTRAINT uq_message_receipt_per_agent UNIQUE (message_id, agent_id)
                );
                CREATE INDEX IF NOT EXISTS ix_a2a_message_receipts_mid ON a2a_message_receipts(message_id);
                CREATE INDEX IF NOT EXISTS ix_a2a_message_receipts_agent ON a2a_message_receipts(agent_id);
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    pass
