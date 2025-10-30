"""
SQLAlchemy models for Multi-Agent Workflows (Sprint 5)

These models enable DAG-based orchestration of multi-agent workflows
with support for parallel execution, retries, human gates, and conditions.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base
import json


class Workflow(Base):
    """
    A multi-agent workflow definition (DAG template).
    Can be versioned, shared, and templated.
    """
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    timeout_seconds = Column(Integer, nullable=True)
    max_retries = Column(Integer, default=3)
    on_error = Column(String(50), default="fail")  # fail, continue, rollback
    workflow_metadata = Column(Text, nullable=True)  # JSON - renamed to avoid SQLAlchemy conflict
    tags = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")
    permissions = relationship("WorkflowPermission", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflows_owner_id", "owner_id"),
        Index("ix_workflows_organization_id", "organization_id"),
        Index("ix_workflows_is_public", "is_public"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "organization_id": self.organization_id,
            "version": self.version,
            "is_template": self.is_template,
            "is_public": self.is_public,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "on_error": self.on_error,
            "metadata": json.loads(self.workflow_metadata) if self.workflow_metadata else {},
            "tags": json.loads(self.tags) if self.tags else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }


class WorkflowNode(Base):
    """
    A node in the workflow DAG.
    Types: agent_call, tool_call, human_gate, condition, parallel, join
    """
    __tablename__ = "workflow_nodes"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String(100), nullable=False)  # Unique within workflow
    name = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False)
    agent_id = Column(String, nullable=True)  # For agent_call nodes
    action = Column(String(255), nullable=True)  # Capability or tool
    inputs = Column(Text, nullable=True)  # JSON - input bindings
    outputs = Column(Text, nullable=True)  # JSON - output variable names
    config = Column(Text, nullable=True)  # JSON - node-specific config
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    timeout_seconds = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=5)
    fallback_node_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")

    __table_args__ = (
        UniqueConstraint("workflow_id", "node_id", name="uq_workflow_node"),
        Index("ix_workflow_nodes_workflow_id", "workflow_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type,
            "agent_id": self.agent_id,
            "action": self.action,
            "inputs": json.loads(self.inputs) if self.inputs else {},
            "outputs": json.loads(self.outputs) if self.outputs else {},
            "config": json.loads(self.config) if self.config else {},
            "position": {"x": self.position_x, "y": self.position_y},
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "fallback_node_id": self.fallback_node_id,
        }


class WorkflowEdge(Base):
    """
    An edge (connection) in the workflow DAG.
    """
    __tablename__ = "workflow_edges"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    from_node_id = Column(String(100), nullable=False)
    to_node_id = Column(String(100), nullable=False)
    condition = Column(Text, nullable=True)  # JSON - optional condition
    label = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")

    __table_args__ = (
        UniqueConstraint("workflow_id", "from_node_id", "to_node_id", name="uq_workflow_edge"),
        Index("ix_workflow_edges_workflow_id", "workflow_id"),
        Index("ix_workflow_edges_from_node", "workflow_id", "from_node_id"),
        Index("ix_workflow_edges_to_node", "workflow_id", "to_node_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "condition": json.loads(self.condition) if self.condition else None,
            "label": self.label,
            "is_default": self.is_default,
        }


class WorkflowRun(Base):
    """
    An execution instance of a workflow.
    Tracks overall run status and results.
    """
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    triggered_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String, nullable=True)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, cancelled, paused
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    input_data = Column(Text, nullable=True)  # JSON
    output_data = Column(Text, nullable=True)  # JSON
    context = Column(Text, nullable=True)  # JSON - workflow variables
    total_cost = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="runs")
    node_runs = relationship("NodeRun", back_populates="workflow_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflow_runs_workflow_id", "workflow_id"),
        Index("ix_workflow_runs_status", "status"),
        Index("ix_workflow_runs_triggered_by", "triggered_by"),
        Index("ix_workflow_runs_created_at", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "triggered_by": self.triggered_by,
            "organization_id": self.organization_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "input_data": json.loads(self.input_data) if self.input_data else {},
            "output_data": json.loads(self.output_data) if self.output_data else {},
            "context": json.loads(self.context) if self.context else {},
            "total_cost": self.total_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NodeRun(Base):
    """
    Execution of a single node within a workflow run.
    """
    __tablename__ = "node_runs"

    id = Column(String, primary_key=True)
    workflow_run_id = Column(String, ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, skipped, cancelled
    attempt_number = Column(Integer, default=1)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    input_data = Column(Text, nullable=True)  # JSON
    output_data = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    agent_response = Column(Text, nullable=True)
    cost = Column(Float, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="node_runs")

    __table_args__ = (
        Index("ix_node_runs_workflow_run_id", "workflow_run_id"),
        Index("ix_node_runs_status", "status"),
        Index("ix_node_runs_node_id", "workflow_run_id", "node_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_run_id": self.workflow_run_id,
            "node_id": self.node_id,
            "status": self.status,
            "attempt_number": self.attempt_number,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_data": json.loads(self.input_data) if self.input_data else {},
            "output_data": json.loads(self.output_data) if self.output_data else {},
            "error_message": self.error_message,
            "agent_response": json.loads(self.agent_response) if self.agent_response else None,
            "cost": self.cost,
            "duration_ms": self.duration_ms,
        }


class WorkflowTemplate(Base):
    """
    Reusable workflow patterns for common use cases.
    """
    __tablename__ = "workflow_templates"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    template_data = Column(Text, nullable=False)  # JSON - full workflow definition
    icon = Column(String(255), nullable=True)
    example_input = Column(Text, nullable=True)  # JSON
    example_output = Column(Text, nullable=True)  # JSON
    required_capabilities = Column(Text, nullable=True)  # JSON array
    estimated_cost = Column(Float, nullable=True)
    estimated_duration_seconds = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    created_by = Column(String, nullable=True)
    is_official = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_workflow_templates_category", "category"),
        Index("ix_workflow_templates_is_official", "is_official"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "template_data": json.loads(self.template_data) if self.template_data else {},
            "icon": self.icon,
            "example_input": json.loads(self.example_input) if self.example_input else {},
            "example_output": json.loads(self.example_output) if self.example_output else {},
            "required_capabilities": json.loads(self.required_capabilities) if self.required_capabilities else [],
            "estimated_cost": self.estimated_cost,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "created_by": self.created_by,
            "is_official": self.is_official,
        }


class WorkflowPermission(Base):
    """
    Access control for workflows (sharing and permissions).
    """
    __tablename__ = "workflow_permissions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    organization_id = Column(String, nullable=True)
    permission = Column(String(50), nullable=False)  # view, run, edit, delete
    granted_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="permissions")

    __table_args__ = (
        Index("ix_workflow_permissions_workflow_id", "workflow_id"),
        Index("ix_workflow_permissions_user_id", "user_id"),
        Index("ix_workflow_permissions_organization_id", "organization_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "permission": self.permission,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
