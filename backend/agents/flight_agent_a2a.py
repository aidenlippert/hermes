#!/usr/bin/env python3
"""
A2A-Compliant Flight Booking Agent

This agent handles flight searches and bookings using the A2A protocol.
It can use real Amadeus API or fall back to mock data.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.base_a2a_agent import A2AAgent
from backend.services.real_agents_v2 import execute_flight_booker
from backend.services.llm_provider import get_llm_provider
import logging
import json
import re

logger = logging.getLogger(__name__)


class FlightAgent(A2AAgent):
    """A2A-compliant flight booking agent"""

    def __init__(self):
        super().__init__(
            name="FlightBooker",
            description="Books flights using Amadeus API or mock data",
            version="2.0.0",
            port=10005
        )

    def get_skills(self):
        """Define flight agent skills"""
        return [
            {
                "id": "search_flights",
                "name": "Search Flights",
                "description": "Search for available flights between cities",
                "tags": ["travel", "flights", "booking", "airlines"],
                "examples": [
                    "Find flights from San Francisco to Seattle",
                    "Search for flights from NYC to Miami on December 25th",
                    "Book a round trip from LAX to JFK for 2 people"
                ]
            },
            {
                "id": "find_deals",
                "name": "Find Flight Deals",
                "description": "Find the best flight deals and cheapest options",
                "tags": ["deals", "cheap", "budget", "savings"],
                "examples": [
                    "Find cheapest flights to Paris",
                    "What are the best flight deals this weekend?",
                    "Budget flights from Chicago to Vegas"
                ]
            }
        ]

    async def execute(self, message: str, context: dict, metadata: dict):
        """Execute flight search based on user message"""

        logger.info(f"✈️ FlightAgent processing: {message}")

        # Extract travel information from message using LLM
        extracted_info = await self.extract_flight_info(message, context)

        if not extracted_info:
            return {
                "type": "error",
                "content": "Could not understand your flight request. Please specify origin, destination, and travel dates."
            }

        # Execute flight search using our existing logic
        result = await execute_flight_booker(extracted_info)

        # Format response for A2A
        if result["status"] == "success":
            flights = result["data"].get("flights", [])
            summary = result["data"].get("summary", "")

            # Format flights for display
            formatted_flights = []
            for flight in flights[:5]:  # Top 5 results
                formatted_flights.append({
                    "airline": flight.get("airline", "Unknown"),
                    "departure": flight.get("departure", {}),
                    "arrival": flight.get("arrival", {}),
                    "price": flight.get("price", "N/A"),
                    "duration": flight.get("duration", "N/A"),
                    "stops": flight.get("stops", 0)
                })

            return {
                "type": "flight_results",
                "content": {
                    "summary": summary,
                    "flights": formatted_flights,
                    "search_params": extracted_info
                }
            }
        else:
            return {
                "type": "error",
                "content": result.get("message", "Failed to search flights")
            }

    async def extract_flight_info(self, message: str, context: dict):
        """Extract flight search parameters from natural language"""

        llm = get_llm_provider()

        # Check if context has information
        existing_info = context.get("extracted_info", {})

        prompt = f"""Extract flight search information from this request.

User message: "{message}"

Previous context: {json.dumps(existing_info, indent=2) if existing_info else "None"}

Extract:
- departure_location: city flying FROM
- destination: city flying TO
- travel_dates: when they want to travel
- num_travelers: number of passengers (default 1)
- trip_type: "one-way" or "round-trip" (default round-trip)

Return ONLY valid JSON:
{{
    "departure_location": "city name or null",
    "destination": "city name or null",
    "travel_dates": "date description or null",
    "num_travelers": number,
    "trip_type": "one-way or round-trip"
}}

Examples:
"flights from NYC to LA" → {{"departure_location": "New York", "destination": "Los Angeles", "travel_dates": null, "num_travelers": 1, "trip_type": "round-trip"}}
"one way ticket from Seattle to Miami for 2 people" → {{"departure_location": "Seattle", "destination": "Miami", "travel_dates": null, "num_travelers": 2, "trip_type": "one-way"}}
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

            logger.info(f"📋 Extracted flight info: {extracted}")
            return extracted

        except Exception as e:
            logger.error(f"Failed to extract flight info: {e}")
            return None


def main():
    """Run the flight agent"""
    agent = FlightAgent()
    agent.run()


if __name__ == "__main__":
    main()