#!/usr/bin/env python3
"""
A2A-Compliant Hotel Booking Agent

This agent handles hotel searches and bookings using the A2A protocol.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.base_a2a_agent import A2AAgent
from backend.services.real_agents_v2 import execute_hotel_booker
from backend.services.llm_provider import get_llm_provider
import logging
import json
import re

logger = logging.getLogger(__name__)


class HotelAgent(A2AAgent):
    """A2A-compliant hotel booking agent"""

    def __init__(self):
        super().__init__(
            name="HotelBooker",
            description="Finds and books hotels using Amadeus API or mock data",
            version="2.0.0",
            port=10006
        )

    def get_skills(self):
        """Define hotel agent skills"""
        return [
            {
                "id": "search_hotels",
                "name": "Search Hotels",
                "description": "Search for available hotels in any city",
                "tags": ["travel", "hotels", "accommodation", "lodging"],
                "examples": [
                    "Find hotels in Seattle",
                    "Search for hotels in Paris for next week",
                    "Book a hotel in Miami for 3 nights"
                ]
            },
            {
                "id": "find_deals",
                "name": "Find Hotel Deals",
                "description": "Find the best hotel deals and budget options",
                "tags": ["deals", "cheap", "budget", "discounts"],
                "examples": [
                    "Find cheapest hotels in New York",
                    "Best hotel deals in Tokyo",
                    "Budget accommodation in London"
                ]
            },
            {
                "id": "luxury_hotels",
                "name": "Find Luxury Hotels",
                "description": "Search for luxury and premium hotels",
                "tags": ["luxury", "premium", "5-star", "boutique"],
                "examples": [
                    "Find luxury hotels in Dubai",
                    "5-star hotels in Paris",
                    "Best boutique hotels in Bali"
                ]
            }
        ]

    async def execute(self, message: str, context: dict, metadata: dict):
        """Execute hotel search based on user message"""

        logger.info(f"🏨 HotelAgent processing: {message}")

        # Extract hotel information from message using LLM
        extracted_info = await self.extract_hotel_info(message, context)

        if not extracted_info:
            return {
                "type": "error",
                "content": "Could not understand your hotel request. Please specify the destination and travel dates."
            }

        # Execute hotel search using our existing logic
        result = await execute_hotel_booker(extracted_info)

        # Format response for A2A
        if result["status"] == "success":
            hotels = result["data"].get("hotels", [])
            summary = result["data"].get("summary", "")

            # Format hotels for display
            formatted_hotels = []
            for hotel in hotels[:6]:  # Top 6 results
                formatted_hotels.append({
                    "name": hotel.get("name", "Unknown Hotel"),
                    "location": hotel.get("location", {}),
                    "price_per_night": hotel.get("price_per_night", "N/A"),
                    "total_price": hotel.get("total_price", "N/A"),
                    "rating": hotel.get("rating", 0),
                    "amenities": hotel.get("amenities", []),
                    "availability": hotel.get("availability", "Unknown")
                })

            return {
                "type": "hotel_results",
                "content": {
                    "summary": summary,
                    "hotels": formatted_hotels,
                    "search_params": extracted_info
                }
            }
        else:
            return {
                "type": "error",
                "content": result.get("message", "Failed to search hotels")
            }

    async def extract_hotel_info(self, message: str, context: dict):
        """Extract hotel search parameters from natural language"""

        llm = get_llm_provider()

        # Check if context has information
        existing_info = context.get("extracted_info", {})

        prompt = f"""Extract hotel search information from this request.

User message: "{message}"

Previous context: {json.dumps(existing_info, indent=2) if existing_info else "None"}

Extract:
- destination: city/location for the hotel
- travel_dates: check-in and check-out dates
- num_travelers: number of guests (default 2)
- room_preference: type of room or hotel preferred

Return ONLY valid JSON:
{{
    "destination": "city name or null",
    "travel_dates": "date description or null",
    "num_travelers": number,
    "room_preference": "preference or null"
}}

Examples:
"hotels in NYC" → {{"destination": "New York", "travel_dates": null, "num_travelers": 2, "room_preference": null}}
"luxury hotel in Paris for 3 people" → {{"destination": "Paris", "travel_dates": null, "num_travelers": 3, "room_preference": "luxury"}}
"""

        try:
            response = await llm.chat_completion([
                {"role": "user", "content": prompt}
            ], temperature=0.1)

            # Parse JSON
            response_text = response.strip()
            if "```" in response_text:
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if match:
                    response_text = match.group(1)

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            extracted = json.loads(response_text.strip())

            # Merge with existing context
            if existing_info:
                for key, value in existing_info.items():
                    if not extracted.get(key) and value:
                        extracted[key] = value

            logger.info(f"📋 Extracted hotel info: {extracted}")
            return extracted

        except Exception as e:
            logger.error(f"Failed to extract hotel info: {e}")
            return None


def main():
    """Run the hotel agent"""
    agent = HotelAgent()
    agent.run()


if __name__ == "__main__":
    main()