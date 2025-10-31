"""
ML-Powered Reputation Engine

Multi-dimensional reputation scoring with machine learning for Astraeus agents.

Sprint 4: Advanced Security & Trust
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent, Contract, ContractStatus
from backend.database.models_payments import Delivery
from backend.database.models_security import ReputationScore, TrustMetric

logger = logging.getLogger(__name__)


class ReputationEngine:
    """
    ML-powered reputation engine with multi-dimensional scoring.

    Reputation Dimensions:
    - Quality (40%): Delivery quality from validation scores
    - Reliability (25%): Success rate and uptime
    - Speed (15%): Response time vs. promised ETA
    - Honesty (10%): Bid accuracy (promised vs actual)
    - Collaboration (10%): Works well with other agents
    """

    # Weights for overall reputation
    WEIGHTS = {
        "quality": 0.40,
        "reliability": 0.25,
        "speed": 0.15,
        "honesty": 0.10,
        "collaboration": 0.10
    }

    # Trust grade thresholds
    GRADE_THRESHOLDS = {
        "A+": 0.95,
        "A": 0.90,
        "B": 0.75,
        "C": 0.60,
        "D": 0.40,
        "F": 0.00
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_reputation(self, agent_id: str) -> ReputationScore:
        """
        Calculate comprehensive reputation score for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            ReputationScore object with all dimensions
        """
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            raise ValueError("Agent not found")

        # Get or create reputation record
        reputation = await self.db.get(ReputationScore, agent_id)
        if not reputation:
            reputation = ReputationScore(agent_id=agent_id)
            self.db.add(reputation)

        # Calculate each dimension
        quality = await self._calculate_quality_score(agent_id)
        reliability = await self._calculate_reliability_score(agent_id)
        speed = await self._calculate_speed_score(agent_id)
        honesty = await self._calculate_honesty_score(agent_id)
        collaboration = await self._calculate_collaboration_score(agent_id)

        # Update scores
        reputation.quality_score = quality
        reputation.reliability_score = reliability
        reputation.speed_score = speed
        reputation.honesty_score = honesty
        reputation.collaboration_score = collaboration

        # Calculate overall reputation (weighted average)
        overall = (
            quality * self.WEIGHTS["quality"] +
            reliability * self.WEIGHTS["reliability"] +
            speed * self.WEIGHTS["speed"] +
            honesty * self.WEIGHTS["honesty"] +
            collaboration * self.WEIGHTS["collaboration"]
        )
        reputation.overall_reputation = overall

        # Assign trust grade
        reputation.trust_grade = self._get_trust_grade(overall)

        # Update statistics
        stats = await self._get_contract_stats(agent_id)
        reputation.total_contracts = stats["total"]
        reputation.successful_contracts = stats["successful"]
        reputation.failed_contracts = stats["failed"]
        reputation.disputed_contracts = stats["disputed"]
        reputation.average_rating = stats["avg_rating"]

        # Update metadata
        reputation.last_calculated = datetime.utcnow()
        reputation.calculation_count += 1

        await self.db.commit()

        # Store historical metric
        await self._store_historical_metric(reputation)

        logger.info(f"Calculated reputation for agent {agent_id}: {overall:.2f} ({reputation.trust_grade})")

        return reputation

    async def _calculate_quality_score(self, agent_id: str) -> float:
        """
        Calculate quality score based on delivery validation scores.

        Returns score between 0.0 and 1.0
        """
        # Get average validation score from deliveries
        result = await self.db.execute(
            select(func.avg(Delivery.validation_score))
            .join(Contract)
            .where(Contract.awarded_to == agent_id)
            .where(Delivery.is_validated == True)
        )

        avg_validation = result.scalar_one_or_none()

        if avg_validation is None:
            return 0.5  # Default for new agents

        # Validation scores are 0.0-1.0, so we can use directly
        return float(avg_validation)

    async def _calculate_reliability_score(self, agent_id: str) -> float:
        """
        Calculate reliability score based on success rate.

        Returns score between 0.0 and 1.0
        """
        agent = await self.db.get(Agent, agent_id)

        if agent.total_calls == 0:
            return 0.5  # Default for new agents

        success_rate = agent.successful_calls / agent.total_calls

        # Boost score if high volume (more reliable data)
        if agent.total_calls > 100:
            success_rate = min(1.0, success_rate * 1.05)  # 5% boost
        elif agent.total_calls > 50:
            success_rate = min(1.0, success_rate * 1.02)  # 2% boost

        return success_rate

    async def _calculate_speed_score(self, agent_id: str) -> float:
        """
        Calculate speed score based on actual vs. promised delivery time.

        Returns score between 0.0 and 1.0
        """
        # Get contracts with bids and deliveries
        from backend.database.models_payments import Bid

        result = await self.db.execute(
            select(Bid.eta_seconds, Contract.created_at, Contract.completed_at)
            .join(Contract, Bid.contract_id == Contract.id)
            .where(Contract.awarded_to == agent_id)
            .where(Contract.status == ContractStatus.SETTLED)
        )

        rows = result.all()

        if not rows:
            return 0.5  # Default for new agents

        # Calculate ratio of actual time to promised time
        ratios = []
        for promised_eta, created_at, completed_at in rows:
            if promised_eta and created_at and completed_at:
                actual_seconds = (completed_at - created_at).total_seconds()
                ratio = actual_seconds / promised_eta

                # Score: 1.0 if faster than promised, decreases as slower
                if ratio <= 1.0:
                    score = 1.0
                else:
                    # Penalize delays: 2x slower = 0.5 score, 3x slower = 0.33 score
                    score = 1.0 / ratio

                ratios.append(score)

        return sum(ratios) / len(ratios) if ratios else 0.5

    async def _calculate_honesty_score(self, agent_id: str) -> float:
        """
        Calculate honesty score based on bid accuracy.

        Compares promised price/time with actual.

        Returns score between 0.0 and 1.0
        """
        from backend.database.models_payments import Bid

        # Get bids with actual outcomes
        result = await self.db.execute(
            select(
                Bid.price,
                Bid.confidence,
                Delivery.validation_score
            )
            .join(Contract, Bid.contract_id == Contract.id)
            .join(Delivery, Delivery.contract_id == Contract.id)
            .where(Contract.awarded_to == agent_id)
            .where(Delivery.is_validated == True)
        )

        rows = result.all()

        if not rows:
            return 0.5  # Default for new agents

        # Honesty = how close confidence matches actual validation score
        accuracy_scores = []
        for bid_price, confidence, validation_score in rows:
            if confidence and validation_score:
                # Difference between claimed confidence and actual quality
                diff = abs(confidence - validation_score)
                # Convert to score (0 diff = 1.0, 0.5 diff = 0.5, 1.0 diff = 0.0)
                accuracy = 1.0 - diff
                accuracy_scores.append(max(0.0, accuracy))

        return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.5

    async def _calculate_collaboration_score(self, agent_id: str) -> float:
        """
        Calculate collaboration score based on multi-agent orchestrations.

        Returns score between 0.0 and 1.0
        """
        # For now, use a simplified version based on success in orchestrations
        # In production, this would analyze agent behavior in multi-agent tasks

        from backend.database.models_orchestration import CollaborationResult

        result = await self.db.execute(
            select(func.count(CollaborationResult.id))
            .where(CollaborationResult.agent_id == agent_id)
        )

        collab_count = result.scalar_one_or_none() or 0

        if collab_count == 0:
            return 0.5  # Default for agents not in collaborations

        # Simple scoring: more collaborations = higher score (up to limit)
        # Cap at 50 collaborations for max score
        score = min(1.0, 0.5 + (collab_count / 100.0))

        return score

    async def _get_contract_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get contract statistics for an agent"""
        # Total contracts
        result = await self.db.execute(
            select(func.count(Contract.id))
            .where(Contract.awarded_to == agent_id)
        )
        total = result.scalar_one_or_none() or 0

        # Successful
        result = await self.db.execute(
            select(func.count(Contract.id))
            .where(Contract.awarded_to == agent_id)
            .where(Contract.status == ContractStatus.SETTLED)
        )
        successful = result.scalar_one_or_none() or 0

        # Failed
        result = await self.db.execute(
            select(func.count(Contract.id))
            .where(Contract.awarded_to == agent_id)
            .where(Contract.status == ContractStatus.FAILED)
        )
        failed = result.scalar_one_or_none() or 0

        # Disputed
        from backend.database.models_payments import Dispute

        result = await self.db.execute(
            select(func.count(Dispute.id))
            .join(Contract)
            .where(Contract.awarded_to == agent_id)
        )
        disputed = result.scalar_one_or_none() or 0

        # Average rating (from deliveries)
        result = await self.db.execute(
            select(func.avg(Delivery.validation_score))
            .join(Contract)
            .where(Contract.awarded_to == agent_id)
            .where(Delivery.is_validated == True)
        )
        avg_rating = result.scalar_one_or_none() or 0.0

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "disputed": disputed,
            "avg_rating": float(avg_rating)
        }

    def _get_trust_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "F"

    async def _store_historical_metric(self, reputation: ReputationScore):
        """Store historical metric for trend analysis"""
        metric = TrustMetric(
            agent_id=reputation.agent_id,
            quality_score=reputation.quality_score,
            reliability_score=reputation.reliability_score,
            speed_score=reputation.speed_score,
            honesty_score=reputation.honesty_score,
            collaboration_score=reputation.collaboration_score,
            overall_reputation=reputation.overall_reputation,
            contracts_at_time=reputation.total_contracts,
            successful_at_time=reputation.successful_contracts
        )

        self.db.add(metric)
        await self.db.commit()

    async def get_reputation_trends(
        self,
        agent_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get reputation trend over time.

        Returns:
            List of {timestamp, score} dictionaries
        """
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(TrustMetric)
            .where(TrustMetric.agent_id == agent_id)
            .where(TrustMetric.recorded_at >= since)
            .order_by(TrustMetric.recorded_at)
        )

        metrics = result.scalars().all()

        return [
            {
                "timestamp": m.recorded_at.isoformat(),
                "score": m.overall_reputation,
                "quality": m.quality_score,
                "reliability": m.reliability_score,
                "speed": m.speed_score,
                "contracts": m.contracts_at_time
            }
            for m in metrics
        ]

    async def recalculate_all_reputations(self):
        """
        Recalculate reputation for all active agents.

        This should be run as a periodic background task.
        """
        result = await self.db.execute(
            select(Agent).where(Agent.status == "active")
        )

        agents = result.scalars().all()
        count = 0

        for agent in agents:
            try:
                await self.calculate_reputation(agent.id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to calculate reputation for agent {agent.id}: {e}")

        logger.info(f"Recalculated reputation for {count} agents")

        return count
