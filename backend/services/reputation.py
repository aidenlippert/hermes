"""
Agent Reputation & Trust Score System

Dynamically calculates agent trust scores based on:
- Success rate (40%)
- Latency performance (20%)
- User ratings (20%)
- Time on network (10%)
- Consistency (10%)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from backend.database.models import (
    Agent, AgentMetric, AgentTrustScore, Contract, Bid, Delivery
)

logger = logging.getLogger(__name__)


class ReputationManager:
    """Manages agent reputation and trust scores"""
    
    @staticmethod
    async def record_metric(
        db: AsyncSession,
        agent_id: str,
        contract_id: str,
        execution_time: float,
        promised_time: float,
        success: bool,
        user_rating: Optional[int] = None
    ):
        """Record performance metric for agent
        
        Args:
            agent_id: Agent ID
            contract_id: Contract ID
            execution_time: Actual time taken (seconds)
            promised_time: Promised time from bid (seconds)
            success: Whether execution succeeded
            user_rating: Optional 1-5 star rating from user
        """
        metric = AgentMetric(
            agent_id=agent_id,
            contract_id=contract_id,
            execution_time=execution_time,
            promised_time=promised_time,
            success=success,
            user_rating=user_rating
        )
        
        db.add(metric)
        await db.commit()
        
        logger.info(f"📊 Recorded metric for {agent_id}: {'✅' if success else '❌'}")
        
        # Recalculate trust score
        await ReputationManager.calculate_trust_score(db, agent_id)
    
    @staticmethod
    async def calculate_trust_score(db: AsyncSession, agent_id: str) -> float:
        """Calculate comprehensive trust score for agent
        
        Returns:
            Trust score 0.0 - 1.0
        """
        
        # Get all metrics for agent
        metrics_query = select(AgentMetric).where(AgentMetric.agent_id == agent_id)
        result = await db.execute(metrics_query)
        metrics = result.scalars().all()
        
        if not metrics:
            # No data yet, default to 0.5
            return await ReputationManager._save_trust_score(
                db, agent_id,
                success_rate=0.5,
                latency_score=0.5,
                rating_score=0.5,
                uptime_score=0.0,
                trust_score=0.5,
                total_contracts=0,
                successful=0,
                failed=0
            )
        
        # 1. Success Rate (40% weight)
        total = len(metrics)
        successful = sum(1 for m in metrics if m.success)
        failed = total - successful
        success_rate = successful / total if total > 0 else 0.0
        
        # 2. Latency Score (20% weight)
        # How often does agent meet/beat promised time?
        latency_scores = []
        for m in metrics:
            if m.promised_time > 0:
                # 1.0 if faster than promised, proportional penalty if slower
                ratio = m.execution_time / m.promised_time
                score = max(0.0, min(1.0, 1.0 - (ratio - 1.0)))
                latency_scores.append(score)
        
        latency_score = sum(latency_scores) / len(latency_scores) if latency_scores else 0.5
        
        # 3. Rating Score (20% weight)
        # Average user ratings (1-5 stars) normalized to 0-1
        rated_metrics = [m for m in metrics if m.user_rating is not None]
        if rated_metrics:
            avg_rating = sum(m.user_rating for m in rated_metrics) / len(rated_metrics)
            rating_score = (avg_rating - 1) / 4.0  # Normalize 1-5 to 0-1
        else:
            rating_score = 0.5  # Default if no ratings
        
        # 4. Uptime Score (10% weight)
        # Time on network (older = more trusted)
        agent_query = select(Agent).where(Agent.id == agent_id)
        result = await db.execute(agent_query)
        agent = result.scalar_one_or_none()
        
        if agent and agent.created_at:
            days_active = (datetime.now() - agent.created_at.replace(tzinfo=None)).days
            # Max out at 365 days
            uptime_score = min(1.0, days_active / 365.0)
        else:
            uptime_score = 0.0
        
        # 5. Consistency Score (10% weight)
        # Variance in performance (lower variance = higher score)
        if len(latency_scores) > 1:
            mean = sum(latency_scores) / len(latency_scores)
            variance = sum((x - mean) ** 2 for x in latency_scores) / len(latency_scores)
            consistency_score = max(0.0, 1.0 - variance)
        else:
            consistency_score = 0.5
        
        # Calculate weighted trust score
        trust_score = (
            (success_rate * 0.40) +
            (latency_score * 0.20) +
            (rating_score * 0.20) +
            (uptime_score * 0.10) +
            (consistency_score * 0.10)
        )
        
        # Calculate stats
        avg_execution = sum(m.execution_time for m in metrics) / len(metrics)
        
        # Get earnings (from settled contracts)
        contracts_query = select(Contract).where(
            and_(
                Contract.awarded_to == agent_id,
                Contract.status == "settled"
            )
        )
        result = await db.execute(contracts_query)
        contracts = result.scalars().all()
        total_earnings = sum(c.reward_amount for c in contracts)
        
        # Save to database
        return await ReputationManager._save_trust_score(
            db, agent_id,
            success_rate=success_rate,
            latency_score=latency_score,
            rating_score=rating_score,
            uptime_score=uptime_score,
            trust_score=trust_score,
            total_contracts=total,
            successful=successful,
            failed=failed,
            avg_execution=avg_execution,
            total_earnings=total_earnings
        )
    
    @staticmethod
    async def _save_trust_score(
        db: AsyncSession,
        agent_id: str,
        success_rate: float,
        latency_score: float,
        rating_score: float,
        uptime_score: float,
        trust_score: float,
        total_contracts: int,
        successful: int,
        failed: int,
        avg_execution: float = 0.0,
        total_earnings: float = 0.0
    ) -> float:
        """Save calculated trust score to database"""
        
        # Check if exists
        query = select(AgentTrustScore).where(AgentTrustScore.agent_id == agent_id)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.success_rate = success_rate
            existing.latency_score = latency_score
            existing.rating_score = rating_score
            existing.uptime_score = uptime_score
            existing.trust_score = trust_score
            existing.total_contracts = total_contracts
            existing.successful_contracts = successful
            existing.failed_contracts = failed
            existing.average_execution_time = avg_execution
            existing.total_earnings = total_earnings
            existing.last_calculated = datetime.now()
        else:
            # Create
            score_obj = AgentTrustScore(
                agent_id=agent_id,
                success_rate=success_rate,
                latency_score=latency_score,
                rating_score=rating_score,
                uptime_score=uptime_score,
                trust_score=trust_score,
                total_contracts=total_contracts,
                successful_contracts=successful,
                failed_contracts=failed,
                average_execution_time=avg_execution,
                total_earnings=total_earnings
            )
            db.add(score_obj)
        
        await db.commit()
        
        logger.info(
            f"✅ Trust score updated for {agent_id}: "
            f"{trust_score:.2f} "
            f"({successful}/{total_contracts} success, "
            f"${total_earnings:.2f} earned)"
        )
        
        return trust_score
    
    @staticmethod
    async def get_trust_score(db: AsyncSession, agent_id: str) -> float:
        """Get current trust score for agent
        
        Returns:
            Trust score 0.0 - 1.0 (defaults to 0.5 if not calculated)
        """
        query = select(AgentTrustScore).where(AgentTrustScore.agent_id == agent_id)
        result = await db.execute(query)
        score = result.scalar_one_or_none()
        
        if score:
            return score.trust_score
        else:
            # Not calculated yet, trigger calculation
            return await ReputationManager.calculate_trust_score(db, agent_id)
    
    @staticmethod
    async def get_detailed_stats(db: AsyncSession, agent_id: str) -> Optional[Dict]:
        """Get detailed reputation stats for agent"""
        
        query = select(AgentTrustScore).where(AgentTrustScore.agent_id == agent_id)
        result = await db.execute(query)
        score = result.scalar_one_or_none()
        
        if not score:
            return None
        
        return {
            "trust_score": score.trust_score,
            "breakdown": {
                "success_rate": score.success_rate,
                "latency_performance": score.latency_score,
                "user_ratings": score.rating_score,
                "uptime": score.uptime_score
            },
            "statistics": {
                "total_contracts": score.total_contracts,
                "successful": score.successful_contracts,
                "failed": score.failed_contracts,
                "success_percentage": round(
                    (score.successful_contracts / score.total_contracts * 100) 
                    if score.total_contracts > 0 else 0, 1
                ),
                "average_execution_time": round(score.average_execution_time, 2),
                "total_earnings": round(score.total_earnings, 2)
            },
            "badges": ReputationManager._calculate_badges(score),
            "last_updated": score.last_calculated.isoformat() if score.last_calculated else None
        }
    
    @staticmethod
    def _calculate_badges(score: AgentTrustScore) -> list:
        """Calculate achievement badges for agent"""
        badges = []
        
        # Trust badges
        if score.trust_score >= 0.95:
            badges.append({"name": "Elite", "icon": "🏆", "description": "Top 5% trusted agent"})
        elif score.trust_score >= 0.85:
            badges.append({"name": "Verified Pro", "icon": "⭐", "description": "Highly trusted"})
        elif score.trust_score >= 0.70:
            badges.append({"name": "Verified", "icon": "✅", "description": "Trusted agent"})
        
        # Success badges
        if score.total_contracts >= 1000:
            badges.append({"name": "Veteran", "icon": "🎖️", "description": "1000+ contracts"})
        elif score.total_contracts >= 100:
            badges.append({"name": "Experienced", "icon": "💪", "description": "100+ contracts"})
        
        # Earnings badges
        if score.total_earnings >= 10000:
            badges.append({"name": "Top Earner", "icon": "💰", "description": "$10k+ earned"})
        elif score.total_earnings >= 1000:
            badges.append({"name": "Professional", "icon": "💵", "description": "$1k+ earned"})
        
        # Performance badges
        if score.success_rate >= 0.99:
            badges.append({"name": "Perfect", "icon": "🎯", "description": "99%+ success rate"})
        elif score.success_rate >= 0.95:
            badges.append({"name": "Reliable", "icon": "🔒", "description": "95%+ success rate"})
        
        if score.latency_score >= 0.90:
            badges.append({"name": "Lightning Fast", "icon": "⚡", "description": "Consistently fast"})
        
        return badges


# Background task for periodic recalculation
async def recalculate_all_trust_scores(db: AsyncSession):
    """Recalculate trust scores for all agents (run periodically)"""
    
    logger.info("🔄 Starting trust score recalculation for all agents...")
    
    # Get all agents
    query = select(Agent.id)
    result = await db.execute(query)
    agent_ids = [row[0] for row in result.all()]
    
    logger.info(f"📊 Recalculating {len(agent_ids)} agents...")
    
    for agent_id in agent_ids:
        try:
            await ReputationManager.calculate_trust_score(db, agent_id)
        except Exception as e:
            logger.error(f"❌ Failed to calculate trust for {agent_id}: {e}")
    
    logger.info("✅ Trust score recalculation complete!")


if __name__ == "__main__":
    import asyncio
    from backend.database.connection import AsyncSessionLocal, init_db
    
    async def test_reputation():
        """Test reputation system"""
        
        await init_db()
        
        async with AsyncSessionLocal() as db:
            # Test recording a metric
            test_agent_id = "test-agent-123"
            test_contract_id = "test-contract-456"
            
            print("\n📊 Testing Reputation System\n")
            
            # Record some test metrics
            print("1️⃣ Recording test metrics...")
            await ReputationManager.record_metric(
                db, test_agent_id, test_contract_id,
                execution_time=2.5,
                promised_time=3.0,
                success=True,
                user_rating=5
            )
            
            await ReputationManager.record_metric(
                db, test_agent_id, f"{test_contract_id}-2",
                execution_time=1.8,
                promised_time=2.0,
                success=True,
                user_rating=4
            )
            
            await ReputationManager.record_metric(
                db, test_agent_id, f"{test_contract_id}-3",
                execution_time=5.0,
                promised_time=3.0,
                success=False,
                user_rating=2
            )
            
            # Get trust score
            print("\n2️⃣ Calculating trust score...")
            score = await ReputationManager.get_trust_score(db, test_agent_id)
            print(f"   Trust Score: {score:.2f}")
            
            # Get detailed stats
            print("\n3️⃣ Detailed stats:")
            stats = await ReputationManager.get_detailed_stats(db, test_agent_id)
            if stats:
                print(f"   Overall Score: {stats['trust_score']:.2f}")
                print(f"   Success Rate: {stats['breakdown']['success_rate']:.2%}")
                print(f"   Latency Performance: {stats['breakdown']['latency_performance']:.2%}")
                print(f"   User Ratings: {stats['breakdown']['user_ratings']:.2%}")
                print(f"   Total Contracts: {stats['statistics']['total_contracts']}")
                print(f"   Success: {stats['statistics']['successful']} | Failed: {stats['statistics']['failed']}")
                print(f"\n   Badges:")
                for badge in stats['badges']:
                    print(f"     {badge['icon']} {badge['name']}: {badge['description']}")
            
            print("\n✅ Test complete!")
    
    asyncio.run(test_reputation())
