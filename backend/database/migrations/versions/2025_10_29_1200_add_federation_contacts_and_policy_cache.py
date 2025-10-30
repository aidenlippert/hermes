"""add_federation_contacts_and_policy_cache

Revision ID: federation_contacts_v1
Revises: mesh_protocol_v1
Create Date: 2025-10-29 12:00:00

"""
from alembic import op
import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql  # not used in this revision

# revision identifiers, used by Alembic.
revision = 'federation_contacts_v1'
down_revision = 'mesh_protocol_v1'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # federation_contacts
    op.create_table(
        'federation_contacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('remote_agent_at', sa.String(), nullable=False),
        sa.Column('remote_agent_name', sa.String(), nullable=True),
        sa.Column('remote_domain', sa.String(), nullable=True),
        sa.Column('remote_org_id', sa.String(), nullable=True),
        sa.Column('local_agent_id', sa.String(), nullable=True),
        sa.Column('local_org_id', sa.String(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['remote_org_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['local_agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['local_org_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('remote_agent_at', name='uq_fed_contact_remote_identity'),
    )
    op.create_index('ix_fed_contact_domain_name', 'federation_contacts', ['remote_domain', 'remote_agent_name'], unique=False)
    op.create_index(op.f('ix_federation_contacts_remote_agent_at'), 'federation_contacts', ['remote_agent_at'], unique=False)

    # a2a_policy_cache
    op.create_table(
        'a2a_policy_cache',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_org_id', sa.String(), nullable=True),
        sa.Column('target_org_id', sa.String(), nullable=True),
        sa.Column('source_agent_id', sa.String(), nullable=True),
        sa.Column('target_agent_id', sa.String(), nullable=True),
        sa.Column('allowed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['source_org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_org_id', 'target_org_id', 'source_agent_id', 'target_agent_id', name='uq_a2a_policy_cache_key'),
    )
    op.create_index(op.f('ix_a2a_policy_cache_source_org_id'), 'a2a_policy_cache', ['source_org_id'], unique=False)
    op.create_index(op.f('ix_a2a_policy_cache_target_org_id'), 'a2a_policy_cache', ['target_org_id'], unique=False)
    op.create_index(op.f('ix_a2a_policy_cache_source_agent_id'), 'a2a_policy_cache', ['source_agent_id'], unique=False)
    op.create_index(op.f('ix_a2a_policy_cache_target_agent_id'), 'a2a_policy_cache', ['target_agent_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_a2a_policy_cache_target_agent_id'), table_name='a2a_policy_cache')
    op.drop_index(op.f('ix_a2a_policy_cache_source_agent_id'), table_name='a2a_policy_cache')
    op.drop_index(op.f('ix_a2a_policy_cache_target_org_id'), table_name='a2a_policy_cache')
    op.drop_index(op.f('ix_a2a_policy_cache_source_org_id'), table_name='a2a_policy_cache')
    op.drop_table('a2a_policy_cache')
    op.drop_index('ix_fed_contact_domain_name', table_name='federation_contacts')
    op.drop_index(op.f('ix_federation_contacts_remote_agent_at'), table_name='federation_contacts')
    op.drop_table('federation_contacts')
