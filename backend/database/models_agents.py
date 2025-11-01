"""
Agent database models for ASTRAEUS Network
A2A Protocol compliant agent storage
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str
    description: Optional[str] = None
    confidence: float = 1.0
    cost_per_call: float = 0.0
    avg_latency_ms: int = 0


class AgentCard(BaseModel):
    """A2A Protocol Agent Card"""
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[Dict[str, Any]]
    endpoint: str
    authentication: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Agent(BaseModel):
    """Agent model"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agent_id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    endpoint: str
    status: str = "active"

    agent_card: Dict[str, Any]
    capabilities: List[Dict[str, Any]] = Field(default_factory=list)

    version: Optional[str] = None
    framework: Optional[str] = None
    trust_score: float = 0.0

    base_cost_per_call: float = 0.0
    currency: str = "USD"

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_revenue: float = 0.0
    avg_latency_ms: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)


class AgentAPICall(BaseModel):
    """API call metering"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    call_id: str

    caller_agent_id: Optional[str] = None
    callee_agent_id: str
    caller_user_id: Optional[str] = None

    capability: str
    task_type: Optional[str] = None

    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    status: str
    error_message: Optional[str] = None

    cost: float = 0.0
    currency: str = "USD"

    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


async def create_agent(pool, agent: Agent) -> Agent:
    """Create new agent in database"""
    query = """
    INSERT INTO agents (
        agent_id, name, description, owner_id, endpoint, status,
        agent_card, capabilities, version, framework, trust_score,
        base_cost_per_call, currency
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    RETURNING *
    """

    import json
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            query,
            agent.agent_id, agent.name, agent.description, agent.owner_id,
            agent.endpoint, agent.status,
            json.dumps(agent.agent_card), json.dumps(agent.capabilities),
            agent.version, agent.framework, agent.trust_score,
            agent.base_cost_per_call, agent.currency
        )

    return Agent(**dict(row))


async def get_agent(pool, agent_id: str) -> Optional[Agent]:
    """Get agent by ID"""
    query = "SELECT * FROM agents WHERE agent_id = $1"

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, agent_id)

    if row:
        return Agent(**dict(row))
    return None


async def list_agents(
    pool,
    status: str = "active",
    framework: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Agent]:
    """List agents with filters"""
    conditions = ["status = $1"]
    params = [status]

    if framework:
        conditions.append(f"framework = ${len(params) + 1}")
        params.append(framework)

    query = f"""
    SELECT * FROM agents
    WHERE {" AND ".join(conditions)}
    ORDER BY created_at DESC
    LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
    """

    params.extend([limit, offset])

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [Agent(**dict(row)) for row in rows]


async def search_agents_by_capability(
    pool,
    capability: str,
    limit: int = 10
) -> List[Agent]:
    """Search agents by capability"""
    query = """
    SELECT DISTINCT a.* FROM agents a
    JOIN agent_capabilities ac ON a.agent_id = ac.agent_id
    WHERE ac.capability_name = $1 AND a.status = 'active'
    ORDER BY ac.confidence DESC, a.trust_score DESC
    LIMIT $2
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, capability, limit)

    return [Agent(**dict(row)) for row in rows]


async def record_api_call(pool, call: AgentAPICall) -> AgentAPICall:
    """Record API call for metering"""
    query = """
    INSERT INTO agent_api_calls (
        call_id, caller_agent_id, callee_agent_id, caller_user_id,
        capability, task_type, started_at, completed_at, duration_ms,
        status, error_message, cost, currency,
        request_size_bytes, response_size_bytes, metadata
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
    RETURNING *
    """

    import json
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            query,
            call.call_id, call.caller_agent_id, call.callee_agent_id, call.caller_user_id,
            call.capability, call.task_type, call.started_at, call.completed_at, call.duration_ms,
            call.status, call.error_message, call.cost, call.currency,
            call.request_size_bytes, call.response_size_bytes, json.dumps(call.metadata)
        )

    # Update agent stats
    await update_agent_stats(pool, call.callee_agent_id, call)

    return AgentAPICall(**dict(row))


async def update_agent_stats(pool, agent_id: str, call: AgentAPICall):
    """Update agent statistics"""
    query = """
    UPDATE agents SET
        total_calls = total_calls + 1,
        successful_calls = CASE WHEN $2 = 'success' THEN successful_calls + 1 ELSE successful_calls END,
        failed_calls = CASE WHEN $2 != 'success' THEN failed_calls + 1 ELSE failed_calls END,
        total_revenue = total_revenue + $3,
        last_seen_at = CURRENT_TIMESTAMP
    WHERE agent_id = $1
    """

    async with pool.acquire() as conn:
        await conn.execute(query, agent_id, call.status, call.cost)
