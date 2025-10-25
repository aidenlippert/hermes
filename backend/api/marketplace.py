"""
Marketplace API Endpoints

Provides REST API for agent marketplace operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.connection import get_db
from backend.services.auth import get_current_user
from backend.database.models import User
from backend.services.marketplace_service import MarketplaceService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])


# Request/Response Models

class RegisterAgentRequest(BaseModel):
    """Request to register a new agent"""
    agent_url: str
    category: str = "general"
    description: Optional[str] = None


class RateAgentRequest(BaseModel):
    """Request to rate an agent"""
    rating: int  # 1-5 stars
    review: Optional[str] = None


class AgentSearchRequest(BaseModel):
    """Search for agents"""
    query: Optional[str] = None
    category: Optional[str] = None
    limit: int = 10


# Endpoints

@router.post("/register")
async def register_agent(
    request: RegisterAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new agent in the marketplace.

    Requires authentication. The agent will be:
    1. Discovered via A2A protocol
    2. Validated and certified
    3. Added to the marketplace
    """

    logger.info(f"📝 User {current_user.email} registering agent from {request.agent_url}")

    result = await MarketplaceService.register_agent(
        db=db,
        agent_url=request.agent_url,
        submitted_by=current_user.id,
        category=request.category
    )

    if result["success"]:
        return JSONResponse(
            status_code=201,
            content={
                "message": "Agent registered successfully",
                "agent": result["agent"]
            }
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )


@router.get("/agents")
async def list_agents(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(20, description="Max results", le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List agents in the marketplace.

    Public endpoint - no authentication required.
    """

    agents = await MarketplaceService.search_agents(
        db=db,
        query=search,
        category=category,
        limit=limit
    )

    return {
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "endpoint": agent.endpoint,
                "rating": agent.average_rating or 0,
                "total_ratings": agent.total_ratings or 0,
                "is_verified": agent.is_verified
            }
            for agent in agents
        ],
        "count": len(agents)
    }


@router.get("/agents/{agent_id}")
async def get_agent_details(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about an agent.

    Public endpoint - no authentication required.
    """

    stats = await MarketplaceService.get_agent_stats(db, agent_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Agent not found")

    return stats


@router.post("/agents/{agent_id}/rate")
async def rate_agent(
    agent_id: int,
    request: RateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rate and review an agent.

    Requires authentication.
    """

    if request.rating < 1 or request.rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5"
        )

    success = await MarketplaceService.rate_agent(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
        rating=request.rating,
        review=request.review
    )

    if success:
        return {"message": "Rating submitted successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to submit rating"
        )


@router.get("/trending")
async def get_trending_agents(
    limit: int = Query(10, description="Number of results", le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trending agents based on usage and ratings.

    Public endpoint.
    """

    agents = await MarketplaceService.get_trending_agents(db, limit)

    return {
        "trending": [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "rating": agent.average_rating or 0,
                "usage_count": agent.usage_count or 0
            }
            for agent in agents
        ]
    }


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    Get all available agent categories.

    Public endpoint.
    """

    categories = await MarketplaceService.get_categories(db)

    # Add predefined categories
    all_categories = list(set(categories + [
        "general",
        "travel",
        "coding",
        "research",
        "writing",
        "data",
        "finance",
        "health",
        "education",
        "entertainment"
    ]))

    return {"categories": sorted(all_categories)}


@router.post("/search")
async def search_agents(
    request: AgentSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced agent search with filters.

    Public endpoint.
    """

    agents = await MarketplaceService.search_agents(
        db=db,
        query=request.query,
        category=request.category,
        limit=request.limit
    )

    return {
        "results": [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "endpoint": agent.endpoint,
                "rating": agent.average_rating or 0,
                "skills": agent.capabilities if hasattr(agent, 'capabilities') else []
            }
            for agent in agents
        ],
        "count": len(agents)
    }


@router.get("/stats")
async def get_marketplace_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overall marketplace statistics.

    Public endpoint.
    """

    from sqlalchemy import select, func
    from backend.database.models import Agent, AgentRating

    # Total agents
    total_agents = await db.execute(
        select(func.count(Agent.id)).where(Agent.is_active == True)
    )

    # Total ratings
    total_ratings = await db.execute(
        select(func.count(AgentRating.id))
    )

    # Average rating across all agents
    avg_rating = await db.execute(
        select(func.avg(Agent.average_rating)).where(Agent.average_rating != None)
    )

    return {
        "total_agents": total_agents.scalar() or 0,
        "total_ratings": total_ratings.scalar() or 0,
        "average_rating": round(avg_rating.scalar() or 0, 2),
        "categories": await MarketplaceService.get_categories(db)
    }