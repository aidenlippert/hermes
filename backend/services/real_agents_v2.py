"""
Real Agent Execution with External APIs (Version 2)

This version includes proper fallback to mock data when APIs fail.
Executes travel agents using real API integrations with fallback:
- FlightBooker: Amadeus API → Mock Data
- HotelBooker: Amadeus API → Mock Data
- RestaurantFinder: Foursquare API → Mock Data
- EventsFinder: Amadeus API → Mock Data
"""

import logging
from typing import Dict, Any, Optional
from backend.services.llm_provider import get_llm_provider
from backend.services.mock_travel_api import mock_travel_api

logger = logging.getLogger(__name__)

# Try to import real APIs, but don't fail if they're broken
try:
    from backend.services.amadeus_api import AmadeusService
    AMADEUS_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Amadeus API not available: {e}")
    AMADEUS_AVAILABLE = False

try:
    from backend.services.foursquare_api import FoursquareService
    FOURSQUARE_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Foursquare API not available: {e}")
    FOURSQUARE_AVAILABLE = False


# Cache for location resolutions to avoid hitting Gemini rate limits
_location_cache = {}


async def resolve_location_info(location_name: str, is_destination: bool = True) -> Optional[Dict[str, Any]]:
    """
    Dynamically resolve airport code and coordinates for any location using LLM.

    Args:
        location_name: City or location name (e.g., "Seattle", "San Francisco", "Tokyo")
        is_destination: True if this is a destination, False if it's a departure location

    Returns:
        Dictionary with airport code, latitude, and longitude, or None if failed
    """
    # Check cache first
    cache_key = location_name.lower()
    if cache_key in _location_cache:
        logger.info(f"📍 Using cached location for {location_name}")
        return _location_cache[cache_key]

    try:
        llm = get_llm_provider()

        prompt = f"""You are a travel data expert. For the location "{location_name}", provide the main airport code and coordinates.

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "airport": "XXX",
    "latitude": 00.0000,
    "longitude": -00.0000
}}

Examples:
- Seattle → {{"airport": "SEA", "latitude": 47.6062, "longitude": -122.3321}}
- San Francisco → {{"airport": "SFO", "latitude": 37.7749, "longitude": -122.4194}}
- New York → {{"airport": "JFK", "latitude": 40.7128, "longitude": -74.0060}}
- Tokyo → {{"airport": "NRT", "latitude": 35.6762, "longitude": 139.6503}}

Now for: {location_name}"""

        response = await llm.chat_completion([
            {"role": "user", "content": prompt}
        ], temperature=0.1)

        # Parse JSON response
        import json
        import re

        # Clean response
        response_text = response.strip()

        # Remove markdown code blocks if present
        if "```" in response_text:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)

        # Extract JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        location_info = json.loads(response_text.strip())

        # Cache the result
        _location_cache[cache_key] = location_info

        logger.info(f"📍 Resolved {location_name} → {location_info['airport']} ({location_info['latitude']}, {location_info['longitude']})")
        return location_info

    except Exception as e:
        logger.error(f"❌ Failed to resolve location {location_name}: {e}")

        # Fallback to common defaults
        fallback_map = {
            "san francisco": {"airport": "SFO", "latitude": 37.7749, "longitude": -122.4194},
            "los angeles": {"airport": "LAX", "latitude": 34.0522, "longitude": -118.2437},
            "new york": {"airport": "JFK", "latitude": 40.7128, "longitude": -74.0060},
            "seattle": {"airport": "SEA", "latitude": 47.6062, "longitude": -122.3321},
            "miami": {"airport": "MIA", "latitude": 25.7617, "longitude": -80.1918},
        }

        return fallback_map.get(location_name.lower())


