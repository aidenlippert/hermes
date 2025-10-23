"""
Real Agent Execution with External APIs

Executes travel agents using real API integrations:
- FlightBooker: Amadeus API
- HotelBooker: Amadeus API
- RestaurantFinder: Foursquare API
- EventsFinder: Amadeus API
"""

import logging
from typing import Dict, Any
from backend.services.amadeus_api import AmadeusService
from backend.services.foursquare_api import FoursquareService

logger = logging.getLogger(__name__)

# Location coordinates for common destinations
DESTINATION_COORDS = {
    "cancun": {"lat": 21.1619, "lon": -86.8515, "airport": "CUN"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "airport": "MIA"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "airport": "JFK"},
    "los angeles": {"lat": 34.0522, "lon": -118.2437, "airport": "LAX"},
    "san diego": {"lat": 32.7157, "lon": -117.1611, "airport": "SAN"},
    "seattle": {"lat": 47.6062, "lon": -122.3321, "airport": "SEA"},
}

AIRPORT_CODES = {
    "san diego": "SAN",
    "los angeles": "LAX",
    "new york": "JFK",
    "miami": "MIA",
    "chicago": "ORD",
    "boston": "BOS",
    "san francisco": "SFO",
    "seattle": "SEA",
}


async def execute_flight_booker(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute FlightBooker agent with Amadeus API.

    Args:
        extracted_info: User's travel requirements

    Returns:
        Flight search results
    """
    try:
        destination = extracted_info.get("destination", "").lower()
        departure_location = extracted_info.get("departure_location", "").lower()
        travel_dates = extracted_info.get("travel_dates", "")
        num_travelers = extracted_info.get("num_travelers", 1)

        # Get airport codes
        origin_code = AIRPORT_CODES.get(departure_location, "SAN")
        dest_coords = DESTINATION_COORDS.get(destination, DESTINATION_COORDS["cancun"])
        dest_code = dest_coords["airport"]

        # Parse dates (simplified - assumes format like "25th to 30th" or "October 25-30")
        # For demo, use hardcoded dates
        departure_date = "2025-10-25"
        return_date = "2025-10-30"

        logger.info(f"✈️ Searching flights: {origin_code} → {dest_code}")

        flights = await AmadeusService.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            return_date=return_date,
            adults=int(num_travelers) if num_travelers else 1,
            max_results=3
        )

        if not flights:
            return {
                "status": "error",
                "message": "No flights found",
                "data": []
            }

        return {
            "status": "success",
            "data": {
                "flights": flights,
                "summary": f"Found {len(flights)} flight options from {origin_code} to {dest_code}"
            }
        }

    except Exception as e:
        logger.error(f"❌ FlightBooker execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


async def execute_hotel_booker(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute HotelBooker agent with Amadeus API.

    Args:
        extracted_info: User's travel requirements

    Returns:
        Hotel search results
    """
    try:
        destination = extracted_info.get("destination", "").lower()
        num_travelers = extracted_info.get("num_travelers", 1)

        # Get destination city code
        dest_coords = DESTINATION_COORDS.get(destination, DESTINATION_COORDS["cancun"])
        city_code = dest_coords["airport"]

        # Parse dates
        check_in = "2025-10-25"
        check_out = "2025-10-30"

        logger.info(f"🏨 Searching hotels in {city_code}")

        hotels = await AmadeusService.search_hotels(
            city_code=city_code,
            check_in=check_in,
            check_out=check_out,
            adults=int(num_travelers) if num_travelers else 1,
            max_results=5
        )

        if not hotels:
            return {
                "status": "error",
                "message": "No hotels found",
                "data": []
            }

        return {
            "status": "success",
            "data": {
                "hotels": hotels,
                "summary": f"Found {len(hotels)} hotel options in {destination.title()}"
            }
        }

    except Exception as e:
        logger.error(f"❌ HotelBooker execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


async def execute_restaurant_finder(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute RestaurantFinder agent with Foursquare API.

    Args:
        extracted_info: User's travel requirements

    Returns:
        Restaurant recommendations
    """
    try:
        destination = extracted_info.get("destination", "").lower()

        # Get destination coordinates
        dest_coords = DESTINATION_COORDS.get(destination, DESTINATION_COORDS["cancun"])

        logger.info(f"🍽️ Searching restaurants in {destination}")

        restaurants = await FoursquareService.search_restaurants(
            location=destination.title(),
            latitude=dest_coords["lat"],
            longitude=dest_coords["lon"],
            limit=10
        )

        if not restaurants:
            return {
                "status": "error",
                "message": "No restaurants found",
                "data": []
            }

        return {
            "status": "success",
            "data": {
                "restaurants": restaurants[:5],  # Top 5
                "summary": f"Found {len(restaurants)} restaurant recommendations in {destination.title()}"
            }
        }

    except Exception as e:
        logger.error(f"❌ RestaurantFinder execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


async def execute_events_finder(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute EventsFinder agent with Amadeus API.

    Args:
        extracted_info: User's travel requirements

    Returns:
        Activities and tours
    """
    try:
        destination = extracted_info.get("destination", "").lower()

        # Get destination coordinates
        dest_coords = DESTINATION_COORDS.get(destination, DESTINATION_COORDS["cancun"])

        logger.info(f"🎭 Searching activities in {destination}")

        activities = await AmadeusService.search_activities(
            latitude=dest_coords["lat"],
            longitude=dest_coords["lon"],
            radius=20,
            max_results=10
        )

        if not activities:
            return {
                "status": "error",
                "message": "No activities found",
                "data": []
            }

        return {
            "status": "success",
            "data": {
                "activities": activities[:5],  # Top 5
                "summary": f"Found {len(activities)} activities and tours in {destination.title()}"
            }
        }

    except Exception as e:
        logger.error(f"❌ EventsFinder execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


# Agent execution mapping
AGENT_EXECUTORS = {
    "FlightBooker": execute_flight_booker,
    "HotelBooker": execute_hotel_booker,
    "RestaurantFinder": execute_restaurant_finder,
    "EventsFinder": execute_events_finder
}


async def execute_real_agents(
    agents: list,
    extracted_info: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Execute all approved agents with real API calls.

    Args:
        agents: List of approved agents
        extracted_info: Extracted travel information

    Returns:
        Dictionary mapping agent names to their results
    """
    results = {}

    for agent in agents:
        agent_name = agent.get("name")

        if agent_name in AGENT_EXECUTORS:
            logger.info(f"🔄 Executing {agent_name}...")
            result = await AGENT_EXECUTORS[agent_name](extracted_info)
            results[agent_name] = result
        else:
            logger.warning(f"⚠️ No executor found for {agent_name}")
            results[agent_name] = {
                "status": "error",
                "message": f"Agent {agent_name} not implemented",
                "data": []
            }

    return results
