"""
Hotel Booking Agent - Full A2A Protocol Compliance

Searches and books hotels based on user preferences.
Fully compliant with Google's Agent-to-Agent (A2A) Protocol v0.3.0
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum
import uvicorn
import os
import json
import asyncio
import uuid

app = FastAPI()

# A2A Protocol Data Models

class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str

class DataPart(BaseModel):
    type: Literal["data"] = "data"
    data: Dict[str, Any]
    mimeType: str = "application/json"

Part = Union[TextPart, DataPart]

class Message(BaseModel):
    role: Literal["user", "agent"]
    parts: List[Part]
    messageId: Optional[str] = None

class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[str] = None

class Artifact(BaseModel):
    parts: List[Part]
    index: int = 0

class Task(BaseModel):
    id: str
    status: TaskStatus
    artifacts: List[Artifact] = []

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Dict[str, Any]
    id: Union[str, int]

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "HotelBooker",
    "description": "Find and book hotels worldwide. I can search by location, price range, amenities, and ratings.",
    "version": "1.0.0",
    "skills": [
        {
            "name": "search_hotels",
            "description": "Find available hotels based on location, dates, and preferences",
            "examples": [
                "Find hotels in Paris for December 15-20",
                "Search for hotels near Times Square under $200 per night",
                "I need a 4-star hotel in Tokyo with free wifi"
            ],
            "inputs": {
                "location": "City or address",
                "check_in": "Check-in date in YYYY-MM-DD format",
                "check_out": "Check-out date in YYYY-MM-DD format",
                "guests": "Number of guests (default: 2)",
                "max_price": "Maximum price per night (optional)",
                "min_rating": "Minimum star rating 1-5 (optional)",
                "amenities": "List of required amenities (optional)"
            }
        },
        {
            "name": "book_hotel",
            "description": "Book a specific hotel room",
            "examples": [
                "Book the Hilton Paris for 2 nights",
                "I want to book room at the Grand Hotel"
            ],
            "inputs": {
                "hotel_name": "Name of the hotel",
                "guest_name": "Full name of guest",
                "contact_email": "Email for confirmation (optional)",
                "special_requests": "Special requests (optional)"
            }
        }
    ],
    "category": "travel",
    "provider": "Hermes Travel Services",
    "endpoint": "http://localhost:10011",
    "defaultInputModes": ["text", "data"],
    "defaultOutputModes": ["text", "data"],
    "securitySchemes": {"none": {"type": "none"}}
}

tasks_db: Dict[str, Task] = {}

def create_text_part(text: str) -> TextPart:
    return TextPart(text=text)

def create_data_part(data: Dict[str, Any]) -> DataPart:
    return DataPart(data=data)

def create_artifact(parts: List[Part]) -> Artifact:
    return Artifact(parts=parts)

def create_task(task_id: str, state: TaskState, message: str = None, artifacts: List[Artifact] = None) -> Task:
    return Task(id=task_id, status=TaskStatus(state=state, message=message), artifacts=artifacts or [])

async def search_hotels(params: Dict[str, Any], task_id: str) -> Task:
    location = params.get("location")
    check_in = params.get("check_in")
    check_out = params.get("check_out")
    guests = params.get("guests", 2)
    max_price = params.get("max_price")
    min_rating = params.get("min_rating")

    if not location:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "Where would you like to stay?",
            [create_artifact([create_text_part("Please provide the city or location.")])])

    if not check_in:
        return create_task(task_id, TaskState.INPUT_REQUIRED, f"When would you like to check in to a hotel in {location}?",
            [create_artifact([create_text_part("When is your check-in date? (e.g., 2025-12-15)")])])

    if not check_out:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "When would you like to check out?",
            [create_artifact([create_text_part("When is your check-out date?")])])

    hotels = [
        {"name": "Grand Plaza Hotel", "location": f"{location} City Center", "rating": 4.5, "price_per_night": 180,
         "amenities": ["WiFi", "Pool", "Gym", "Restaurant", "Parking"], "distance_to_center": "0.5 km", "room_type": "Deluxe King"},
        {"name": "Comfort Inn & Suites", "location": f"{location} Downtown", "rating": 4.0, "price_per_night": 120,
         "amenities": ["WiFi", "Breakfast", "Parking"], "distance_to_center": "1.2 km", "room_type": "Standard Double"},
        {"name": "Luxury Resort & Spa", "location": f"{location} Waterfront", "rating": 5.0, "price_per_night": 350,
         "amenities": ["WiFi", "Pool", "Spa", "Gym", "Restaurant", "Beach Access", "Concierge"], "distance_to_center": "3.0 km", "room_type": "Ocean View Suite"},
        {"name": "Budget Stay Hotel", "location": f"{location} Airport Area", "rating": 3.5, "price_per_night": 75,
         "amenities": ["WiFi", "Parking", "Airport Shuttle"], "distance_to_center": "8.0 km", "room_type": "Economy Room"}
    ]

    filtered = hotels
    if max_price:
        filtered = [h for h in filtered if h["price_per_night"] <= max_price]
    if min_rating:
        filtered = [h for h in filtered if h["rating"] >= min_rating]

    result = {
        "location": location, "check_in": check_in, "check_out": check_out, "guests": guests,
        "hotels_found": len(filtered), "hotels": filtered,
        "best_value": min(filtered, key=lambda x: x["price_per_night"]) if filtered else None,
        "highest_rated": max(filtered, key=lambda x: x["rating"]) if filtered else None
    }

    text_summary = f"Found {len(filtered)} hotels in {location} for {check_in} to {check_out}. Best value: ${result['best_value']['price_per_night']}/night at {result['best_value']['name']}" if filtered else f"No hotels found matching your criteria in {location}"
    return create_task(task_id, TaskState.COMPLETED, "Hotel search completed successfully",
        [create_artifact([create_text_part(text_summary), create_data_part(result)])])

async def book_hotel(params: Dict[str, Any], task_id: str) -> Task:
    hotel_name = params.get("hotel_name")
    guest_name = params.get("guest_name")
    contact_email = params.get("contact_email")

    if not hotel_name:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "Which hotel would you like to book?",
            [create_artifact([create_text_part("Please provide the hotel name.")])])
    if not guest_name:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "What name should the reservation be under?",
            [create_artifact([create_text_part("Please provide the guest name.")])])

    confirmation = f"HTL{uuid.uuid4().hex[:8].upper()}"
    result = {"booking_confirmed": True, "confirmation_number": confirmation, "hotel_name": hotel_name,
              "guest_name": guest_name, "contact_email": contact_email, "booking_date": datetime.utcnow().isoformat()}
    text_summary = f"🏨 Hotel reservation confirmed at {hotel_name} for {guest_name}! Confirmation: {confirmation}"
    return create_task(task_id, TaskState.COMPLETED, "Hotel booking completed successfully",
        [create_artifact([create_text_part(text_summary), create_data_part(result)])])

@app.get("/.well-known/agent-card.json")
@app.get("/")
async def get_agent_card():
    return AGENT_CARD

@app.post("/")
async def json_rpc_endpoint(request: Request):
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)
        if rpc_request.method == "message/send":
            result = await message_send(rpc_request.params)
        elif rpc_request.method == "tasks/get":
            result = await tasks_get(rpc_request.params)
        elif rpc_request.method == "tasks/cancel":
            result = await tasks_cancel(rpc_request.params)
        elif rpc_request.method == "tasks/list":
            result = await tasks_list(rpc_request.params)
        else:
            return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {rpc_request.method}"}, "id": rpc_request.id})
        return JSONResponse({"jsonrpc": "2.0", "result": result, "id": rpc_request.id})
    except Exception as e:
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error", "data": str(e)}, "id": body.get("id") if isinstance(body, dict) else None})

async def message_send(params: Dict[str, Any]) -> Dict[str, Any]:
    task_id = params.get("taskId") or str(uuid.uuid4())
    messages = params.get("messages", [])
    skill = params.get("skill")
    user_params = {}
    if messages:
        for part in messages[-1].get("parts", []):
            if part.get("type") == "data":
                user_params = part.get("data", {})
    if not skill and messages:
        last_text = "".join([part.get("text", "") for part in messages[-1].get("parts", []) if part.get("type") == "text"])
        skill = "book_hotel" if "book" in last_text.lower() else "search_hotels"
    task = await search_hotels(user_params, task_id) if skill == "search_hotels" else await book_hotel(user_params, task_id) if skill == "book_hotel" else create_task(task_id, TaskState.FAILED, f"Unknown skill: {skill}")
    tasks_db[task_id] = task
    return task.dict()

async def tasks_get(params: Dict[str, Any]) -> Dict[str, Any]:
    task_id = params.get("taskId")
    if not task_id or task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id].dict()

async def tasks_cancel(params: Dict[str, Any]) -> Dict[str, Any]:
    task_id = params.get("taskId")
    if task_id in tasks_db:
        tasks_db[task_id].status.state = TaskState.CANCELED
        return tasks_db[task_id].dict()
    raise HTTPException(status_code=404, detail="Task not found")

async def tasks_list(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"tasks": [task.dict() for task in tasks_db.values()]}

@app.get("/stream/{task_id}")
async def stream_task(task_id: str):
    async def event_stream():
        if task_id in tasks_db:
            yield f"data: {json.dumps({'type': 'TaskStatusUpdateEvent', 'task': tasks_db[task_id].dict()})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/execute")
async def execute_legacy(request: Request):
    body = await request.json()
    task_id = body.get("task_id", str(uuid.uuid4()))
    action = body.get("action")
    parameters = body.get("parameters", {})
    task = await search_hotels(parameters, task_id) if action == "search_hotels" else await book_hotel(parameters, task_id) if action == "book_hotel" else None
    if not task:
        return {"error": f"Unknown action: {action}"}
    tasks_db[task_id] = task
    return {
        "task_id": task.id, "status": task.status.state.value,
        "result": task.artifacts[0].parts[1].data if task.artifacts and len(task.artifacts[0].parts) > 1 else None,
        "needs_input": task.status.state == TaskState.INPUT_REQUIRED,
        "follow_up_question": task.status.message if task.status.state == TaskState.INPUT_REQUIRED else None
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10011))
    print(f"🏨 Hotel Booking Agent (A2A v0.3.0) starting on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: {', '.join([s['name'] for s in AGENT_CARD['skills']])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
