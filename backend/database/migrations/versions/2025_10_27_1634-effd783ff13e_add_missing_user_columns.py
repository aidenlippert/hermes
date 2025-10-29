"""add_missing_user_columns

Revision ID: effd783ff13e
Revises: mesh_protocol_v1
Create Date: 2025-10-27 16:34:01.161192

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'effd783ff13e'
down_revision = 'mesh_protocol_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('users', sa.Column('total_spent', sa.Float(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'total_spent')
    op.drop_column('users', 'is_verified')
