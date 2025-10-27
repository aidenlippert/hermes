"""rename_endpoint_url_to_endpoint

Revision ID: 47d50c10b0e5
Revises: feb9903a3819
Create Date: 2025-10-27 14:33:13.269057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47d50c10b0e5'
down_revision = 'feb9903a3819'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename endpoint_url to endpoint (if the column exists)
    op.execute("ALTER TABLE agents RENAME COLUMN endpoint_url TO endpoint")


def downgrade() -> None:
    # Rename back
    op.execute("ALTER TABLE agents RENAME COLUMN endpoint TO endpoint_url")
