"""
Mock Travel API Service

Since Amadeus isn't working, we'll use mock data for demo
and later integrate with alternative APIs like:
- Skyscanner API
- Booking.com API
- Google Travel API
- Expedia Rapid API
"""

import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MockTravelAPI:
    """Mock travel data for demo purposes"""

    @staticmethod
    async def search_flights(origin: str, destination: str, departure_date: str,
                           return_date: str = None, passengers: int = 1) -> Dict[str, Any]:
        """Generate realistic flight data"""

        # Generate mock flights
        airlines = ["United", "Delta", "American", "Southwest", "JetBlue", "Alaska"]
        flights = []

        for i in range(5):
            base_price = random.randint(150, 800)
            flights.append({
                "id": f"FL{random.randint(1000, 9999)}",
                "airline": random.choice(airlines),
                "departure": {
                    "airport": origin,
                    "time": f"{random.randint(6, 20):02d}:{random.randint(0, 59):02d}",
                    "date": departure_date
                },
                "arrival": {
                    "airport": destination,
                    "time": f"{random.randint(9, 23):02d}:{random.randint(0, 59):02d}",
                    "date": departure_date
                },
                "duration": f"{random.randint(2, 8)}h {random.randint(0, 59)}m",
                "price": f"${base_price * passengers}",
                "price_numeric": base_price * passengers,
                "stops": random.choice([0, 1, 2]),
                "class": "Economy",
                "available_seats": random.randint(1, 20)
            })

        # Sort by price
        flights.sort(key=lambda x: x["price_numeric"])

        return {
            "status": "success",
            "data": {
                "flights": flights,
                "summary": f"Found {len(flights)} flights from {origin} to {destination}",
                "search_params": {
                    "origin": origin,
                    "destination": destination,
                    "departure": departure_date,
                    "return": return_date,
                    "passengers": passengers
                }
            }
        }

    @staticmethod
    async def search_hotels(location: str, checkin: str, checkout: str,
                          guests: int = 2) -> Dict[str, Any]:
        """Generate realistic hotel data"""

        hotel_chains = ["Marriott", "Hilton", "Hyatt", "InterContinental", "Westin", "Sheraton"]
        hotel_types = ["Resort", "Hotel", "Inn", "Suites", "Plaza", "Grand"]

        hotels = []

        for i in range(6):
            base_price = random.randint(80, 400)
            rating = round(random.uniform(3.5, 5.0), 1)

            hotels.append({
                "id": f"HT{random.randint(1000, 9999)}",
                "name": f"{random.choice(hotel_chains)} {location} {random.choice(hotel_types)}",
                "location": {
                    "address": f"{random.randint(100, 999)} {random.choice(['Main', 'First', 'Park', 'Ocean'])} Street",
                    "city": location,
                    "distance_from_center": f"{round(random.uniform(0.5, 10), 1)} miles"
                },
                "price_per_night": f"${base_price}",
                "price_numeric": base_price,
                "total_price": f"${base_price * 3}",  # Assuming 3 nights
                "rating": rating,
                "stars": int(rating),
                "reviews": random.randint(100, 2000),
                "amenities": random.sample([
                    "Free WiFi", "Pool", "Gym", "Spa", "Restaurant",
                    "Bar", "Room Service", "Parking", "Pet Friendly"
                ], k=random.randint(4, 7)),
                "room_type": random.choice(["Standard", "Deluxe", "Suite", "Executive"]),
                "availability": random.choice(["Available", "Limited", "Last Room"])
            })

        # Sort by rating
        hotels.sort(key=lambda x: x["rating"], reverse=True)

        return {
            "status": "success",
            "data": {
                "hotels": hotels,
                "summary": f"Found {len(hotels)} hotels in {location}",
                "search_params": {
                    "location": location,
                    "checkin": checkin,
                    "checkout": checkout,
                    "guests": guests
                }
            }
        }

    @staticmethod
    async def search_restaurants(location: str, cuisine: str = None) -> Dict[str, Any]:
        """Generate restaurant recommendations"""

        cuisines = ["Italian", "Japanese", "Mexican", "Thai", "French", "American", "Indian", "Chinese"]
        restaurant_types = ["Bistro", "Grill", "Kitchen", "House", "Cafe", "Restaurant", "Eatery"]

        restaurants = []

        for i in range(8):
            selected_cuisine = cuisine if cuisine else random.choice(cuisines)
            rating = round(random.uniform(3.8, 5.0), 1)

            restaurants.append({
                "id": f"RS{random.randint(1000, 9999)}",
                "name": f"{selected_cuisine} {random.choice(restaurant_types)}",
                "cuisine": selected_cuisine,
                "location": {
                    "address": f"{random.randint(100, 999)} {random.choice(['Downtown', 'Uptown', 'Midtown'])} Ave",
                    "city": location,
                    "neighborhood": random.choice(["Downtown", "Historic District", "Waterfront", "Arts District"])
                },
                "rating": rating,
                "price_range": "$" * random.randint(1, 4),
                "reviews": random.randint(50, 1500),
                "popular_dishes": random.sample([
                    "Chef's Special", "Seasonal Menu", "Tasting Menu",
                    "Local Favorites", "Signature Dish"
                ], k=random.randint(2, 4)),
                "features": random.sample([
                    "Outdoor Seating", "Reservations", "Delivery",
                    "Takeout", "Live Music", "Happy Hour", "Brunch"
                ], k=random.randint(3, 5)),
                "hours": "11:00 AM - 10:00 PM",
                "reservation_available": random.choice([True, False])
            })

        # Sort by rating
        restaurants.sort(key=lambda x: x["rating"], reverse=True)

        return {
            "status": "success",
            "data": {
                "restaurants": restaurants,
                "summary": f"Found {len(restaurants)} restaurants in {location}",
                "search_params": {
                    "location": location,
                    "cuisine": cuisine
                }
            }
        }

    @staticmethod
    async def search_activities(location: str, activity_type: str = None) -> Dict[str, Any]:
        """Generate activity recommendations"""

        activity_categories = ["Tour", "Adventure", "Museum", "Show", "Experience", "Workshop"]

        activities = []

        for i in range(6):
            price = random.randint(25, 200)
            rating = round(random.uniform(4.0, 5.0), 1)

            activities.append({
                "id": f"AC{random.randint(1000, 9999)}",
                "name": f"{location} {random.choice(activity_categories)}",
                "category": activity_type if activity_type else random.choice([
                    "Sightseeing", "Adventure", "Cultural", "Entertainment", "Food & Drink"
                ]),
                "description": f"Experience the best of {location} with this amazing activity",
                "duration": f"{random.randint(1, 8)} hours",
                "price": f"${price}",
                "price_numeric": price,
                "rating": rating,
                "reviews": random.randint(50, 1000),
                "highlights": random.sample([
                    "Skip the Line", "Free Cancellation", "Mobile Ticket",
                    "Instant Confirmation", "Small Group", "Private Tour"
                ], k=random.randint(2, 4)),
                "included": random.sample([
                    "Guide", "Transportation", "Entrance Fees",
                    "Lunch", "Equipment", "Insurance"
                ], k=random.randint(2, 4)),
                "availability": "Daily",
                "time_slots": ["9:00 AM", "2:00 PM", "6:00 PM"]
            })

        # Sort by rating
        activities.sort(key=lambda x: x["rating"], reverse=True)

        return {
            "status": "success",
            "data": {
                "activities": activities,
                "summary": f"Found {len(activities)} activities in {location}",
                "search_params": {
                    "location": location,
                    "type": activity_type
                }
            }
        }


# Create singleton instance
mock_travel_api = MockTravelAPI()