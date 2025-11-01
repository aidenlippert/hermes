"""
Agent Database Connection - AsyncPG Pool

Separate connection pool for agent registry using raw asyncpg for better performance.
"""

import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

agent_pool = None


async def init_agent_db():
    """Initialize asyncpg connection pool for agent registry"""
    global agent_pool

    logger.info("🔧 Initializing agent database pool...")

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://hermes:hermes_dev_password@localhost:5432/hermes"
    )

    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    try:
        agent_pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )

        async with agent_pool.acquire() as conn:
            await conn.execute("SELECT 1")

        logger.info("✅ Agent database pool created")

        await init_agent_schema()

    except Exception as e:
        logger.error(f"❌ Agent database init failed: {e}")
        agent_pool = None


async def init_agent_schema():
    """Initialize agent database schema"""
    global agent_pool

    if not agent_pool:
        logger.warning("⚠️ Agent pool not available, skipping schema init")
        return

    logger.info("🔧 Initializing agent schema...")

    schema_sql = """
-- ASTRAEUS Agent Registry Schema
-- A2A Protocol Compliant Agent Storage

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id VARCHAR(255) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',

    agent_card JSONB NOT NULL,
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,

    version VARCHAR(50),
    framework VARCHAR(100),
    trust_score DECIMAL(3,2) DEFAULT 0.0,

    base_cost_per_call DECIMAL(10,4) DEFAULT 0.0,
    currency VARCHAR(10) DEFAULT 'USD',

    total_calls BIGINT DEFAULT 0,
    successful_calls BIGINT DEFAULT 0,
    failed_calls BIGINT DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0.0,
    avg_latency_ms INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'suspended', 'deleted'))
);

CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON agents USING GIN (capabilities);
CREATE INDEX IF NOT EXISTS idx_agents_trust_score ON agents(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_agents_framework ON agents(framework);

CREATE TABLE IF NOT EXISTS agent_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    capability_name VARCHAR(255) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    cost_per_call DECIMAL(10,4) DEFAULT 0.0,
    avg_latency_ms INTEGER DEFAULT 0,
    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(agent_id, capability_name)
);

CREATE INDEX IF NOT EXISTS idx_capability_name ON agent_capabilities(capability_name);
CREATE INDEX IF NOT EXISTS idx_capability_agent ON agent_capabilities(agent_id);

CREATE TABLE IF NOT EXISTS agent_api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id VARCHAR(255) UNIQUE NOT NULL,

    caller_agent_id VARCHAR(255),
    callee_agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id),
    caller_user_id VARCHAR(255),

    capability VARCHAR(255) NOT NULL,
    task_type VARCHAR(100),

    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    status VARCHAR(50) NOT NULL,
    error_message TEXT,

    cost DECIMAL(10,4) DEFAULT 0.0,
    currency VARCHAR(10) DEFAULT 'USD',

    request_size_bytes INTEGER,
    response_size_bytes INTEGER,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_call_status CHECK (status IN ('pending', 'success', 'error', 'timeout', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_api_calls_callee ON agent_api_calls(callee_agent_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_caller_agent ON agent_api_calls(caller_agent_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_caller_user ON agent_api_calls(caller_user_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_status ON agent_api_calls(status);
CREATE INDEX IF NOT EXISTS idx_api_calls_created_at ON agent_api_calls(created_at DESC);

CREATE TABLE IF NOT EXISTS agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) UNIQUE NOT NULL,

    initiator_agent_id VARCHAR(255) NOT NULL,
    target_agent_id VARCHAR(255) NOT NULL,

    topic VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,

    message_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_conv_status CHECK (status IN ('active', 'completed', 'failed', 'timeout'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_initiator ON agent_conversations(initiator_agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_target ON agent_conversations(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON agent_conversations(status);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""

    try:
        async with agent_pool.acquire() as conn:
            await conn.execute(schema_sql)
        logger.info("✅ Agent schema initialized")
    except Exception as e:
        logger.error(f"❌ Agent schema init failed: {e}")


async def close_agent_db():
    """Close agent database pool"""
    global agent_pool

    if agent_pool:
        await agent_pool.close()
        logger.info("👋 Agent database pool closed")


def get_agent_pool():
    """Get agent database pool"""
    return agent_pool
