"""
Flight Booking Agent

Searches and books flights based on user preferences.
A2A-compliant agent for the Hermes platform.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os

app = FastAPI()

# Agent Card (A2A Protocol)
AGENT_CARD = {
    "name": "FlightBooker",
    "description": "Search and book flights worldwide. I can find the best deals based on your dates, budget, and preferences.",
    "version": "1.0.0",
    "capabilities": ["flight_search", "flight_booking", "price_comparison", "travel"],
    "endpoint": "http://localhost:10010/execute",
    "category": "travel",
    "provider": "Hermes Travel Services"
}


class TaskRequest(BaseModel):
    """A2A Task Request"""
    task_id: str
    action: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """A2A Task Response"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    needs_input: bool = False
    follow_up_question: Optional[str] = None


@app.get("/")
async def get_agent_card():
    """Return agent card (A2A discovery)"""
    return AGENT_CARD


@app.post("/execute")
async def execute_task(request: TaskRequest) -> TaskResponse:
    """
    Execute flight-related tasks

    Supported actions:
    - search_flights: Find available flights
    - get_price: Get price for specific flight
    - book_flight: Book a flight
    """

    if request.action == "search_flights":
        # Extract parameters
        origin = request.parameters.get("origin")
        destination = request.parameters.get("destination")
        departure_date = request.parameters.get("departure_date")
        return_date = request.parameters.get("return_date")
        passengers = request.parameters.get("passengers", 1)
        class_type = request.parameters.get("class", "economy")

        # Check if we need more info
        if not origin:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Where will you be departing from? (e.g., LAX, JFK, SFO)"
            )

        if not destination:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question=f"Great! Where would you like to fly from {origin}?"
            )

        if not departure_date:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question=f"When would you like to depart from {origin} to {destination}? (e.g., 2025-12-15)"
            )

        # Simulate flight search results
        flights = [
            {
                "flight_number": "AA123",
                "airline": "American Airlines",
                "departure": f"{origin} at 8:00 AM",
                "arrival": f"{destination} at 2:30 PM",
                "duration": "6h 30m",
                "price": 450,
                "class": class_type,
                "stops": 0
            },
            {
                "flight_number": "UA456",
                "airline": "United Airlines",
                "departure": f"{origin} at 11:00 AM",
                "arrival": f"{destination} at 5:45 PM",
                "duration": "6h 45m",
                "price": 380,
                "class": class_type,
                "stops": 1,
                "layover": "DEN (2h)"
            },
            {
                "flight_number": "DL789",
                "airline": "Delta Airlines",
                "departure": f"{origin} at 2:00 PM",
                "arrival": f"{destination} at 8:20 PM",
                "duration": "6h 20m",
                "price": 520,
                "class": class_type,
                "stops": 0,
                "premium": True
            }
        ]

        result = {
            "route": f"{origin} → {destination}",
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": passengers,
            "class": class_type,
            "flights_found": len(flights),
            "flights": flights,
            "cheapest": min(flights, key=lambda x: x["price"]),
            "fastest": min(flights, key=lambda x: float(x["duration"].replace("h", ".").replace("m", "").split()[0]))
        }

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result=result
        )

    elif request.action == "book_flight":
        flight_number = request.parameters.get("flight_number")
        passenger_name = request.parameters.get("passenger_name")

        if not flight_number:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Which flight would you like to book? Please provide the flight number."
            )

        if not passenger_name:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="What name should the ticket be under?"
            )

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "booking_confirmed": True,
                "confirmation_number": "ABC123XYZ",
                "flight_number": flight_number,
                "passenger": passenger_name,
                "message": f"✈️ Flight {flight_number} booked successfully! Confirmation: ABC123XYZ"
            }
        )

    else:
        return TaskResponse(
            task_id=request.task_id,
            status="error",
            error=f"Unknown action: {request.action}"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10010))
    print(f"🛫 Flight Booking Agent starting on port {port}")
    print(f"   Capabilities: {', '.join(AGENT_CARD['capabilities'])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
