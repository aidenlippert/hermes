"""
Agents API Router

Endpoints for agent-to-agent communication and discovery.

This enables autonomous agent collaboration - agents can discover
and call other agents without human intervention.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import Agent, Task, TaskStatus, AgentStatus, APIKey, User
from backend.middleware.agent_auth import get_current_agent
from backend.middleware.auth import get_current_user
from backend.services.acl_service import ACLService
from backend.services.agent_registry import AgentRegistry
from hermes.protocols.a2a_client import A2AClient
from hermes.conductor.executor_streaming import StreamingExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Initialize A2A client for agent execution
a2a_client = A2AClient()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AgentRegistrationRequest(BaseModel):
    """Request to register a new agent"""
    name: str = Field(..., description="Agent name (must be unique)")
    description: str = Field(..., description="Agent description")
    endpoint: str = Field(..., description="Agent endpoint URL")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities")
    category: Optional[str] = Field(None, description="Agent category")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    is_public: bool = Field(False, description="Allow any agent to call this agent")
    max_calls_per_hour: int = Field(100, description="Rate limit per hour")
    organization_id: Optional[str] = Field(None, description="Organization ID")


class AgentRegistrationResponse(BaseModel):
    """Response from agent registration"""
    agent_id: str
    name: str
    api_key: str
    message: str


class AgentDiscoveryRequest(BaseModel):
    """Request to discover agents by capability"""
    capability: str = Field(..., description="Required capability (semantic search)")
    max_price: Optional[float] = Field(None, description="Maximum price willing to pay")
    min_reputation: float = Field(0.0, description="Minimum reputation score (0.0-1.0)")
    available_only: bool = Field(True, description="Only return currently available agents")
    organization_id: Optional[str] = Field(None, description="Filter by organization")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")


class AgentInfoResponse(BaseModel):
    """Agent information for discovery"""
    id: str
    name: str
    description: str
    capabilities: List[str]
    endpoint: str
    trust_score: float
    is_public: bool
    organization_id: Optional[str]
    status: str


class AgentDiscoveryResponse(BaseModel):
    """Response from agent discovery"""
    agents: List[AgentInfoResponse]
    total: int


class AgentExecutionRequest(BaseModel):
    """Request to execute a task on another agent"""
    agent_id: str = Field(..., description="Target agent ID")
    task: str = Field(..., description="Task description (natural language)")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    max_wait: Optional[float] = Field(None, description="Maximum wait time (seconds)")


class AgentExecutionResponse(BaseModel):
    """Response from agent execution"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_id: str


# ============================================================================
# AGENT REGISTRATION
# ============================================================================

