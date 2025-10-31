"""
ACL (Access Control List) Service

Manages permissions for agent-to-agent communication.

Permission hierarchy:
1. Agent-level explicit allow (A2AAgentAllow)
2. Organization-level allow (A2AOrgAllow)
3. Target agent is_public flag
4. Default deny if none match
"""

import logging
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Agent,
    A2AAgentAllow,
    A2AOrgAllow,
    AgentStatus
)

logger = logging.getLogger(__name__)


class ACLService:
    """Service for checking agent-to-agent permissions"""

    @staticmethod
    async def check_agent_permission(
        source_agent: Agent,
        target_agent: Agent,
        db: AsyncSession
    ) -> tuple[bool, str]:
        """
        Check if source agent can call target agent.

        Permission rules (in order of priority):
        1. Agent-level explicit allow - Highest priority
        2. Organization-level allow - If both in orgs with permissions
        3. Target agent is public - Anyone can call
        4. Same organization - Agents in same org can call each other
        5. Default deny - If none of the above match

        Args:
            source_agent: Agent making the request
            target_agent: Agent being called
            db: Database session

        Returns:
            (allowed: bool, reason: str)

        Example:
            allowed, reason = await ACLService.check_agent_permission(
                source_agent=agent_a,
                target_agent=agent_b,
                db=db
            )
            if not allowed:
                raise PermissionError(reason)
        """
        # Check if target agent is active
        if target_agent.status != AgentStatus.ACTIVE:
            return False, f"Target agent is {target_agent.status}"

        # Check if source agent is active
        if source_agent.status != AgentStatus.ACTIVE:
            return False, f"Source agent is {source_agent.status}"

        # Rule 1: Check agent-level explicit allow
        stmt = select(A2AAgentAllow).where(
            and_(
                A2AAgentAllow.source_agent_id == source_agent.id,
                A2AAgentAllow.target_agent_id == target_agent.id
            )
        )
        result = await db.execute(stmt)
        agent_allow = result.scalar_one_or_none()

        if agent_allow:
            logger.info(
                f"Agent-level permission: {source_agent.name} → {target_agent.name}"
            )
            return True, "Agent-level explicit allow"

        # Rule 2: Check organization-level allow
        if source_agent.organization_id and target_agent.organization_id:
            stmt = select(A2AOrgAllow).where(
                and_(
                    A2AOrgAllow.source_org_id == source_agent.organization_id,
                    A2AOrgAllow.target_org_id == target_agent.organization_id
                )
            )
            result = await db.execute(stmt)
            org_allow = result.scalar_one_or_none()

            if org_allow:
                logger.info(
                    f"Org-level permission: {source_agent.name} → {target_agent.name}"
                )
                return True, "Organization-level allow"

        # Rule 3: Check if agents in same organization
        if (source_agent.organization_id and
            target_agent.organization_id and
            source_agent.organization_id == target_agent.organization_id):
            logger.info(
                f"Same org permission: {source_agent.name} → {target_agent.name}"
            )
            return True, "Same organization"

        # Rule 4: Check if target agent is public
        if target_agent.is_public:
            logger.info(
                f"Public agent permission: {source_agent.name} → {target_agent.name}"
            )
            return True, "Target agent is public"

        # Rule 5: Default deny
        logger.warning(
            f"Permission denied: {source_agent.name} → {target_agent.name}"
        )
        return False, "No permission rules allow this access"

    @staticmethod
    async def check_bulk_permissions(
        source_agent: Agent,
        target_agent_ids: list[str],
        db: AsyncSession
    ) -> dict[str, tuple[bool, str]]:
        """
        Check permissions for multiple target agents at once.

        Useful for discovery/filtering operations where we need to
        check many agents efficiently.

        Args:
            source_agent: Agent making requests
            target_agent_ids: List of target agent IDs
            db: Database session

        Returns:
            Dictionary mapping agent_id to (allowed, reason)

        Example:
            permissions = await ACLService.check_bulk_permissions(
                source_agent=agent_a,
                target_agent_ids=["agent-1", "agent-2", "agent-3"],
                db=db
            )
            accessible_agents = [
                aid for aid, (allowed, _) in permissions.items()
                if allowed
            ]
        """
        results = {}

        # Get all target agents in one query
        stmt = select(Agent).where(Agent.id.in_(target_agent_ids))
        result = await db.execute(stmt)
        target_agents = {agent.id: agent for agent in result.scalars()}

        # Check each agent's permissions
        for agent_id in target_agent_ids:
            target_agent = target_agents.get(agent_id)

            if not target_agent:
                results[agent_id] = (False, "Agent not found")
                continue

            allowed, reason = await ACLService.check_agent_permission(
                source_agent, target_agent, db
            )
            results[agent_id] = (allowed, reason)

        return results

    @staticmethod
    async def grant_agent_permission(
        source_agent_id: str,
        target_agent_id: str,
        db: AsyncSession
    ) -> A2AAgentAllow:
        """
        Grant agent-level permission.

        Args:
            source_agent_id: Agent being granted permission
            target_agent_id: Agent that can be called
            db: Database session

        Returns:
            Created permission record

        Example:
            # Allow agent-a to call agent-b
            await ACLService.grant_agent_permission(
                source_agent_id="agent-a",
                target_agent_id="agent-b",
                db=db
            )
        """
        # Check if permission already exists
        stmt = select(A2AAgentAllow).where(
            and_(
                A2AAgentAllow.source_agent_id == source_agent_id,
                A2AAgentAllow.target_agent_id == target_agent_id
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"Permission already exists: {source_agent_id} → {target_agent_id}")
            return existing

        # Create new permission
        permission = A2AAgentAllow(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id
        )
        db.add(permission)
        await db.commit()
        await db.refresh(permission)

        logger.info(f"Permission granted: {source_agent_id} → {target_agent_id}")
        return permission

    @staticmethod
    async def revoke_agent_permission(
        source_agent_id: str,
        target_agent_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Revoke agent-level permission.

        Args:
            source_agent_id: Agent permission being revoked from
            target_agent_id: Agent that can no longer be called
            db: Database session

        Returns:
            True if permission was revoked, False if it didn't exist

        Example:
            revoked = await ACLService.revoke_agent_permission(
                source_agent_id="agent-a",
                target_agent_id="agent-b",
                db=db
            )
        """
        stmt = select(A2AAgentAllow).where(
            and_(
                A2AAgentAllow.source_agent_id == source_agent_id,
                A2AAgentAllow.target_agent_id == target_agent_id
            )
        )
        result = await db.execute(stmt)
        permission = result.scalar_one_or_none()

        if not permission:
            logger.warning(
                f"No permission to revoke: {source_agent_id} → {target_agent_id}"
            )
            return False

        await db.delete(permission)
        await db.commit()

        logger.info(f"Permission revoked: {source_agent_id} → {target_agent_id}")
        return True

    @staticmethod
    async def grant_org_permission(
        source_org_id: str,
        target_org_id: str,
        db: AsyncSession
    ) -> A2AOrgAllow:
        """
        Grant organization-level permission.

        All agents in source_org can call all agents in target_org.

        Args:
            source_org_id: Organization being granted permission
            target_org_id: Organization that can be called
            db: Database session

        Returns:
            Created permission record

        Example:
            # Allow all agents in org-a to call all agents in org-b
            await ACLService.grant_org_permission(
                source_org_id="org-a",
                target_org_id="org-b",
                db=db
            )
        """
        # Check if permission already exists
        stmt = select(A2AOrgAllow).where(
            and_(
                A2AOrgAllow.source_org_id == source_org_id,
                A2AOrgAllow.target_org_id == target_org_id
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"Org permission already exists: {source_org_id} → {target_org_id}")
            return existing

        # Create new permission
        permission = A2AOrgAllow(
            source_org_id=source_org_id,
            target_org_id=target_org_id
        )
        db.add(permission)
        await db.commit()
        await db.refresh(permission)

        logger.info(f"Org permission granted: {source_org_id} → {target_org_id}")
        return permission

    @staticmethod
    async def revoke_org_permission(
        source_org_id: str,
        target_org_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Revoke organization-level permission.

        Args:
            source_org_id: Organization permission being revoked from
            target_org_id: Organization that can no longer be called
            db: Database session

        Returns:
            True if permission was revoked, False if it didn't exist
        """
        stmt = select(A2AOrgAllow).where(
            and_(
                A2AOrgAllow.source_org_id == source_org_id,
                A2AOrgAllow.target_org_id == target_org_id
            )
        )
        result = await db.execute(stmt)
        permission = result.scalar_one_or_none()

        if not permission:
            logger.warning(
                f"No org permission to revoke: {source_org_id} → {target_org_id}"
            )
            return False

        await db.delete(permission)
        await db.commit()

        logger.info(f"Org permission revoked: {source_org_id} → {target_org_id}")
        return True
