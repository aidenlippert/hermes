"""reset_database - Clean slate for fresh migration

Revision ID: 8f4f678fe91e
Revises: None (runs before everything)
Create Date: 2025-10-27 02:40:54.059229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f4f678fe91e'
down_revision = None  # This runs FIRST, before all other migrations
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop all existing tables and types to start fresh"""
    
    # Drop all tables (if they exist) - SQLite doesn't support CASCADE
    op.execute("DROP TABLE IF EXISTS a2a_messages")
    op.execute("DROP TABLE IF EXISTS a2a_conversations")
    op.execute("DROP TABLE IF EXISTS agent_trust_scores")
    op.execute("DROP TABLE IF EXISTS agent_metrics")
    op.execute("DROP TABLE IF EXISTS user_preferences")
    op.execute("DROP TABLE IF EXISTS deliveries")
    op.execute("DROP TABLE IF EXISTS bids")
    op.execute("DROP TABLE IF EXISTS contracts")
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS conversations")
    op.execute("DROP TABLE IF EXISTS agents")
    op.execute("DROP TABLE IF EXISTS users")
    
    # Drop all custom types (if they exist) - only for PostgreSQL
    # SQLite doesn't have custom types, so these will be no-ops
    # op.execute("DROP TYPE IF EXISTS conversationstatus CASCADE")
    # op.execute("DROP TYPE IF EXISTS messagetype CASCADE")
    # op.execute("DROP TYPE IF EXISTS contractstatus CASCADE")
    # op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    # op.execute("DROP TYPE IF EXISTS agentstatus CASCADE")
    # op.execute("DROP TYPE IF EXISTS subscriptiontier CASCADE")
    # op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    
    print("✅ Database cleaned - ready for fresh migrations")


def downgrade() -> None:
    # No downgrade - this is a one-way cleanup
    pass
