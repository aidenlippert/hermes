"""
Workflow API Endpoints (Sprint 5)

RESTful API for multi-agent workflow orchestration with WebSocket streaming.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from backend.database.connection import get_db
from backend.database.models_workflows import (
    Workflow, WorkflowNode, WorkflowEdge, WorkflowRun, NodeRun
)
from backend.services.workflows import WorkflowCompiler, validate_workflow, compile_workflow
from backend.services.workflow_runner import WorkflowRunner
from backend.services.auth import get_current_user

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class WorkflowNodeCreate(BaseModel):
    node_id: str
    name: str
    node_type: str  # agent_call, tool_call, human_gate, condition, parallel, join
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    config: Optional[dict] = None
    inputs: Optional[dict] = None
    retry_count: int = 3
    timeout_seconds: Optional[int] = None


class WorkflowEdgeCreate(BaseModel):
    from_node_id: str
    to_node_id: str
    condition: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[WorkflowNodeCreate]
    edges: List[WorkflowEdgeCreate]
    timeout_seconds: Optional[int] = None
    max_retries: int = 3
    on_error: str = "fail"  # fail, continue
    tags: Optional[List[str]] = None
    is_public: bool = False


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNodeCreate]] = None
    edges: Optional[List[WorkflowEdgeCreate]] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    on_error: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class WorkflowExecuteRequest(BaseModel):
    inputs: Optional[dict] = Field(default_factory=dict, description="Initial workflow inputs")


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    version: int
    is_public: bool
    is_active: bool
    timeout_seconds: Optional[int]
    max_retries: int
    on_error: str
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    node_count: int = 0
    edge_count: int = 0

    class Config:
        from_attributes = True


class WorkflowDetailResponse(WorkflowResponse):
    nodes: List[dict]
    edges: List[dict]


class WorkflowRunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str  # pending, running, completed, failed, cancelled
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    inputs: dict
    outputs: Optional[dict]
    total_cost: float
    nodes_completed: int = 0
    nodes_total: int = 0

    class Config:
        from_attributes = True


class NodeRunResponse(BaseModel):
    id: str
    workflow_run_id: str
    node_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    inputs: Optional[dict]
    outputs: Optional[dict]
    retry_count: int
    cost: float

    class Config:
        from_attributes = True


# ============================================================================
# WORKFLOW CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=WorkflowDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new multi-agent workflow (DAG).
    
    Validates the workflow structure before saving:
    - No cycles
    - All nodes reachable
    - Valid node types
    - Valid parameter bindings
    """
    # Build workflow dict for validation
    workflow_dict = {
        "id": str(uuid.uuid4()),
        "name": workflow_data.name,
        "description": workflow_data.description,
        "nodes": [node.model_dump() for node in workflow_data.nodes],
        "edges": [edge.model_dump() for edge in workflow_data.edges],
    }
    
    # Validate workflow structure
    is_valid, errors = validate_workflow(workflow_dict)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid workflow structure", "errors": errors}
        )
    
    # Create workflow
    workflow = Workflow(
        id=workflow_dict["id"],
        name=workflow_data.name,
        description=workflow_data.description,
        owner_id=current_user.id,
        timeout_seconds=workflow_data.timeout_seconds,
        max_retries=workflow_data.max_retries,
        on_error=workflow_data.on_error,
        tags=str(workflow_data.tags or []),
        is_public=workflow_data.is_public,
    )
    db.add(workflow)
    
    # Create nodes
    for node_data in workflow_data.nodes:
        node = WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            node_id=node_data.node_id,
            name=node_data.name,
            node_type=node_data.node_type,
            agent_id=node_data.agent_id,
            tool_name=node_data.tool_name,
            config=str(node_data.config or {}),
            inputs=str(node_data.inputs or {}),
            retry_count=node_data.retry_count,
            timeout_seconds=node_data.timeout_seconds,
        )
        db.add(node)
    
    # Create edges
    for edge_data in workflow_data.edges:
        edge = WorkflowEdge(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            from_node_id=edge_data.from_node_id,
            to_node_id=edge_data.to_node_id,
            condition=edge_data.condition,
        )
        db.add(edge)
    
    await db.commit()
    await db.refresh(workflow)
    
    # Load nodes and edges for response
    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == workflow.id)
    )
    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow.id)
    )
    
    nodes = [n.to_dict() for n in nodes_result.scalars().all()]
    edges = [e.to_dict() for e in edges_result.scalars().all()]
    
    return {
        **workflow.to_dict(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_public: Optional[bool] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List workflows owned by the current user or public workflows.
    """
    # Build query
    conditions = [
        or_(
            Workflow.owner_id == current_user.id,
            Workflow.is_public == True
        ),
        Workflow.is_active == True
    ]
    
    if is_public is not None:
        conditions.append(Workflow.is_public == is_public)
    
    # TODO: Add tag filtering when we parse the JSON tags column
    
    result = await db.execute(
        select(Workflow)
        .where(and_(*conditions))
        .offset(skip)
        .limit(limit)
        .order_by(Workflow.created_at.desc())
    )
    workflows = result.scalars().all()
    
    # Add node/edge counts
    response = []
    for workflow in workflows:
        nodes_result = await db.execute(
            select(WorkflowNode).where(WorkflowNode.workflow_id == workflow.id)
        )
        edges_result = await db.execute(
            select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow.id)
        )
        
        response.append({
            **workflow.to_dict(),
            "node_count": len(nodes_result.scalars().all()),
            "edge_count": len(edges_result.scalars().all()),
        })
    
    return response


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific workflow with all nodes and edges.
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to view this workflow")
    
    # Load nodes and edges
    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id)
    )
    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id)
    )
    
    nodes = [n.to_dict() for n in nodes_result.scalars().all()]
    edges = [e.to_dict() for e in edges_result.scalars().all()]
    
    return {
        **workflow.to_dict(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a workflow (soft delete by marking inactive).
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this workflow")
    
    workflow.is_active = False
    await db.commit()
    
    return None


# ============================================================================
# WORKFLOW EXECUTION ENDPOINTS
# ============================================================================

@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED)
async def execute_workflow(
    workflow_id: str,
    execute_request: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Execute a workflow and return the run ID.
    Use WebSocket to stream real-time progress.
    """
    # Load workflow
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to execute this workflow")
    
    # Load nodes and edges
    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id)
    )
    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id)
    )
    
    nodes = nodes_result.scalars().all()
    edges = edges_result.scalars().all()
    
    # Build workflow dict for compiler
    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "nodes": [n.to_dict() for n in nodes],
        "edges": [e.to_dict() for e in edges],
    }
    
    # Compile workflow
    compiled = compile_workflow(workflow_dict)
    if not compiled["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Workflow failed validation", "errors": compiled["errors"]}
        )
    
    # Create workflow run
    run = WorkflowRun(
        id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        user_id=current_user.id,
        status="pending",
        inputs=str(execute_request.inputs),
        total_cost=0.0,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    
    # Execute asynchronously (don't await - it runs in background)
    # TODO: Use background tasks or Celery for production
    runner = WorkflowRunner(workflow_dict, db, run.id)
    
    # Note: This is a simplified version. In production, use:
    # - FastAPI BackgroundTasks
    # - Celery/Redis queue
    # - Or run in separate asyncio task
    
    import asyncio
    asyncio.create_task(runner.execute(execute_request.inputs))
    
    return run.to_dict()


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the status and results of a workflow run.
    """
    result = await db.execute(
        select(WorkflowRun).where(WorkflowRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    
    if run.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this run")
    
    # Count completed nodes
    nodes_result = await db.execute(
        select(NodeRun).where(NodeRun.workflow_run_id == run_id)
    )
    node_runs = nodes_result.scalars().all()
    
    nodes_completed = sum(1 for nr in node_runs if nr.status == "completed")
    nodes_total = len(node_runs)
    
    return {
        **run.to_dict(),
        "nodes_completed": nodes_completed,
        "nodes_total": nodes_total,
    }


@router.post("/runs/{run_id}/cancel", response_model=WorkflowRunResponse)
async def cancel_workflow_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancel a running workflow.
    """
    result = await db.execute(
        select(WorkflowRun).where(WorkflowRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    
    if run.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this run")
    
    if run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending or running workflows"
        )
    
    run.status = "cancelled"
    run.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(run)
    
    return run.to_dict()


@router.get("/runs/{run_id}/nodes", response_model=List[NodeRunResponse])
async def get_workflow_run_nodes(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all node executions for a workflow run.
    """
    # Check permissions on the run
    run_result = await db.execute(
        select(WorkflowRun).where(WorkflowRun.id == run_id)
    )
    run = run_result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    
    if run.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this run")
    
    # Get node runs
    result = await db.execute(
        select(NodeRun)
        .where(NodeRun.workflow_run_id == run_id)
        .order_by(NodeRun.started_at)
    )
    node_runs = result.scalars().all()
    
    return [nr.to_dict() for nr in node_runs]
