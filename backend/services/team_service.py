"""
Agent Team Service

Manages persistent agent teams and collaborative sessions.

Sprint 9: Advanced Collaboration
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent
from backend.database.models_collaboration import (
    AgentTeam,
    CollaborativeSession,
    AgentRelationship
)

logger = logging.getLogger(__name__)


class TeamService:
    """
    Agent team management service.

    Features:
    - Create and manage persistent agent teams
    - Track team performance and dynamics
    - Execute team-based orchestrations
    - Analyze agent relationships and compatibility
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_team(
        self,
        name: str,
        agent_ids: List[str],
        owner_id: str,
        description: Optional[str] = None,
        collaboration_pattern: str = "hierarchical",
        leader_agent_id: Optional[str] = None,
        is_public: bool = False
    ) -> AgentTeam:
        """
        Create new agent team.

        Args:
            name: Team name
            agent_ids: List of agent IDs
            owner_id: Team owner user ID
            description: Optional description
            collaboration_pattern: hierarchical, sequential, parallel
            leader_agent_id: Optional team leader
            is_public: Whether team is publicly visible

        Returns:
            Created AgentTeam
        """
        # Validate agents exist
        for agent_id in agent_ids:
            agent = await self.db.get(Agent, agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")

        # Validate leader if specified
        if leader_agent_id and leader_agent_id not in agent_ids:
            raise ValueError("Leader must be a team member")

        team = AgentTeam(
            name=name,
            description=description,
            owner_id=owner_id,
            agent_ids=agent_ids,
            leader_agent_id=leader_agent_id,
            collaboration_pattern=collaboration_pattern,
            is_public=is_public
        )

        self.db.add(team)
        await self.db.commit()

        logger.info(f"Created team: {name} with {len(agent_ids)} agents")

        return team

    async def get_team(self, team_id: str) -> AgentTeam:
        """Get team by ID"""
        team = await self.db.get(AgentTeam, team_id)
        if not team:
            raise ValueError("Team not found")
        return team

    async def list_teams(
        self,
        owner_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentTeam]:
        """
        List agent teams.

        Args:
            owner_id: Filter by owner
            is_public: Filter by visibility
            limit: Max results
            offset: Pagination offset

        Returns:
            List of teams
        """
        query = select(AgentTeam)

        if owner_id:
            query = query.where(AgentTeam.owner_id == owner_id)

        if is_public is not None:
            query = query.where(AgentTeam.is_public == is_public)

        query = query.order_by(AgentTeam.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_agent_to_team(
        self,
        team_id: str,
        agent_id: str
    ) -> AgentTeam:
        """Add agent to team"""
        team = await self.get_team(team_id)

        # Validate agent exists
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            raise ValueError("Agent not found")

        if agent_id not in team.agent_ids:
            team.agent_ids = team.agent_ids + [agent_id]
            await self.db.commit()

        logger.info(f"Added agent {agent_id} to team {team_id}")

        return team

    async def remove_agent_from_team(
        self,
        team_id: str,
        agent_id: str
    ) -> AgentTeam:
        """Remove agent from team"""
        team = await self.get_team(team_id)

        if agent_id in team.agent_ids:
            team.agent_ids = [a for a in team.agent_ids if a != agent_id]

            # Clear leader if removed
            if team.leader_agent_id == agent_id:
                team.leader_agent_id = None

            await self.db.commit()

        logger.info(f"Removed agent {agent_id} from team {team_id}")

        return team

    async def start_collaborative_session(
        self,
        goal: str,
        participant_agent_ids: List[str],
        session_type: str = "team_execution",
        team_id: Optional[str] = None,
        coordinator_agent_id: Optional[str] = None
    ) -> CollaborativeSession:
        """
        Start new collaborative session.

        Args:
            goal: Session goal
            participant_agent_ids: Agents participating
            session_type: team_execution, knowledge_sharing, peer_learning
            team_id: Optional team ID
            coordinator_agent_id: Optional coordinator

        Returns:
            CollaborativeSession
        """
        session = CollaborativeSession(
            session_type=session_type,
            team_id=team_id,
            participant_agent_ids=participant_agent_ids,
            coordinator_agent_id=coordinator_agent_id,
            goal=goal,
            status="active"
        )

        self.db.add(session)
        await self.db.commit()

        logger.info(f"Started collaborative session: {session_type} with {len(participant_agent_ids)} agents")

        return session

    async def complete_session(
        self,
        session_id: str,
        result: Dict[str, Any],
        quality_score: Optional[float] = None,
        knowledge_created: Optional[List[str]] = None
    ) -> CollaborativeSession:
        """Complete collaborative session"""
        session = await self.db.get(CollaborativeSession, session_id)
        if not session:
            raise ValueError("Session not found")

        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.result = result
        session.quality_score = quality_score
        session.knowledge_created = knowledge_created or []

        # Calculate execution time
        if session.started_at:
            total_time = (session.completed_at - session.started_at).total_seconds() * 1000
            session.total_time_ms = total_time

        await self.db.commit()

        # Update team metrics if session was for a team
        if session.team_id:
            await self._update_team_metrics(session.team_id, quality_score or 0.0, total_time)

        # Update agent relationships
        await self._update_agent_relationships(session.participant_agent_ids, quality_score or 0.5)

        logger.info(f"Completed session {session_id}")

        return session

    async def _update_team_metrics(
        self,
        team_id: str,
        quality_score: float,
        execution_time_ms: float
    ):
        """Update team performance metrics"""
        team = await self.db.get(AgentTeam, team_id)
        if not team:
            return

        team.total_executions += 1

        if quality_score >= 0.7:  # Consider 70%+ as successful
            team.successful_executions += 1

        # Update running averages
        if team.total_executions == 1:
            team.average_execution_time_ms = execution_time_ms
            team.average_quality_score = quality_score
        else:
            # Exponential moving average
            alpha = 0.2
            team.average_execution_time_ms = (
                alpha * execution_time_ms + (1 - alpha) * team.average_execution_time_ms
            )
            team.average_quality_score = (
                alpha * quality_score + (1 - alpha) * team.average_quality_score
            )

        await self.db.commit()

    async def _update_agent_relationships(
        self,
        agent_ids: List[str],
        quality_score: float
    ):
        """Update relationships between collaborating agents"""
        # Update each pair of agents
        for i, agent_a_id in enumerate(agent_ids):
            for agent_b_id in agent_ids[i+1:]:
                # Ensure consistent ordering (a < b)
                if agent_a_id > agent_b_id:
                    agent_a_id, agent_b_id = agent_b_id, agent_a_id

                # Get or create relationship
                result = await self.db.execute(
                    select(AgentRelationship).where(
                        AgentRelationship.agent_a_id == agent_a_id,
                        AgentRelationship.agent_b_id == agent_b_id
                    )
                )

                relationship = result.scalar_one_or_none()

                if not relationship:
                    relationship = AgentRelationship(
                        agent_a_id=agent_a_id,
                        agent_b_id=agent_b_id,
                        first_collaboration=datetime.utcnow()
                    )
                    self.db.add(relationship)

                # Update metrics
                relationship.collaboration_count += 1

                if quality_score >= 0.7:
                    relationship.successful_collaborations += 1

                # Update compatibility score (exponential moving average)
                alpha = 0.2
                success_rate = relationship.successful_collaborations / relationship.collaboration_count
                relationship.compatibility_score = (
                    alpha * success_rate + (1 - alpha) * relationship.compatibility_score
                )

                relationship.last_collaboration = datetime.utcnow()

        await self.db.commit()

    async def get_agent_relationships(
        self,
        agent_id: str,
        min_collaborations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get agent's relationships with other agents.

        Args:
            agent_id: Agent ID
            min_collaborations: Minimum collaborations to include

        Returns:
            List of relationships with metrics
        """
        # Query both directions (agent as A or B)
        result = await self.db.execute(
            select(AgentRelationship).where(
                (AgentRelationship.agent_a_id == agent_id) |
                (AgentRelationship.agent_b_id == agent_id)
            ).where(
                AgentRelationship.collaboration_count >= min_collaborations
            ).order_by(AgentRelationship.compatibility_score.desc())
        )

        relationships = result.scalars().all()

        return [
            {
                "partner_agent_id": rel.agent_b_id if rel.agent_a_id == agent_id else rel.agent_a_id,
                "collaboration_count": rel.collaboration_count,
                "success_rate": rel.successful_collaborations / rel.collaboration_count if rel.collaboration_count > 0 else 0,
                "compatibility_score": rel.compatibility_score,
                "last_collaboration": rel.last_collaboration.isoformat() if rel.last_collaboration else None
            }
            for rel in relationships
        ]

    async def get_team_performance(
        self,
        team_id: str
    ) -> Dict[str, Any]:
        """Get team performance summary"""
        team = await self.get_team(team_id)

        success_rate = (
            team.successful_executions / team.total_executions
            if team.total_executions > 0
            else 0.0
        )

        return {
            "team_id": team.id,
            "team_name": team.name,
            "total_executions": team.total_executions,
            "successful_executions": team.successful_executions,
            "success_rate": success_rate,
            "average_execution_time_ms": team.average_execution_time_ms,
            "average_quality_score": team.average_quality_score,
            "agent_count": len(team.agent_ids),
            "collaboration_pattern": team.collaboration_pattern
        }
