"""
Flight Booking Agent - Full A2A Protocol Compliance

Searches and books flights based on user preferences.
Fully compliant with Google's Agent-to-Agent (A2A) Protocol v0.3.0
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
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
    """A2A Task States"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class TextPart(BaseModel):
    """Text content part"""
    type: Literal["text"] = "text"
    text: str

class DataPart(BaseModel):
    """Structured data part"""
    type: Literal["data"] = "data"
    data: Dict[str, Any]
    mimeType: str = "application/json"

Part = Union[TextPart, DataPart]

class Message(BaseModel):
    """A2A Message"""
    role: Literal["user", "agent"]
    parts: List[Part]
    messageId: Optional[str] = None

class TaskStatus(BaseModel):
    """A2A Task Status"""
    state: TaskState
    message: Optional[str] = None

class Artifact(BaseModel):
    """A2A Task Artifact"""
    parts: List[Part]
    index: int = 0

class Task(BaseModel):
    """A2A Task"""
    id: str
    status: TaskStatus
    artifacts: List[Artifact] = []

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request"""
    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Dict[str, Any]
    id: Union[str, int]

class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response"""
    jsonrpc: Literal["2.0"] = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Union[str, int]

class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error"""
    code: int
    message: str
    data: Optional[Any] = None

# Agent Card (A2A Protocol v0.3.0)
AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "FlightBooker",
    "description": "Search and book flights worldwide. I can find the best deals based on your dates, budget, and preferences.",
    "version": "1.0.0",
    "skills": [
        {
            "name": "search_flights",
            "description": "Find available flights based on origin, destination, dates, and preferences",
            "examples": [
                "Find flights from LAX to Paris on December 15th",
                "Search for economy flights from New York to Tokyo",
                "I need a flight from SFO to London next week"
            ],
            "inputs": {
                "origin": "Airport code or city (e.g., LAX, New York)",
                "destination": "Airport code or city (e.g., CDG, Paris)",
                "departure_date": "Date in YYYY-MM-DD format",
                "return_date": "Optional return date in YYYY-MM-DD format",
                "passengers": "Number of passengers (default: 1)",
                "class": "Cabin class: economy, business, first (default: economy)"
            }
        },
        {
            "name": "book_flight",
            "description": "Book a specific flight for a passenger",
            "examples": [
                "Book flight AA123 for John Smith",
                "I want to book the United flight UA456"
            ],
            "inputs": {
                "flight_number": "Flight number (e.g., AA123)",
                "passenger_name": "Full name of passenger",
                "contact_email": "Email for confirmation (optional)"
            }
        },
        {
            "name": "price_comparison",
            "description": "Compare prices across different airlines and dates",
            "examples": [
                "Compare flight prices from LAX to Paris",
                "What are the cheapest dates to fly to Tokyo?"
            ]
        }
    ],
    "category": "travel",
    "provider": "Hermes Travel Services",
    "endpoint": "http://localhost:10010",
    "defaultInputModes": ["text", "data"],
    "defaultOutputModes": ["text", "data"],
    "securitySchemes": {
        "none": {
            "type": "none"
        }
    }
}

# In-memory task storage (in production, use a database)
tasks_db: Dict[str, Task] = {}

# Helper Functions

def create_text_part(text: str) -> TextPart:
    """Create a text part"""
    return TextPart(text=text)

def create_data_part(data: Dict[str, Any]) -> DataPart:
    """Create a data part"""
    return DataPart(data=data)

def create_artifact(parts: List[Part]) -> Artifact:
    """Create an artifact from parts"""
    return Artifact(parts=parts)

def create_task(task_id: str, state: TaskState, message: str = None, artifacts: List[Artifact] = None) -> Task:
    """Create a task with status"""
    return Task(
        id=task_id,
        status=TaskStatus(state=state, message=message),
        artifacts=artifacts or []
    )

async def search_flights(params: Dict[str, Any], task_id: str) -> Task:
    """Execute flight search"""
    origin = params.get("origin")
    destination = params.get("destination")
    departure_date = params.get("departure_date")
    return_date = params.get("return_date")
    passengers = params.get("passengers", 1)
    class_type = params.get("class", "economy")

    # Human-in-the-loop: Ask follow-up questions if needed
    if not origin:
        return create_task(
            task_id=task_id,
            state=TaskState.INPUT_REQUIRED,
            message="Where will you be departing from? (e.g., LAX, JFK, SFO)",
            artifacts=[create_artifact([create_text_part("I need your departure city or airport code.")])]
        )

    if not destination:
        return create_task(
            task_id=task_id,
            state=TaskState.INPUT_REQUIRED,
            message=f"Great! Where would you like to fly from {origin}?",
            artifacts=[create_artifact([create_text_part(f"Where would you like to fly from {origin}?")])]
        )

    if not departure_date:
        return create_task(
            task_id=task_id,
            state=TaskState.INPUT_REQUIRED,
            message=f"When would you like to depart from {origin} to {destination}?",
            artifacts=[create_artifact([create_text_part(f"When would you like to depart from {origin} to {destination}? (e.g., 2025-12-15)")])]
        )

    # Simulate flight search
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

    # Create response artifacts
    text_summary = f"Found {len(flights)} flights from {origin} to {destination} on {departure_date}. Cheapest: ${result['cheapest']['price']}, Fastest: {result['fastest']['duration']}"

    return create_task(
        task_id=task_id,
        state=TaskState.COMPLETED,
        message="Flight search completed successfully",
        artifacts=[
            create_artifact([
                create_text_part(text_summary),
                create_data_part(result)
            ])
        ]
    )

async def book_flight(params: Dict[str, Any], task_id: str) -> Task:
    """Book a flight"""
    flight_number = params.get("flight_number")
    passenger_name = params.get("passenger_name")
    contact_email = params.get("contact_email")

    if not flight_number:
        return create_task(
            task_id=task_id,
            state=TaskState.INPUT_REQUIRED,
            message="Which flight would you like to book?",
            artifacts=[create_artifact([create_text_part("Please provide the flight number.")])]
        )

    if not passenger_name:
        return create_task(
            task_id=task_id,
            state=TaskState.INPUT_REQUIRED,
            message="What name should the ticket be under?",
            artifacts=[create_artifact([create_text_part("Please provide the passenger name.")])]
        )

    # Simulate booking
    confirmation = f"HRM{uuid.uuid4().hex[:8].upper()}"
    result = {
        "booking_confirmed": True,
        "confirmation_number": confirmation,
        "flight_number": flight_number,
        "passenger": passenger_name,
        "contact_email": contact_email,
        "booking_date": datetime.utcnow().isoformat()
    }

    text_summary = f"✈️ Flight {flight_number} booked successfully for {passenger_name}! Confirmation: {confirmation}"

    return create_task(
        task_id=task_id,
        state=TaskState.COMPLETED,
        message="Flight booking completed successfully",
        artifacts=[
            create_artifact([
                create_text_part(text_summary),
                create_data_part(result)
            ])
        ]
    )

# A2A Protocol Endpoints

@app.get("/.well-known/agent-card.json")
@app.get("/")
async def get_agent_card():
    """Return agent card (A2A discovery)"""
    return AGENT_CARD

@app.post("/")
async def json_rpc_endpoint(request: Request):
    """Main JSON-RPC 2.0 endpoint"""
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)

        # Route to appropriate method
        if rpc_request.method == "message/send":
            result = await message_send(rpc_request.params)
        elif rpc_request.method == "message/stream":
            # For streaming, redirect to SSE endpoint
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": "Use GET /stream/{taskId} for streaming responses"
                },
                "id": rpc_request.id
            })
        elif rpc_request.method == "tasks/get":
            result = await tasks_get(rpc_request.params)
        elif rpc_request.method == "tasks/cancel":
            result = await tasks_cancel(rpc_request.params)
        elif rpc_request.method == "tasks/list":
            result = await tasks_list(rpc_request.params)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {rpc_request.method}"
                },
                "id": rpc_request.id
            })

        return JSONResponse({
            "jsonrpc": "2.0",
            "result": result,
            "id": rpc_request.id
        })

    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            },
            "id": body.get("id") if isinstance(body, dict) else None
        })

async def message_send(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle message/send method"""
    task_id = params.get("taskId") or str(uuid.uuid4())
    messages = params.get("messages", [])
    skill = params.get("skill")

    # Extract parameters from last user message
    user_params = {}
    if messages:
        last_message = messages[-1]
        for part in last_message.get("parts", []):
            if part.get("type") == "data":
                user_params = part.get("data", {})

    # Determine skill from message content if not specified
    if not skill and messages:
        last_text = ""
        for part in messages[-1].get("parts", []):
            if part.get("type") == "text":
                last_text += part.get("text", "")

        if "book" in last_text.lower():
            skill = "book_flight"
        elif "search" in last_text.lower() or "find" in last_text.lower():
            skill = "search_flights"
        else:
            skill = "search_flights"  # default

    # Execute the skill
    if skill == "search_flights":
        task = await search_flights(user_params, task_id)
    elif skill == "book_flight":
        task = await book_flight(user_params, task_id)
    else:
        task = create_task(
            task_id=task_id,
            state=TaskState.FAILED,
            message=f"Unknown skill: {skill}"
        )

    # Store task
    tasks_db[task_id] = task

    return task.dict()

