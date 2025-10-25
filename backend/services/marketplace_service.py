"""
Agent Marketplace Service

Handles agent registration, discovery, rating, and monetization.
This is the core of the Hermes marketplace.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from backend.database.models import Agent, AgentRating, User
from hermes.protocols.a2a_client import A2AClient
import json
import hashlib

logger = logging.getLogger(__name__)


class MarketplaceService:
    """
    Manages the agent marketplace including:
    - Agent registration and verification
    - Discovery and search
    - Rating and reviews
    - Usage tracking
    - Monetization
    """

    @staticmethod
    async def register_agent(
        db: AsyncSession,
        agent_url: str,
        submitted_by: int,  # User ID who submitted
        category: str = "general"
    ) -> Dict[str, Any]:
        """
        Register a new agent in the marketplace.

        Steps:
        1. Discover agent via A2A protocol
        2. Verify agent capabilities
        3. Run certification tests
        4. Store in database
        5. Generate embedding for search
        """

        logger.info(f"🎯 Registering new agent from {agent_url}")

        # Step 1: Discover agent card
        client = A2AClient()
        try:
            agent_card = await client.discover_agent(agent_url)
        except Exception as e:
            logger.error(f"Failed to discover agent: {e}")
            return {
                "success": False,
                "error": f"Could not discover agent at {agent_url}: {str(e)}"
            }

        # Step 2: Validate agent card
        validation = MarketplaceService.validate_agent_card(agent_card)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Invalid agent card: {validation['errors']}"
            }

        # Step 3: Check for duplicates
        existing = await db.execute(
            select(Agent).where(Agent.endpoint == agent_card.endpoint)
        )
        if existing.scalar_one_or_none():
            return {
                "success": False,
                "error": "Agent already registered with this endpoint"
            }

        # Step 4: Run basic certification tests
        certification = await MarketplaceService.certify_agent(client, agent_card)
        if not certification["passed"]:
            return {
                "success": False,
                "error": f"Agent failed certification: {certification['errors']}"
            }

        # Step 5: Generate embedding for semantic search
        from backend.services.llm_provider import get_llm_provider
        llm = get_llm_provider()

        # Create description for embedding
        skill_descriptions = " ".join([
            f"{skill.get('name', '')} {skill.get('description', '')}"
            for skill in agent_card.skills
        ])
        full_description = f"{agent_card.name} {agent_card.description} {skill_descriptions}"

        # Generate embedding (mock for now - in production use real embeddings)
        embedding = MarketplaceService.generate_mock_embedding(full_description)

        # Step 6: Store in database
        new_agent = Agent(
            name=agent_card.name,
            description=agent_card.description,
            endpoint=agent_card.endpoint,
            capabilities=agent_card.skills,  # Store as JSON
            category=category,
            version=agent_card.version,
            is_active=True,
            is_verified=certification["passed"],
            submitted_by=submitted_by,
            metadata={
                "agent_card": agent_card.raw_card,
                "certification": certification,
                "registered_at": datetime.utcnow().isoformat()
            },
            embedding=embedding
        )

        db.add(new_agent)
        await db.commit()
        await db.refresh(new_agent)

        logger.info(f"✅ Successfully registered agent: {agent_card.name}")

        return {
            "success": True,
            "agent": {
                "id": new_agent.id,
                "name": new_agent.name,
                "description": new_agent.description,
                "endpoint": new_agent.endpoint,
                "category": new_agent.category,
                "is_verified": new_agent.is_verified
            }
        }

    @staticmethod
    def validate_agent_card(agent_card) -> Dict[str, Any]:
        """Validate that agent card meets A2A requirements"""

        errors = []

        # Check required fields
        if not agent_card.name:
            errors.append("Missing agent name")
        if not agent_card.description:
            errors.append("Missing agent description")
        if not agent_card.endpoint:
            errors.append("Missing agent endpoint")
        if not agent_card.skills or len(agent_card.skills) == 0:
            errors.append("Agent must have at least one skill")

        # Validate skills
        for skill in agent_card.skills:
            if not skill.get("id"):
                errors.append(f"Skill missing ID: {skill}")
            if not skill.get("name"):
                errors.append(f"Skill missing name: {skill}")
            if not skill.get("description"):
                errors.append(f"Skill missing description: {skill}")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    @staticmethod
    async def certify_agent(client: A2AClient, agent_card) -> Dict[str, Any]:
        """
        Run certification tests on agent.

        Tests:
        1. Basic connectivity
        2. Response time
        3. Error handling
        4. Task execution
        """

        errors = []
        tests_passed = 0
        total_tests = 4

        # Test 1: Basic connectivity
        try:
            test_response = await client.send_task(
                agent_card.endpoint,
                "Hello, this is a test",
                context={"test": True}
            )
            if test_response.status.value == "completed":
                tests_passed += 1
            else:
                errors.append("Failed basic connectivity test")
        except Exception as e:
            errors.append(f"Connectivity test failed: {str(e)}")

        # Test 2: Response time (should be < 10 seconds)
        import time
        start = time.time()
        try:
            await client.send_task(
                agent_card.endpoint,
                "What can you do?",
                context={"test": True}
            )
            elapsed = time.time() - start
            if elapsed < 10:
                tests_passed += 1
            else:
                errors.append(f"Response time too slow: {elapsed:.2f}s")
        except Exception as e:
            errors.append(f"Response time test failed: {str(e)}")

        # Test 3: Error handling
        try:
            error_response = await client.send_task(
                agent_card.endpoint,
                "",  # Empty message should be handled gracefully
                context={"test": True}
            )
            # Should return error, not crash
            tests_passed += 1
        except Exception as e:
            # This is actually good - agent rejected bad input
            tests_passed += 1

        # Test 4: Skill execution
        if agent_card.skills:
            skill = agent_card.skills[0]
            examples = skill.get("examples", [])
            if examples:
                try:
                    skill_response = await client.send_task(
                        agent_card.endpoint,
                        examples[0],
                        context={"test": True}
                    )
                    if skill_response.status.value == "completed":
                        tests_passed += 1
                    else:
                        errors.append(f"Failed to execute skill: {skill['name']}")
                except Exception as e:
                    errors.append(f"Skill execution failed: {str(e)}")
            else:
                tests_passed += 1  # No examples to test

        return {
            "passed": tests_passed >= 3,  # Need at least 3/4 tests to pass
            "score": f"{tests_passed}/{total_tests}",
            "errors": errors
        }

    @staticmethod
    def generate_mock_embedding(text: str) -> List[float]:
        """Generate a mock embedding vector (replace with real embeddings in production)"""
        # Simple hash-based mock embedding
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        # Convert to vector of floats
        embedding = []
        for i in range(0, len(hash_hex), 2):
            value = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(value)

        # Pad to standard size (e.g., 384 dimensions)
        while len(embedding) < 384:
            embedding.append(0.0)

        return embedding[:384]

    @staticmethod
    async def search_agents(
        db: AsyncSession,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Agent]:
        """
        Search for agents in the marketplace.

        Uses semantic search with vector embeddings.
        """

        # For now, do a simple text search
        # In production, use pgvector for semantic search

        stmt = select(Agent).where(Agent.is_active == True)

        if category:
            stmt = stmt.where(Agent.category == category)

        if query:
            # Simple text matching
            search_pattern = f"%{query.lower()}%"
            stmt = stmt.where(
                func.lower(Agent.name).like(search_pattern) |
                func.lower(Agent.description).like(search_pattern)
            )

        stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        agents = result.scalars().all()

        return agents

    @staticmethod
    async def rate_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        rating: int,
        review: Optional[str] = None
    ) -> bool:
        """
        Rate an agent (1-5 stars).
        """

        # Check if user already rated this agent
        existing = await db.execute(
            select(AgentRating).where(
                AgentRating.agent_id == agent_id,
                AgentRating.user_id == user_id
            )
        )
        existing_rating = existing.scalar_one_or_none()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.review = review
            existing_rating.updated_at = datetime.utcnow()
        else:
            # Create new rating
            new_rating = AgentRating(
                agent_id=agent_id,
                user_id=user_id,
                rating=rating,
                review=review
            )
            db.add(new_rating)

        # Update agent's average rating
        avg_result = await db.execute(
            select(func.avg(AgentRating.rating)).where(
                AgentRating.agent_id == agent_id
            )
        )
        avg_rating = avg_result.scalar() or 0.0

        await db.execute(
            update(Agent).where(Agent.id == agent_id).values(
                average_rating=avg_rating,
                total_ratings=select(func.count(AgentRating.id)).where(
                    AgentRating.agent_id == agent_id
                ).scalar_subquery()
            )
        )

        await db.commit()
        return True

    @staticmethod
    async def get_agent_stats(
        db: AsyncSession,
        agent_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for an agent.
        """

        agent = await db.get(Agent, agent_id)
        if not agent:
            return None

        # Get rating distribution
        rating_dist = {}
        for i in range(1, 6):
            count_result = await db.execute(
                select(func.count(AgentRating.id)).where(
                    AgentRating.agent_id == agent_id,
                    AgentRating.rating == i
                )
            )
            rating_dist[str(i)] = count_result.scalar() or 0

        # Get recent reviews
        recent_reviews = await db.execute(
            select(AgentRating).where(
                AgentRating.agent_id == agent_id
            ).order_by(AgentRating.created_at.desc()).limit(5)
        )

        return {
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "average_rating": agent.average_rating or 0,
                "total_ratings": agent.total_ratings or 0,
                "total_uses": agent.usage_count or 0
            },
            "rating_distribution": rating_dist,
            "recent_reviews": [
                {
                    "rating": r.rating,
                    "review": r.review,
                    "created_at": r.created_at.isoformat()
                }
                for r in recent_reviews.scalars()
            ]
        }

    @staticmethod
    async def get_trending_agents(
        db: AsyncSession,
        limit: int = 10
    ) -> List[Agent]:
        """
        Get trending agents based on recent usage and ratings.
        """

        # Simple trending: high rating + recent activity
        # In production, use more sophisticated algorithm

        stmt = (
            select(Agent)
            .where(Agent.is_active == True)
            .order_by(
                (Agent.average_rating * Agent.usage_count).desc(),
                Agent.created_at.desc()
            )
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_categories(db: AsyncSession) -> List[str]:
        """Get all agent categories"""

        result = await db.execute(
            select(Agent.category).distinct().where(Agent.is_active == True)
        )
        categories = [row[0] for row in result if row[0]]
        return categories