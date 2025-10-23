"""
Amadeus Travel API Service

Handles flights, hotels, and activities using Amadeus Self-Service API.
"""

import logging
import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
AMADEUS_BASE_URL = "https://api.amadeus.com/v1"  # Production environment


class AmadeusService:
    """Service for Amadeus Travel API integration"""

    _access_token: Optional[str] = None
    _token_expiry: Optional[datetime] = None

    @classmethod
    async def _get_access_token(cls) -> str:
        """Get or refresh OAuth access token"""

        # Return cached token if still valid
        if cls._access_token and cls._token_expiry and datetime.now() < cls._token_expiry:
            return cls._access_token

        if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
            logger.error("❌ AMADEUS_API_KEY or AMADEUS_API_SECRET not set")
            raise ValueError("Amadeus credentials not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.amadeus.com/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": AMADEUS_API_KEY,
                        "client_secret": AMADEUS_API_SECRET
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            cls._access_token = data["access_token"]
            cls._token_expiry = datetime.now() + timedelta(seconds=data.get("expires_in", 1800))

            logger.info("✅ Amadeus access token obtained")
            return cls._access_token

        except Exception as e:
            logger.error(f"❌ Amadeus token error: {e}")
            raise

    @classmethod
    async def search_flights(
        cls,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for flights.

        Args:
            origin: Origin airport code (e.g., "SAN")
            destination: Destination airport code (e.g., "CUN")
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Optional return date for round trip
            adults: Number of adult passengers
            max_results: Max number of results

        Returns:
            List of flight offer dictionaries
        """
        try:
            token = await cls._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}

            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "max": max_results,
                "currencyCode": "USD"
            }

            if return_date:
                params["returnDate"] = return_date

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{AMADEUS_BASE_URL}/shopping/flight-offers",
                    headers=headers,
                    params=params,
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()

            flights = []
            for offer in data.get("data", [])[:max_results]:
                # Parse first itinerary (outbound)
                itinerary = offer["itineraries"][0]
                first_segment = itinerary["segments"][0]
                last_segment = itinerary["segments"][-1]

                flight = {
                    "price": f"${offer['price']['total']}",
                    "currency": offer['price']['currency'],
                    "outbound": {
                        "departure": {
                            "airport": first_segment['departure']['iataCode'],
                            "time": first_segment['departure']['at']
                        },
                        "arrival": {
                            "airport": last_segment['arrival']['iataCode'],
                            "time": last_segment['arrival']['at']
                        },
                        "duration": itinerary['duration'],
                        "carrier": first_segment.get('carrierCode', 'Unknown'),
                        "stops": len(itinerary["segments"]) - 1
                    }
                }

                # Add return flight if exists
                if len(offer["itineraries"]) > 1:
                    return_itinerary = offer["itineraries"][1]
                    first_return = return_itinerary["segments"][0]
                    last_return = return_itinerary["segments"][-1]

                    flight["return"] = {
                        "departure": {
                            "airport": first_return['departure']['iataCode'],
                            "time": first_return['departure']['at']
                        },
                        "arrival": {
                            "airport": last_return['arrival']['iataCode'],
                            "time": last_return['arrival']['at']
                        },
                        "duration": return_itinerary['duration'],
                        "carrier": first_return.get('carrierCode', 'Unknown'),
                        "stops": len(return_itinerary["segments"]) - 1
                    }

                flights.append(flight)

            logger.info(f"✈️ Found {len(flights)} flights from {origin} to {destination}")
            return flights

        except Exception as e:
            logger.error(f"❌ Amadeus flight search error: {e}")
            return []

    @classmethod
    async def search_hotels(
        cls,
        city_code: str,
        check_in: str,
        check_out: str,
        adults: int = 1,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels.

        Args:
            city_code: City code (e.g., "CUN" for Cancun)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adults
            max_results: Max number of results

        Returns:
            List of hotel offer dictionaries
        """
        try:
            token = await cls._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}

            # First, get hotel IDs in the city
            params = {
                "cityCode": city_code,
                "radius": 20,
                "radiusUnit": "KM",
                "hotelSource": "ALL"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{AMADEUS_BASE_URL}/reference-data/locations/hotels/by-city",
                    headers=headers,
                    params=params,
                    timeout=15.0
                )
                response.raise_for_status()
                hotel_data = response.json()

            hotel_ids = [h["hotelId"] for h in hotel_data.get("data", [])[:max_results]]

            if not hotel_ids:
                logger.warning(f"No hotels found in {city_code}")
                return []

            # Then search for offers
            offer_params = {
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": adults,
                "currency": "USD"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{AMADEUS_BASE_URL}/shopping/hotel-offers",
                    headers=headers,
                    params=offer_params,
                    timeout=15.0
                )
                response.raise_for_status()
                offers_data = response.json()

            hotels = []
            for hotel in offers_data.get("data", [])[:max_results]:
                if not hotel.get("offers"):
                    continue

                best_offer = hotel["offers"][0]

                hotel_info = {
                    "name": hotel.get("hotel", {}).get("name", "Unknown Hotel"),
                    "rating": hotel.get("hotel", {}).get("rating"),
                    "price_per_night": f"${best_offer['price']['total']}",
                    "currency": best_offer['price']['currency'],
                    "room_type": best_offer.get("room", {}).get("typeEstimated", {}).get("category"),
                    "address": hotel.get("hotel", {}).get("address", {}),
                    "amenities": hotel.get("hotel", {}).get("amenities", [])
                }
                hotels.append(hotel_info)

            logger.info(f"🏨 Found {len(hotels)} hotels in {city_code}")
            return hotels

        except Exception as e:
            logger.error(f"❌ Amadeus hotel search error: {e}")
            return []

    @classmethod
    async def search_activities(
        cls,
        latitude: float,
        longitude: float,
        radius: int = 20,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for activities and tours.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius: Search radius in km
            max_results: Max number of results

        Returns:
            List of activity dictionaries
        """
        try:
            token = await cls._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{AMADEUS_BASE_URL}/shopping/activities",
                    headers=headers,
                    params=params,
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()

            activities = []
            for activity in data.get("data", [])[:max_results]:
                activity_info = {
                    "name": activity.get("name", "Unknown Activity"),
                    "description": activity.get("shortDescription", ""),
                    "rating": activity.get("rating"),
                    "price": f"${activity.get('price', {}).get('amount', 'N/A')}",
                    "currency": activity.get("price", {}).get("currencyCode", "USD"),
                    "duration": activity.get("minimumDuration"),
                    "pictures": activity.get("pictures", [])[:3]
                }
                activities.append(activity_info)

            logger.info(f"🎭 Found {len(activities)} activities")
            return activities

        except Exception as e:
            logger.error(f"❌ Amadeus activity search error: {e}")
            return []
