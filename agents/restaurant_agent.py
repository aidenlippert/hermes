"""
Restaurant Recommendation Agent

Finds and recommends restaurants based on cuisine, location, and preferences.
A2A-compliant agent for the Hermes platform.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os

app = FastAPI()

AGENT_CARD = {
    "name": "RestaurantFinder",
    "description": "Discover amazing restaurants and make reservations. I can find dining options based on cuisine, location, budget, and dietary preferences.",
    "version": "1.0.0",
    "capabilities": ["restaurant_search", "restaurant_reservation", "dining", "food", "travel"],
    "endpoint": "http://localhost:10012/execute",
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
    """Execute restaurant-related tasks"""

    if request.action == "find_restaurants":
        location = request.parameters.get("location")
        cuisine = request.parameters.get("cuisine")
        budget = request.parameters.get("budget", "moderate")
        dietary = request.parameters.get("dietary_restrictions", [])

        if not location:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Where would you like to dine?"
            )

        # Simulate restaurant search
        restaurants = [
            {
                "name": "La Bella Vista",
                "cuisine": "Italian",
                "rating": 4.7,
                "price_range": "$$$",
                "location": location,
                "specialties": ["Pasta", "Pizza", "Wine"],
                "atmosphere": "Romantic",
                "dietary_options": ["Vegetarian", "Gluten-free"]
            },
            {
                "name": "Sakura Sushi House",
                "cuisine": "Japanese",
                "rating": 4.8,
                "price_range": "$$",
                "location": location,
                "specialties": ["Sushi", "Ramen", "Sake"],
                "atmosphere": "Modern",
                "dietary_options": ["Vegetarian", "Pescatarian"]
            },
            {
                "name": "The Steakhouse Prime",
                "cuisine": "American",
                "rating": 4.6,
                "price_range": "$$$$",
                "location": location,
                "specialties": ["Steaks", "Seafood", "Wine"],
                "atmosphere": "Upscale",
                "dietary_options": ["Gluten-free"]
            },
            {
                "name": "Green Garden Bistro",
                "cuisine": "Vegetarian/Vegan",
                "rating": 4.5,
                "price_range": "$$",
                "location": location,
                "specialties": ["Plant-based", "Organic", "Smoothies"],
                "atmosphere": "Casual",
                "dietary_options": ["Vegan", "Gluten-free", "Organic"]
            }
        ]

        # Filter by cuisine if specified
        if cuisine:
            restaurants = [r for r in restaurants if cuisine.lower() in r["cuisine"].lower()]

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "location": location,
                "cuisine": cuisine or "All cuisines",
                "budget": budget,
                "restaurants_found": len(restaurants),
                "restaurants": restaurants,
                "top_rated": max(restaurants, key=lambda x: x["rating"]) if restaurants else None
            }
        )

    elif request.action == "make_reservation":
        restaurant_name = request.parameters.get("restaurant_name")
        date = request.parameters.get("date")
        time = request.parameters.get("time")
        party_size = request.parameters.get("party_size")
        guest_name = request.parameters.get("guest_name")

        if not restaurant_name:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Which restaurant would you like to book?"
            )

        if not date or not time:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question=f"When would you like to dine at {restaurant_name}? (date and time)"
            )

        if not party_size:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="How many people will be dining?"
            )

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "reservation_confirmed": True,
                "confirmation_number": "RST456GHI",
                "restaurant": restaurant_name,
                "date": date,
                "time": time,
                "party_size": party_size,
                "message": f"🍽️ Table for {party_size} reserved at {restaurant_name} on {date} at {time}. Confirmation: RST456GHI"
            }
        )

    else:
        return TaskResponse(
            task_id=request.task_id,
            status="error",
            error=f"Unknown action: {request.action}"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10012))
    print(f"🍽️  Restaurant Finder Agent starting on port {port}")
    print(f"   Capabilities: {', '.join(AGENT_CARD['capabilities'])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
