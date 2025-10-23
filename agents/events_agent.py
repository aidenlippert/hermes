"""
Events & Activities Agent - Full A2A Protocol Compliance

Finds local events, attractions, and activities for travelers.
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
    "name": "EventsFinder",
    "description": "Discover local events, attractions, and activities. I can find concerts, shows, tours, museums, and unique experiences.",
    "version": "1.0.0",
    "skills": [
        {
            "name": "find_events",
            "description": "Search for local events and activities",
            "examples": [
                "What events are happening in Paris this weekend?",
                "Find museums in Tokyo",
                "Show me concerts in New York next month"
            ],
            "inputs": {
                "location": "City or area",
                "date": "Date or date range (optional)",
                "event_type": "Type: tour/museum/concert/festival/experience (optional)",
                "interests": "List of interests (optional)"
            }
        },
        {
            "name": "book_event",
            "description": "Book tickets for an event or activity",
            "examples": [
                "Book 2 tickets for the City Walking Tour",
                "I want to book the Symphony Orchestra Concert"
            ],
            "inputs": {
                "event_name": "Name of event",
                "tickets": "Number of tickets",
                "guest_name": "Name for booking"
            }
        }
    ],
    "category": "travel",
    "provider": "Hermes Travel Services",
    "endpoint": "http://localhost:10013",
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

async def find_events(params: Dict[str, Any], task_id: str) -> Task:
    location = params.get("location")
    date = params.get("date")
    event_type = params.get("event_type")

    if not location:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "Where would you like to explore events and activities?",
            [create_artifact([create_text_part("Please provide the city or location.")])])

    if not date:
        return create_task(task_id, TaskState.INPUT_REQUIRED, f"When will you be visiting {location}?",
            [create_artifact([create_text_part("Please provide the date or date range.")])])

    events = [
        {"name": "City Walking Tour", "type": "Tour", "date": date, "time": "10:00 AM", "duration": "3 hours",
         "price": 35, "rating": 4.9, "description": "Guided walking tour of historic downtown", "availability": "Open"},
        {"name": "Symphony Orchestra Concert", "type": "Music", "date": date, "time": "7:30 PM", "duration": "2 hours",
         "price": 85, "rating": 4.8, "description": "Classical music performance at the Grand Hall", "availability": "Limited seats"},
        {"name": "Museum of Modern Art", "type": "Museum", "date": date, "time": "9:00 AM - 6:00 PM", "duration": "Flexible",
         "price": 25, "rating": 4.7, "description": "World-class contemporary art collection", "availability": "Open"},
        {"name": "Food & Wine Festival", "type": "Festival", "date": date, "time": "12:00 PM - 10:00 PM", "duration": "All day",
         "price": 60, "rating": 4.6, "description": "Sample local cuisine and wines from 50+ vendors", "availability": "Open"},
        {"name": "Sunset Harbor Cruise", "type": "Experience", "date": date, "time": "6:00 PM", "duration": "2.5 hours",
         "price": 75, "rating": 4.9, "description": "Scenic cruise with dinner and live music", "availability": "Open"}
    ]

    filtered = events
    if event_type:
        filtered = [e for e in filtered if event_type.lower() in e["type"].lower()]

    result = {
        "location": location, "date": date, "event_type": event_type or "All types",
        "events_found": len(filtered), "events": filtered,
        "top_rated": max(filtered, key=lambda x: x["rating"]) if filtered else None,
        "must_do": [e for e in filtered if e["rating"] >= 4.8]
    }

    text_summary = f"Found {len(filtered)} events and activities in {location} for {date}. Top rated: {result['top_rated']['name']} ({result['top_rated']['rating']} stars)" if filtered else f"No events found in {location}"
    return create_task(task_id, TaskState.COMPLETED, "Event search completed successfully",
        [create_artifact([create_text_part(text_summary), create_data_part(result)])])

async def book_event(params: Dict[str, Any], task_id: str) -> Task:
    event_name = params.get("event_name")
    tickets = params.get("tickets", 1)
    guest_name = params.get("guest_name")

    if not event_name:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "Which event or activity would you like to book?",
            [create_artifact([create_text_part("Please provide the event name.")])])
    if not guest_name:
        return create_task(task_id, TaskState.INPUT_REQUIRED, "What name should the tickets be under?",
            [create_artifact([create_text_part("Please provide the guest name.")])])

    confirmation = f"EVT{uuid.uuid4().hex[:8].upper()}"
    result = {"booking_confirmed": True, "confirmation_number": confirmation, "event": event_name,
              "tickets": tickets, "guest": guest_name}
    text_summary = f"🎟️ {tickets} ticket(s) booked for {event_name}! Confirmation: {confirmation}"
    return create_task(task_id, TaskState.COMPLETED, "Event booking completed successfully",
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
        skill = "book_event" if "book" in last_text.lower() else "find_events"
    task = await find_events(user_params, task_id) if skill == "find_events" else await book_event(user_params, task_id) if skill == "book_event" else create_task(task_id, TaskState.FAILED, f"Unknown skill: {skill}")
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
    task = await find_events(parameters, task_id) if action == "find_events" else await book_event(parameters, task_id) if action == "book_event" else None
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
    port = int(os.getenv("PORT", 10013))
    print(f"🎭 Events Finder Agent (A2A v0.3.0) starting on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: {', '.join([s['name'] for s in AGENT_CARD['skills']])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
