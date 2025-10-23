"""
Restaurant Finder Agent - Full A2A Protocol Compliance

Finds and recommends restaurants based on cuisine, location, and preferences.
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
    "name": "RestaurantFinder",
    "description": "Discover amazing restaurants and make reservations. I can find dining options based on cuisine, location, budget, and dietary preferences.",
    "version": "1.0.0",
    "skills": [
        {
            "name": "find_restaurants",
            "description": "Search for restaurants based on location, cuisine, and preferences",
            "examples": [
                "Find Italian restaurants in Paris",
                "I need a vegan restaurant near Times Square",
                "Show me romantic restaurants in Tokyo"
            ],
            "inputs": {
                "location": "City or area",
                "cuisine": "Type of cuisine (optional)",
                "budget": "Budget level: budget/moderate/upscale (optional)",
                "dietary_restrictions": "Dietary needs (optional)"
            }
        },
        {
            "name": "make_reservation",
            "description": "Make a restaurant reservation",
            "examples": [
                "Book a table at La Bella Vista for 2 people",
                "Reserve dinner at Sakura Sushi House for tomorrow at 7pm"
            ],
            "inputs": {
                "restaurant_name": "Name of restaurant",
                "date": "Reservation date",
                "time": "Reservation time",
                "party_size": "Number of people",
                "guest_name": "Name for reservation"
            }
        }
    ],
    "category": "travel",
    "provider": "Hermes Travel Services",
    "endpoint": "http://localhost:10012",
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

async def find_restaurants(params: Dict[str, Any], task_id: str) -> Task:
    location = params.get("location")
    cuisine = params.get("cuisine")
    budget = params.get("budget", "moderate")

    if not location:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "Where would you like to dine?",
            [create_artifact([create_text_part("Please provide the city or area.")])])

    restaurants = [
        {"name": "La Bella Vista", "cuisine": "Italian", "rating": 4.7, "price_range": "$$$",
         "location": location, "specialties": ["Pasta", "Pizza", "Wine"], "atmosphere": "Romantic", "dietary_options": ["Vegetarian", "Gluten-free"]},
        {"name": "Sakura Sushi House", "cuisine": "Japanese", "rating": 4.8, "price_range": "$$",
         "location": location, "specialties": ["Sushi", "Ramen", "Sake"], "atmosphere": "Modern", "dietary_options": ["Vegetarian", "Pescatarian"]},
        {"name": "The Steakhouse Prime", "cuisine": "American", "rating": 4.6, "price_range": "$$$$",
         "location": location, "specialties": ["Steaks", "Seafood", "Wine"], "atmosphere": "Upscale", "dietary_options": ["Gluten-free"]},
        {"name": "Green Garden Bistro", "cuisine": "Vegetarian/Vegan", "rating": 4.5, "price_range": "$$",
         "location": location, "specialties": ["Plant-based", "Organic", "Smoothies"], "atmosphere": "Casual", "dietary_options": ["Vegan", "Gluten-free", "Organic"]}
    ]

    filtered = restaurants
    if cuisine:
        filtered = [r for r in filtered if cuisine.lower() in r["cuisine"].lower()]

    result = {
        "location": location, "cuisine": cuisine or "All cuisines", "budget": budget,
        "restaurants_found": len(filtered), "restaurants": filtered,
        "top_rated": max(filtered, key=lambda x: x["rating"]) if filtered else None
    }

    text_summary = f"Found {len(filtered)} restaurants in {location}. Top rated: {result['top_rated']['name']} ({result['top_rated']['rating']} stars)" if filtered else f"No restaurants found in {location}"
    return create_task(task_id, TaskState.COMPLETED, "Restaurant search completed successfully",
        [create_artifact([create_text_part(text_summary), create_data_part(result)])])

async def make_reservation(params: Dict[str, Any], task_id: str) -> Task:
    restaurant_name = params.get("restaurant_name")
    date = params.get("date")
    time = params.get("time")
    party_size = params.get("party_size")
    guest_name = params.get("guest_name")

    if not restaurant_name:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "Which restaurant would you like to book?",
            [create_artifact([create_text_part("Please provide the restaurant name.")])])
    if not date or not time:
        return create_task(task_id, TaskState.INPUT_REQUIRED, f"When would you like to dine at {restaurant_name}?",
            [create_artifact([create_text_part("Please provide date and time.")])])
    if not party_size:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "How many people will be dining?",
            [create_artifact([create_text_part("Please provide party size.")])])

    confirmation = f"RST{uuid.uuid4().hex[:8].upper()}"
    result = {"reservation_confirmed": True, "confirmation_number": confirmation, "restaurant": restaurant_name,
              "date": date, "time": time, "party_size": party_size, "guest_name": guest_name}
    text_summary = f"🍽️ Table for {party_size} reserved at {restaurant_name} on {date} at {time}. Confirmation: {confirmation}"
    return create_task(task_id, TaskState.COMPLETED, "Reservation completed successfully",
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
        skill = "make_reservation" if "book" in last_text.lower() or "reserve" in last_text.lower() else "find_restaurants"
    task = await find_restaurants(user_params, task_id) if skill == "find_restaurants" else await make_reservation(user_params, task_id) if skill == "make_reservation" else create_task(task_id, TaskState.FAILED, f"Unknown skill: {skill}")
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
    task = await find_restaurants(parameters, task_id) if action == "find_restaurants" else await make_reservation(parameters, task_id) if action == "make_reservation" else None
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
    port = int(os.getenv("PORT", 10012))
    print(f"🍽️ Restaurant Finder Agent (A2A v0.3.0) starting on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: {', '.join([s['name'] for s in AGENT_CARD['skills']])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
