"""
Orchestration Models

Advanced multi-agent orchestration models for Sprint 2.

Tables:
- orchestration_plans: Multi-agent execution plans
- orchestration_dependencies: Task dependency graphs
- agent_collaborations: Collaboration pattern instances
- collaboration_results: Results from multi-agent collaborations
- orchestration_metrics: Performance tracking for orchestrations
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from .connection import Base


class CollaborationPattern(str, Enum):
    """Multi-agent collaboration patterns"""
    SEQUENTIAL = "sequential"  # Pipeline: A -> B -> C
    PARALLEL = "parallel"      # Parallel: A, B, C (independent)
    VOTE = "vote"             # Consensus voting
    DEBATE = "debate"         # Multi-round debate
    SWARM = "swarm"           # Swarm intelligence
    CONSENSUS = "consensus"    # Distributed consensus
    HIERARCHICAL = "hierarchical"  # Leader-follower


class OrchestrationStatus(str, Enum):
    """Orchestration execution status"""
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DependencyType(str, Enum):
    """Dependency relationship types"""
    REQUIRES = "requires"      # Hard dependency (must complete before)
    ENHANCES = "enhances"      # Soft dependency (improves quality if available)
    CONFLICTS = "conflicts"    # Cannot run concurrently
    VALIDATES = "validates"    # Validation relationship


class OrchestrationPlan(Base):
    """Multi-agent orchestration execution plans"""
    __tablename__ = "orchestration_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)

    # Plan details
    query = Column(Text, nullable=False)
    pattern = Column(SQLEnum(CollaborationPattern), nullable=False)
    status = Column(SQLEnum(OrchestrationStatus), default=OrchestrationStatus.PLANNING, nullable=False)

    # Intent analysis
    parsed_intents = Column(JSON, nullable=True)  # List of decomposed sub-intents
    complexity_score = Column(Float, default=0.0)  # 0.0 - 1.0
    estimated_duration = Column(Float, nullable=True)  # seconds
    estimated_cost = Column(Float, nullable=True)  # USD

    # Execution graph
    execution_graph = Column(JSON, nullable=True)  # DAG representation
    agent_assignments = Column(JSON, nullable=True)  # {step_id: agent_id}

    # Results
    final_result = Column(JSON, nullable=True)
    synthesis_strategy = Column(String, nullable=True)  # merge, vote, debate_winner, etc.

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
    dependencies = relationship("OrchestrationDependency", back_populates="plan", cascade="all, delete-orphan")
    collaborations = relationship("AgentCollaboration", back_populates="plan", cascade="all, delete-orphan")
    metrics = relationship("OrchestrationMetric", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrchestrationPlan {self.id[:8]}... - {self.pattern.value}>"


class OrchestrationDependency(Base):
    """Dependency relationships between orchestration steps"""
    __tablename__ = "orchestration_dependencies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("orchestration_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Dependency relationship
    source_step_id = Column(String, nullable=False, index=True)  # Upstream step
    target_step_id = Column(String, nullable=False, index=True)  # Downstream step
    dependency_type = Column(SQLEnum(DependencyType), default=DependencyType.REQUIRES, nullable=False)

    # Metadata
    weight = Column(Float, default=1.0)  # Importance weight
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plan = relationship("OrchestrationPlan", back_populates="dependencies")

    # Index for efficient graph traversal
    __table_args__ = (
        Index('ix_orch_dep_graph', 'plan_id', 'source_step_id', 'target_step_id'),
    )

    def __repr__(self):
        return f"<Dependency {self.source_step_id} -> {self.target_step_id}>"


class AgentCollaboration(Base):
    """Agent collaboration instances (execution of a pattern)"""
    __tablename__ = "agent_collaborations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("orchestration_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Collaboration details
    pattern = Column(SQLEnum(CollaborationPattern), nullable=False)
    step_id = Column(String, nullable=False, index=True)
    step_description = Column(Text, nullable=False)

    # Participants
    agent_ids = Column(JSON, nullable=False)  # List of agent IDs
    coordinator_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # Status
    status = Column(SQLEnum(OrchestrationStatus), default=OrchestrationStatus.READY, nullable=False)

    # Pattern-specific configuration
    config = Column(JSON, nullable=True)  # e.g., {"rounds": 3} for debate

    # Results
    individual_results = Column(JSON, nullable=True)  # {agent_id: result}
    synthesized_result = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0

    # Metrics
    duration = Column(Float, default=0.0)  # seconds
    cost = Column(Float, default=0.0)  # USD

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    plan = relationship("OrchestrationPlan", back_populates="collaborations")
    results = relationship("CollaborationResult", back_populates="collaboration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Collaboration {self.pattern.value} - {len(self.agent_ids)} agents>"


class CollaborationResult(Base):
    """Individual agent results within a collaboration"""
    __tablename__ = "collaboration_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collaboration_id = Column(String, ForeignKey("agent_collaborations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # Result data
    result_data = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)  # Agent's confidence in result

    # Vote/debate specific
    vote_weight = Column(Float, default=1.0)  # Weighted voting
    debate_round = Column(Integer, nullable=True)  # For multi-round debates

    # Metrics
    duration = Column(Float, default=0.0)  # seconds
    cost = Column(Float, default=0.0)  # USD

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    collaboration = relationship("AgentCollaboration", back_populates="results")

    def __repr__(self):
        return f"<CollaborationResult {self.agent_id}>"


class OrchestrationMetric(Base):
    """Performance metrics for orchestration analysis"""
    __tablename__ = "orchestration_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("orchestration_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    # Performance data
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)

    # Context
    step_id = Column(String, nullable=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plan = relationship("OrchestrationPlan", back_populates="metrics")

    # Index for time-series queries
    __table_args__ = (
        Index('ix_orch_metrics_time', 'plan_id', 'metric_name', 'recorded_at'),
    )

    def __repr__(self):
        return f"<Metric {self.metric_name}: {self.metric_value}{self.metric_unit or ''}>"


class AgentCapabilityCache(Base):
    """Cached agent capabilities for faster orchestration planning"""
    __tablename__ = "agent_capability_cache"

    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)

    # Capability analysis
    capability_vector = Column(JSON, nullable=False)  # Semantic embedding or feature vector
    skill_tags = Column(JSON, default=list)  # Extracted skills
    domain_expertise = Column(JSON, default=dict)  # {domain: confidence_score}

    # Performance profile
    avg_response_time = Column(Float, default=0.0)  # seconds
    success_rate = Column(Float, default=0.0)  # 0.0 - 1.0
    quality_score = Column(Float, default=0.0)  # 0.0 - 1.0
    cost_efficiency = Column(Float, default=0.0)  # results per dollar

    # Collaboration metrics
    works_well_with = Column(JSON, default=list)  # Agent IDs with good synergy
    conflict_agents = Column(JSON, default=list)  # Agent IDs with conflicts

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    update_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<CapabilityCache {self.agent_id}>"


class OrchestrationTemplate(Base):
    """Reusable orchestration patterns and templates"""
    __tablename__ = "orchestration_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Template details
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    pattern = Column(SQLEnum(CollaborationPattern), nullable=False)

    # Template definition
    template_graph = Column(JSON, nullable=False)  # DAG template
    required_capabilities = Column(JSON, default=list)  # Required agent capabilities

    # Performance estimates
    avg_duration = Column(Float, default=0.0)  # seconds
    avg_cost = Column(Float, default=0.0)  # USD
    avg_quality = Column(Float, default=0.0)  # 0.0 - 1.0

    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Access control
    is_public = Column(Boolean, default=True)
    creator_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Template {self.name} - {self.pattern.value}>"
