"""
Events & Activities Agent

Finds local events, attractions, and activities for travelers.
A2A-compliant agent for the Hermes platform.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os

app = FastAPI()

AGENT_CARD = {
    "name": "EventsFinder",
    "description": "Discover local events, attractions, and activities. I can find concerts, shows, tours, museums, and unique experiences.",
    "version": "1.0.0",
    "capabilities": ["events_search", "activities", "attractions", "entertainment", "travel"],
    "endpoint": "http://localhost:10013/execute",
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
    """Execute events-related tasks"""

    if request.action == "find_events":
        location = request.parameters.get("location")
        date = request.parameters.get("date")
        event_type = request.parameters.get("event_type")
        interests = request.parameters.get("interests", [])

        if not location:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Where would you like to explore events and activities?"
            )

        if not date:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question=f"When will you be visiting {location}?"
            )

        # Simulate events search
        events = [
            {
                "name": "City Walking Tour",
                "type": "Tour",
                "date": date,
                "time": "10:00 AM",
                "duration": "3 hours",
                "price": 35,
                "rating": 4.9,
                "description": "Guided walking tour of historic downtown",
                "availability": "Open"
            },
            {
                "name": "Symphony Orchestra Concert",
                "type": "Music",
                "date": date,
                "time": "7:30 PM",
                "duration": "2 hours",
                "price": 85,
                "rating": 4.8,
                "description": "Classical music performance at the Grand Hall",
                "availability": "Limited seats"
            },
            {
                "name": "Museum of Modern Art",
                "type": "Museum",
                "date": date,
                "time": "9:00 AM - 6:00 PM",
                "duration": "Flexible",
                "price": 25,
                "rating": 4.7,
                "description": "World-class contemporary art collection",
                "availability": "Open"
            },
            {
                "name": "Food & Wine Festival",
                "type": "Festival",
                "date": date,
                "time": "12:00 PM - 10:00 PM",
                "duration": "All day",
                "price": 60,
                "rating": 4.6,
                "description": "Sample local cuisine and wines from 50+ vendors",
                "availability": "Open"
            },
            {
                "name": "Sunset Harbor Cruise",
                "type": "Experience",
                "date": date,
                "time": "6:00 PM",
                "duration": "2.5 hours",
                "price": 75,
                "rating": 4.9,
                "description": "Scenic cruise with dinner and live music",
                "availability": "Open"
            }
        ]

        # Filter by event type if specified
        if event_type:
            events = [e for e in events if event_type.lower() in e["type"].lower()]

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "location": location,
                "date": date,
                "event_type": event_type or "All types",
                "events_found": len(events),
                "events": events,
                "top_rated": max(events, key=lambda x: x["rating"]) if events else None,
                "must_do": [e for e in events if e["rating"] >= 4.8]
            }
        )

    elif request.action == "book_event":
        event_name = request.parameters.get("event_name")
        tickets = request.parameters.get("tickets", 1)
        guest_name = request.parameters.get("guest_name")

        if not event_name:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="Which event or activity would you like to book?"
            )

        if not guest_name:
            return TaskResponse(
                task_id=request.task_id,
                status="needs_input",
                needs_input=True,
                follow_up_question="What name should the tickets be under?"
            )

        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={
                "booking_confirmed": True,
                "confirmation_number": "EVT123JKL",
                "event": event_name,
                "tickets": tickets,
                "guest": guest_name,
                "message": f"🎟️ {tickets} ticket(s) booked for {event_name}! Confirmation: EVT123JKL"
            }
        )

    else:
        return TaskResponse(
            task_id=request.task_id,
            status="error",
            error=f"Unknown action: {request.action}"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10013))
    print(f"🎭 Events Finder Agent starting on port {port}")
    print(f"   Capabilities: {', '.join(AGENT_CARD['capabilities'])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
