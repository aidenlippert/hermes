"""fix_userrole_enum_values

Revision ID: 5eab1991a14d
Revises: a1afb20e28ab
Create Date: 2025-10-30 02:43:35.828297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5eab1991a14d'
down_revision = 'a1afb20e28ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix UserRole enum: change 'agent_developer' to 'agent_creator'
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'admin', 'agent_creator')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole")
    op.execute("DROP TYPE userrole_old")


def downgrade() -> None:
    # Revert back to agent_developer
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'agent_developer', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole")
    op.execute("DROP TYPE userrole_old")
