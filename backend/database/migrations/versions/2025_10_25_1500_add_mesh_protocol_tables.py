"""add_mesh_protocol_tables

Revision ID: mesh_protocol_v1
Revises: 
Create Date: 2025-10-25 15:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'mesh_protocol_v1'
down_revision = '6bf111ac0804'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (only if they don't exist)
    op.execute("DO $$ BEGIN CREATE TYPE contractstatus AS ENUM ('open', 'bidding', 'awarded', 'in_progress', 'delivered', 'validated', 'settled', 'cancelled', 'failed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE messagetype AS ENUM ('query', 'response', 'notification', 'proposal', 'acceptance', 'rejection', 'termination'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE conversationstatus AS ENUM ('active', 'awaiting_response', 'resolved', 'failed', 'terminated'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Contracts table
    op.create_table(
        'contracts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('intent', sa.String(), nullable=False),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('reward_amount', sa.Float(), nullable=True),
        sa.Column('reward_currency', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('open', 'bidding', 'awarded', 'in_progress', 'delivered', 'validated', 'settled', 'cancelled', 'failed', name='contractstatus'), nullable=False),
        sa.Column('awarded_to', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('awarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['awarded_to'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contracts_intent'), 'contracts', ['intent'], unique=False)
    op.create_index(op.f('ix_contracts_status'), 'contracts', ['status'], unique=False)

    # Bids table
    op.create_table(
        'bids',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('contract_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('eta_seconds', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bids_contract_id'), 'bids', ['contract_id'], unique=False)

    # Deliveries table
    op.create_table(
        'deliveries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('contract_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('validation_score', sa.Float(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deliveries_contract_id'), 'deliveries', ['contract_id'], unique=True)

    # User preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('price_weight', sa.Float(), nullable=True),
        sa.Column('performance_weight', sa.Float(), nullable=True),
        sa.Column('speed_weight', sa.Float(), nullable=True),
        sa.Column('reputation_weight', sa.Float(), nullable=True),
        sa.Column('max_price', sa.Float(), nullable=True),
        sa.Column('min_confidence', sa.Float(), nullable=True),
        sa.Column('max_latency', sa.Float(), nullable=True),
        sa.Column('min_reputation', sa.Float(), nullable=True),
        sa.Column('free_only', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=True)

    # Agent metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('contract_id', sa.String(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=False),
        sa.Column('promised_time', sa.Float(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_metrics_agent_id'), 'agent_metrics', ['agent_id'], unique=False)

    # Agent trust scores table
    op.create_table(
        'agent_trust_scores',
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('latency_score', sa.Float(), nullable=True),
        sa.Column('rating_score', sa.Float(), nullable=True),
        sa.Column('uptime_score', sa.Float(), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=True),
        sa.Column('total_contracts', sa.Integer(), nullable=True),
        sa.Column('successful_contracts', sa.Integer(), nullable=True),
        sa.Column('failed_contracts', sa.Integer(), nullable=True),
        sa.Column('average_execution_time', sa.Float(), nullable=True),
        sa.Column('total_earnings', sa.Float(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('agent_id')
    )
    op.create_index(op.f('ix_agent_trust_scores_trust_score'), 'agent_trust_scores', ['trust_score'], unique=False)

    # A2A Conversations table
    op.create_table(
        'a2a_conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('initiator_id', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'awaiting_response', 'resolved', 'failed', 'terminated', name='conversationstatus'), nullable=False),
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['initiator_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # A2A Messages table
    op.create_table(
        'a2a_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('from_agent_id', sa.String(), nullable=False),
        sa.Column('to_agent_id', sa.String(), nullable=False),
        sa.Column('message_type', postgresql.ENUM('query', 'response', 'notification', 'proposal', 'acceptance', 'rejection', 'termination', name='messagetype'), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('requires_response', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['a2a_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_a2a_messages_conversation_id'), 'a2a_messages', ['conversation_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_a2a_messages_conversation_id'), table_name='a2a_messages')
    op.drop_table('a2a_messages')
    op.drop_table('a2a_conversations')
    op.drop_index(op.f('ix_agent_trust_scores_trust_score'), table_name='agent_trust_scores')
    op.drop_table('agent_trust_scores')
    op.drop_index(op.f('ix_agent_metrics_agent_id'), table_name='agent_metrics')
    op.drop_table('agent_metrics')
    op.drop_index(op.f('ix_user_preferences_user_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index(op.f('ix_deliveries_contract_id'), table_name='deliveries')
    op.drop_table('deliveries')
    op.drop_index(op.f('ix_bids_contract_id'), table_name='bids')
    op.drop_table('bids')
    op.drop_index(op.f('ix_contracts_status'), table_name='contracts')
    op.drop_index(op.f('ix_contracts_intent'), table_name='contracts')
    op.drop_table('contracts')
    
    # Drop enums
    op.execute("DROP TYPE conversationstatus")
    op.execute("DROP TYPE messagetype")
    op.execute("DROP TYPE contractstatus")
