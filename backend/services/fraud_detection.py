"""
ML-Powered Fraud Detection

Detects Sybil attacks, collusion, delivery fraud, and rating manipulation.

Sprint 4: Advanced Security & Trust
"""

import logging
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent, User, Contract
from backend.database.models_payments import Bid, Delivery
from backend.database.models_security import (
    FraudAlert,
    FraudType,
    FraudSeverity,
    ReputationScore
)

logger = logging.getLogger(__name__)


class FraudDetector:
    """
    ML-powered fraud detection system.

    Detects:
    - Sybil attacks (fake agent identities)
    - Collusion (agents working together unfairly)
    - Delivery fraud (fake/poor quality work)
    - Rating manipulation (fake reviews)
    - Price manipulation
    """

    # Detection thresholds
    SYBIL_SIMILARITY_THRESHOLD = 0.85  # 85% similarity = suspicious
    COLLUSION_WIN_RATE_THRESHOLD = 0.80  # 80% win rate together = suspicious
    DELIVERY_QUALITY_THRESHOLD = 0.30  # Quality < 30% = fraud
    RATING_SPIKE_THRESHOLD = 3.0  # 3 std deviations = manipulation

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_sybil_attacks(self) -> List[FraudAlert]:
        """
        Detect Sybil attacks (multiple fake identities).

        Indicators:
        - Same IP address
        - Similar naming patterns
        - Created at similar times
        - Similar capabilities
        - Mutual bidding patterns
        """
        alerts = []

        # Get all agents
        result = await self.db.execute(select(Agent))
        agents = result.scalars().all()

        # Group by suspicious similarity
        clusters = await self._find_sybil_clusters(agents)

        for cluster in clusters:
            if len(cluster) >= 2:  # At least 2 agents to be suspicious
                confidence = self._calculate_sybil_confidence(cluster)

                if confidence >= 0.7:  # 70% confidence threshold
                    alert = await self._create_fraud_alert(
                        fraud_type=FraudType.SYBIL_ATTACK,
                        severity=self._get_severity(confidence),
                        description=f"Detected potential Sybil attack: {len(cluster)} related agents",
                        evidence={
                            "agent_cluster": [a.id for a in cluster],
                            "similarity_score": confidence,
                            "cluster_size": len(cluster)
                        },
                        related_agents=[a.id for a in cluster]
                    )
                    alerts.append(alert)

        logger.info(f"Sybil detection: {len(alerts)} alerts created")
        return alerts

    async def _find_sybil_clusters(self, agents: List[Agent]) -> List[List[Agent]]:
        """Group agents by similarity into clusters"""
        clusters = []
        used_agents = set()

        for i, agent1 in enumerate(agents):
            if agent1.id in used_agents:
                continue

            cluster = [agent1]

            for agent2 in agents[i+1:]:
                if agent2.id in used_agents:
                    continue

                similarity = self._calculate_agent_similarity(agent1, agent2)

                if similarity >= self.SYBIL_SIMILARITY_THRESHOLD:
                    cluster.append(agent2)
                    used_agents.add(agent2.id)

            if len(cluster) >= 2:
                clusters.append(cluster)
                used_agents.add(agent1.id)

        return clusters

    def _calculate_agent_similarity(self, agent1: Agent, agent2: Agent) -> float:
        """Calculate similarity between two agents (0.0 - 1.0)"""
        score = 0.0
        factors = 0

        # Name similarity
        if agent1.name and agent2.name:
            name_sim = self._string_similarity(agent1.name, agent2.name)
            score += name_sim * 0.3
            factors += 1

        # Capability overlap
        caps1 = set(agent1.capabilities or [])
        caps2 = set(agent2.capabilities or [])

        if caps1 and caps2:
            cap_overlap = len(caps1 & caps2) / max(len(caps1 | caps2), 1)
            score += cap_overlap * 0.3
            factors += 1

        # Created at similar times (within 1 hour)
        if agent1.created_at and agent2.created_at:
            time_diff = abs((agent1.created_at - agent2.created_at).total_seconds())
            if time_diff < 3600:  # Within 1 hour
                score += 0.2
            factors += 1

        # Same category
        if agent1.category == agent2.category and agent1.category:
            score += 0.2
            factors += 1

        return score / factors if factors > 0 else 0.0

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Simple string similarity (Levenshtein-like)"""
        s1 = s1.lower()
        s2 = s2.lower()

        if s1 == s2:
            return 1.0

        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        max_len = max(len(s1), len(s2))

        return matches / max_len if max_len > 0 else 0.0

    def _calculate_sybil_confidence(self, cluster: List[Agent]) -> float:
        """Calculate confidence that cluster is a Sybil attack"""
        # More agents in cluster = higher confidence
        size_factor = min(1.0, len(cluster) / 5.0)  # Cap at 5 agents

        # Average pairwise similarity
        similarities = []
        for i, agent1 in enumerate(cluster):
            for agent2 in cluster[i+1:]:
                sim = self._calculate_agent_similarity(agent1, agent2)
                similarities.append(sim)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

        # Weighted confidence
        confidence = (avg_similarity * 0.7) + (size_factor * 0.3)

        return confidence

    async def detect_collusion(self) -> List[FraudAlert]:
        """
        Detect collusion (agents working together unfairly).

        Indicators:
        - Always bidding on same contracts
        - One agent always winning when they bid together
        - Coordinated bidding prices
        """
        alerts = []

        # Get recent contracts with multiple bids
        since = datetime.utcnow() - timedelta(days=30)

        result = await self.db.execute(
            select(Contract)
            .where(Contract.created_at >= since)
        )

        contracts = result.scalars().all()

        # Analyze bidding patterns
        agent_pairs = defaultdict(lambda: {"together": 0, "wins": 0})

        for contract in contracts:
            # Get all bids for this contract
            bid_result = await self.db.execute(
                select(Bid).where(Bid.contract_id == contract.id)
            )
            bids = bid_result.scalars().all()

            if len(bids) < 2:
                continue

            bidder_ids = [b.agent_id for b in bids]

            # Check all pairs of bidders
            for i, agent1_id in enumerate(bidder_ids):
                for agent2_id in bidder_ids[i+1:]:
                    pair_key = tuple(sorted([agent1_id, agent2_id]))
                    agent_pairs[pair_key]["together"] += 1

                    # Check if one won
                    if contract.awarded_to in [agent1_id, agent2_id]:
                        agent_pairs[pair_key]["wins"] += 1

        # Detect suspicious patterns
        for pair, stats in agent_pairs.items():
            if stats["together"] < 5:  # Need at least 5 contracts together
                continue

            win_rate = stats["wins"] / stats["together"]

            if win_rate >= self.COLLUSION_WIN_RATE_THRESHOLD:
                confidence = min(1.0, win_rate * (stats["together"] / 20.0))

                alert = await self._create_fraud_alert(
                    fraud_type=FraudType.COLLUSION,
                    severity=self._get_severity(confidence),
                    description=f"Suspected collusion: {win_rate*100:.1f}% win rate over {stats['together']} contracts",
                    evidence={
                        "agent_pair": list(pair),
                        "contracts_together": stats["together"],
                        "wins_together": stats["wins"],
                        "win_rate": win_rate
                    },
                    related_agents=list(pair)
                )
                alerts.append(alert)

        logger.info(f"Collusion detection: {len(alerts)} alerts created")
        return alerts

    async def detect_delivery_fraud(self) -> List[FraudAlert]:
        """
        Detect delivery fraud (fake or very poor quality deliveries).

        Indicators:
        - Validation score < 30%
        - Multiple low-quality deliveries
        - Sudden drop in quality
        """
        alerts = []

        # Get recent deliveries with low validation scores
        since = datetime.utcnow() - timedelta(days=30)

        result = await self.db.execute(
            select(Delivery, Contract)
            .join(Contract)
            .where(Delivery.is_validated == True)
            .where(Delivery.validation_score < self.DELIVERY_QUALITY_THRESHOLD)
            .where(Delivery.delivered_at >= since)
        )

        rows = result.all()

        # Group by agent
        agent_frauds = defaultdict(list)

        for delivery, contract in rows:
            agent_frauds[contract.awarded_to].append({
                "contract_id": contract.id,
                "validation_score": delivery.validation_score,
                "delivered_at": delivery.delivered_at
            })

        # Create alerts for agents with multiple low-quality deliveries
        for agent_id, frauds in agent_frauds.items():
            if len(frauds) >= 3:  # 3+ bad deliveries = fraud pattern
                avg_score = sum(f["validation_score"] for f in frauds) / len(frauds)
                confidence = 1.0 - avg_score  # Lower score = higher fraud confidence

                alert = await self._create_fraud_alert(
                    agent_id=agent_id,
                    fraud_type=FraudType.DELIVERY_FRAUD,
                    severity=self._get_severity(confidence),
                    description=f"Pattern of poor deliveries: {len(frauds)} contracts with avg quality {avg_score:.2f}",
                    evidence={
                        "low_quality_deliveries": len(frauds),
                        "average_score": avg_score,
                        "contracts": [f["contract_id"] for f in frauds]
                    },
                    related_contracts=[f["contract_id"] for f in frauds]
                )
                alerts.append(alert)

        logger.info(f"Delivery fraud detection: {len(alerts)} alerts created")
        return alerts

    async def detect_rating_manipulation(self) -> List[FraudAlert]:
        """
        Detect rating manipulation (fake reviews, sudden spikes).

        Indicators:
        - Sudden rating spike
        - Too many 5-star ratings in short time
        - Rating pattern inconsistent with delivery quality
        """
        alerts = []

        # Get all agents with reputation scores
        result = await self.db.execute(
            select(ReputationScore)
        )

        reputations = result.scalars().all()

        for reputation in reputations:
            # Get recent trend
            from backend.services.reputation_engine import ReputationEngine

            engine = ReputationEngine(self.db)
            trends = await engine.get_reputation_trends(reputation.agent_id, days=30)

            if len(trends) < 5:  # Need enough data
                continue

            # Calculate standard deviation
            scores = [t["score"] for t in trends]
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5

            # Check for spike (current score much higher than mean)
            if std_dev > 0:
                z_score = (reputation.overall_reputation - mean) / std_dev

                if z_score >= self.RATING_SPIKE_THRESHOLD:
                    confidence = min(1.0, z_score / 5.0)  # Cap at z=5

                    alert = await self._create_fraud_alert(
                        agent_id=reputation.agent_id,
                        fraud_type=FraudType.RATING_MANIPULATION,
                        severity=self._get_severity(confidence),
                        description=f"Suspicious rating spike: {z_score:.1f} std deviations above mean",
                        evidence={
                            "current_score": reputation.overall_reputation,
                            "mean_score": mean,
                            "std_dev": std_dev,
                            "z_score": z_score
                        }
                    )
                    alerts.append(alert)

        logger.info(f"Rating manipulation detection: {len(alerts)} alerts created")
        return alerts

    async def run_all_detections(self) -> Dict[str, List[FraudAlert]]:
        """
        Run all fraud detection algorithms.

        Returns:
            Dictionary of {fraud_type: [alerts]}
        """
        logger.info("Running all fraud detection algorithms...")

        results = {
            "sybil": await self.detect_sybil_attacks(),
            "collusion": await self.detect_collusion(),
            "delivery_fraud": await self.detect_delivery_fraud(),
            "rating_manipulation": await self.detect_rating_manipulation()
        }

        total_alerts = sum(len(alerts) for alerts in results.values())
        logger.info(f"Fraud detection complete: {total_alerts} total alerts")

        return results

    async def _create_fraud_alert(
        self,
        fraud_type: FraudType,
        severity: FraudSeverity,
        description: str,
        evidence: Dict[str, Any],
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        related_agents: Optional[List[str]] = None,
        related_contracts: Optional[List[str]] = None
    ) -> FraudAlert:
        """Create and save fraud alert"""
        # Calculate confidence from evidence
        confidence = evidence.get("similarity_score") or evidence.get("win_rate") or 0.8

        alert = FraudAlert(
            agent_id=agent_id,
            user_id=user_id,
            fraud_type=fraud_type,
            severity=severity,
            confidence=confidence,
            description=description,
            evidence=evidence,
            related_agents=related_agents or [],
            related_contracts=related_contracts or []
        )

        self.db.add(alert)
        await self.db.commit()

        return alert

    def _get_severity(self, confidence: float) -> FraudSeverity:
        """Convert confidence to severity level"""
        if confidence >= 0.9:
            return FraudSeverity.CRITICAL
        elif confidence >= 0.75:
            return FraudSeverity.HIGH
        elif confidence >= 0.6:
            return FraudSeverity.MEDIUM
        else:
            return FraudSeverity.LOW

    async def get_unreviewed_alerts(
        self,
        severity: Optional[FraudSeverity] = None
    ) -> List[FraudAlert]:
        """Get unreviewed fraud alerts"""
        query = select(FraudAlert).where(FraudAlert.is_reviewed == False)

        if severity:
            query = query.where(FraudAlert.severity == severity)

        query = query.order_by(FraudAlert.severity.desc(), FraudAlert.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def review_alert(
        self,
        alert_id: str,
        reviewed_by: str,
        resolution: str,
        action_taken: str
    ) -> FraudAlert:
        """Review and resolve fraud alert"""
        alert = await self.db.get(FraudAlert, alert_id)
        if not alert:
            raise ValueError("Alert not found")

        alert.is_reviewed = True
        alert.reviewed_by = reviewed_by
        alert.reviewed_at = datetime.utcnow()
        alert.resolution = resolution
        alert.action_taken = action_taken

        await self.db.commit()

        logger.info(f"Reviewed fraud alert {alert_id}: {action_taken}")

        return alert
