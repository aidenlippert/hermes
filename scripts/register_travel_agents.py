#!/usr/bin/env python3
"""
Register Travel Planning Agents

Adds the travel planning agents to the Hermes database.
Run this after starting the agents with ./start_travel_agents.sh
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import AsyncSessionLocal
from backend.services.agent_registry import AgentRegistry


async def register_agents():
    """Register all travel planning agents"""

    agents = [
        {
            "name": "FlightBooker",
            "description": "Search and book flights worldwide. I can find the best deals based on your dates, budget, and preferences.",
            "endpoint": "http://localhost:10010/execute",
            "capabilities": ["flight_search", "flight_booking", "price_comparison", "travel"],
            "category": "travel",
            "version": "1.0.0"
        },
        {
            "name": "HotelBooker",
            "description": "Find and book hotels worldwide. I can search by location, price range, amenities, and ratings.",
            "endpoint": "http://localhost:10011/execute",
            "capabilities": ["hotel_search", "hotel_booking", "accommodation", "travel"],
            "category": "travel",
            "version": "1.0.0"
        },
        {
            "name": "RestaurantFinder",
            "description": "Discover amazing restaurants and make reservations. I can find dining options based on cuisine, location, budget, and dietary preferences.",
            "endpoint": "http://localhost:10012/execute",
            "capabilities": ["restaurant_search", "restaurant_reservation", "dining", "food", "travel"],
            "category": "travel",
            "version": "1.0.0"
        },
        {
            "name": "EventsFinder",
            "description": "Discover local events, attractions, and activities. I can find concerts, shows, tours, museums, and unique experiences.",
            "endpoint": "http://localhost:10013/execute",
            "capabilities": ["events_search", "activities", "attractions", "entertainment", "travel"],
            "category": "travel",
            "version": "1.0.0"
        }
    ]

    async with AsyncSessionLocal() as db:
        print("\n🎯 Registering Travel Planning Agents...\n")

        for agent_data in agents:
            try:
                agent = await AgentRegistry.register_agent(
                    db,
                    name=agent_data["name"],
                    description=agent_data["description"],
                    endpoint=agent_data["endpoint"],
                    capabilities=agent_data["capabilities"],
                    category=agent_data["category"],
                    version=agent_data["version"]
                )

                print(f"✅ {agent.name}")
                print(f"   Endpoint: {agent.endpoint}")
                print(f"   Capabilities: {', '.join(agent.capabilities)}")
                print()

            except Exception as e:
                print(f"❌ Failed to register {agent_data['name']}: {e}\n")

        print("🎉 Agent registration complete!")
        print("\nNow you can ask Hermes:")
        print('   "Plan a trip to Paris for me"')
        print('   "I want to visit Tokyo next month"')
        print('   "Find me flights and hotels to New York"')


if __name__ == "__main__":
    asyncio.run(register_agents())
