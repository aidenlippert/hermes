"""
Comprehensive unit tests for HTN Planning data models.

Following FAANG best practices with >90% coverage target.
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from hermes.planning.models import (
    DependencyType,
    HTNPlan,
    HTNState,
    HTNTask,
    LLMError,
    PlanningError,
    TaskDependency,
    TaskStatus,
    TaskType,
    ValidationError,
)


class TestHTNState:
    """Test cases for HTNState model."""

    def test_create_empty_state(self):
        """Test creating an empty state with defaults."""
        state = HTNState()

        assert state.state_id is not None
        assert isinstance(state.facts, frozenset)
        assert len(state.facts) == 0
        assert isinstance(state.resources, dict)
        assert isinstance(state.agent_capabilities, frozenset)

    def test_create_state_with_facts(self):
        """Test creating state with facts."""
        facts = frozenset(["user_authenticated", "database_connected"])
        state = HTNState(facts=facts)

        assert state.facts == facts
        assert "user_authenticated" in state.facts
        assert "database_connected" in state.facts

    def test_state_immutability(self):
        """Test that state is immutable (frozen)."""
        state = HTNState(facts=frozenset(["fact1"]))

        with pytest.raises(Exception):
            state.facts = frozenset(["fact2"])

    def test_satisfies_preconditions(self):
        """Test precondition checking."""
        state = HTNState(
            facts=frozenset(["logged_in", "has_permission", "data_loaded"])
        )

        assert state.satisfies(["logged_in"])
        assert state.satisfies(["logged_in", "has_permission"])
        assert not state.satisfies(["logged_in", "missing_fact"])
        assert state.satisfies([])

    def test_apply_effects_add_facts(self):
        """Test applying effects that add facts."""
        initial_state = HTNState(facts=frozenset(["fact1"]))
        new_state = initial_state.apply_effects(["fact2", "fact3"])

        assert "fact1" in new_state.facts
        assert "fact2" in new_state.facts
        assert "fact3" in new_state.facts
        assert initial_state.facts == frozenset(["fact1"])

    def test_apply_effects_remove_facts(self):
        """Test applying effects that remove facts."""
        initial_state = HTNState(
            facts=frozenset(["fact1", "fact2", "fact3"])
        )
        new_state = initial_state.apply_effects(["!fact2"])

        assert "fact1" in new_state.facts
        assert "fact2" not in new_state.facts
        assert "fact3" in new_state.facts

    def test_apply_effects_mixed(self):
        """Test applying mixed add/remove effects."""
        initial_state = HTNState(
            facts=frozenset(["fact1", "fact2"])
        )
        new_state = initial_state.apply_effects(["!fact1", "fact3", "fact4"])

        assert "fact1" not in new_state.facts
        assert "fact2" in new_state.facts
        assert "fact3" in new_state.facts
        assert "fact4" in new_state.facts

    def test_state_with_resources(self):
        """Test state with resource tracking."""
        state = HTNState(
            resources={"tokens": 1000.0, "time_budget": 30.0, "api_calls": 10.0}
        )

        assert state.resources["tokens"] == 1000.0
        assert state.resources["time_budget"] == 30.0
        assert state.resources["api_calls"] == 10.0


class TestHTNTask:
    """Test cases for HTNTask model."""

    def test_create_primitive_task(self):
        """Test creating a primitive task."""
        task = HTNTask(
            name="search_flights",
            type=TaskType.PRIMITIVE,
            parameters={"destination": "NYC"},
            preconditions=["user_authenticated"],
            effects=["flights_found"],
        )

        assert task.name == "search_flights"
        assert task.type == TaskType.PRIMITIVE
        assert task.parameters["destination"] == "NYC"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 5
        assert task.subtasks is None

    def test_create_composite_task(self):
        """Test creating a composite task with subtasks."""
        subtask1 = HTNTask(
            name="validate_input",
            type=TaskType.PRIMITIVE,
        )
        subtask2 = HTNTask(
            name="process_data",
            type=TaskType.PRIMITIVE,
        )

        composite = HTNTask(
            name="handle_request",
            type=TaskType.COMPOSITE,
            subtasks=[subtask1, subtask2],
        )

        assert composite.type == TaskType.COMPOSITE
        assert len(composite.subtasks) == 2
        assert composite.subtasks[0].name == "validate_input"
        assert composite.subtasks[1].name == "process_data"

    def test_composite_task_without_subtasks_fails(self):
        """Test that composite tasks require subtasks."""
        with pytest.raises(ValueError, match="must have at least one subtask"):
            HTNTask(
                name="composite_task",
                type=TaskType.COMPOSITE,
                subtasks=[],
            )

    def test_primitive_task_with_subtasks_fails(self):
        """Test that primitive tasks cannot have subtasks."""
        subtask = HTNTask(name="sub", type=TaskType.PRIMITIVE)

        with pytest.raises(ValueError, match="cannot have subtasks"):
            HTNTask(
                name="primitive_task",
                type=TaskType.PRIMITIVE,
                subtasks=[subtask],
            )

    def test_task_immutability(self):
        """Test that tasks are immutable."""
        task = HTNTask(name="test_task", type=TaskType.PRIMITIVE)

        with pytest.raises(Exception):
            task.name = "modified_name"

    def test_is_executable(self):
        """Test executable status checking."""
        task = HTNTask(
            name="book_flight",
            type=TaskType.PRIMITIVE,
            preconditions=["flights_found", "payment_method_valid"],
        )

        state_ready = HTNState(
            facts=frozenset(["flights_found", "payment_method_valid"])
        )
        state_not_ready = HTNState(facts=frozenset(["flights_found"]))

        assert task.is_executable(state_ready)
        assert not task.is_executable(state_not_ready)

    def test_task_validation_name_required(self):
        """Test that task name is required."""
        with pytest.raises(PydanticValidationError):
            HTNTask(name="", type=TaskType.PRIMITIVE)

    def test_task_priority_range(self):
        """Test task priority validation."""
        task_low = HTNTask(
            name="low_priority",
            type=TaskType.PRIMITIVE,
            priority=1,
        )
        task_high = HTNTask(
            name="high_priority",
            type=TaskType.PRIMITIVE,
            priority=10,
        )

        assert task_low.priority == 1
        assert task_high.priority == 10

        with pytest.raises(PydanticValidationError):
            HTNTask(
                name="invalid_priority",
                type=TaskType.PRIMITIVE,
                priority=11,
            )

    def test_task_estimated_duration(self):
        """Test estimated duration validation."""
        task = HTNTask(
            name="long_task",
            type=TaskType.PRIMITIVE,
            estimated_duration=120.5,
        )

        assert task.estimated_duration == 120.5

        with pytest.raises(PydanticValidationError):
            HTNTask(
                name="negative_duration",
                type=TaskType.PRIMITIVE,
                estimated_duration=-10.0,
            )

    def test_task_to_dict(self):
        """Test task serialization to dictionary."""
        task = HTNTask(
            name="test_task",
            type=TaskType.PRIMITIVE,
            parameters={"key": "value"},
            preconditions=["pre1"],
            effects=["eff1"],
            priority=7,
        )

        data = task.to_dict()

        assert data["name"] == "test_task"
        assert data["type"] == "primitive"
        assert data["parameters"]["key"] == "value"
        assert data["preconditions"] == ["pre1"]
        assert data["effects"] == ["eff1"]
        assert data["priority"] == 7

    def test_task_to_dict_with_subtasks(self):
        """Test composite task serialization."""
        subtask = HTNTask(name="subtask", type=TaskType.PRIMITIVE)
        composite = HTNTask(
            name="composite",
            type=TaskType.COMPOSITE,
            subtasks=[subtask],
        )

        data = composite.to_dict()

        assert data["type"] == "composite"
        assert len(data["subtasks"]) == 1
        assert data["subtasks"][0]["name"] == "subtask"


class TestHTNPlan:
    """Test cases for HTNPlan model."""

    def test_create_simple_plan(self):
        """Test creating a simple valid plan."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE)
        task2 = HTNTask(name="task2", type=TaskType.PRIMITIVE)

        plan = HTNPlan(
            user_intent="Test plan",
            tasks=[task1, task2],
        )

        assert plan.plan_id is not None
        assert plan.user_intent == "Test plan"
        assert len(plan.tasks) == 2
        assert plan.version == "1.0.0"

    def test_plan_with_dependencies(self):
        """Test plan with task dependencies."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE, task_id="t1")
        task2 = HTNTask(name="task2", type=TaskType.PRIMITIVE, task_id="t2")

        dep = TaskDependency(
            from_task_id="t1",
            to_task_id="t2",
            type=DependencyType.SEQUENTIAL,
        )

        plan = HTNPlan(
            user_intent="Sequential tasks",
            tasks=[task1, task2],
            dependencies=[dep],
        )

        assert len(plan.dependencies) == 1
        assert plan.dependencies[0].from_task_id == "t1"
        assert plan.dependencies[0].to_task_id == "t2"

    def test_plan_invalid_dependency_reference(self):
        """Test that invalid dependency references are caught."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE, task_id="t1")

        dep = TaskDependency(
            from_task_id="t1",
            to_task_id="nonexistent",
            type=DependencyType.SEQUENTIAL,
        )

        with pytest.raises(ValueError, match="not found"):
            HTNPlan(
                user_intent="Invalid dependency",
                tasks=[task1],
                dependencies=[dep],
            )

    def test_plan_self_referential_dependency(self):
        """Test that self-referential dependencies are rejected."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE, task_id="t1")

        dep = TaskDependency(
            from_task_id="t1",
            to_task_id="t1",
            type=DependencyType.SEQUENTIAL,
        )

        with pytest.raises(ValueError, match="Self-referential"):
            HTNPlan(
                user_intent="Self-ref dependency",
                tasks=[task1],
                dependencies=[dep],
            )

    def test_plan_cycle_detection(self):
        """Test that dependency cycles are detected."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE, task_id="t1")
        task2 = HTNTask(name="task2", type=TaskType.PRIMITIVE, task_id="t2")
        task3 = HTNTask(name="task3", type=TaskType.PRIMITIVE, task_id="t3")

        deps = [
            TaskDependency(from_task_id="t1", to_task_id="t2", type=DependencyType.SEQUENTIAL),
            TaskDependency(from_task_id="t2", to_task_id="t3", type=DependencyType.SEQUENTIAL),
            TaskDependency(from_task_id="t3", to_task_id="t1", type=DependencyType.SEQUENTIAL),
        ]

        with pytest.raises(ValueError, match="cycle"):
            HTNPlan(
                user_intent="Cyclic plan",
                tasks=[task1, task2, task3],
                dependencies=deps,
            )

    def test_get_task_by_id(self):
        """Test retrieving tasks by ID."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE, task_id="t1")
        task2 = HTNTask(name="task2", type=TaskType.PRIMITIVE, task_id="t2")

        plan = HTNPlan(
            user_intent="Test",
            tasks=[task1, task2],
        )

        found = plan.get_task_by_id("t1")
        assert found is not None
        assert found.name == "task1"

        not_found = plan.get_task_by_id("t999")
        assert not_found is None

    def test_get_executable_tasks(self):
        """Test finding executable tasks."""
        task1 = HTNTask(
            name="task1",
            type=TaskType.PRIMITIVE,
            preconditions=["fact1"],
            status=TaskStatus.PENDING,
        )
        task2 = HTNTask(
            name="task2",
            type=TaskType.PRIMITIVE,
            preconditions=["fact2"],
            status=TaskStatus.PENDING,
        )
        task3 = HTNTask(
            name="task3",
            type=TaskType.PRIMITIVE,
            preconditions=["fact1"],
            status=TaskStatus.COMPLETED,
        )

        plan = HTNPlan(
            user_intent="Test executability",
            tasks=[task1, task2, task3],
        )

        state = HTNState(facts=frozenset(["fact1"]))
        executable = plan.get_executable_tasks(state)

        assert len(executable) == 1
        assert executable[0].name == "task1"

    def test_plan_validate_success(self):
        """Test successful plan validation."""
        task1 = HTNTask(name="task1", type=TaskType.PRIMITIVE)
        plan = HTNPlan(user_intent="Valid plan", tasks=[task1])

        assert plan.validate() is True

    def test_plan_validate_no_tasks(self):
        """Test validation fails with no tasks."""
        with pytest.raises(PydanticValidationError):
            HTNPlan(user_intent="Empty plan", tasks=[])

    def test_plan_validate_no_primitives(self):
        """Test validation fails with no primitive tasks."""
        composite = HTNTask(
            name="composite",
            type=TaskType.COMPOSITE,
            subtasks=[
                HTNTask(
                    name="inner_composite",
                    type=TaskType.COMPOSITE,
                    subtasks=[
                        HTNTask(name="deep", type=TaskType.PRIMITIVE)
                    ]
                )
            ],
        )

        plan = HTNPlan(user_intent="No primitives at root", tasks=[composite])

        with pytest.raises(ValidationError) as exc_info:
            plan.validate()

        assert "no primitive" in exc_info.value.violations[0].lower()

    def test_plan_serialization_roundtrip(self):
        """Test plan can be serialized and deserialized."""
        task1 = HTNTask(
            name="task1",
            type=TaskType.PRIMITIVE,
            parameters={"key": "value"},
            preconditions=["pre1"],
            effects=["eff1"],
        )

        initial_state = HTNState(
            facts=frozenset(["initial_fact"]),
            resources={"tokens": 100.0},
        )

        goal_state = HTNState(facts=frozenset(["goal_fact"]))

        original_plan = HTNPlan(
            user_intent="Test serialization",
            tasks=[task1],
            initial_state=initial_state,
            goal_state=goal_state,
            metadata={"complexity": 0.5},
        )

        data = original_plan.to_dict()
        json_str = json.dumps(data)
        loaded_data = json.loads(json_str)
        restored_plan = HTNPlan.from_dict(loaded_data)

        assert restored_plan.plan_id == original_plan.plan_id
        assert restored_plan.user_intent == original_plan.user_intent
        assert len(restored_plan.tasks) == 1
        assert restored_plan.tasks[0].name == "task1"
        assert restored_plan.metadata["complexity"] == 0.5
        assert "initial_fact" in restored_plan.initial_state.facts
        assert "goal_fact" in restored_plan.goal_state.facts


class TestExceptions:
    """Test cases for custom exceptions."""

    def test_planning_error(self):
        """Test base PlanningError exception."""
        error = PlanningError(
            "Something went wrong",
            context={"plan_id": "123"}
        )

        assert error.message == "Something went wrong"
        assert error.context["plan_id"] == "123"
        assert isinstance(error.timestamp, datetime)

    def test_validation_error(self):
        """Test ValidationError with violations."""
        error = ValidationError(
            "Validation failed",
            violations=["Missing task", "Invalid dependency"],
            context={"plan_id": "456"}
        )

        assert error.message == "Validation failed"
        assert len(error.violations) == 2
        assert "Missing task" in error.violations

    def test_llm_error(self):
        """Test LLMError with retry information."""
        error = LLMError(
            "Gemini API timeout",
            llm_response="partial response",
            retry_count=3,
        )

        assert error.message == "Gemini API timeout"
        assert error.llm_response == "partial response"
        assert error.retry_count == 3


class TestTaskDependency:
    """Test cases for TaskDependency model."""

    def test_create_sequential_dependency(self):
        """Test creating sequential dependency."""
        dep = TaskDependency(
            from_task_id="t1",
            to_task_id="t2",
            type=DependencyType.SEQUENTIAL,
        )

        assert dep.from_task_id == "t1"
        assert dep.to_task_id == "t2"
        assert dep.type == DependencyType.SEQUENTIAL
        assert dep.condition is None

    def test_create_conditional_dependency(self):
        """Test creating conditional dependency."""
        dep = TaskDependency(
            from_task_id="t1",
            to_task_id="t2",
            type=DependencyType.CONDITIONAL,
            condition="success",
        )

        assert dep.type == DependencyType.CONDITIONAL
        assert dep.condition == "success"

    def test_dependency_immutability(self):
        """Test that dependencies are immutable."""
        dep = TaskDependency(
            from_task_id="t1",
            to_task_id="t2",
            type=DependencyType.SEQUENTIAL,
        )

        with pytest.raises(Exception):
            dep.from_task_id = "t3"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=hermes.planning.models", "--cov-report=term-missing"])
