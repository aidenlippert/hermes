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

    -- A2A Agent Card
    agent_card JSONB NOT NULL,

    -- Capabilities
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Metadata
    version VARCHAR(50),
    framework VARCHAR(100),  -- langchain, crewai, custom, etc
    trust_score DECIMAL(3,2) DEFAULT 0.0,

    -- Pricing
    base_cost_per_call DECIMAL(10,4) DEFAULT 0.0,
    currency VARCHAR(10) DEFAULT 'USD',

    -- Stats
    total_calls BIGINT DEFAULT 0,
    successful_calls BIGINT DEFAULT 0,
    failed_calls BIGINT DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0.0,
    avg_latency_ms INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexing
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'suspended', 'deleted'))
);

CREATE INDEX idx_agents_owner ON agents(owner_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_capabilities ON agents USING GIN (capabilities);
CREATE INDEX idx_agents_trust_score ON agents(trust_score DESC);
CREATE INDEX idx_agents_framework ON agents(framework);

-- Agent Capabilities Table (for better querying)
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

CREATE INDEX idx_capability_name ON agent_capabilities(capability_name);
CREATE INDEX idx_capability_agent ON agent_capabilities(agent_id);

-- Agent API Calls (metering)
CREATE TABLE IF NOT EXISTS agent_api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id VARCHAR(255) UNIQUE NOT NULL,

    -- Who
    caller_agent_id VARCHAR(255),  -- can be NULL for human-initiated
    callee_agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id),
    caller_user_id VARCHAR(255),  -- if human

    -- What
    capability VARCHAR(255) NOT NULL,
    task_type VARCHAR(100),

    -- When
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    -- How
    status VARCHAR(50) NOT NULL,  -- success, error, timeout
    error_message TEXT,

    -- Cost
    cost DECIMAL(10,4) DEFAULT 0.0,
    currency VARCHAR(10) DEFAULT 'USD',

    -- Data
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_call_status CHECK (status IN ('pending', 'success', 'error', 'timeout', 'cancelled'))
);

CREATE INDEX idx_api_calls_callee ON agent_api_calls(callee_agent_id);
CREATE INDEX idx_api_calls_caller_agent ON agent_api_calls(caller_agent_id);
CREATE INDEX idx_api_calls_caller_user ON agent_api_calls(caller_user_id);
CREATE INDEX idx_api_calls_status ON agent_api_calls(status);
CREATE INDEX idx_api_calls_created_at ON agent_api_calls(created_at DESC);

-- Agent Reviews
CREATE TABLE IF NOT EXISTS agent_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    reviewer_user_id VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    helpful_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(agent_id, reviewer_user_id)
);

CREATE INDEX idx_reviews_agent ON agent_reviews(agent_id);
CREATE INDEX idx_reviews_rating ON agent_reviews(rating DESC);

-- Agent Conversations (A2A messaging)
CREATE TABLE IF NOT EXISTS agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) UNIQUE NOT NULL,

    -- Participants
    initiator_agent_id VARCHAR(255) NOT NULL,
    target_agent_id VARCHAR(255) NOT NULL,

    -- Context
    topic VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',

    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,

    -- Metadata
    message_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_conv_status CHECK (status IN ('active', 'completed', 'failed', 'timeout'))
);

CREATE INDEX idx_conversations_initiator ON agent_conversations(initiator_agent_id);
CREATE INDEX idx_conversations_target ON agent_conversations(target_agent_id);
CREATE INDEX idx_conversations_status ON agent_conversations(status);

-- Agent Messages
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    conversation_id VARCHAR(255) NOT NULL REFERENCES agent_conversations(conversation_id) ON DELETE CASCADE,

    -- Who
    from_agent_id VARCHAR(255) NOT NULL,
    to_agent_id VARCHAR(255) NOT NULL,

    -- What
    message_type VARCHAR(50) NOT NULL,  -- request, response, event, notification
    content JSONB NOT NULL,
    requires_response BOOLEAN DEFAULT false,

    -- When
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_msg_type CHECK (message_type IN ('request', 'response', 'event', 'notification', 'error'))
);

CREATE INDEX idx_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX idx_messages_from ON agent_messages(from_agent_id);
CREATE INDEX idx_messages_to ON agent_messages(to_agent_id);
CREATE INDEX idx_messages_sent_at ON agent_messages(sent_at DESC);

-- Update triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON agent_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