async def execute_flight_booker(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute FlightBooker agent with Amadeus API or Mock Data.
    """
    try:
        destination = extracted_info.get("destination", "")
        departure_location = extracted_info.get("departure_location", "")
        travel_dates = extracted_info.get("travel_dates", "")
        num_travelers = extracted_info.get("num_travelers", 1)

        # Dynamically resolve airport codes
        logger.info(f"🔍 Resolving locations: {departure_location} → {destination}")

        origin_info = await resolve_location_info(departure_location, is_destination=False)
        dest_info = await resolve_location_info(destination, is_destination=True)

        if not origin_info or not dest_info:
            return {
                "status": "error",
                "message": f"Could not resolve airport codes for {departure_location} or {destination}",
                "data": []
            }

        origin_code = origin_info["airport"]
        dest_code = dest_info["airport"]

        # Parse dates (simplified - assumes format like "25th to 30th" or "October 25-30")
        # For demo, use hardcoded dates
        departure_date = "2025-10-25"
        return_date = "2025-10-30"

        logger.info(f"✈️ Searching flights: {origin_code} → {dest_code}")

        # Try real API if available
        if AMADEUS_AVAILABLE:
            try:
                flights = await AmadeusService.search_flights(
                    origin=origin_code,
                    destination=dest_code,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=int(num_travelers) if num_travelers else 1,
                    max_results=3
                )

                if flights:
                    return {
                        "status": "success",
                        "data": {
                            "flights": flights,
                            "summary": f"Found {len(flights)} flight options from {origin_code} to {dest_code}"
                        }
                    }
            except Exception as e:
                logger.warning(f"⚠️ Amadeus API failed: {e}")

        # Fall back to mock data
        logger.info("📦 Using mock flight data")
        return await mock_travel_api.search_flights(
            origin=origin_code,
            destination=dest_code,
            departure_date=departure_date,
            return_date=return_date,
            passengers=int(num_travelers) if num_travelers else 1
        )

    except Exception as e:
        logger.error(f"❌ FlightBooker execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


async def execute_hotel_booker(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute HotelBooker agent with Amadeus API or Mock Data.
    """
    try:
        destination = extracted_info.get("destination", "")
        num_travelers = extracted_info.get("num_travelers", 1)

        # Resolve destination info
        dest_info = await resolve_location_info(destination, is_destination=True)

        if not dest_info:
            return {
                "status": "error",
                "message": f"Could not resolve location for {destination}",
                "data": []
            }

        city_code = dest_info["airport"]

        # Parse dates
        check_in = "2025-10-25"
        check_out = "2025-10-30"

        logger.info(f"🏨 Searching hotels in {destination}")

        # Try real API if available
        if AMADEUS_AVAILABLE:
            try:
                hotels = await AmadeusService.search_hotels(
                    city_code=city_code,
                    check_in=check_in,
                    check_out=check_out,
                    adults=int(num_travelers) if num_travelers else 1,
                    max_results=5
                )

                if hotels:
                    return {
                        "status": "success",
                        "data": {
                            "hotels": hotels,
                            "summary": f"Found {len(hotels)} hotels in {destination}"
                        }
                    }
            except Exception as e:
                logger.warning(f"⚠️ Amadeus Hotels API failed: {e}")

        # Fall back to mock data
        logger.info("📦 Using mock hotel data")
        return await mock_travel_api.search_hotels(
            location=destination,
            checkin=check_in,
            checkout=check_out,
            guests=int(num_travelers) if num_travelers else 1
        )

    except Exception as e:
        logger.error(f"❌ HotelBooker execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


async def execute_restaurant_finder(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute RestaurantFinder agent with Foursquare API or Mock Data.
    """
    try:
        destination = extracted_info.get("destination", "")

        # Resolve destination info
        dest_info = await resolve_location_info(destination, is_destination=True)

        if not dest_info:
            return {
                "status": "error",
                "message": f"Could not resolve location for {destination}",
                "data": []
            }

        logger.info(f"🍽️ Searching restaurants in {destination}")

        # Try real API if available
        if FOURSQUARE_AVAILABLE:
            try:
                restaurants = await FoursquareService.search_restaurants(
                    location=destination.title(),
                    latitude=dest_info["latitude"],
                    longitude=dest_info["longitude"],
                    limit=10
                )

                if restaurants:
                    return {
                        "status": "success",
                        "data": {
                            "restaurants": restaurants,
                            "summary": f"Found {len(restaurants)} restaurants in {destination}"
                        }
                    }
            except Exception as e:
                logger.warning(f"⚠️ Foursquare API failed: {e}")

        # Fall back to mock data
        logger.info("📦 Using mock restaurant data")
        return await mock_travel_api.search_restaurants(location=destination)

    except Exception as e:
        logger.error(f"❌ RestaurantFinder execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


async def execute_events_finder(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute EventsFinder agent with Amadeus API or Mock Data.
    """
    try:
        destination = extracted_info.get("destination", "")

        # Resolve destination info
        dest_info = await resolve_location_info(destination, is_destination=True)

        if not dest_info:
            return {
                "status": "error",
                "message": f"Could not resolve location for {destination}",
                "data": []
            }

        city_code = dest_info["airport"]

        logger.info(f"🎭 Searching activities in {destination}")

        # Try real API if available
        if AMADEUS_AVAILABLE:
            try:
                activities = await AmadeusService.search_activities(
                    latitude=dest_info["latitude"],
                    longitude=dest_info["longitude"],
                    radius=20,
                    max_results=5
                )

                if activities:
                    return {
                        "status": "success",
                        "data": {
                            "activities": activities,
                            "summary": f"Found {len(activities)} activities in {destination}"
                        }
                    }
            except Exception as e:
                logger.warning(f"⚠️ Amadeus Activities API failed: {e}")

        # Fall back to mock data
        logger.info("📦 Using mock activity data")
        return await mock_travel_api.search_activities(location=destination)

    except Exception as e:
        logger.error(f"❌ EventsFinder execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }


# Registry of agent executors
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
    Execute all approved agents with real API calls or mock data fallback.

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