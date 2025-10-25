"""
Contract Manager - Task Lifecycle Management

Handles contracts from OPEN → BIDDING → AWARDED → VALIDATED → SETTLED
"""

import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum


class ContractStatus(str, Enum):
    OPEN = "OPEN"
    BIDDING = "BIDDING"
    AWARDED = "AWARDED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    VALIDATED = "VALIDATED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass
class TaskContract:
    contract_id: str
    issuer: str
    intent: str
    context: Dict[str, Any]
    reward_amount: float = 5.0
    reward_currency: str = "USD"
    status: ContractStatus = ContractStatus.OPEN
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    awarded_to: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value
        }


@dataclass
class Bid:
    bid_id: str
    contract_id: str
    agent_id: str
    agent_name: str
    price: float
    eta_seconds: float
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Delivery:
    contract_id: str
    agent_id: str
    data: Dict[str, Any]
    delivered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)


# In-memory storage
contracts_db: Dict[str, TaskContract] = {}
bids_db: Dict[str, List[Bid]] = {}  # contract_id -> List[Bid]
deliveries_db: Dict[str, Delivery] = {}  # contract_id -> Delivery


class ContractManager:
    """Manages contract lifecycle"""
    
    def __init__(self):
        self.contracts = contracts_db
        self.bids = bids_db
        self.deliveries = deliveries_db
        self.event_handlers = []
    
    def on_event(self, handler):
        """Register event handler"""
        self.event_handlers.append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict):
        """Emit event to all handlers"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"❌ Event handler error: {e}")
    
    async def create_contract(self, contract: TaskContract) -> str:
        """Create new contract"""
        
        # Set expiry if not provided (default 5 minutes)
        if not contract.expires_at:
            expires = datetime.now() + timedelta(minutes=5)
            contract.expires_at = expires.isoformat()
        
        # Store contract
        self.contracts[contract.contract_id] = contract
        self.bids[contract.contract_id] = []
        
        # Emit event
        await self._emit_event("contract_announced", contract.to_dict())
        
        print(f"📢 Contract announced: {contract.contract_id} ({contract.intent})")
        return contract.contract_id
    
    async def submit_bid(self, bid: Bid) -> str:
        """Submit bid for contract"""
        
        contract = self.contracts.get(bid.contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {bid.contract_id}")
        
        if contract.status not in [ContractStatus.OPEN, ContractStatus.BIDDING]:
            raise ValueError(f"Contract not accepting bids: {contract.status}")
        
        # Store bid
        self.bids[bid.contract_id].append(bid)
        
        # Update contract status
        contract.status = ContractStatus.BIDDING
        
        # Emit event
        await self._emit_event("bid_submitted", {
            **bid.to_dict(),
            "total_bids": len(self.bids[bid.contract_id])
        })
        
        print(f"🙋 Bid submitted by {bid.agent_name} for {bid.contract_id}: ${bid.price}")
        return bid.bid_id
    
    async def award_contract(
        self, 
        contract_id: str, 
        strategy: str = "lowest_price",
        user_id: Optional[str] = None,
        user_preferences: Optional[Dict] = None
    ) -> Optional[str]:
        """Award contract to winning agent
        
        Args:
            contract_id: Contract ID
            strategy: Award strategy ('lowest_price', 'reputation_weighted', 'user_preferences')
            user_id: User ID (for preference-based awarding)
            user_preferences: User preference weights (overrides user_id lookup)
        """
        
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")
        
        bids = self.bids.get(contract_id, [])
        if not bids:
            print(f"⚠️ No bids for contract {contract_id}")
            return None
        
        # Select winner based on strategy
        if strategy == "user_preferences" and (user_id or user_preferences):
            # Use user preference-based scoring
            from backend.mesh.preferences import preference_manager
            
            # Convert bids to dict format for scoring
            bid_dicts = []
            for bid in bids:
                bid_dict = bid.to_dict()
                bid_dict["agent_trust_score"] = 0.8  # TODO: Get from discovery service
                bid_dicts.append(bid_dict)
            
            # Rank by user preferences
            if user_id:
                ranked = preference_manager.rank_bids(user_id, bid_dicts)
            else:
                # Use provided preferences
                from backend.mesh.preferences import PreferenceManager, UserPreferences
                temp_manager = PreferenceManager()
                temp_prefs = UserPreferences(user_id="temp", **user_preferences)
                temp_manager.set_preferences(temp_prefs)
                ranked = temp_manager.rank_bids("temp", bid_dicts)
            
            # Get highest scoring bid
            if not ranked or ranked[0]["preference_score"] == 0:
                print(f"⚠️ No bids matched user preferences for {contract_id}")
                return None
            
            winner_dict = ranked[0]
            winner = next(b for b in bids if b.bid_id == winner_dict["bid_id"])
            
        elif strategy == "lowest_price":
            winner = min(bids, key=lambda b: b.price)
        elif strategy == "reputation_weighted":
            # For now, use confidence as proxy for reputation
            winner = max(bids, key=lambda b: b.confidence - (0.3 * b.price))
        else:
            winner = bids[0]
        
        # Update contract
        contract.status = ContractStatus.AWARDED
        contract.awarded_to = [winner.agent_id]
        
        # Emit event
        await self._emit_event("contract_awarded", {
            "contract_id": contract_id,
            "winner": {
                "agent_id": winner.agent_id,
                "agent_name": winner.agent_name,
                "price": winner.price,
                "eta_seconds": winner.eta_seconds
            },
            "total_bids": len(bids)
        })
        
        print(f"🏆 Contract awarded to {winner.agent_name} (${winner.price})")
        return winner.agent_id
    
    async def deliver_result(self, delivery: Delivery):
        """Agent delivers result"""
        
        contract = self.contracts.get(delivery.contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {delivery.contract_id}")
        
        # Store delivery
        self.deliveries[delivery.contract_id] = delivery
        
        # Update status
        contract.status = ContractStatus.DELIVERED
        
        # Emit event
        await self._emit_event("contract_delivered", delivery.to_dict())
        
        print(f"📦 Result delivered for {delivery.contract_id}")
    
    async def validate_and_settle(self, contract_id: str):
        """Validate delivery and settle payment"""
        
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")
        
        delivery = self.deliveries.get(contract_id)
        if not delivery:
            raise ValueError(f"No delivery for contract: {contract_id}")
        
        # Simple validation (just check delivery exists)
        contract.status = ContractStatus.VALIDATED
        
        # Settle (in production, release escrow)
        contract.status = ContractStatus.SETTLED
        
        # Emit event
        await self._emit_event("contract_settled", {
            "contract_id": contract_id,
            "agent_id": delivery.agent_id,
            "amount": contract.reward_amount,
            "currency": contract.reward_currency
        })
        
        print(f"✅ Contract settled: {contract_id}")
    
    def get_contract(self, contract_id: str) -> Optional[TaskContract]:
        """Get contract by ID"""
        return self.contracts.get(contract_id)
    
    def get_bids(self, contract_id: str) -> List[Bid]:
        """Get all bids for a contract"""
        return self.bids.get(contract_id, [])
    
    def list_contracts(self, status: Optional[ContractStatus] = None) -> List[TaskContract]:
        """List contracts, optionally filtered by status"""
        if status:
            return [c for c in self.contracts.values() if c.status == status]
        return list(self.contracts.values())


# Global contract manager
contract_manager = ContractManager()


async def test_contract_lifecycle():
    """Test full contract lifecycle"""
    
    print("\n" + "="*60)
    print("CONTRACT LIFECYCLE TEST")
    print("="*60 + "\n")
    
    # Create contract
    contract = TaskContract(
        contract_id=str(uuid.uuid4())[:8],
        issuer="user-aiden",
        intent="hotel_search",
        context={
            "city": "San Francisco",
            "checkin": "2026-03-12",
            "checkout": "2026-03-15",
            "budget": 200
        },
        reward_amount=5.0
    )
    
    await contract_manager.create_contract(contract)
    
    # Simulate bids from 3 agents
    await asyncio.sleep(0.5)
    
    bid1 = Bid(
        bid_id=str(uuid.uuid4())[:8],
        contract_id=contract.contract_id,
        agent_id="hotel-agent-1",
        agent_name="HotelBot Premium",
        price=3.50,
        eta_seconds=5.0,
        confidence=0.95
    )
    
    bid2 = Bid(
        bid_id=str(uuid.uuid4())[:8],
        contract_id=contract.contract_id,
        agent_id="hotel-agent-2",
        agent_name="HotelBot Budget",
        price=2.00,
        eta_seconds=8.0,
        confidence=0.80
    )
    
    bid3 = Bid(
        bid_id=str(uuid.uuid4())[:8],
        contract_id=contract.contract_id,
        agent_id="hotel-agent-3",
        agent_name="HotelBot Express",
        price=4.00,
        eta_seconds=3.0,
        confidence=0.92
    )
    
    await contract_manager.submit_bid(bid1)
    await contract_manager.submit_bid(bid2)
    await contract_manager.submit_bid(bid3)
    
    # Award contract (lowest price strategy)
    await asyncio.sleep(0.5)
    winner_id = await contract_manager.award_contract(contract.contract_id, strategy="lowest_price")
    
    # Winner delivers result
    await asyncio.sleep(1.0)
    delivery = Delivery(
        contract_id=contract.contract_id,
        agent_id=winner_id,
        data={
            "hotels": [
                {"name": "Hilton SF", "price": 180, "rating": 4.5},
                {"name": "Marriott SF", "price": 195, "rating": 4.7}
            ]
        }
    )
    
    await contract_manager.deliver_result(delivery)
    
    # Validate and settle
    await asyncio.sleep(0.5)
    await contract_manager.validate_and_settle(contract.contract_id)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
    
    # Show final state
    final_contract = contract_manager.get_contract(contract.contract_id)
    print(f"Final Status: {final_contract.status}")
    print(f"Awarded To: {final_contract.awarded_to}")


if __name__ == "__main__":
    asyncio.run(test_contract_lifecycle())
