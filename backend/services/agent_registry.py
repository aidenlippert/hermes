"""
Agent Registry Service

Handles agent discovery, registration, and semantic search using pgvector.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, or_, String
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai
import os

from backend.database.models import Agent, AgentStatus, AgentRating
from backend.database.connection import Cache

logger = logging.getLogger(__name__)

# Configure Gemini for embeddings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")
genai.configure(api_key=GOOGLE_API_KEY)


class AgentRegistry:
    """
    Agent Registry with Semantic Search

    Features:
    - Register new agents
    - Semantic search using embeddings
    - Agent discovery and ranking
    - Performance tracking
    - Rating management
    """

    @staticmethod
    async def create_embedding(text: str) -> List[float]:
        """
        Create embedding vector for text using Gemini.

        Args:
            text: Text to embed

        Returns:
            List of floats (1536 dimensions)
        """
        try:
            # Use Gemini's embedding model
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']

        except Exception as e:
            logger.error(f"❌ Embedding creation failed: {e}")
            # Return zero vector as fallback
            return [0.0] * 768  # embedding-001 is 768 dimensions


    @staticmethod
    async def register_agent(
        db: AsyncSession,
        name: str,
        description: str,
        endpoint: str,
        capabilities: List[str],
        category: Optional[str] = None,
        agent_card: Optional[Dict] = None,
        creator_id: Optional[str] = None
    ) -> Agent:
        """
        Register a new agent in the registry.

        Args:
            db: Database session
            name: Agent name
            description: Agent description
            endpoint: A2A endpoint URL
            capabilities: List of capability strings
            category: Category (code, content, data, etc.)
            agent_card: Raw A2A agent card
            creator_id: User ID of creator

        Returns:
            Created Agent object
        """
        logger.info(f"📝 Registering agent: {name}")

        # Create embedding for semantic search
        embedding_text = f"{name}. {description}. Capabilities: {', '.join(capabilities)}"
        embedding = await AgentRegistry.create_embedding(embedding_text)

        # Create agent
        agent = Agent(
            name=name,
            description=description,
            endpoint=endpoint,
            capabilities=capabilities,
            category=category,
            description_embedding=embedding,
            agent_card=agent_card,
            creator_id=creator_id,
            status=AgentStatus.ACTIVE if not creator_id else AgentStatus.PENDING_REVIEW
        )

        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        logger.info(f"✅ Agent registered: {name} (ID: {agent.id})")

        return agent

    @staticmethod
    async def semantic_search(
        db: AsyncSession,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        status: AgentStatus = AgentStatus.ACTIVE
    ) -> List[Agent]:
        """
        Search for agents using semantic similarity or text search.

        Args:
            db: Database session
            query: Search query (natural language)
            limit: Max results
            category: Filter by category
            status: Filter by status

        Returns:
            List of agents ranked by relevance
        """
        logger.info(f"🔍 Agent search: '{query}'")

        # Check if pgvector is available
        USE_PGVECTOR = os.getenv("USE_PGVECTOR", "false").lower() == "true"

        # Build SQL query
        stmt = select(Agent)

        # Filter by status
        stmt = stmt.where(Agent.status == status)

        # Filter by category if specified
        if category:
            stmt = stmt.where(Agent.category == category)

        if USE_PGVECTOR:
            try:
                # Create query embedding for vector search
                query_embedding = await AgentRegistry.create_embedding(query)

                # Order by cosine similarity (pgvector)
                stmt = stmt.order_by(
                    Agent.description_embedding.l2_distance(query_embedding)
                )
            except Exception as e:
                logger.warning(f"⚠️ Vector search failed, using text search: {e}")
                USE_PGVECTOR = False

        if not USE_PGVECTOR:
            # Fallback to text search
            logger.info("   Using text-based search (pgvector disabled)")
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Agent.name.ilike(search_pattern),
                    Agent.description.ilike(search_pattern),
                    Agent.category.ilike(search_pattern)
                )
            )
            stmt = stmt.order_by(Agent.average_rating.desc())

        # Limit results
        stmt = stmt.limit(limit)

        # Execute
        result = await db.execute(stmt)
        agents = result.scalars().all()

        logger.info(f"   ✅ Found {len(agents)} agents")

        # Cache results
        # TODO: Serialize and cache

        return agents

    @staticmethod
    async def search_by_capabilities(
        db: AsyncSession,
        capabilities: List[str],
        limit: int = 10
    ) -> List[Agent]:
        """
        Find agents that match required capabilities.

        Args:
            db: Database session
            capabilities: List of required capabilities
            limit: Max results

        Returns:
            List of matching agents
        """
        logger.info(f"🔍 Capability search: {capabilities}")

        # Build query - find agents with ANY of the requested capabilities
        stmt = select(Agent).where(
            Agent.status == AgentStatus.ACTIVE
        )

        # Check if capabilities array contains any of the requested
        # PostgreSQL JSON array containment
        capability_filters = []
        for cap in capabilities:
            # Use ILIKE with CAST for JSON compatibility
            capability_filters.append(
                func.cast(Agent.capabilities, String).ilike(f'%{cap}%')
            )

        if capability_filters:
            stmt = stmt.where(or_(*capability_filters))

        # Order by performance metrics
        stmt = stmt.order_by(
            Agent.average_rating.desc(),
            Agent.successful_calls.desc()
        )

        stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        agents = result.scalars().all()

        logger.info(f"   ✅ Found {len(agents)} agents")

        return agents

    @staticmethod
    async def get_agent_by_name(db: AsyncSession, name: str) -> Optional[Agent]:
        """Get agent by name"""
        stmt = select(Agent).where(Agent.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_agent_by_id(db: AsyncSession, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        stmt = select(Agent).where(Agent.id == agent_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_agents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        status: AgentStatus = AgentStatus.ACTIVE
    ) -> List[Agent]:
        """
        List all agents with pagination.

        Args:
            db: Database session
            skip: Number to skip (for pagination)
            limit: Max results
            category: Filter by category
            status: Filter by status

        Returns:
            List of agents
        """
        stmt = select(Agent).where(Agent.status == status)

        if category:
            stmt = stmt.where(Agent.category == category)

        stmt = stmt.order_by(Agent.average_rating.desc(), Agent.total_calls.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_agent_metrics(
        db: AsyncSession,
        agent_id: str,
        success: bool,
        duration: float
    ):
        """
        Update agent performance metrics after execution.

        Args:
            db: Database session
            agent_id: Agent ID
            success: Whether execution succeeded
            duration: Execution duration in seconds
        """
        agent = await AgentRegistry.get_agent_by_id(db, agent_id)
        if not agent:
            return

        # Update call counts
        agent.total_calls += 1
        if success:
            agent.successful_calls += 1
        else:
            agent.failed_calls += 1

        # Update average duration (running average)
        if agent.total_calls == 1:
            agent.average_duration = duration
        else:
            agent.average_duration = (
                (agent.average_duration * (agent.total_calls - 1) + duration)
                / agent.total_calls
            )

        await db.commit()

        logger.info(f"📊 Updated metrics for {agent.name}")

    @staticmethod
    async def rate_agent(
        db: AsyncSession,
        agent_id: str,
        user_id: str,
        rating: int,
        review: Optional[str] = None
    ) -> AgentRating:
        """
        Rate an agent (1-5 stars).

        Args:
            db: Database session
            agent_id: Agent ID
            user_id: User ID
            rating: Rating (1-5)
            review: Optional review text

        Returns:
            Created AgentRating
        """
        # Create rating
        agent_rating = AgentRating(
            agent_id=agent_id,
            user_id=user_id,
            rating=rating,
            review=review
        )

        db.add(agent_rating)

        # Update agent's average rating
        agent = await AgentRegistry.get_agent_by_id(db, agent_id)
        if agent:
            # Recalculate average from all ratings
            stmt = select(func.avg(AgentRating.rating)).where(
                AgentRating.agent_id == agent_id
            )
            result = await db.execute(stmt)
            avg_rating = result.scalar()

            agent.average_rating = float(avg_rating) if avg_rating else 0.0

        await db.commit()
        await db.refresh(agent_rating)

        logger.info(f"⭐ Agent {agent_id} rated: {rating}/5")

        return agent_rating
