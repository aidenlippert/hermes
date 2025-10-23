"""
WebSocket API Endpoints

Real-time streaming endpoints for task progress updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.websocket.manager import manager
from backend.websocket.events import Event, EventType, message_event
from backend.database.connection import get_db
from backend.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_endpoint(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(..., description="JWT access token")
):
    """
    WebSocket endpoint for real-time task updates.

    Usage:
        ws://localhost:8000/api/v1/ws/tasks/{task_id}?token=YOUR_JWT_TOKEN

    Events sent to client:
        - task_created
        - intent_parsing_started
        - intent_parsed
        - planning_started
        - plan_created
        - execution_started
        - step_started
        - agent_thinking
        - step_completed
        - step_failed
        - task_completed
        - task_failed
        - progress_update
    """

    # Validate token (we can't use Depends with WebSocket easily)
    payload = AuthService.decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    # Connect
    await manager.connect(websocket, task_id, user_id)

    # Send welcome message
    welcome_event = Event(
        EventType.CONNECTED,
        task_id,
        {"task_id": task_id, "user_id": user_id},
        f"✅ Connected to task {task_id[:8]}..."
    )
    await websocket.send_json(welcome_event.to_dict())

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Handle client messages (e.g., "ping" for keepalive)
            if data == "ping":
                await websocket.send_text("pong")
            else:
                logger.info(f"📨 Received from client: {data}")

    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected from task {task_id[:8]}...")
        manager.disconnect(websocket, task_id, user_id)


@router.websocket("/ws/user")
async def websocket_user_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token")
):
    """
    WebSocket endpoint for user-wide updates.

    Receives updates for all tasks belonging to the user.

    Usage:
        ws://localhost:8000/api/v1/ws/user?token=YOUR_JWT_TOKEN
    """

    # Validate token
    payload = AuthService.decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    # Connect (use user_id as task_id for user-wide updates)
    await manager.connect(websocket, f"user_{user_id}", user_id)

    # Send welcome
    welcome_event = Event(
        EventType.CONNECTED,
        f"user_{user_id}",
        {"user_id": user_id},
        "✅ Connected to user updates"
    )
    await websocket.send_json(welcome_event.to_dict())

    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
            elif data == "stats":
                # Send connection stats
                stats = manager.get_stats()
                await websocket.send_json({
                    "type": "stats",
                    "data": stats
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 User {user_id[:8]}... disconnected")
        manager.disconnect(websocket, f"user_{user_id}", user_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns number of active connections, tasks, etc.
    """
    stats = manager.get_stats()
    return {
        "websocket_stats": stats
    }
