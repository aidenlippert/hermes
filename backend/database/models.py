"""
Database Models

All SQLAlchemy models for Hermes.

Tables:
- users: User accounts and authentication
- api_keys: API key management
- agents: Agent registry with embeddings
- agent_ratings: User ratings for agents
- tasks: Orchestration requests
- executions: Step-by-step execution logs
- conversations: Multi-turn chat sessions
- messages: Individual messages in conversations
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from .connection import Base

# Try to import pgvector, fallback to JSON if not available
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None


# Enums
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    AGENT_CREATOR = "agent_creator"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


# Models

class User(Base):
    """User accounts"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)

    # Role and subscription
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)

    # Usage tracking
    total_requests = Column(Integer, default=0)
    requests_this_month = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)

    # Metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    agent_ratings = relationship("AgentRating", back_populates="user", cascade="all, delete-orphan")
    created_agents = relationship("Agent", back_populates="creator", foreign_keys="Agent.creator_id")

    def __repr__(self):
        return f"<User {self.email}>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)

    # Permissions
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # requests per minute

    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.name or self.key[:8]}...>"


class Agent(Base):
    """Agent registry with embeddings for semantic search"""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    endpoint = Column(String, nullable=False)

    # Agent metadata
    version = Column(String, default="1.0.0")
    capabilities = Column(JSON, default=list)  # List of capability strings
    category = Column(String, nullable=True, index=True)  # code, content, data, etc.
    tags = Column(JSON, default=list)  # Searchable tags

    # Embeddings for semantic search (1536 dimensions for OpenAI/Gemini)
    # Falls back to JSON array if pgvector not available
    description_embedding = Column(Vector(1536) if HAS_PGVECTOR and Vector else JSON, nullable=True)

    # Performance metrics
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    average_duration = Column(Float, default=0.0)  # seconds
    average_rating = Column(Float, default=0.0)  # 0-5 stars

    # Pricing
    cost_per_request = Column(Float, default=0.0)  # USD
    is_free = Column(Boolean, default=True)

    # Status
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.PENDING_REVIEW, nullable=False)
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # Agent card (raw JSON from A2A discovery)
    agent_card = Column(JSON, nullable=True)

    # Creator
    creator_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_called = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_agents", foreign_keys=[creator_id])
    ratings = relationship("AgentRating", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="agent")

    def __repr__(self):
        return f"<Agent {self.name}>"


class AgentRating(Base):
    """User ratings for agents"""
    __tablename__ = "agent_ratings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    rating = Column(Integer, nullable=False)  # 1-5 stars
    review = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="ratings")
    user = relationship("User", back_populates="agent_ratings")

    def __repr__(self):
        return f"<AgentRating {self.agent_id} - {self.rating}★>"


class Conversation(Base):
    """Multi-turn conversation sessions"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=True)  # Auto-generated from first message

    # Context management
    total_messages = Column(Integer, default=0)
    context_summary = Column(Text, nullable=True)  # Summarized context for long conversations

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="conversation")

    def __repr__(self):
        return f"<Conversation {self.id[:8]}... - {self.total_messages} messages>"


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Optional task reference (if this message triggered orchestration)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    task = relationship("Task", foreign_keys=[task_id])

    def __repr__(self):
        return f"<Message {self.role}: {self.content[:30]}...>"


class Task(Base):
    """Orchestration tasks"""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    # Task details
    query = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # Intent and planning
    parsed_intent = Column(JSON, nullable=True)  # From intent parser
    execution_plan = Column(JSON, nullable=True)  # From planner

    # Results
    final_output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metrics
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)  # seconds
    total_cost = Column(Float, default=0.0)  # USD

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="tasks")
    conversation = relationship("Conversation", back_populates="tasks")
    executions = relationship("Execution", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task {self.id[:8]}... - {self.status.value}>"


class Execution(Base):
    """Individual step executions within a task"""
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # Execution details
    step_number = Column(Integer, nullable=False)
    agent_name = Column(String, nullable=False)
    task_description = Column(Text, nullable=False)

    # Status
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # Results
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metrics
    duration = Column(Float, default=0.0)  # seconds
    cost = Column(Float, default=0.0)  # USD
    retry_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="executions")
    agent = relationship("Agent", back_populates="executions")

    def __repr__(self):
        return f"<Execution {self.step_number} - {self.agent_name}>"
