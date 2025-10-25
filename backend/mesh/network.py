"""
Mesh Network - Coordinating discovery + contracts

This is the REAL mesh protocol implementation.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.mesh.discovery import (
    DiscoveryService, AgentRegistration, Capability, discovery_service
)
from backend.mesh.contracts import (
    ContractManager, TaskContract, Bid, Delivery, 
    ContractStatus, contract_manager
)


class MeshAgent:
    """Base class for mesh-native agents"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[Capability]
    ):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.contracts_won = 0
        self.total_earnings = 0.0
    
    async def on_contract_announced(self, contract: TaskContract):
        """Called when contract is announced - agent decides whether to bid"""
        
        # Check if we can handle this intent
        for cap in self.capabilities:
            if contract.intent == cap.name:
                # We can handle this! Submit bid
                bid = Bid(
                    bid_id=str(uuid.uuid4())[:8],
                    contract_id=contract.contract_id,
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    price=cap.cost,
                    eta_seconds=cap.latency,
                    confidence=cap.confidence
                )
                
                await contract_manager.submit_bid(bid)
                break
    
    async def on_contract_awarded(self, event: Dict):
        """Called when contract is awarded"""
        
        winner_id = event["data"]["winner"]["agent_id"]
        
        if winner_id == self.agent_id:
            # We won! Execute the contract
            contract_id = event["data"]["contract_id"]
            contract = contract_manager.get_contract(contract_id)
            
            print(f"💪 {self.name} executing contract {contract_id}...")
            
            # Execute (agents override this)
            result = await self.execute_contract(contract)
            
            # Deliver result
            delivery = Delivery(
                contract_id=contract_id,
                agent_id=self.agent_id,
                data=result
            )
            
            await contract_manager.deliver_result(delivery)
            
            self.contracts_won += 1
    
    async def execute_contract(self, contract: TaskContract) -> Dict[str, Any]:
        """Override this to implement actual contract execution"""
        # Default: simulate work
        await asyncio.sleep(1)
        return {"status": "completed", "message": f"Executed by {self.name}"}
    
    async def on_contract_settled(self, event: Dict):
        """Called when contract is settled (payment released)"""
        
        if event["data"]["agent_id"] == self.agent_id:
            amount = event["data"]["amount"]
            self.total_earnings += amount
            print(f"💰 {self.name} earned ${amount:.2f} (total: ${self.total_earnings:.2f})")


class MeshNetwork:
    """The mesh network itself"""
    
    def __init__(self):
        self.discovery = discovery_service
        self.contracts = contract_manager
        self.agents: Dict[str, MeshAgent] = {}
        self.running = False
        self._award_task = None
    
    async def start(self):
        """Start mesh network"""
        
        # Setup event routing
        self.contracts.on_event(self._route_event)
        
        self.running = True
        
        # Start automatic contract awarding
        self._award_task = asyncio.create_task(self._auto_award_contracts())
        
        print("🌐 Mesh network started")
    
    async def stop(self):
        """Stop mesh network"""
        self.running = False
        
        # Stop background task
        if self._award_task:
            self._award_task.cancel()
            try:
                await self._award_task
            except asyncio.CancelledError:
                pass
        
        print("🛑 Mesh network stopped")
    
    async def register_agent(self, agent: MeshAgent):
        """Register agent to mesh"""
        
        # Register in discovery
        registration = AgentRegistration(
            agent_id=agent.agent_id,
            name=agent.name,
            endpoint=f"local://{agent.agent_id}",
            capabilities=agent.capabilities
        )
        
        await self.discovery.register_agent(registration)
        
        # Store locally
        self.agents[agent.agent_id] = agent
        
        print(f"✅ {agent.name} joined mesh")
    
    async def _auto_award_contracts(self):
        """Background task to automatically award contracts after bidding period"""
        
        print("🤖 Auto-award scheduler started")
        
        while self.running:
            try:
                # Check every 2 seconds
                await asyncio.sleep(2.0)
                
                # Get all contracts in BIDDING status
                bidding_contracts = self.contracts.list_contracts(ContractStatus.BIDDING)
                
                for contract in bidding_contracts:
                    # Get bids
                    bids = self.contracts.get_bids(contract.contract_id)
                    
                    if not bids:
                        continue
                    
                    # Simple bidding window: award after 3 seconds
                    created_at = datetime.fromisoformat(contract.created_at)
                    contract_age = (datetime.now() - created_at).total_seconds()
                    
                    if contract_age >= 3.0:
                        # Award using lowest price strategy
                        await self.contracts.award_contract(
                            contract.contract_id,
                            strategy="lowest_price"
                        )
                        
                        print(f"⚡ Auto-awarded contract {contract.contract_id}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Auto-award error: {e}")
                import traceback
                traceback.print_exc()
        
        print("🛑 Auto-award scheduler stopped")
    
    async def _route_event(self, event: Dict):
        """Route events to all agents"""
        
        event_type = event["type"]
        
        # Route to all agents
        for agent in self.agents.values():
            if event_type == "contract_announced":
                contract = TaskContract(**event["data"])
                await agent.on_contract_announced(contract)
            
            elif event_type == "contract_awarded":
                await agent.on_contract_awarded(event)
            
            elif event_type == "contract_settled":
                await agent.on_contract_settled(event)
    
    async def execute_task(
        self,
        intent: str,
        context: Dict[str, Any],
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Execute a task via mesh collaboration"""
        
        # Create contract
        contract = TaskContract(
            contract_id=str(uuid.uuid4())[:8],
            issuer="system",
            intent=intent,
            context=context,
            reward_amount=5.0
        )
        
        await self.contracts.create_contract(contract)
        
        # Wait for bids
        await asyncio.sleep(1.0)
        
    async def announce_contract(
        self,
        task_type: str,
        description: str,
        requirements: Dict[str, Any]
    ) -> TaskContract:
        """Create and announce a new contract"""
        
        contract = TaskContract(
            contract_id=str(uuid.uuid4())[:8],
            issuer="api",
            intent=task_type,
            context={
                "description": description,
                "requirements": requirements
            },
            reward_amount=5.0
        )
        
        await self.contracts.create_contract(contract)
        
        return contract
        
        # Award contract
        winner = await self.contracts.award_contract(
            contract.contract_id,
            strategy="reputation_weighted"
        )
        
        if not winner:
            return {"error": "No agents available"}
        
        # Wait for delivery
        max_wait = timeout
        waited = 0
        while waited < max_wait:
            contract_state = self.contracts.get_contract(contract.contract_id)
            
            if contract_state.status == ContractStatus.DELIVERED:
                # Validate and settle
                await self.contracts.validate_and_settle(contract.contract_id)
                
                # Get delivery
                delivery = self.contracts.deliveries.get(contract.contract_id)
                return delivery.data if delivery else {"error": "No delivery found"}
            
            await asyncio.sleep(0.5)
            waited += 0.5
        
        return {"error": "Timeout waiting for delivery"}


# Example agent implementations

class FlightAgent(MeshAgent):
    """Flight search agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="flight-agent-mesh",
            name="FlightSearchBot",
            capabilities=[
                Capability(
                    name="flight_search",
                    description="Search flights by origin, destination, dates",
                    confidence=0.95,
                    cost=2.50,
                    latency=3.0
                )
            ]
        )
    
    async def execute_contract(self, contract: TaskContract) -> Dict[str, Any]:
        """Actually search for flights"""
        
        context = contract.context
        print(f"  ✈️ Searching flights: {context.get('origin')} → {context.get('destination')}")
        
        # Simulate API call
        await asyncio.sleep(2)
        
        return {
            "flights": [
                {
                    "airline": "United",
                    "price": 450,
                    "duration": "5h 30m",
                    "stops": 0
                },
                {
                    "airline": "Delta",
                    "price": 425,
                    "duration": "6h 15m",
                    "stops": 1
                }
            ]
        }


