"""
Seed Agents - Auto-register travel agents on startup

This ensures travel agents are always available in production.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


async def seed_travel_agents(db: AsyncSession):
    """
    Register travel agents if they don't exist.

    This is called on backend startup to ensure agents are available.
    """

    travel_agents = [
        {
            "name": "FlightBooker",
            "description": "Search and book flights worldwide. Find the best deals based on dates, budget, and preferences.",
            "endpoint": "http://localhost:10010",
            "capabilities": ["flight_search", "flight_booking", "price_comparison", "travel", "book_flight"],
            "category": "travel"
        },
        {
            "name": "HotelBooker",
            "description": "Find and book hotels worldwide. Search by location, price range, amenities, and ratings.",
            "endpoint": "http://localhost:10011",
            "capabilities": ["hotel_search", "hotel_booking", "accommodation", "travel", "book_hotel"],
            "category": "travel"
        },
        {
            "name": "RestaurantFinder",
            "description": "Discover amazing restaurants and make reservations. Find dining options based on cuisine, location, budget, and dietary preferences.",
            "endpoint": "http://localhost:10012",
            "capabilities": ["restaurant_search", "restaurant_reservation", "dining", "food", "travel"],
            "category": "travel"
        },
        {
            "name": "EventsFinder",
            "description": "Discover local events, attractions, and activities. Find concerts, shows, tours, museums, and unique experiences.",
            "endpoint": "http://localhost:10013",
            "capabilities": ["events_search", "activities", "attractions", "entertainment", "travel"],
            "category": "travel"
        }
    ]

    logger.info("🌱 Seeding travel agents...")

    for agent_data in travel_agents:
        try:
            # Check if agent already exists
            existing = await AgentRegistry.get_agent_by_name(db, agent_data["name"])

            if existing:
                logger.info(f"   ✓ {agent_data['name']} already registered")
                continue

            # Register new agent
            agent = await AgentRegistry.register_agent(
                db,
                name=agent_data["name"],
                description=agent_data["description"],
                endpoint=agent_data["endpoint"],
                capabilities=agent_data["capabilities"],
                category=agent_data["category"]
            )

            logger.info(f"   ✅ Registered {agent.name}")

        except Exception as e:
            logger.error(f"   ❌ Failed to register {agent_data['name']}: {e}")

    logger.info("🌱 Agent seeding complete!")