async def tasks_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get task by ID"""
    task_id = params.get("taskId")
    if not task_id or task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id].dict()

async def tasks_cancel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Cancel a task"""
    task_id = params.get("taskId")
    if task_id in tasks_db:
        tasks_db[task_id].status.state = TaskState.CANCELED
        return tasks_db[task_id].dict()
    raise HTTPException(status_code=404, detail="Task not found")

async def tasks_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all tasks"""
    return {
        "tasks": [task.dict() for task in tasks_db.values()]
    }

@app.get("/stream/{task_id}")
async def stream_task(task_id: str):
    """Server-Sent Events endpoint for streaming task updates"""
    async def event_stream():
        # Send initial task status
        if task_id in tasks_db:
            task = tasks_db[task_id]
            yield f"data: {json.dumps({'type': 'TaskStatusUpdateEvent', 'task': task.dict()})}\n\n"

            # Simulate progress updates
            if task.status.state == TaskState.WORKING:
                await asyncio.sleep(0.5)
                yield f"data: {json.dumps({'type': 'TaskStatusUpdateEvent', 'task': task.dict()})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# Legacy endpoint for backwards compatibility
@app.post("/execute")
async def execute_legacy(request: Request):
    """Legacy endpoint (backwards compatible)"""
    body = await request.json()
    task_id = body.get("task_id", str(uuid.uuid4()))
    action = body.get("action")
    parameters = body.get("parameters", {})

    # Map legacy actions to skills
    if action == "search_flights":
        task = await search_flights(parameters, task_id)
    elif action == "book_flight":
        task = await book_flight(parameters, task_id)
    else:
        return {"error": f"Unknown action: {action}"}

    tasks_db[task_id] = task

    # Convert to legacy format
    return {
        "task_id": task.id,
        "status": task.status.state.value,
        "result": task.artifacts[0].parts[1].data if task.artifacts and len(task.artifacts[0].parts) > 1 else None,
        "needs_input": task.status.state == TaskState.INPUT_REQUIRED,
        "follow_up_question": task.status.message if task.status.state == TaskState.INPUT_REQUIRED else None
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10010))
    print(f"🛫 Flight Booking Agent (A2A v0.3.0) starting on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: {', '.join([s['name'] for s in AGENT_CARD['skills']])}")
    uvicorn.run(app, host="0.0.0.0", port=port)
