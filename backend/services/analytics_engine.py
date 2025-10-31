"""
Real-Time Analytics Engine

Tracks user behavior, agent performance, and platform metrics with time-series aggregation.

Sprint 5: Analytics & Observability
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User, Agent, Contract, ContractStatus
from backend.database.models_payments import Payment, Credit
from backend.database.models_analytics import (
    UserAnalytics,
    AgentAnalytics,
    PlatformMetrics
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Real-time analytics engine for users, agents, and platform.

    Features:
    - User behavior tracking
    - Agent performance metrics
    - Platform health metrics
    - Time-series aggregation (hourly, daily, weekly, monthly)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_user_analytics(
        self,
        user_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "day"
    ) -> UserAnalytics:
        """
        Calculate and store user analytics for a time period.

        Args:
            user_id: User ID
            period_start: Period start time
            period_end: Period end time
            period_type: hour, day, week, month

        Returns:
            UserAnalytics record
        """
        # Check if analytics already exist for this period
        existing = await self.db.execute(
            select(UserAnalytics)
            .where(UserAnalytics.user_id == user_id)
            .where(UserAnalytics.period_start == period_start)
            .where(UserAnalytics.period_type == period_type)
        )

        existing_analytics = existing.scalar_one_or_none()
        if existing_analytics:
            return existing_analytics

        # Calculate contract metrics
        contract_result = await self.db.execute(
            select(
                func.count(Contract.id).label("total"),
                func.sum(func.cast(Contract.status == ContractStatus.SETTLED, Integer)).label("completed"),
                func.sum(func.cast(Contract.status == ContractStatus.CANCELLED, Integer)).label("cancelled")
            )
            .where(Contract.requester_id == user_id)
            .where(and_(
                Contract.created_at >= period_start,
                Contract.created_at < period_end
            ))
        )

        contract_stats = contract_result.one()

        # Calculate financial metrics
        credits_purchased_result = await self.db.execute(
            select(func.sum(Credit.amount))
            .where(Credit.user_id == user_id)
            .where(Credit.transaction_type == "purchase")
            .where(and_(
                Credit.created_at >= period_start,
                Credit.created_at < period_end
            ))
        )
        credits_purchased = credits_purchased_result.scalar_one_or_none() or 0.0

        credits_spent_result = await self.db.execute(
            select(func.sum(Credit.amount))
            .where(Credit.user_id == user_id)
            .where(Credit.transaction_type == "deduction")
            .where(and_(
                Credit.created_at >= period_start,
                Credit.created_at < period_end
            ))
        )
        credits_spent = abs(credits_spent_result.scalar_one_or_none() or 0.0)

        payments_result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(Payment.user_id == user_id)
            .where(and_(
                Payment.created_at >= period_start,
                Payment.created_at < period_end
            ))
        )
        total_spent = payments_result.scalar_one_or_none() or 0.0

        # Get unique agents used
        agents_result = await self.db.execute(
            select(Contract.awarded_to)
            .where(Contract.requester_id == user_id)
            .where(Contract.awarded_to.isnot(None))
            .where(and_(
                Contract.created_at >= period_start,
                Contract.created_at < period_end
            ))
            .distinct()
        )
        unique_agents = [agent_id for agent_id, in agents_result.all()]

        # Count orchestrations (from orchestration models)
        from backend.database.models_orchestration import OrchestrationPlan

        orchestrations_result = await self.db.execute(
            select(func.count(OrchestrationPlan.id))
            .where(OrchestrationPlan.user_id == user_id)
            .where(and_(
                OrchestrationPlan.created_at >= period_start,
                OrchestrationPlan.created_at < period_end
            ))
        )
        orchestrations = orchestrations_result.scalar_one_or_none() or 0

        # Create analytics record
        analytics = UserAnalytics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            contracts_created=contract_stats.total or 0,
            contracts_completed=contract_stats.completed or 0,
            contracts_cancelled=contract_stats.cancelled or 0,
            credits_purchased=float(credits_purchased),
            credits_spent=float(credits_spent),
            total_spent=float(total_spent),
            agents_used=len(unique_agents),
            unique_agents=unique_agents,
            orchestrations_run=orchestrations
        )

        self.db.add(analytics)
        await self.db.commit()

        logger.info(f"Tracked user analytics: {user_id} for {period_type}")

        return analytics

    async def track_agent_analytics(
        self,
        agent_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "day"
    ) -> AgentAnalytics:
        """
        Calculate and store agent analytics for a time period.

        Args:
            agent_id: Agent ID
            period_start: Period start time
            period_end: Period end time
            period_type: hour, day, week, month

        Returns:
            AgentAnalytics record
        """
        # Check if analytics already exist
        existing = await self.db.execute(
            select(AgentAnalytics)
            .where(AgentAnalytics.agent_id == agent_id)
            .where(AgentAnalytics.period_start == period_start)
            .where(AgentAnalytics.period_type == period_type)
        )

        existing_analytics = existing.scalar_one_or_none()
        if existing_analytics:
            return existing_analytics

        # Get agent performance stats
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            raise ValueError("Agent not found")

        # Calculate contract metrics
        from backend.database.models_payments import Bid

        bids_result = await self.db.execute(
            select(func.count(Bid.id))
            .where(Bid.agent_id == agent_id)
            .where(and_(
                Bid.created_at >= period_start,
                Bid.created_at < period_end
            ))
        )
        bids_placed = bids_result.scalar_one_or_none() or 0

        contracts_result = await self.db.execute(
            select(
                func.count(Contract.id).label("total"),
                func.sum(func.cast(Contract.status == ContractStatus.SETTLED, Integer)).label("completed"),
                func.sum(func.cast(Contract.status == ContractStatus.FAILED, Integer)).label("failed")
            )
            .where(Contract.awarded_to == agent_id)
            .where(and_(
                Contract.created_at >= period_start,
                Contract.created_at < period_end
            ))
        )

        contract_stats = contracts_result.one()

        # Calculate revenue
        revenue_result = await self.db.execute(
            select(func.sum(Contract.budget))
            .where(Contract.awarded_to == agent_id)
            .where(Contract.status == ContractStatus.SETTLED)
            .where(and_(
                Contract.created_at >= period_start,
                Contract.created_at < period_end
            ))
        )
        revenue = revenue_result.scalar_one_or_none() or 0.0

        # Calculate average bid price
        avg_bid_result = await self.db.execute(
            select(func.avg(Bid.price))
            .where(Bid.agent_id == agent_id)
            .where(and_(
                Bid.created_at >= period_start,
                Bid.created_at < period_end
            ))
        )
        avg_bid_price = avg_bid_result.scalar_one_or_none() or 0.0

        # Calculate quality metrics
        from backend.database.models_payments import Delivery

        quality_result = await self.db.execute(
            select(func.avg(Delivery.validation_score))
            .join(Contract)
            .where(Contract.awarded_to == agent_id)
            .where(Delivery.is_validated == True)
            .where(and_(
                Delivery.delivered_at >= period_start,
                Delivery.delivered_at < period_end
            ))
        )
        avg_validation_score = quality_result.scalar_one_or_none() or 0.0

        # Get reputation score
        from backend.database.models_security import ReputationScore

        reputation = await self.db.get(ReputationScore, agent_id)
        reputation_score = reputation.overall_reputation if reputation else 0.5

        # Get unique users
        users_result = await self.db.execute(
            select(Contract.requester_id)
            .where(Contract.awarded_to == agent_id)
            .where(and_(
                Contract.created_at >= period_start,
                Contract.created_at < period_end
            ))
            .distinct()
        )
        unique_users = [user_id for user_id, in users_result.all()]

        # Create analytics record
        analytics = AgentAnalytics(
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            total_calls=agent.total_calls,
            successful_calls=agent.successful_calls,
            failed_calls=agent.failed_calls,
            bids_placed=bids_placed,
            contracts_won=contract_stats.total or 0,
            contracts_completed=contract_stats.completed or 0,
            contracts_failed=contract_stats.failed or 0,
            revenue=float(revenue),
            avg_bid_price=float(avg_bid_price),
            avg_validation_score=float(avg_validation_score),
            reputation_score=reputation_score,
            unique_users=len(unique_users),
            unique_user_list=unique_users
        )

        self.db.add(analytics)
        await self.db.commit()

        logger.info(f"Tracked agent analytics: {agent_id} for {period_type}")

        return analytics

    async def track_platform_metrics(
        self,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "day"
    ) -> PlatformMetrics:
        """
        Calculate and store platform-wide metrics.

        Args:
            period_start: Period start time
            period_end: Period end time
            period_type: hour, day, week, month

        Returns:
            PlatformMetrics record
        """
        # Check if metrics already exist
        existing = await self.db.execute(
            select(PlatformMetrics)
            .where(PlatformMetrics.period_start == period_start)
            .where(PlatformMetrics.period_type == period_type)
        )

        existing_metrics = existing.scalar_one_or_none()
        if existing_metrics:
            return existing_metrics

        # User metrics
        total_users_result = await self.db.execute(
            select(func.count(User.id))
        )
        total_users = total_users_result.scalar_one_or_none() or 0

        new_users_result = await self.db.execute(
            select(func.count(User.id))
            .where(and_(
                User.created_at >= period_start,
                User.created_at < period_end
            ))
        )
        new_users = new_users_result.scalar_one_or_none() or 0

        # Agent metrics
        total_agents_result = await self.db.execute(
            select(func.count(Agent.id))
        )
        total_agents = total_agents_result.scalar_one_or_none() or 0

        new_agents_result = await self.db.execute(
            select(func.count(Agent.id))
            .where(and_(
                Agent.created_at >= period_start,
                Agent.created_at < period_end
            ))
        )
        new_agents = new_agents_result.scalar_one_or_none() or 0

        # Contract metrics
        contracts_result = await self.db.execute(
            select(
                func.count(Contract.id).label("total"),
                func.sum(func.cast(Contract.status.in_([ContractStatus.PENDING, ContractStatus.ACTIVE]), Integer)).label("active"),
                func.sum(func.cast(Contract.status == ContractStatus.SETTLED, Integer)).label("completed"),
                func.sum(func.cast(Contract.status == ContractStatus.FAILED, Integer)).label("failed")
            )
            .where(and_(
                Contract.created_at >= period_start,
                Contract.created_at < period_end
            ))
        )

        contract_stats = contracts_result.one()

        # Financial metrics
        revenue_result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(and_(
                Payment.created_at >= period_start,
                Payment.created_at < period_end
            ))
        )
        total_revenue = revenue_result.scalar_one_or_none() or 0.0

        # Assume 15% platform fee
        platform_fees = float(total_revenue) * 0.15

        credits_purchased_result = await self.db.execute(
            select(func.sum(Credit.amount))
            .where(Credit.transaction_type == "purchase")
            .where(and_(
                Credit.created_at >= period_start,
                Credit.created_at < period_end
            ))
        )
        credits_purchased = credits_purchased_result.scalar_one_or_none() or 0.0

        credits_spent_result = await self.db.execute(
            select(func.sum(Credit.amount))
            .where(Credit.transaction_type == "deduction")
            .where(and_(
                Credit.created_at >= period_start,
                Credit.created_at < period_end
            ))
        )
        credits_spent = abs(credits_spent_result.scalar_one_or_none() or 0.0)

        # Orchestration metrics
        from backend.database.models_orchestration import OrchestrationPlan

        orchestrations_result = await self.db.execute(
            select(func.count(OrchestrationPlan.id))
            .where(and_(
                OrchestrationPlan.created_at >= period_start,
                OrchestrationPlan.created_at < period_end
            ))
        )
        orchestrations = orchestrations_result.scalar_one_or_none() or 0

        # Fraud and security metrics
        from backend.database.models_security import FraudAlert, SecurityEvent

        fraud_alerts_result = await self.db.execute(
            select(func.count(FraudAlert.id))
            .where(and_(
                FraudAlert.created_at >= period_start,
                FraudAlert.created_at < period_end
            ))
        )
        fraud_alerts = fraud_alerts_result.scalar_one_or_none() or 0

        security_events_result = await self.db.execute(
            select(func.count(SecurityEvent.id))
            .where(and_(
                SecurityEvent.created_at >= period_start,
                SecurityEvent.created_at < period_end
            ))
        )
        security_events = security_events_result.scalar_one_or_none() or 0

        # Create metrics record
        metrics = PlatformMetrics(
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            total_users=total_users,
            new_users=new_users,
            total_agents=total_agents,
            new_agents=new_agents,
            total_contracts=contract_stats.total or 0,
            active_contracts=contract_stats.active or 0,
            completed_contracts=contract_stats.completed or 0,
            failed_contracts=contract_stats.failed or 0,
            total_revenue=float(total_revenue),
            platform_fees=platform_fees,
            credits_purchased=float(credits_purchased),
            credits_spent=float(credits_spent),
            orchestrations=orchestrations,
            fraud_alerts=fraud_alerts,
            security_events=security_events
        )

        self.db.add(metrics)
        await self.db.commit()

        logger.info(f"Tracked platform metrics for {period_type}")

        return metrics

    async def get_user_trends(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user activity trends over time.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of analytics data points
        """
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(UserAnalytics)
            .where(UserAnalytics.user_id == user_id)
            .where(UserAnalytics.period_start >= since)
            .where(UserAnalytics.period_type == "day")
            .order_by(UserAnalytics.period_start)
        )

        analytics = result.scalars().all()

        return [
            {
                "date": a.period_start.isoformat(),
                "contracts": a.contracts_created,
                "credits_spent": a.credits_spent,
                "agents_used": a.agents_used,
                "orchestrations": a.orchestrations_run
            }
            for a in analytics
        ]

    async def get_agent_trends(
        self,
        agent_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get agent performance trends over time.

        Args:
            agent_id: Agent ID
            days: Number of days to look back

        Returns:
            List of analytics data points
        """
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(AgentAnalytics)
            .where(AgentAnalytics.agent_id == agent_id)
            .where(AgentAnalytics.period_start >= since)
            .where(AgentAnalytics.period_type == "day")
            .order_by(AgentAnalytics.period_start)
        )

        analytics = result.scalars().all()

        return [
            {
                "date": a.period_start.isoformat(),
                "calls": a.total_calls,
                "success_rate": (a.successful_calls / a.total_calls * 100) if a.total_calls > 0 else 0,
                "revenue": a.revenue,
                "contracts": a.contracts_won,
                "reputation": a.reputation_score
            }
            for a in analytics
        ]

    async def get_platform_trends(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get platform-wide trends over time.

        Args:
            days: Number of days to look back

        Returns:
            List of metrics data points
        """
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(PlatformMetrics)
            .where(PlatformMetrics.period_start >= since)
            .where(PlatformMetrics.period_type == "day")
            .order_by(PlatformMetrics.period_start)
        )

        metrics = result.scalars().all()

        return [
            {
                "date": m.period_start.isoformat(),
                "users": m.total_users,
                "agents": m.total_agents,
                "contracts": m.total_contracts,
                "revenue": m.total_revenue,
                "active_users": m.active_users
            }
            for m in metrics
        ]

    async def batch_track_analytics(
        self,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "day"
    ) -> Dict[str, int]:
        """
        Batch track analytics for all users, agents, and platform.

        This should be run as a periodic background task.

        Args:
            period_start: Period start time
            period_end: Period end time
            period_type: hour, day, week, month

        Returns:
            Summary of tracking results
        """
        # Track platform metrics first
        await self.track_platform_metrics(period_start, period_end, period_type)

        # Get all active users
        user_result = await self.db.execute(select(User))
        users = user_result.scalars().all()

        user_count = 0
        for user in users:
            try:
                await self.track_user_analytics(user.id, period_start, period_end, period_type)
                user_count += 1
            except Exception as e:
                logger.error(f"Failed to track user analytics for {user.id}: {e}")

        # Get all active agents
        agent_result = await self.db.execute(
            select(Agent).where(Agent.status == "active")
        )
        agents = agent_result.scalars().all()

        agent_count = 0
        for agent in agents:
            try:
                await self.track_agent_analytics(agent.id, period_start, period_end, period_type)
                agent_count += 1
            except Exception as e:
                logger.error(f"Failed to track agent analytics for {agent.id}: {e}")

        logger.info(f"Batch tracked analytics: {user_count} users, {agent_count} agents")

        return {
            "users_tracked": user_count,
            "agents_tracked": agent_count,
            "platform_tracked": 1
        }
