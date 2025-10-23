"""
Conversation Memory Service

Handles multi-turn conversations with context management.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.database.models import Conversation, Message, Task

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Conversation memory and context management.

    Features:
    - Multi-turn conversations
    - Context window management
    - Conversation summarization
    - Message history
    """

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: str,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            db: Database session
            user_id: User ID
            title: Optional conversation title

        Returns:
            Created Conversation object
        """
        conversation = Conversation(
            user_id=user_id,
            title=title
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        logger.info(f"💬 New conversation created: {conversation.id}")

        return conversation

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        task_id: Optional[str] = None
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            task_id: Optional task ID if this message triggered orchestration

        Returns:
            Created Message object
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            task_id=task_id
        )

        db.add(message)

        # Update conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.total_messages += 1
            conversation.last_message_at = datetime.utcnow()

            # Auto-generate title from first user message
            if not conversation.title and role == "user" and conversation.total_messages == 1:
                # Use first 50 chars as title
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")

        await db.commit()
        await db.refresh(message)

        logger.info(f"📨 Message added to conversation {conversation_id[:8]}...")

        return message

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Get conversation by ID"""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: str,
        limit: int = 50
    ) -> List[Message]:
        """
        Get messages in a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            limit: Max messages to return (most recent first)

        Returns:
            List of messages
        """
        stmt = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit)

        result = await db.execute(stmt)
        messages = result.scalars().all()

        # Reverse to get chronological order
        return list(reversed(messages))

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Get all conversations for a user.

        Args:
            db: Database session
            user_id: User ID
            skip: Number to skip (pagination)
            limit: Max results

        Returns:
            List of conversations
        """
        stmt = select(Conversation).where(
            Conversation.user_id == user_id
        ).order_by(Conversation.last_message_at.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def build_context(
        db: AsyncSession,
        conversation_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Build context for LLM from conversation history.

        Args:
            db: Database session
            conversation_id: Conversation ID
            max_messages: Max messages to include

        Returns:
            List of message dicts in format: [{"role": "user", "content": "..."}]
        """
        messages = await ConversationService.get_conversation_messages(
            db, conversation_id, limit=max_messages
        )

        context = []
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.content
            })

        return context

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            True if deleted successfully
        """
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if not conversation:
            return False

        await db.delete(conversation)
        await db.commit()

        logger.info(f"🗑️ Conversation deleted: {conversation_id}")

        return True

    @staticmethod
    async def get_conversation_summary(
        db: AsyncSession,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            Summary dict with stats
        """
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if not conversation:
            return {}

        # Count tasks in this conversation
        stmt = select(Task).where(Task.conversation_id == conversation_id)
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        return {
            "id": conversation.id,
            "title": conversation.title,
            "total_messages": conversation.total_messages,
            "total_tasks": len(tasks),
            "created_at": conversation.created_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None
        }
