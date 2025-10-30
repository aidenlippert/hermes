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

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid
import os

from .connection import Base

# Check if pgvector is enabled via environment variable (default: disabled for Railway)
USE_PGVECTOR = os.getenv("USE_PGVECTOR", "false").lower() == "true"

if USE_PGVECTOR:
    try:
        from pgvector.sqlalchemy import Vector
    except ImportError:
        USE_PGVECTOR = False


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


class OrganizationRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"


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
    # Falls back to JSON array if pgvector not enabled
    description_embedding = Column(Vector(1536) if USE_PGVECTOR else JSON, nullable=True)

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

    # Organization ownership (optional)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Creator
    creator_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_called = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_agents", foreign_keys=[creator_id])
    # Set by Organization.agents relationship below once Organization is defined
    ratings = relationship("AgentRating", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="agent")

    def __repr__(self):
        return f"<Agent {self.name}>"


class Organization(Base):
    """Tenant organization for users and agents"""
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    domain = Column(String, unique=True, nullable=True, index=True)  # optional DNS domain for federation

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    agents = relationship("Agent", backref="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"


class OrganizationMember(Base):
    """Membership linking users to organizations with roles"""
    __tablename__ = "organization_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique member per org
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_member'),
    )

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User")

    def __repr__(self):
        return f"<OrgMember {self.organization_id}:{self.user_id} ({self.role.value})>"


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


# ============================================================
# MESH PROTOCOL MODELS
# ============================================================