@router.post("/register", response_model=AgentRegistrationResponse)
async def register_agent(
    request: AgentRegistrationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new agent and generate API key.

    This endpoint allows users to register their agents on the Hermes network.
    Each agent receives a unique API key for authentication.

    **Requirements:**
    - User authentication (JWT token)
    - Unique agent name
    - Valid endpoint URL

    **Returns:**
    - Agent ID
    - API key (store this securely - it won't be shown again!)

    **Example:**
    ```json
    {
        "name": "my-image-generator",
        "description": "AI image generation agent using Stable Diffusion",
        "endpoint": "https://my-agent.com/api/v1",
        "capabilities": ["image_generation", "style_transfer"],
        "category": "content",
        "tags": ["images", "ai", "stable-diffusion"],
        "is_public": true,
        "max_calls_per_hour": 100
    }
    ```
    """
    logger.info(f"User {user.email} registering agent: {request.name}")

    try:
        import secrets
        import hashlib

        # Check if agent name already exists
        stmt = select(Agent).where(Agent.name == request.name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.warning(f"Agent name already exists: {request.name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent name '{request.name}' is already taken"
            )

        # Create agent
        agent = Agent(
            name=request.name,
            description=request.description,
            endpoint=request.endpoint,
            capabilities=request.capabilities,
            category=request.category,
            tags=request.tags,
            is_public=request.is_public,
            max_calls_per_hour=request.max_calls_per_hour,
            organization_id=request.organization_id,
            creator_id=user.id,
            status=AgentStatus.ACTIVE,
            trust_score=0.5
        )

        db.add(agent)
        await db.flush()

        # Generate API key
        api_key = f"hsk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Create API key record
        api_key_record = APIKey(
            agent_id=agent.id,
            key=api_key,
            key_hash=key_hash,
            name=f"{request.name}-key",
            is_active=True,
            rate_limit=request.max_calls_per_hour
        )

        db.add(api_key_record)
        await db.commit()
        await db.refresh(agent)

        logger.info(f"Agent registered successfully: {agent.id} ({agent.name})")

        return AgentRegistrationResponse(
            agent_id=agent.id,
            name=agent.name,
            api_key=api_key,
            message="Agent registered successfully. Store your API key securely - it won't be shown again!"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent registration failed: {str(e)}"
        )


# ============================================================================
# AGENT DISCOVERY
# ============================================================================

@router.post("/discover", response_model=AgentDiscoveryResponse)
async def discover_agents(
    request: AgentDiscoveryRequest,
    calling_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Discover agents that match capability requirements.

    This is the foundation of agent autonomy - agents can find other agents
    to collaborate with based on capabilities, reputation, and permissions.

    **Filtering:**
    - Semantic search on capability
    - Price ceiling
    - Reputation threshold
    - Availability status
    - Organization membership
    - ACL permissions (agents can only discover agents they can call)

    **Returns:**
    - List of matching agents sorted by relevance/reputation
    - Only includes agents the calling agent has permission to call

    **Example:**
    ```json
    {
        "capability": "image_generation",
        "max_price": 10.0,
        "min_reputation": 0.7,
        "limit": 5
    }
    ```
    """
    logger.info(
        f"Agent {calling_agent.name} discovering agents with capability: {request.capability}"
    )

    try:
        # Use AgentRegistry for semantic search
        registry = AgentRegistry()
        matching_agents = await registry.search_agents(
            db=db,
            query=request.capability,
            limit=request.limit * 3  # Get more than needed for ACL filtering
        )

        # Filter by status
        if request.available_only:
            matching_agents = [
                a for a in matching_agents
                if a.status == AgentStatus.ACTIVE
            ]

        # Filter by reputation
        matching_agents = [
            a for a in matching_agents
            if (a.trust_score or 0.0) >= request.min_reputation
        ]

        # Filter by organization if specified
        if request.organization_id:
            matching_agents = [
                a for a in matching_agents
                if a.organization_id == request.organization_id
            ]

        # Filter by price if specified
        if request.max_price is not None:
            # TODO: Add pricing field to Agent model
            pass

        # Check ACL permissions for each agent
        accessible_agents = []
        for agent in matching_agents:
            if agent.id == calling_agent.id:
                # Skip self
                continue

            allowed, reason = await ACLService.check_agent_permission(
                source_agent=calling_agent,
                target_agent=agent,
                db=db
            )

            if allowed:
                accessible_agents.append(agent)

        # Limit results
        accessible_agents = accessible_agents[:request.limit]

        # Convert to response model
        agent_responses = [
            AgentInfoResponse(
                id=agent.id,
                name=agent.name,
                description=agent.description or "",
                capabilities=agent.capabilities or [],
                endpoint=agent.endpoint or "",
                trust_score=agent.trust_score or 0.5,
                is_public=agent.is_public if hasattr(agent, 'is_public') else True,
                organization_id=agent.organization_id,
                status=agent.status.value if agent.status else "active"
            )
            for agent in accessible_agents
        ]

        logger.info(
            f"Found {len(agent_responses)} accessible agents for {calling_agent.name}"
        )

        return AgentDiscoveryResponse(
            agents=agent_responses,
            total=len(agent_responses)
        )

    except Exception as e:
        logger.error(f"Agent discovery failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent discovery failed: {str(e)}"
        )


# ============================================================================
# AGENT EXECUTION
# ============================================================================

@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    request: AgentExecutionRequest,
    calling_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a task on another agent.

    This is agent-to-agent communication - the core of autonomous collaboration.
    Agents can call other agents to delegate sub-tasks.

    **Flow:**
    1. Validate calling agent has permission to call target agent (ACL)
    2. Check rate limits
    3. Validate target agent exists and is active
    4. Create task in database
    5. Call target agent via A2A protocol
    6. Return result
    7. Update reputation based on success

    **Permissions:**
    - Agent-level explicit allow (highest priority)
    - Organization-level allow
    - Target agent is public
    - Default deny

    **Raises:**
    - 403: Permission denied
    - 404: Target agent not found
    - 429: Rate limit exceeded
    - 500: Execution failed

    **Example:**
    ```json
    {
        "agent_id": "image-gen-1",
        "task": "Generate a realistic sunset image",
        "context": {
            "style": "realistic",
            "size": "1024x1024",
            "format": "png"
        }
    }
    ```
    """
    logger.info(
        f"Agent {calling_agent.name} executing task on agent {request.agent_id}"
    )

    try:
        # Get target agent
        stmt = select(Agent).where(Agent.id == request.agent_id)
        result = await db.execute(stmt)
        target_agent = result.scalar_one_or_none()

        if not target_agent:
            logger.warning(f"Target agent not found: {request.agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {request.agent_id} not found"
            )

        # Check if target agent is active
        if target_agent.status != AgentStatus.ACTIVE:
            logger.warning(f"Target agent is not active: {request.agent_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {request.agent_id} is {target_agent.status}"
            )

        # Check ACL permissions
        allowed, reason = await ACLService.check_agent_permission(
            source_agent=calling_agent,
            target_agent=target_agent,
            db=db
        )

        if not allowed:
            logger.warning(
                f"Permission denied: {calling_agent.name} → {target_agent.name}. "
                f"Reason: {reason}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {reason}"
            )

        # Create task in database
        task = Task(
            user_id=calling_agent.created_by if hasattr(calling_agent, 'created_by') else None,
            agent_id=target_agent.id,
            query=request.task,
            context=request.context,
            status=TaskStatus.IN_PROGRESS
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Task created: {task.id}")

        # Execute task via A2A protocol
        try:
            # Call target agent
            task_result = await a2a_client.send_task(
                agent_endpoint=target_agent.endpoint,
                task_description=request.task,
                context=request.context,
                task_id=task.id
            )

            # Update task with result
            task.status = TaskStatus.COMPLETED
            task.result = task_result
            await db.commit()

            logger.info(f"Task {task.id} completed successfully")

            # TODO: Update agent reputation
            # await reputation_service.update_after_execution(
            #     agent_id=target_agent.id,
            #     success=True,
            #     latency=...,
            #     db=db
            # )

            return AgentExecutionResponse(
                task_id=task.id,
                status="completed",
                result=task_result,
                agent_id=target_agent.id
            )

        except Exception as e:
            # Update task with error
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}
            await db.commit()

            logger.error(f"Task {task.id} failed: {e}")

            # TODO: Update agent reputation (negative)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent execution failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent execution endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


# ============================================================================
# AGENT INFO
# ============================================================================

@router.get("/{agent_id}", response_model=AgentInfoResponse)
async def get_agent_info(
    agent_id: str,
    calling_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about a specific agent.

    Returns agent details if calling agent has permission to see it.

    **Permissions:**
    - Same as execution permissions (ACL check)

    **Returns:**
    - Agent information including capabilities, reputation, etc.

    **Raises:**
    - 403: Permission denied
    - 404: Agent not found
    """
    logger.info(f"Agent {calling_agent.name} requesting info for agent {agent_id}")

    # Get target agent
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    target_agent = result.scalar_one_or_none()

    if not target_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    # Check ACL permissions
    allowed, reason = await ACLService.check_agent_permission(
        source_agent=calling_agent,
        target_agent=target_agent,
        db=db
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {reason}"
        )

    return AgentInfoResponse(
        id=target_agent.id,
        name=target_agent.name,
        description=target_agent.description or "",
        capabilities=target_agent.capabilities or [],
        endpoint=target_agent.endpoint or "",
        trust_score=target_agent.trust_score or 0.5,
        is_public=target_agent.is_public if hasattr(target_agent, 'is_public') else True,
        organization_id=target_agent.organization_id,
        status=target_agent.status.value if target_agent.status else "active"
    )
