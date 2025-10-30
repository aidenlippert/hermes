"""
WebSocket Event Types

Defines all event types that can be streamed to clients.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class EventType(str, Enum):
    """All possible WebSocket event types"""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"

    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Intent parsing
    INTENT_PARSING_STARTED = "intent_parsing_started"
    INTENT_PARSING_COMPLETED = "intent_parsing_completed"
    INTENT_PARSED = "intent_parsed"

    # Planning
    PLANNING_STARTED = "planning_started"
    PLANNING_COMPLETED = "planning_completed"
    PLAN_CREATED = "plan_created"

    # Agent discovery
    AGENT_SEARCH_STARTED = "agent_search_started"
    AGENT_SEARCH_COMPLETED = "agent_search_completed"
    AGENTS_FOUND = "agents_found"

    # Execution
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"

    # Step events
    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"

    # Agent events
    AGENT_CALLED = "agent_called"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONDED = "agent_responded"
    AGENT_FAILED = "agent_failed"

    # Progress
    PROGRESS_UPDATE = "progress_update"
    STATUS_UPDATE = "status_update"

    # Messages
    MESSAGE = "message"
    ERROR = "error"
    WARNING = "warning"

    # Workflow events (Sprint 5)
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    WORKFLOW_CANCELLING = "workflow_cancelling"
    LEVEL_STARTED = "level_started"
    LEVEL_COMPLETED = "level_completed"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_RETRY = "node_retry"
    AGENT_CALLING = "agent_calling"
    HUMAN_GATE_WAITING = "human_gate_waiting"


class Event:
    """Base event class"""

    def __init__(
        self,
        event_type: EventType,
        task_id: str,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ):
        self.event_type = event_type
        self.task_id = task_id
        self.data = data or {}
        self.message = message
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        return {
            "type": self.event_type.value,
            "task_id": self.task_id,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp
        }


# ============================================================================
# EVENT BUILDERS - Helper functions to create common events
# ============================================================================

def task_created_event(task_id: str, query: str) -> Event:
    """Task was created"""
    return Event(
        EventType.TASK_CREATED,
        task_id,
        {"query": query},
        f"Task created: {query[:50]}..."
    )


def intent_parsing_started_event(task_id: str) -> Event:
    """Starting to parse user intent"""
    return Event(
        EventType.INTENT_PARSING_STARTED,
        task_id,
        message="🧠 Understanding your request..."
    )


def intent_parsed_event(task_id: str, intent: Dict) -> Event:
    """Intent parsing completed"""
    return Event(
        EventType.INTENT_PARSED,
        task_id,
        {"intent": intent},
        f"✅ Detected: {intent.get('category', 'unknown')}"
    )


def agent_search_started_event(task_id: str, capabilities: list) -> Event:
    """Starting agent search"""
    return Event(
        EventType.AGENT_SEARCH_STARTED,
        task_id,
        {"capabilities": capabilities},
        f"🔍 Finding agents with: {', '.join(capabilities[:3])}..."
    )


def agents_found_event(task_id: str, agents: list) -> Event:
    """Agents discovered"""
    agent_names = [a.get("name", "Unknown") for a in agents]
    return Event(
        EventType.AGENTS_FOUND,
        task_id,
        {"agents": agents, "count": len(agents)},
        f"✅ Found {len(agents)} agents: {', '.join(agent_names[:3])}"
    )


def planning_started_event(task_id: str) -> Event:
    """Starting workflow planning"""
    return Event(
        EventType.PLANNING_STARTED,
        task_id,
        message="📋 Creating execution plan..."
    )


def plan_created_event(task_id: str, steps: list) -> Event:
    """Execution plan created"""
    return Event(
        EventType.PLAN_CREATED,
        task_id,
        {"steps": steps, "total_steps": len(steps)},
        f"✅ Plan ready: {len(steps)} steps"
    )


def execution_started_event(task_id: str, total_steps: int) -> Event:
    """Starting execution"""
    return Event(
        EventType.EXECUTION_STARTED,
        task_id,
        {"total_steps": total_steps},
        f"⚡ Starting execution: {total_steps} steps"
    )


def step_started_event(task_id: str, step_number: int, agent_name: str, total_steps: int) -> Event:
    """Step execution started"""
    return Event(
        EventType.STEP_STARTED,
        task_id,
        {
            "step_number": step_number,
            "agent_name": agent_name,
            "total_steps": total_steps,
            "progress": step_number / total_steps
        },
        f"▶️ Step {step_number}/{total_steps}: {agent_name}"
    )


def agent_thinking_event(task_id: str, agent_name: str, step_number: int) -> Event:
    """Agent is processing"""
    return Event(
        EventType.AGENT_THINKING,
        task_id,
        {"agent_name": agent_name, "step_number": step_number},
        f"💭 {agent_name} is working..."
    )


def step_completed_event(
    task_id: str,
    step_number: int,
    agent_name: str,
    result_preview: str,
    total_steps: int
) -> Event:
    """Step completed successfully"""
    return Event(
        EventType.STEP_COMPLETED,
        task_id,
        {
            "step_number": step_number,
            "agent_name": agent_name,
            "result_preview": result_preview,
            "total_steps": total_steps,
            "progress": step_number / total_steps
        },
        f"✅ Step {step_number}/{total_steps} completed"
    )


def step_failed_event(task_id: str, step_number: int, agent_name: str, error: str) -> Event:
    """Step failed"""
    return Event(
        EventType.STEP_FAILED,
        task_id,
        {"step_number": step_number, "agent_name": agent_name, "error": error},
        f"❌ Step {step_number} failed: {error[:50]}..."
    )


def task_completed_event(task_id: str, result_preview: str, duration: float) -> Event:
    """Task completed successfully"""
    return Event(
        EventType.TASK_COMPLETED,
        task_id,
        {"result_preview": result_preview, "duration": duration},
        f"✅ Task completed in {duration:.1f}s"
    )


def task_failed_event(task_id: str, error: str) -> Event:
    """Task failed"""
    return Event(
        EventType.TASK_FAILED,
        task_id,
        {"error": error},
        f"❌ Task failed: {error}"
    )


def progress_update_event(task_id: str, current: int, total: int, message: str = None) -> Event:
    """Generic progress update"""
    progress = current / total if total > 0 else 0
    return Event(
        EventType.PROGRESS_UPDATE,
        task_id,
        {
            "current": current,
            "total": total,
            "progress": progress,
            "percentage": int(progress * 100)
        },
        message or f"Progress: {current}/{total} ({int(progress * 100)}%)"
    )


def message_event(task_id: str, message: str, data: Dict = None) -> Event:
    """Generic message event"""
    return Event(
        EventType.MESSAGE,
        task_id,
        data,
        message
    )


def error_event(task_id: str, error: str, data: Dict = None) -> Event:
    """Error event"""
    return Event(
        EventType.ERROR,
        task_id,
        data,
        f"❌ {error}"
    )


# ============================================================================
# WORKFLOW EVENT BUILDERS (Sprint 5)
# ============================================================================

def build_workflow_event(event_type: str, workflow_run_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a workflow event for WebSocket streaming.
    
    Args:
        event_type: Type of workflow event
        workflow_run_id: ID of the workflow run
        data: Event data
        
    Returns:
        Event dictionary ready for JSON serialization
    """
    return {
        "type": event_type,
        "workflow_run_id": workflow_run_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

