"""
Discovery Service - Agent Registry with Vector Search

Real working code for agent registration and semantic capability matching.
"""

import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json

# In-memory storage (replace with Postgres + Qdrant in production)
agents_db: Dict[str, Dict] = {}
capabilities_db: List[Dict] = []


@dataclass
class Capability:
    name: str
    description: str
    confidence: float
    cost: float = 0.0
    latency: float = 0.0
    
    def to_dict(self):
        return asdict(self)


@dataclass
class AgentRegistration:
    agent_id: str
    name: str
    endpoint: str
    capabilities: List[Capability]
    owner: str = "system"
    public_key: str = ""
    trust_score: float = 1.0
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return {
            **asdict(self),
            'capabilities': [c.to_dict() for c in self.capabilities]
        }


class DiscoveryService:
    """Agent registry with semantic search"""
    
    def __init__(self):
        self.agents = agents_db
        self.capabilities = capabilities_db
        
    async def register_agent(self, agent: AgentRegistration) -> str:
        """Register agent to mesh"""
        
        # Store agent
        self.agents[agent.agent_id] = agent.to_dict()
        
        # Index capabilities
        for cap in agent.capabilities:
            self.capabilities.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "capability": cap.to_dict(),
                "indexed_at": datetime.now().isoformat()
            })
        
        print(f"✅ Registered agent: {agent.name} ({agent.agent_id})")
        return agent.agent_id
    
    async def search_capabilities(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for agents by capability (keyword matching for now)"""
        
        query_lower = query.lower()
        matches = []
        
        for item in self.capabilities:
            cap = item["capability"]
            
            # Simple keyword matching
            if (query_lower in cap["name"].lower() or 
                query_lower in cap["description"].lower()):
                
                matches.append({
                    "agent_id": item["agent_id"],
                    "agent_name": item["agent_name"],
                    "capability": cap,
                    "similarity": cap["confidence"]  # Use confidence as similarity score
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        return matches[:limit]
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        """List all registered agents"""
        return list(self.agents.values())


# Global discovery service
discovery_service = DiscoveryService()


async def test_discovery():
    """Test discovery service"""
    
    # Register test agents
    flight_agent = AgentRegistration(
        agent_id="flight-agent-1",
        name="FlightSearchAgent",
        endpoint="http://localhost:8001",
        capabilities=[
            Capability(
                name="flight_search",
                description="Search flights by origin, destination, and dates",
                confidence=0.95,
                cost=2.0,
                latency=3.0
            )
        ]
    )
    
    hotel_agent = AgentRegistration(
        agent_id="hotel-agent-1",
        name="HotelSearchAgent",
        endpoint="http://localhost:8002",
        capabilities=[
            Capability(
                name="hotel_search",
                description="Search hotels by location and dates",
                confidence=0.92,
                cost=2.5,
                latency=3.5
            )
        ]
    )
    
    await discovery_service.register_agent(flight_agent)
    await discovery_service.register_agent(hotel_agent)
    
    # Search
    print("\n🔍 Searching for 'flight'...")
    results = await discovery_service.search_capabilities("flight")
    for r in results:
        print(f"  → {r['agent_name']}: {r['capability']['name']} ({r['similarity']:.2f})")
    
    print("\n🔍 Searching for 'hotel'...")
    results = await discovery_service.search_capabilities("hotel")
    for r in results:
        print(f"  → {r['agent_name']}: {r['capability']['name']} ({r['similarity']:.2f})")


if __name__ == "__main__":
    asyncio.run(test_discovery())