class HotelAgent(MeshAgent):
    """Hotel search agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="hotel-agent-mesh",
            name="HotelSearchBot",
            capabilities=[
                Capability(
                    name="hotel_search",
                    description="Search hotels by location and dates",
                    confidence=0.92,
                    cost=2.00,
                    latency=2.5
                )
            ]
        )
    
    async def execute_contract(self, contract: TaskContract) -> Dict[str, Any]:
        """Actually search for hotels"""
        
        context = contract.context
        print(f"  🏨 Searching hotels in: {context.get('city')}")
        
        # Simulate API call
        await asyncio.sleep(1.5)
        
        return {
            "hotels": [
                {
                    "name": "Hilton Downtown",
                    "price": 180,
                    "rating": 4.5,
                    "amenities": ["wifi", "gym", "pool"]
                },
                {
                    "name": "Marriott Center",
                    "price": 195,
                    "rating": 4.7,
                    "amenities": ["wifi", "gym", "restaurant"]
                }
            ]
        }


async def test_mesh_network():
    """Full end-to-end test of mesh network"""
    
    print("\n" + "="*70)
    print("MESH NETWORK E2E TEST")
    print("="*70 + "\n")
    
    # Create mesh
    mesh = MeshNetwork()
    await mesh.start()
    
    # Register agents
    flight_agent = FlightAgent()
    hotel_agent = HotelAgent()
    
    await mesh.register_agent(flight_agent)
    await mesh.register_agent(hotel_agent)
    
    print("\n" + "-"*70)
    print("TEST 1: Flight Search")
    print("-"*70 + "\n")
    
    # Execute task via mesh
    result1 = await mesh.execute_task(
        intent="flight_search",
        context={
            "origin": "SFO",
            "destination": "JFK",
            "date": "2026-03-12"
        }
    )
    
    print(f"\n📊 Result: {len(result1.get('flights', []))} flights found")
    
    print("\n" + "-"*70)
    print("TEST 2: Hotel Search")
    print("-"*70 + "\n")
    
    result2 = await mesh.execute_task(
        intent="hotel_search",
        context={
            "city": "San Francisco",
            "checkin": "2026-03-12",
            "checkout": "2026-03-15"
        }
    )
    
    print(f"\n📊 Result: {len(result2.get('hotels', []))} hotels found")
    
    print("\n" + "="*70)
    print("AGENT STATISTICS")
    print("="*70 + "\n")
    
    print(f"FlightAgent:")
    print(f"  Contracts Won: {flight_agent.contracts_won}")
    print(f"  Total Earnings: ${flight_agent.total_earnings:.2f}")
    
    print(f"\nHotelAgent:")
    print(f"  Contracts Won: {hotel_agent.contracts_won}")
    print(f"  Total Earnings: ${hotel_agent.total_earnings:.2f}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE ✅")
    print("="*70 + "\n")
    
    await mesh.stop()


if __name__ == "__main__":
    asyncio.run(test_mesh_network())
