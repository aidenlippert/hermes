"""
Core data models for Astraeus HTN Planning System.

Production-grade Pydantic v2 models with immutability, validation, and serialization.
Follows FAANG best practices for type safety and data integrity.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(str, Enum):
    """Task classification for HTN decomposition."""

    PRIMITIVE = "primitive"
    COMPOSITE = "composite"


class TaskStatus(str, Enum):
    """Execution status tracking for tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class PlanningError(Exception):
    """Base exception for all planning-related errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)


class ValidationError(PlanningError):
    """Raised when plan validation fails."""

    def __init__(
        self,
        message: str,
        violations: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.violations = violations or []


class LLMError(PlanningError):
    """Raised when LLM integration fails."""

    def __init__(
        self,
        message: str,
        llm_response: Optional[str] = None,
        retry_count: int = 0,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.llm_response = llm_response
        self.retry_count = retry_count


class HTNState(BaseModel):
    """
    Immutable world state representation for HTN planning.

    Represents the current state of the system including facts, resources,
    and agent capabilities. Used for precondition checking and effect application.
    """

    model_config = {"frozen": True}

    state_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique state identifier"
    )
    facts: frozenset[str] = Field(
        default_factory=frozenset,
        description="Set of true facts in current state"
    )
    resources: Dict[str, float] = Field(
        default_factory=dict,
        description="Available resources (e.g., budget, time, tokens)"
    )
    agent_capabilities: frozenset[str] = Field(
        default_factory=frozenset,
        description="Available agent capabilities"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional state metadata"
    )

    def satisfies(self, preconditions: List[str]) -> bool:
        """Check if state satisfies given preconditions."""
        return all(pre in self.facts for pre in preconditions)

    def apply_effects(self, effects: List[str]) -> HTNState:
        """
        Apply effects to create new state (immutable update).

        Args:
            effects: List of effects to apply (add/remove facts)

        Returns:
            New HTNState with effects applied
        """
        new_facts = set(self.facts)

        for effect in effects:
            if effect.startswith("!"):
                new_facts.discard(effect[1:])
            else:
                new_facts.add(effect)

        return HTNState(
            state_id=str(uuid.uuid4()),
            facts=frozenset(new_facts),
            resources=self.resources.copy(),
            agent_capabilities=self.agent_capabilities,
            metadata=self.metadata.copy(),
        )


class HTNTask(BaseModel):
    """
    Hierarchical task representation supporting both primitive and composite tasks.

    Primitive tasks map directly to executable operators.
    Composite tasks decompose into subtasks via methods.
    """

    model_config = {"frozen": True}

    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique task identifier"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable task name"
    )
    type: TaskType = Field(
        ...,
        description="Task classification (primitive or composite)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task-specific parameters"
    )
    preconditions: List[str] = Field(
        default_factory=list,
        description="Required state preconditions"
    )
    effects: List[str] = Field(
        default_factory=list,
        description="State changes after task completion"
    )
    subtasks: Optional[List[HTNTask]] = Field(
        default=None,
        description="Decomposed subtasks (for composite tasks)"
    )
    agent_id: Optional[str] = Field(
        default=None,
        description="Assigned agent identifier"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current execution status"
    )
    estimated_duration: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Estimated execution time in seconds"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Task priority (1=lowest, 10=highest)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional task metadata"
    )

    @field_validator("subtasks")
    @classmethod
    def validate_subtasks(cls, v: Optional[List[HTNTask]], info) -> Optional[List[HTNTask]]:
        """Ensure composite tasks have subtasks, primitives don't."""
        task_type = info.data.get("type")

        if task_type == TaskType.COMPOSITE and (not v or len(v) == 0):
            raise ValueError("Composite tasks must have at least one subtask")

        if task_type == TaskType.PRIMITIVE and v is not None and len(v) > 0:
            raise ValueError("Primitive tasks cannot have subtasks")

        return v

    def is_executable(self, state: HTNState) -> bool:
        """Check if task can be executed in given state."""
        return state.satisfies(self.preconditions)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "task_id": self.task_id,
            "name": self.name,
            "type": self.type.value,
            "parameters": self.parameters,
            "preconditions": self.preconditions,
            "effects": self.effects,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "estimated_duration": self.estimated_duration,
            "priority": self.priority,
            "metadata": self.metadata,
        }

        if self.subtasks:
            data["subtasks"] = [st.to_dict() for st in self.subtasks]

        return data


