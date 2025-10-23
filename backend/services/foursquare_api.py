"""
Foursquare Places API Service

Handles restaurant and venue search using Foursquare Places API.
"""

import logging
import os
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
FOURSQUARE_BASE_URL = "https://api.foursquare.com/v3"


class FoursquareService:
    """Service for Foursquare Places API integration"""

    @staticmethod
    async def search_restaurants(
        location: str,
        latitude: float,
        longitude: float,
        limit: int = 10,
        categories: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants near a location.

        Args:
            location: Location name (e.g., "Cancun, Mexico")
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            limit: Max number of results
            categories: Optional category filter (e.g., "restaurant,bar")

        Returns:
            List of restaurant dictionaries
        """
        if not FOURSQUARE_API_KEY:
            logger.error("❌ FOURSQUARE_API_KEY not set")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {FOURSQUARE_API_KEY}" if not FOURSQUARE_API_KEY.startswith("Bearer") else FOURSQUARE_API_KEY,
                "Accept": "application/json"
            }

            params = {
                "ll": f"{latitude},{longitude}",
                "categories": categories or "13065",  # Restaurant category
                "limit": limit,
                "sort": "RATING",
                "fields": "name,location,rating,price,photos,hours,description,categories"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{FOURSQUARE_BASE_URL}/places/search",
                    headers=headers,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            restaurants = []
            for place in data.get("results", []):
                restaurant = {
                    "name": place.get("name", "Unknown"),
                    "rating": place.get("rating", 0) / 2,  # Foursquare uses 0-10 scale
                    "price": "".join(["$" for _ in range(place.get("price", 1))]),
                    "address": place.get("location", {}).get("formatted_address", ""),
                    "cuisine": ", ".join([cat.get("name", "") for cat in place.get("categories", [])[:2]]),
                    "photos": [photo.get("prefix", "") + "300x300" + photo.get("suffix", "")
                              for photo in place.get("photos", [])[:3]]
                }
                restaurants.append(restaurant)

            logger.info(f"🍽️ Found {len(restaurants)} restaurants in {location}")
            return restaurants

        except Exception as e:
            logger.error(f"❌ Foursquare API error: {e}")
            return []

    @staticmethod
    async def search_venues(
        location: str,
        latitude: float,
        longitude: float,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for venues (bars, clubs, entertainment) near a location.

        Args:
            location: Location name
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            query: Search query (e.g., "nightlife", "live music")
            limit: Max number of results

        Returns:
            List of venue dictionaries
        """
        if not FOURSQUARE_API_KEY:
            logger.error("❌ FOURSQUARE_API_KEY not set")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {FOURSQUARE_API_KEY}" if not FOURSQUARE_API_KEY.startswith("Bearer") else FOURSQUARE_API_KEY,
                "Accept": "application/json"
            }

            params = {
                "ll": f"{latitude},{longitude}",
                "query": query,
                "limit": limit,
                "sort": "RATING",
                "fields": "name,location,rating,price,photos,hours,description,categories"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{FOURSQUARE_BASE_URL}/places/search",
                    headers=headers,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            venues = []
            for place in data.get("results", []):
                venue = {
                    "name": place.get("name", "Unknown"),
                    "rating": place.get("rating", 0) / 2,
                    "category": ", ".join([cat.get("name", "") for cat in place.get("categories", [])[:2]]),
                    "address": place.get("location", {}).get("formatted_address", ""),
                    "photos": [photo.get("prefix", "") + "300x300" + photo.get("suffix", "")
                              for photo in place.get("photos", [])[:3]]
                }
                venues.append(venue)

            logger.info(f"🎉 Found {len(venues)} venues in {location}")
            return venues

        except Exception as e:
            logger.error(f"❌ Foursquare API error: {e}")
            return []