class ContractStatus(str, Enum):
    """Contract lifecycle states"""
    OPEN = "open"
    BIDDING = "bidding"
    AWARDED = "awarded"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    VALIDATED = "validated"
    SETTLED = "settled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Contract(Base):
    """Mesh protocol contracts"""
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:12])
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Contract details
    intent = Column(String, nullable=False, index=True)  # e.g., "flight_search"
    context = Column(JSON, nullable=False)  # Task parameters
    reward_amount = Column(Float, default=5.0)
    reward_currency = Column(String, default="USD")
    
    # Status
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.OPEN, nullable=False, index=True)
    awarded_to = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    awarded_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    bids = relationship("Bid", back_populates="contract", cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="contract", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Contract {self.id} - {self.intent}>"


class Bid(Base):
    """Agent bids on contracts"""
    __tablename__ = "bids"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    
    # Bid details
    price = Column(Float, nullable=False)
    eta_seconds = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contract = relationship("Contract", back_populates="bids")
    
    def __repr__(self):
        return f"<Bid {self.id} - ${self.price}>"


class Delivery(Base):
    """Contract delivery results"""
    __tablename__ = "deliveries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    # Result data
    data = Column(JSON, nullable=False)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validation_score = Column(Float, nullable=True)  # 0.0 - 1.0
    
    # Timing
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    contract = relationship("Contract", back_populates="delivery")
    
    def __repr__(self):
        return f"<Delivery {self.id} - Contract {self.contract_id}>"


class UserPreference(Base):
    """User agent selection preferences"""
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Weights (must sum to 100)
    price_weight = Column(Float, default=25.0)
    performance_weight = Column(Float, default=25.0)
    speed_weight = Column(Float, default=25.0)
    reputation_weight = Column(Float, default=25.0)
    
    # Filters
    max_price = Column(Float, nullable=True)
    min_confidence = Column(Float, default=0.0)
    max_latency = Column(Float, nullable=True)
    min_reputation = Column(Float, default=0.0)
    free_only = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserPreference {self.user_id}>"


class AgentMetric(Base):
    """Agent performance metrics for trust score calculation"""
    __tablename__ = "agent_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    
    # Performance data
    execution_time = Column(Float, nullable=False)  # seconds
    promised_time = Column(Float, nullable=False)  # seconds (from bid)
    success = Column(Boolean, nullable=False)
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    
    # Metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AgentMetric {self.agent_id} - {'✅' if self.success else '❌'}>"


class AgentTrustScore(Base):
    """Calculated trust scores for agents (updated periodically)"""
    __tablename__ = "agent_trust_scores"

    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    
    # Score components (0.0 - 1.0)
    success_rate = Column(Float, default=0.0)
    latency_score = Column(Float, default=0.0)  # How often meets promised time
    rating_score = Column(Float, default=0.0)   # Average user rating normalized
    uptime_score = Column(Float, default=0.0)   # Time on network
    
    # Overall trust score (weighted combination)
    trust_score = Column(Float, default=0.5, index=True)
    
    # Statistics
    total_contracts = Column(Integer, default=0)
    successful_contracts = Column(Integer, default=0)
    failed_contracts = Column(Integer, default=0)
    average_execution_time = Column(Float, default=0.0)
    total_earnings = Column(Float, default=0.0)
    
    # Metadata
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TrustScore {self.agent_id} - {self.trust_score:.2f}>"


class MessageType(str, Enum):
    """Agent-to-agent message types"""
    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    PROPOSAL = "proposal"
    ACCEPTANCE = "acceptance"
    REJECTION = "rejection"
    TERMINATION = "termination"


class ConversationStatus(str, Enum):
    """Conversation states"""
    ACTIVE = "active"
    AWAITING_RESPONSE = "awaiting_response"
    RESOLVED = "resolved"
    FAILED = "failed"
    TERMINATED = "terminated"


class A2AConversation(Base):
    """Agent-to-agent conversations"""
    __tablename__ = "a2a_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:12])
    
    # Participants (agent IDs)
    initiator_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    
    # Conversation details
    topic = Column(String, nullable=False)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    context_data = Column(JSON, default=dict)  # Changed from 'metadata' to 'context_data'
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    messages = relationship("A2AMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<A2AConversation {self.id} - {self.topic}>"


class A2AMessage(Base):
    """Messages in agent-to-agent conversations"""
    __tablename__ = "a2a_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    conversation_id = Column(String, ForeignKey("a2a_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message details
    from_agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    to_agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(JSON, nullable=False)
    requires_response = Column(Boolean, default=False)
    # Idempotency support (unique per sender)
    idempotency_key = Column(String, nullable=True, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("A2AConversation", back_populates="messages")
    
    def __repr__(self):
        return f"<A2AMessage {self.id} - {self.message_type.value}>"


class A2AMessageReceipt(Base):
    """Delivery receipts per recipient agent for A2A messages"""
    __tablename__ = "a2a_message_receipts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("a2a_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    delivered_at = Column(DateTime(timezone=True), nullable=True)
    acked_at = Column(DateTime(timezone=True), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('message_id', 'agent_id', name='uq_message_receipt_per_agent'),
    )


class A2AOrgAllow(Base):
    """Org-level allowlist for inter-org A2A communication (unidirectional)"""
    __tablename__ = "a2a_org_allows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    target_org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    allowed = Column(Boolean, default=True, nullable=False)

    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('source_org_id', 'target_org_id', name='uq_a2a_org_allow_pair'),
    )


class A2AAgentAllow(Base):
    """Agent-level allowlist for inter-agent A2A communication (unidirectional)"""
    __tablename__ = "a2a_agent_allows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    target_agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    allowed = Column(Boolean, default=True, nullable=False)

    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('source_agent_id', 'target_agent_id', name='uq_a2a_agent_allow_pair'),
    )


# ============================================================
# FEDERATION ADDRESS BOOK & POLICY CACHE
# ============================================================

class FederationContact(Base):
    """Maps a remote federated identity (agent@domain) to local records.

    Used for address book management and auditing of remote participants.
    """
    __tablename__ = "federation_contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    remote_agent_at = Column(String, nullable=False, index=True)  # e.g., "AgentName@example.com"
    remote_agent_name = Column(String, nullable=True)
    remote_domain = Column(String, nullable=True, index=True)

    # Linkages
    remote_org_id = Column(String, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    local_agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    local_org_id = Column(String, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('remote_agent_at', name='uq_fed_contact_remote_identity'),
        Index('ix_fed_contact_domain_name', 'remote_domain', 'remote_agent_name'),
    )


class A2APolicyCache(Base):
    """Cache decisions for A2A ACL evaluations (best-effort, can be stale).

    A row can represent an org-level or agent-level evaluation depending on which ids are set.
    """
    __tablename__ = "a2a_policy_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    target_org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    source_agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True)
    target_agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True)

    allowed = Column(Boolean, default=False, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('source_org_id', 'target_org_id', 'source_agent_id', 'target_agent_id', name='uq_a2a_policy_cache_key'),
    )


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