class DependencyType(str, Enum):
    """Dependency relationship types between tasks."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    RESOURCE = "resource"


class TaskDependency(BaseModel):
    """Represents a dependency relationship between tasks."""

    model_config = {"frozen": True}

    from_task_id: str = Field(..., description="Source task ID")
    to_task_id: str = Field(..., description="Target task ID")
    type: DependencyType = Field(..., description="Dependency type")
    condition: Optional[str] = Field(
        default=None,
        description="Condition for conditional dependencies"
    )


class HTNPlan(BaseModel):
    """
    Complete HTN plan with tasks, dependencies, and execution metadata.

    Supports validation, serialization, and execution graph generation.
    """

    model_config = {"frozen": True}

    plan_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique plan identifier"
    )
    version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Plan version (semantic versioning)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Plan creation timestamp"
    )
    user_intent: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Original user intent/query"
    )
    tasks: List[HTNTask] = Field(
        ...,
        min_length=1,
        description="All tasks in the plan"
    )
    dependencies: List[TaskDependency] = Field(
        default_factory=list,
        description="Task dependency relationships"
    )
    initial_state: Optional[HTNState] = Field(
        default=None,
        description="Initial world state"
    )
    goal_state: Optional[HTNState] = Field(
        default=None,
        description="Desired goal state"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Plan metadata (complexity, confidence, etc.)"
    )

    @model_validator(mode="after")
    def validate_plan_consistency(self) -> HTNPlan:
        """Validate plan consistency (no cycles, valid references)."""
        task_ids = {task.task_id for task in self.tasks}

        for dep in self.dependencies:
            if dep.from_task_id not in task_ids:
                raise ValueError(f"Invalid dependency: task {dep.from_task_id} not found")
            if dep.to_task_id not in task_ids:
                raise ValueError(f"Invalid dependency: task {dep.to_task_id} not found")
            if dep.from_task_id == dep.to_task_id:
                raise ValueError(f"Self-referential dependency: {dep.from_task_id}")

        if self._has_cycles():
            raise ValueError("Plan contains dependency cycles")

        return self

    def _has_cycles(self) -> bool:
        """Check for cycles in dependency graph using DFS."""
        graph: Dict[str, Set[str]] = {}
        for dep in self.dependencies:
            if dep.type in (DependencyType.SEQUENTIAL, DependencyType.CONDITIONAL):
                graph.setdefault(dep.from_task_id, set()).add(dep.to_task_id)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle_util(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task in self.tasks:
            if task.task_id not in visited:
                if has_cycle_util(task.task_id):
                    return True

        return False

    def get_task_by_id(self, task_id: str) -> Optional[HTNTask]:
        """Retrieve task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_executable_tasks(self, state: HTNState) -> List[HTNTask]:
        """Get all tasks executable in current state."""
        return [
            task for task in self.tasks
            if task.status == TaskStatus.PENDING and task.is_executable(state)
        ]

    def validate(self) -> bool:
        """
        Comprehensive plan validation.

        Returns:
            True if plan is valid

        Raises:
            ValidationError: If plan has validation issues
        """
        violations = []

        if not self.tasks:
            violations.append("Plan has no tasks")

        primitive_count = sum(1 for t in self.tasks if t.type == TaskType.PRIMITIVE)
        if primitive_count == 0:
            violations.append("Plan has no primitive (executable) tasks")

        for task in self.tasks:
            if task.type == TaskType.COMPOSITE and not task.subtasks:
                violations.append(f"Composite task {task.task_id} has no subtasks")

        if violations:
            raise ValidationError(
                "Plan validation failed",
                violations=violations,
                context={"plan_id": self.plan_id}
            )

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for JSON serialization."""
        return {
            "plan_id": self.plan_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "user_intent": self.user_intent,
            "tasks": [task.to_dict() for task in self.tasks],
            "dependencies": [
                {
                    "from_task_id": dep.from_task_id,
                    "to_task_id": dep.to_task_id,
                    "type": dep.type.value,
                    "condition": dep.condition,
                }
                for dep in self.dependencies
            ],
            "initial_state": {
                "state_id": self.initial_state.state_id,
                "facts": list(self.initial_state.facts),
                "resources": self.initial_state.resources,
                "agent_capabilities": list(self.initial_state.agent_capabilities),
                "metadata": self.initial_state.metadata,
            } if self.initial_state else None,
            "goal_state": {
                "state_id": self.goal_state.state_id,
                "facts": list(self.goal_state.facts),
                "resources": self.goal_state.resources,
                "agent_capabilities": list(self.goal_state.agent_capabilities),
                "metadata": self.goal_state.metadata,
            } if self.goal_state else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HTNPlan:
        """Create plan from dictionary (deserialization)."""
        def parse_task(task_data: Dict[str, Any]) -> HTNTask:
            subtasks = None
            if "subtasks" in task_data and task_data["subtasks"]:
                subtasks = [parse_task(st) for st in task_data["subtasks"]]

            return HTNTask(
                task_id=task_data["task_id"],
                name=task_data["name"],
                type=TaskType(task_data["type"]),
                parameters=task_data.get("parameters", {}),
                preconditions=task_data.get("preconditions", []),
                effects=task_data.get("effects", []),
                subtasks=subtasks,
                agent_id=task_data.get("agent_id"),
                status=TaskStatus(task_data.get("status", "pending")),
                estimated_duration=task_data.get("estimated_duration"),
                priority=task_data.get("priority", 5),
                metadata=task_data.get("metadata", {}),
            )

        tasks = [parse_task(t) for t in data["tasks"]]

        dependencies = [
            TaskDependency(
                from_task_id=d["from_task_id"],
                to_task_id=d["to_task_id"],
                type=DependencyType(d["type"]),
                condition=d.get("condition"),
            )
            for d in data.get("dependencies", [])
        ]

        initial_state = None
        if data.get("initial_state"):
            s = data["initial_state"]
            initial_state = HTNState(
                state_id=s["state_id"],
                facts=frozenset(s["facts"]),
                resources=s["resources"],
                agent_capabilities=frozenset(s["agent_capabilities"]),
                metadata=s["metadata"],
            )

        goal_state = None
        if data.get("goal_state"):
            s = data["goal_state"]
            goal_state = HTNState(
                state_id=s["state_id"],
                facts=frozenset(s["facts"]),
                resources=s["resources"],
                agent_capabilities=frozenset(s["agent_capabilities"]),
                metadata=s["metadata"],
            )

        return cls(
            plan_id=data["plan_id"],
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            user_intent=data["user_intent"],
            tasks=tasks,
            dependencies=dependencies,
            initial_state=initial_state,
            goal_state=goal_state,
            metadata=data.get("metadata", {}),
        )
