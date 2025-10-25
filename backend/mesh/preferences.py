"""
User Preference System - Customizable Agent Selection

Users can adjust weights for price vs performance vs speed vs reputation.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class PreferencePreset(str, Enum):
    """Built-in preference presets"""
    CHEAPEST = "cheapest"          # 100% price, ignore performance
    FASTEST = "fastest"            # 100% speed, ignore cost
    BALANCED = "balanced"          # Equal weights (25% each)
    PREMIUM = "premium"            # 80% performance, 20% reputation
    FREE_ONLY = "free_only"        # Only free agents
    REPUTATION = "reputation"      # 100% reputation/trust score


@dataclass
class UserPreferences:
    """User's agent selection preferences"""
    user_id: str
    
    # Weights (must sum to 100)
    price_weight: float = 25.0          # Lower price = better
    performance_weight: float = 25.0    # Higher confidence = better
    speed_weight: float = 25.0          # Lower latency = better
    reputation_weight: float = 25.0     # Higher trust score = better
    
    # Filters
    max_price: Optional[float] = None   # Maximum price willing to pay
    min_confidence: float = 0.0         # Minimum confidence threshold
    max_latency: Optional[float] = None # Maximum acceptable latency (seconds)
    min_reputation: float = 0.0         # Minimum trust score
    
    # Special modes
    free_only: bool = False             # Only bid on free agents
    
    def to_dict(self):
        return asdict(self)
    
    def validate(self):
        """Ensure weights sum to 100"""
        total = (self.price_weight + self.performance_weight + 
                 self.speed_weight + self.reputation_weight)
        
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Weights must sum to 100, got {total}")
    
    @classmethod
    def from_preset(cls, user_id: str, preset: PreferencePreset) -> "UserPreferences":
        """Create preferences from preset"""
        
        if preset == PreferencePreset.CHEAPEST:
            return cls(
                user_id=user_id,
                price_weight=100.0,
                performance_weight=0.0,
                speed_weight=0.0,
                reputation_weight=0.0
            )
        
        elif preset == PreferencePreset.FASTEST:
            return cls(
                user_id=user_id,
                price_weight=0.0,
                performance_weight=0.0,
                speed_weight=100.0,
                reputation_weight=0.0
            )
        
        elif preset == PreferencePreset.PREMIUM:
            return cls(
                user_id=user_id,
                price_weight=0.0,
                performance_weight=80.0,
                speed_weight=0.0,
                reputation_weight=20.0
            )
        
        elif preset == PreferencePreset.REPUTATION:
            return cls(
                user_id=user_id,
                price_weight=0.0,
                performance_weight=0.0,
                speed_weight=0.0,
                reputation_weight=100.0
            )
        
        elif preset == PreferencePreset.FREE_ONLY:
            return cls(
                user_id=user_id,
                price_weight=0.0,
                performance_weight=50.0,
                speed_weight=0.0,
                reputation_weight=50.0,
                max_price=0.0,
                free_only=True
            )
        
        else:  # BALANCED
            return cls(
                user_id=user_id,
                price_weight=25.0,
                performance_weight=25.0,
                speed_weight=25.0,
                reputation_weight=25.0
            )


