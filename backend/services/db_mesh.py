"""
Database-backed Mesh Protocol Services

Replaces in-memory storage with PostgreSQL + reputation system.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Dict, Optional
from datetime import datetime
import logging

from backend.database.models import (
    Contract, Bid, Delivery, UserPreference, Agent,
    ContractStatus as DBContractStatus
)
from backend.services.reputation import ReputationManager

logger = logging.getLogger(__name__)


class DBContractManager:
    """Database-backed contract manager"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_contract(
        self,
        user_id: str,
        intent: str,
        context: Dict,
        reward_amount: float = 5.0
    ) -> str:
        """Create new contract"""
        
        contract = Contract(
            user_id=user_id,
            intent=intent,
            context=context,
            reward_amount=reward_amount,
            status=DBContractStatus.BIDDING
        )
        
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        
        logger.info(f"📝 Contract created: {contract.id} ({intent})")
        return contract.id
    
    async def submit_bid(
        self,
        contract_id: str,
        agent_id: str,
        price: float,
        eta_seconds: float,
        confidence: float
    ) -> str:
        """Submit bid on contract"""
        
        bid = Bid(
            contract_id=contract_id,
            agent_id=agent_id,
            price=price,
            eta_seconds=eta_seconds,
            confidence=confidence
        )
        
        self.db.add(bid)
        await self.db.commit()
        await self.db.refresh(bid)
        
        logger.info(f"🙋 Bid submitted: {agent_id} → {contract_id} (${price})")
        return bid.id
    
    async def award_contract(
        self,
        contract_id: str,
        user_id: Optional[str] = None,
        strategy: str = "user_preferences"
    ) -> Optional[str]:
        """Award contract to best bidder
        
        Args:
            contract_id: Contract ID
            user_id: User ID for preference-based awarding
            strategy: "user_preferences", "lowest_price", "highest_trust"
        
        Returns:
            Winning agent ID or None
        """
        
        # Get contract
        contract_query = select(Contract).where(Contract.id == contract_id)
        result = await self.db.execute(contract_query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            logger.error(f"❌ Contract not found: {contract_id}")
            return None
        
        # Get bids
        bids_query = select(Bid).where(Bid.contract_id == contract_id)
        result = await self.db.execute(bids_query)
        bids = result.scalars().all()
        
        if not bids:
            logger.warning(f"⚠️ No bids for contract {contract_id}")
            return None
        
        # Get trust scores for all bidding agents
        bid_scores = []
        for bid in bids:
            trust_score = await ReputationManager.get_trust_score(self.db, bid.agent_id)
            bid_scores.append({
                "bid": bid,
                "trust_score": trust_score
            })
        
        # Select winner based on strategy
        if strategy == "user_preferences" and user_id:
            winner = await self._award_by_preferences(user_id, bid_scores)
        elif strategy == "lowest_price":
            winner = min(bid_scores, key=lambda x: x["bid"].price)["bid"]
        elif strategy == "highest_trust":
            winner = max(bid_scores, key=lambda x: x["trust_score"])["bid"]
        else:
            # Default to user preferences
            winner = await self._award_by_preferences(user_id or contract.user_id, bid_scores)
        
        if not winner:
            logger.warning(f"⚠️ No suitable winner for {contract_id}")
            return None
        
        # Update contract
        contract.status = DBContractStatus.AWARDED
        contract.awarded_to = winner.agent_id
        contract.awarded_at = datetime.now()
        
        await self.db.commit()
        
        logger.info(f"🏆 Contract awarded: {contract_id} → {winner.agent_id} (${winner.price})")
        return winner.agent_id
    
    async def _award_by_preferences(
        self,
        user_id: str,
        bid_scores: List[Dict]
    ) -> Optional[Bid]:
        """Award based on user preferences"""
        
        # Get user preferences
        pref_query = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(pref_query)
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            # Default balanced preferences
            price_w = performance_w = speed_w = reputation_w = 25.0
            max_price = None
            min_confidence = 0.0
        else:
            price_w = prefs.price_weight
            performance_w = prefs.performance_weight
            speed_w = prefs.speed_weight
            reputation_w = prefs.reputation_weight
            max_price = prefs.max_price
            min_confidence = prefs.min_confidence
        
        # Score each bid
        scored_bids = []
        for item in bid_scores:
            bid = item["bid"]
            trust = item["trust_score"]
            
            # Apply filters
            if max_price and bid.price > max_price:
                continue
            if bid.confidence < min_confidence:
                continue
            
            # Calculate normalized scores (0-1)
            price_score = 1.0 - min(bid.price / 100.0, 1.0)  # Lower = better
            performance_score = bid.confidence  # Higher = better
            speed_score = 1.0 - min(bid.eta_seconds / 60.0, 1.0)  # Lower = better
            reputation_score = trust  # Higher = better
            
            # Weighted total
            total_score = (
                (price_score * price_w) +
                (performance_score * performance_w) +
                (speed_score * speed_w) +
                (reputation_score * reputation_w)
            )
            
            scored_bids.append({
                "bid": bid,
                "score": total_score
            })
        
        if not scored_bids:
            return None
        
        # Return highest scoring bid
        winner = max(scored_bids, key=lambda x: x["score"])
        return winner["bid"]
    
    async def deliver_result(
        self,
        contract_id: str,
        agent_id: str,
        data: Dict
    ):
        """Agent delivers result"""
        
        delivery = Delivery(
            contract_id=contract_id,
            agent_id=agent_id,
            data=data
        )
        
        self.db.add(delivery)
        
        # Update contract status
        contract_query = select(Contract).where(Contract.id == contract_id)
        result = await self.db.execute(contract_query)
        contract = result.scalar_one_or_none()
        
        if contract:
            contract.status = DBContractStatus.DELIVERED
        
        await self.db.commit()
        
        logger.info(f"📦 Result delivered: {contract_id} by {agent_id}")
    
    async def settle_contract(self, contract_id: str):
        """Settle contract and record metrics"""
        
        # Get contract + bid + delivery
        contract_query = select(Contract).where(Contract.id == contract_id)
        result = await self.db.execute(contract_query)
        contract = result.scalar_one_or_none()
        
        if not contract or not contract.awarded_to:
            logger.error(f"❌ Cannot settle {contract_id}")
            return
        
        # Get winning bid
        bid_query = select(Bid).where(
            and_(
                Bid.contract_id == contract_id,
                Bid.agent_id == contract.awarded_to
            )
        )
        result = await self.db.execute(bid_query)
        bid = result.scalar_one_or_none()
        
        # Get delivery
        delivery_query = select(Delivery).where(Delivery.contract_id == contract_id)
        result = await self.db.execute(delivery_query)
        delivery = result.scalar_one_or_none()
        
        if not bid or not delivery:
            logger.error(f"❌ Missing bid/delivery for {contract_id}")
            return
        
        # Calculate execution time
        execution_time = (delivery.delivered_at - contract.awarded_at).total_seconds()
        promised_time = bid.eta_seconds
        success = True  # TODO: Add validation logic
        
        # Record metric for reputation
        await ReputationManager.record_metric(
            self.db,
            agent_id=contract.awarded_to,
            contract_id=contract_id,
            execution_time=execution_time,
            promised_time=promised_time,
            success=success,
            user_rating=None  # User can rate later
        )
        
        # Update contract
        contract.status = DBContractStatus.SETTLED
        contract.completed_at = datetime.now()
        
        # Mark delivery validated
        delivery.is_validated = True
        delivery.validated_at = datetime.now()
        
        await self.db.commit()
        
        logger.info(f"✅ Contract settled: {contract_id} (${contract.reward_amount} to {contract.awarded_to})")
    
    async def get_contract(self, contract_id: str) -> Optional[Contract]:
        """Get contract by ID"""
        query = select(Contract).where(Contract.id == contract_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_bids(self, contract_id: str) -> List[Bid]:
        """Get all bids for contract"""
        query = select(Bid).where(Bid.contract_id == contract_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_contracts(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Contract]:
        """List contracts with filters"""
        
        conditions = []
        if user_id:
            conditions.append(Contract.user_id == user_id)
        if status:
            conditions.append(Contract.status == status)
        
        query = select(Contract)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Contract.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()


class DBPreferenceManager:
    """Database-backed preference manager"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def set_preferences(
        self,
        user_id: str,
        price_weight: float = 25.0,
        performance_weight: float = 25.0,
        speed_weight: float = 25.0,
        reputation_weight: float = 25.0,
        max_price: Optional[float] = None,
        min_confidence: float = 0.0,
        max_latency: Optional[float] = None,
        min_reputation: float = 0.0,
        free_only: bool = False
    ):
        """Set user preferences"""
        
        # Check if exists
        query = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.price_weight = price_weight
            existing.performance_weight = performance_weight
            existing.speed_weight = speed_weight
            existing.reputation_weight = reputation_weight
            existing.max_price = max_price
            existing.min_confidence = min_confidence
            existing.max_latency = max_latency
            existing.min_reputation = min_reputation
            existing.free_only = free_only
            existing.updated_at = datetime.now()
        else:
            # Create
            pref = UserPreference(
                user_id=user_id,
                price_weight=price_weight,
                performance_weight=performance_weight,
                speed_weight=speed_weight,
                reputation_weight=reputation_weight,
                max_price=max_price,
                min_confidence=min_confidence,
                max_latency=max_latency,
                min_reputation=min_reputation,
                free_only=free_only
            )
            self.db.add(pref)
        
        await self.db.commit()
        logger.info(f"⚙️ Preferences updated for user {user_id}")
    
    async def get_preferences(self, user_id: str) -> Optional[UserPreference]:
        """Get user preferences"""
        query = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
