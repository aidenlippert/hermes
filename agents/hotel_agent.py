"""
Hotel Booking Agent

Searches and books hotels based on user preferences.
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
    "name": "HotelBooker",
    "description": "Find and book hotels worldwide. I can search by location, price range, amenities, and ratings.",
    "version": "1.0.0",
    "capabilities": ["hotel_search", "hotel_booking", "accommodation", "travel"],
    "endpoint": "http://localhost:10011/execute",
    "category": "travel",
    "provider": "Hermes Travel Services"
}


class TaskRequest(BaseModel):
    task_id: str
    action: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    needs_input: bool = False
    follow_up_question: Optional[str] = None


@app.get("/")
async def get_agent_card():
    return AGENT_CARD


@app.post("/execute")
async def execute_task(request: TaskRequest) -> TaskResponse:
    """Execute hotel-related tasks"""

    if request.action == "search_hotels":
        location = request.parameters.get("location")
        check_in = request.parameters.get("check_in")
        check_out = request.parameters.get("check_out")
        guests = request.parameters.get("guests", 2)
        budget = request.parameters.get("budget")

        if not location:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Where would you like to stay?"
            )

        if not check_in:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question=f"When would you like to check in to your hotel in {location}?"
            )

        if not check_out:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="And when will you be checking out?"
            )

        # Simulate hotel search
        hotels = [
            {
                "name": "The Grand Plaza Hotel",
                "location": location,
                "rating": 4.5,
                "price_per_night": 250,
                "amenities": ["Pool", "Gym", "Free WiFi", "Breakfast"],
                "distance_from_center": "0.5 miles",
                "reviews": 1250
            },
            {
                "name": "Downtown Comfort Inn",
                "location": location,
                "rating": 4.0,
                "price_per_night": 120,
                "amenities": ["Free WiFi", "Parking"],
                "distance_from_center": "1.2 miles",
                "reviews": 850
            },
            {
                "name": "Luxury Suites & Spa",
                "location": location,
                "rating": 4.8,
                "price_per_night": 380,
                "amenities": ["Spa", "Pool", "Restaurant", "Gym", "Concierge"],
                "distance_from_center": "0.3 miles",
                "reviews": 2100
            }
        ]

        # Filter by budget if provided
        if budget:
            hotels = [h for h in hotels if h["price_per_night"] <= budget]

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "hotels_found": len(hotels),
                "hotels": hotels,
                "best_value": min(hotels, key=lambda x: x["price_per_night"] / x["rating"]) if hotels else None
            }
        )

    elif request.action == "book_hotel":
        hotel_name = request.parameters.get("hotel_name")
        guest_name = request.parameters.get("guest_name")

        if not hotel_name:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Which hotel would you like to book?"
            )

        if not guest_name:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="What name should the reservation be under?"
            )

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "booking_confirmed": True,
                "confirmation_number": "HTL789DEF",
                "hotel_name": hotel_name,
                "guest": guest_name,
                "message": f"🏨 {hotel_name} booked successfully! Confirmation: HTL789DEF"
            }
        )

    else:
        return TaskResponse(
            task_id=request.task_id,
            status="error",
            error=f"Unknown action: {request.action}"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10011))
    print(f"🏨 Hotel Booking Agent starting on port {port}")
    print(f"   Capabilities: {', '.join(AGENT_CARD['capabilities'])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
