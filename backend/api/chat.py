"""
Enhanced Chat Endpoint with Intelligent Orchestration

Provides intelligent routing to multi-agent orchestration based on query complexity.

Sprint 2: Orchestration & Intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import User, Conversation, Message
from backend.auth import get_current_user
from backend.services.orchestrator import OrchestratorAgent
from backend.services.collaboration import CollaborationFactory
from backend.database.models_orchestration import CollaborationPattern

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    use_orchestration: Optional[bool] = None  # Force orchestration on/off


class ChatResponse(BaseModel):
    """Chat response with orchestration details"""
    message: str
    conversation_id: str
    orchestration_used: bool
    orchestration_details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class OrchestrationRequest(BaseModel):
    """Direct orchestration request"""
    query: str = Field(..., min_length=1, max_length=10000)
    pattern: Optional[CollaborationPattern] = None
    agent_ids: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatMessage,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a chat message with intelligent orchestration routing.

    Automatically detects if orchestration is needed based on:
    - Query complexity
    - Multiple intents
    - Temporal dependencies
    - Comparison requests
    """
    # Get or create conversation
    if request.conversation_id:
        conversation = await db.get(Conversation, request.conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        await db.flush()

    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)

    # Decide if orchestration is needed
    orchestrator = OrchestratorAgent(db)
    intent_data = await orchestrator.intent_analyzer.analyze(request.message)

    use_orchestration = (
        request.use_orchestration
        if request.use_orchestration is not None
        else intent_data["requires_orchestration"]
    )

    orchestration_details = None
    response_content = ""

    if use_orchestration:
        # Use orchestration for complex queries
        result = await orchestrator.orchestrate(
            user_id=user.id,
            query=request.message,
            context={"conversation_id": conversation.id}
        )

        orchestration_details = result["execution_summary"]
        response_content = str(result["result"].get("final_output", result["result"]))

    else:
        # Simple single-agent response (stub)
        response_content = f"Simple response to: {request.message}"

    # Store assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_content
    )
    db.add(assistant_message)

    # Update conversation
    conversation.total_messages += 2
    conversation.last_message_at = datetime.utcnow()

    if not conversation.title and conversation.total_messages == 2:
        # Auto-generate title from first message
        conversation.title = request.message[:100]

    await db.commit()

    return ChatResponse(
        message=response_content,
        conversation_id=conversation.id,
        orchestration_used=use_orchestration,
        orchestration_details=orchestration_details,
        timestamp=datetime.utcnow()
    )


@router.post("/orchestrate")
async def orchestrate(
    request: OrchestrationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Direct orchestration endpoint for advanced users.

    Allows explicit control over:
    - Collaboration pattern
    - Agent selection
    - Execution configuration
    """
    orchestrator = OrchestratorAgent(db)

    # Override pattern if specified
    if request.pattern:
        orchestrator.intent_analyzer._suggest_pattern = lambda q: request.pattern

    result = await orchestrator.orchestrate(
        user_id=user.id,
        query=request.query,
        context={
            "pattern": request.pattern.value if request.pattern else None,
            "agent_ids": request.agent_ids,
            "config": request.config
        }
    )

    return result


@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """List user's conversations"""
    from sqlalchemy import select, desc

    query = (
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(desc(Conversation.last_message_at))
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    conversations = result.scalars().all()

    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "total_messages": c.total_messages,
                "last_message_at": c.last_message_at,
                "created_at": c.created_at
            }
            for c in conversations
        ],
        "total": len(conversations),
        "limit": limit,
        "offset": offset
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Get messages from a conversation"""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    from sqlalchemy import select

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            }
            for m in messages
        ],
        "total": len(messages),
        "limit": limit,
        "offset": offset
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation"""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    await db.delete(conversation)
    await db.commit()

    return {"status": "deleted", "conversation_id": conversation_id}
