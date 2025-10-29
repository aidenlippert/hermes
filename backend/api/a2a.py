"""
Agent-to-Agent (A2A) Collaboration API

Endpoints for agent presence (WebSocket), conversations, and messages.
Auth:
- Agent WebSocket and agent-sent messages are authenticated via API key (?api_key=...)
- User-initiated conversations/messages use JWT like the rest of the API

Minimal viable substrate to enable agent discovery and infinite communication.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
import logging

from backend.database.connection import get_db
from backend.database.models import Agent, A2AConversation, A2AMessage, MessageType, ConversationStatus, User
from backend.services.auth import AuthService, get_current_user
from backend.websocket.manager import manager

router = APIRouter(prefix="/api/v1/a2a", tags=["a2a"])
logger = logging.getLogger(__name__)


@router.post("/conversations")
async def create_conversation(
    initiator_id: str,
    target_id: str,
    topic: str,
    context: Optional[Dict[str, Any]] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an agent-to-agent conversation (user mediated)."""

    # Validate agents exist
    for aid in (initiator_id, target_id):
        res = await db.execute(select(Agent).where(Agent.id == aid))
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Agent not found: {aid}")

    conv = A2AConversation(
        initiator_id=initiator_id,
        target_id=target_id,
        topic=topic,
        status=ConversationStatus.ACTIVE,
        context_data=context or {},
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return {"id": conv.id, "status": conv.status.value}


@router.post("/messages")
async def send_message(
    conversation_id: str,
    from_agent_id: str,
    to_agent_id: str,
    message_type: MessageType,
    content: Dict[str, Any],
    requires_response: bool = False,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Query(None, description="Bearer token for users"),
    api_key: Optional[str] = Query(None, description="API key for agents"),
):
    """Send a message between agents within a conversation.

    AuthN:
    - Agents: provide ?api_key=... (validated and must own the from_agent_id)
    - Users: provide Authorization: Bearer <JWT>
    """

    # Validate conversation
    res = await db.execute(select(A2AConversation).where(A2AConversation.id == conversation_id))
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Validate agents
    for aid in (from_agent_id, to_agent_id):
        r = await db.execute(select(Agent).where(Agent.id == aid))
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Agent not found: {aid}")

    # Authenticate: either API key (agent) or JWT (user)
    authed_user: Optional[User] = None
    if api_key:
        authed_user = await AuthService.validate_api_key(db, api_key)
        if not authed_user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        # Optional: enforce ownership - user must be creator of from_agent_id if set
        res = await db.execute(select(Agent).where(Agent.id == from_agent_id))
        agent = res.scalar_one_or_none()
        if agent and agent.creator_id and agent.creator_id != authed_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to send from this agent")
    else:
        # Try JWT from Authorization header value ("Bearer ...")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            payload = AuthService.decode_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            raise HTTPException(status_code=401, detail="Missing auth (api_key or Bearer token)")

    # Store message
    msg = A2AMessage(
        conversation_id=conversation_id,
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        message_type=message_type,
        content=content,
        requires_response=requires_response,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Push over agent channel if recipient online
    await manager.send_to_agent(to_agent_id, {
        "type": "a2a_message",
        "conversation_id": conversation_id,
        "from_agent_id": from_agent_id,
        "message_type": message_type.value,
        "content": content,
        "requires_response": requires_response,
    })

    return {"id": msg.id, "status": "queued"}


@router.websocket("/ws/agents/{agent_id}")
async def agent_ws(websocket: WebSocket, agent_id: str, api_key: str = Query("")):
    """WebSocket presence channel for agents.

    Connect with: ws://.../api/v1/a2a/ws/agents/{agent_id}?api_key=YOUR_KEY
    """
    # Basic API key validation (associate to a user)
    from backend.database.connection import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        user = await AuthService.validate_api_key(db, api_key)
        if not user:
            await websocket.close(code=1008, reason="Invalid API key")
            return
        # Optional: verify user owns this agent if it has a creator
        res = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = res.scalar_one_or_none()
        if agent and agent.creator_id and agent.creator_id != user.id:
            await websocket.close(code=1008, reason="Not authorized for this agent")
            return

    await manager.connect_agent(websocket, agent_id)

    # Send welcome
    await websocket.send_json({
        "type": "connected",
        "agent_id": agent_id,
        "message": "✅ Agent connected"
    })

    try:
        while True:
            data = await websocket.receive_json()
            # Expect messages like {"type":"heartbeat"} or {"type":"ack", "message_id": "..."}
            if isinstance(data, dict) and data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
            else:
                logger.info(f"📨 Agent {agent_id} sent: {data}")
    except WebSocketDisconnect:
        logger.info(f"🤖 Agent disconnected: {agent_id}")
        manager.disconnect_agent(websocket, agent_id)
