"""
Advanced Collaboration Models

Persistent agent teams, shared knowledge base, and collaborative learning.

Sprint 9: Advanced Collaboration
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .connection import Base


class AgentTeam(Base):
    """Persistent agent teams for recurring collaboration"""
    __tablename__ = "agent_teams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Owner and visibility
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_public = Column(Boolean, default=False)

    # Team composition
    agent_ids = Column(JSON, default=list)  # List of agent IDs
    leader_agent_id = Column(String, nullable=True)  # Optional team leader

    # Team configuration
    collaboration_pattern = Column(String, default="hierarchical")  # hierarchical, sequential, parallel
    communication_protocol = Column(JSON, default=dict)  # How agents communicate

    # Performance metrics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    average_execution_time_ms = Column(Float, default=0.0)
    average_quality_score = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AgentTeam {self.name}>"


class KnowledgeBase(Base):
    """Shared knowledge base for agent learning"""
    __tablename__ = "knowledge_base"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Knowledge identification
    key = Column(String, nullable=False, index=True)  # Unique key for knowledge item
    category = Column(String, nullable=False, index=True)  # fact, pattern, best_practice, error_solution

    # Content
    content = Column(JSON, nullable=False)  # Knowledge content (structured data)
    summary = Column(Text, nullable=True)  # Human-readable summary
    tags = Column(JSON, default=list)  # Tags for discovery

    # Source and validation
    source_agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    source_execution_id = Column(String, nullable=True)  # Execution that generated this knowledge
    validation_count = Column(Integer, default=0)  # How many times validated
    confidence_score = Column(Float, default=0.5)  # Confidence in this knowledge (0.0-1.0)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Success rate when applied

    # Versioning
    version = Column(Integer, default=1)
    superseded_by = Column(String, ForeignKey("knowledge_base.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Index for efficient lookups
    __table_args__ = (
        Index('ix_knowledge_base_key_category', 'key', 'category'),
    )

    def __repr__(self):
        return f"<KnowledgeBase {self.key}>"


class AgentLearning(Base):
    """Agent learning and adaptation tracking"""
    __tablename__ = "agent_learning"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Learning event
    event_type = Column(String, nullable=False)  # success, failure, feedback, adaptation
    execution_id = Column(String, nullable=True)  # Related execution

    # What was learned
    learned_pattern = Column(JSON, nullable=False)  # Pattern that was learned
    context = Column(JSON, default=dict)  # Context in which learning occurred

    # Learning metrics
    confidence = Column(Float, default=0.5)
    validation_score = Column(Float, nullable=True)

    # Applied knowledge
    applied_knowledge_ids = Column(JSON, default=list)  # Knowledge base items used

    # Outcome
    outcome_improved = Column(Boolean, nullable=True)  # Did learning improve performance?
    improvement_metric = Column(Float, nullable=True)  # Quantified improvement

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AgentLearning {self.agent_id} - {self.event_type}>"


class CollaborativeSession(Base):
    """Multi-agent collaborative session tracking"""
    __tablename__ = "collaborative_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Session info
    session_type = Column(String, nullable=False)  # team_execution, knowledge_sharing, peer_learning
    team_id = Column(String, ForeignKey("agent_teams.id", ondelete="SET NULL"), nullable=True)

    # Participants
    participant_agent_ids = Column(JSON, default=list)
    coordinator_agent_id = Column(String, nullable=True)  # Who coordinated this session

    # Execution
    orchestration_plan_id = Column(String, ForeignKey("orchestration_plans.id", ondelete="SET NULL"), nullable=True)
    goal = Column(Text, nullable=False)
    status = Column(String, default="active")  # active, completed, failed

    # Communication
    message_count = Column(Integer, default=0)
    consensus_reached = Column(Boolean, nullable=True)

    # Outcomes
    result = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)
    knowledge_created = Column(JSON, default=list)  # New knowledge base entries created

    # Performance
    total_time_ms = Column(Float, nullable=True)
    agent_contributions = Column(JSON, default=dict)  # Per-agent contribution scores

    # Metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<CollaborativeSession {self.session_type}>"


class AgentRelationship(Base):
    """Tracks relationships and compatibility between agents"""
    __tablename__ = "agent_relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # The two agents
    agent_a_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_b_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationship metrics
    collaboration_count = Column(Integer, default=0)
    successful_collaborations = Column(Integer, default=0)
    compatibility_score = Column(Float, default=0.5)  # How well they work together (0.0-1.0)

    # Communication analysis
    avg_response_time_ms = Column(Float, nullable=True)
    communication_quality = Column(Float, default=0.5)  # Quality of agent-to-agent communication

    # Complementarity
    skill_overlap = Column(Float, default=0.0)  # 0.0 = no overlap, 1.0 = identical skills
    complementarity_score = Column(Float, default=0.0)  # How well skills complement each other

    # Conflict tracking
    conflict_count = Column(Integer, default=0)
    conflict_resolution_rate = Column(Float, default=0.0)

    # Metadata
    first_collaboration = Column(DateTime(timezone=True), nullable=True)
    last_collaboration = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Unique constraint on agent pair
    __table_args__ = (
        Index('ix_agent_relationships_pair', 'agent_a_id', 'agent_b_id', unique=True),
    )

    def __repr__(self):
        return f"<AgentRelationship {self.agent_a_id} <-> {self.agent_b_id}>"