class PreferenceManager:
    """Manages user preferences"""
    
    def __init__(self):
        # In-memory storage (move to database in production)
        self.preferences: Dict[str, UserPreferences] = {}
    
    def set_preferences(self, prefs: UserPreferences):
        """Set user preferences"""
        prefs.validate()
        self.preferences[prefs.user_id] = prefs
    
    def get_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences (default to balanced)"""
        if user_id not in self.preferences:
            return UserPreferences.from_preset(user_id, PreferencePreset.BALANCED)
        return self.preferences[user_id]
    
    def calculate_score(self, user_id: str, bid: Dict) -> float:
        """Calculate weighted score for a bid
        
        Higher score = better match for user preferences
        
        Args:
            user_id: User ID
            bid: Bid dict with keys: price, confidence, eta_seconds, agent_trust_score
        
        Returns:
            Weighted score (0-100)
        """
        prefs = self.get_preferences(user_id)
        
        # Apply filters first
        if prefs.max_price and bid.get("price", 0) > prefs.max_price:
            return 0.0
        
        if bid.get("confidence", 0) < prefs.min_confidence:
            return 0.0
        
        if prefs.max_latency and bid.get("eta_seconds", 999) > prefs.max_latency:
            return 0.0
        
        if bid.get("agent_trust_score", 0) < prefs.min_reputation:
            return 0.0
        
        if prefs.free_only and bid.get("price", 0) > 0:
            return 0.0
        
        # Calculate normalized scores (0-1 scale)
        # Lower is better for price and latency
        # Higher is better for confidence and reputation
        
        # Price score (inverse - lower price = higher score)
        # Assume max price anyone would pay is $100
        price_score = 1.0 - min(bid.get("price", 0) / 100.0, 1.0)
        
        # Performance score (confidence 0-1)
        performance_score = bid.get("confidence", 0.5)
        
        # Speed score (inverse - lower latency = higher score)
        # Assume max latency anyone would accept is 60 seconds
        speed_score = 1.0 - min(bid.get("eta_seconds", 30) / 60.0, 1.0)
        
        # Reputation score (trust score 0-1)
        reputation_score = bid.get("agent_trust_score", 0.5)
        
        # Calculate weighted score
        total_score = (
            (price_score * prefs.price_weight) +
            (performance_score * prefs.performance_weight) +
            (speed_score * prefs.speed_weight) +
            (reputation_score * prefs.reputation_weight)
        )
        
        return total_score
    
    def rank_bids(self, user_id: str, bids: List[Dict]) -> List[Dict]:
        """Rank bids based on user preferences
        
        Returns bids sorted by score (highest first)
        """
        scored_bids = []
        
        for bid in bids:
            score = self.calculate_score(user_id, bid)
            scored_bids.append({
                **bid,
                "preference_score": score
            })
        
        # Sort by score (descending)
        scored_bids.sort(key=lambda x: x["preference_score"], reverse=True)
        
        return scored_bids


# Global preference manager
preference_manager = PreferenceManager()


# Example usage
if __name__ == "__main__":
    
    # Test preferences
    prefs = UserPreferences.from_preset("user123", PreferencePreset.CHEAPEST)
    print(f"✅ Cheapest preset: {prefs.to_dict()}")
    
    prefs = UserPreferences.from_preset("user123", PreferencePreset.PREMIUM)
    print(f"✅ Premium preset: {prefs.to_dict()}")
    
    # Test scoring
    bids = [
        {"agent_id": "a1", "price": 5.0, "confidence": 0.95, "eta_seconds": 2.0, "agent_trust_score": 0.9},
        {"agent_id": "a2", "price": 1.0, "confidence": 0.7, "eta_seconds": 10.0, "agent_trust_score": 0.5},
        {"agent_id": "a3", "price": 0.0, "confidence": 0.6, "eta_seconds": 15.0, "agent_trust_score": 0.3},
    ]
    
    # Balanced
    manager = PreferenceManager()
    manager.set_preferences(UserPreferences.from_preset("user1", PreferencePreset.BALANCED))
    ranked = manager.rank_bids("user1", bids)
    print("\n🎯 BALANCED ranking:")
    for bid in ranked:
        print(f"  {bid['agent_id']}: score={bid['preference_score']:.2f} (${bid['price']}, {bid['confidence']:.0%} confidence)")
    
    # Cheapest
    manager.set_preferences(UserPreferences.from_preset("user2", PreferencePreset.CHEAPEST))
    ranked = manager.rank_bids("user2", bids)
    print("\n💰 CHEAPEST ranking:")
    for bid in ranked:
        print(f"  {bid['agent_id']}: score={bid['preference_score']:.2f} (${bid['price']}, {bid['confidence']:.0%} confidence)")
    
    # Premium
    manager.set_preferences(UserPreferences.from_preset("user3", PreferencePreset.PREMIUM))
    ranked = manager.rank_bids("user3", bids)
    print("\n⭐ PREMIUM ranking:")
    for bid in ranked:
        print(f"  {bid['agent_id']}: score={bid['preference_score']:.2f} (${bid['price']}, {bid['confidence']:.0%} confidence)")
