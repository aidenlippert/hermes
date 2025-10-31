"""
Agent Authentication Middleware

Separate authentication system for AI agents (vs. human users).

Agents use API keys (long-lived, revocable) instead of JWT tokens.
This enables autonomous operation without session management.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import Agent, APIKey, AgentStatus

logger = logging.getLogger(__name__)


async def get_current_agent(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """
    Get current agent from API key.

    Agents authenticate using:
    - Header: X-API-Key: {api_key}
    - Header: X-Agent-ID: {agent_id}

    Usage in endpoints:
        @app.post("/agents/discover")
        async def discover_agents(agent: Agent = Depends(get_current_agent)):
            # agent is authenticated
            ...

    Raises:
        HTTPException(401): If authentication fails
        HTTPException(403): If agent is inactive
    """
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    agent_id = request.headers.get("X-Agent-ID")

    if not api_key:
        logger.warning("Missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if not agent_id:
        logger.warning("Missing X-Agent-ID header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing agent ID. Include X-Agent-ID header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Verify API key
    stmt = select(APIKey).where(
        APIKey.key_hash == api_key,
        APIKey.is_active == True
    )
    result = await db.execute(stmt)
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        logger.warning(f"Invalid API key for agent {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Verify agent_id matches API key
    if api_key_obj.agent_id != agent_id:
        logger.warning(f"Agent ID mismatch: {agent_id} != {api_key_obj.agent_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent ID does not match API key"
        )

    # Get agent
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        logger.error(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found"
        )

    # Check agent status
    if agent.status != AgentStatus.ACTIVE:
        logger.warning(f"Inactive agent attempted access: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Agent is {agent.status}. Only active agents can make requests."
        )

    # Store agent in request state for later use
    request.state.agent = agent

    logger.debug(f"Agent authenticated: {agent.name} ({agent.id})")
    return agent


async def get_current_agent_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[Agent]:
    """
    Optional agent authentication.

    Returns agent if valid API key provided, None otherwise.
    Useful for endpoints that can work with or without agent auth.

    Usage:
        @app.get("/some-endpoint")
        async def endpoint(agent: Optional[Agent] = Depends(get_current_agent_optional)):
            if agent:
                # Authenticated agent
                pass
            else:
                # Public access
                pass
    """
    try:
        return await get_current_agent(request, db)
    except HTTPException:
        return None


def require_agent_capabilities(required_capabilities: list):
    """
    Decorator to require specific agent capabilities.

    Usage:
        @app.post("/some-endpoint")
        @require_agent_capabilities(["image_generation", "image_editing"])
        async def endpoint(agent: Agent = Depends(get_current_agent)):
            # Agent has required capabilities
            pass

    Args:
        required_capabilities: List of capability strings

    Returns:
        Dependency function
    """
    async def capability_checker(agent: Agent = Depends(get_current_agent)):
        agent_capabilities = agent.capabilities or []

        # Check if agent has all required capabilities
        missing = [cap for cap in required_capabilities if cap not in agent_capabilities]

        if missing:
            logger.warning(
                f"Agent {agent.id} missing capabilities: {missing}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Agent missing required capabilities: {', '.join(missing)}"
            )

        return agent

    return capability_checker
