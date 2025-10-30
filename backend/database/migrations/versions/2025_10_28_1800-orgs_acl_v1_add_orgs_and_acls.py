"""add_orgs_and_acls

Revision ID: orgs_acl_v1
Revises: a830587d5e99
Create Date: 2025-10-28 18:00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'orgs_acl_v1'
down_revision = 'a830587d5e99'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Organizations table
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='organizations'
            ) THEN
                CREATE TABLE organizations (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL UNIQUE,
                    domain VARCHAR UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations(name);
                CREATE INDEX IF NOT EXISTS ix_organizations_domain ON organizations(domain);
            END IF;
        END$$;
        """
    )

    # Organization members
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='organization_members'
            ) THEN
                CREATE TABLE organization_members (
                    id VARCHAR PRIMARY KEY,
                    organization_id VARCHAR NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR NOT NULL DEFAULT 'member',
                    joined_at TIMESTAMPTZ DEFAULT now(),
                    CONSTRAINT uq_org_member UNIQUE (organization_id, user_id)
                );
                CREATE INDEX IF NOT EXISTS ix_org_members_org ON organization_members(organization_id);
                CREATE INDEX IF NOT EXISTS ix_org_members_user ON organization_members(user_id);
            END IF;
        END$$;
        """
    )

    # agents.org_id column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='agents' AND column_name='org_id'
            ) THEN
                ALTER TABLE agents ADD COLUMN org_id VARCHAR;
                ALTER TABLE agents ADD CONSTRAINT fk_agents_org FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE SET NULL;
                CREATE INDEX IF NOT EXISTS ix_agents_org_id ON agents(org_id);
            END IF;
        END$$;
        """
    )

    # A2A org allows
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='a2a_org_allows'
            ) THEN
                CREATE TABLE a2a_org_allows (
                    id VARCHAR PRIMARY KEY,
                    source_org_id VARCHAR NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                    target_org_id VARCHAR NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                    allowed BOOLEAN NOT NULL DEFAULT true,
                    created_by VARCHAR REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    CONSTRAINT uq_a2a_org_allow_pair UNIQUE (source_org_id, target_org_id)
                );
                CREATE INDEX IF NOT EXISTS ix_a2a_org_allows_src ON a2a_org_allows(source_org_id);
                CREATE INDEX IF NOT EXISTS ix_a2a_org_allows_tgt ON a2a_org_allows(target_org_id);
            END IF;
        END$$;
        """
    )

    # A2A agent allows
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables WHERE table_name='a2a_agent_allows'
            ) THEN
                CREATE TABLE a2a_agent_allows (
                    id VARCHAR PRIMARY KEY,
                    source_agent_id VARCHAR NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    target_agent_id VARCHAR NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    allowed BOOLEAN NOT NULL DEFAULT true,
                    created_by VARCHAR REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    CONSTRAINT uq_a2a_agent_allow_pair UNIQUE (source_agent_id, target_agent_id)
                );
                CREATE INDEX IF NOT EXISTS ix_a2a_agent_allows_src ON a2a_agent_allows(source_agent_id);
                CREATE INDEX IF NOT EXISTS ix_a2a_agent_allows_tgt ON a2a_agent_allows(target_agent_id);
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Safe no-op downgrade (data loss risk) – leave structures in place
    pass
