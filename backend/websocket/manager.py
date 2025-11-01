"""
WebSocket Connection Manager

Manages WebSocket connections and broadcasts events to connected clients.

Features:
- Connection management per task
- Event broadcasting
- Automatic cleanup
- Support for multiple subscribers per task
"""

import logging
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
import json
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket Connection Manager

    Manages active WebSocket connections and routes events to the right clients.
    """

    def __init__(self):
        # Maps task_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Maps user_id -> set of WebSocket connections (for user-wide updates)
        self.user_connections: Dict[str, Set[WebSocket]] = {}

        # Maps agent_id -> set of WebSocket connections (for A2A)
        self.agent_connections: Dict[str, Set[WebSocket]] = {}

        # Maps workflow_run_id -> set of WebSocket connections (Sprint 5)
        self.workflow_connections: Dict[str, Set[WebSocket]] = {}

        # Message buffer: Maps task_id -> list of buffered events
        self.message_buffer: Dict[str, list] = {}

        logger.info("📡 WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket, task_id: str, user_id: Optional[str] = None):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            task_id: Task ID to subscribe to
            user_id: Optional user ID for user-wide updates
        """
        await websocket.accept()

        # Add to task subscribers
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)

        # Add to user subscribers if provided
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

        logger.info(f"🔌 WebSocket connected - Task: {task_id[:8]}..., Subscribers: {len(self.active_connections[task_id])}")

        # Send any buffered messages for this task
        if task_id in self.message_buffer and self.message_buffer[task_id]:
            logger.info(f"📦 Sending {len(self.message_buffer[task_id])} buffered messages to new connection")
            for buffered_event in self.message_buffer[task_id]:
                try:
                    await websocket.send_json(buffered_event)
                except Exception as e:
                    logger.error(f"❌ Failed to send buffered message: {e}")
            # Clear buffer after sending
            del self.message_buffer[task_id]

    def disconnect(self, websocket: WebSocket, task_id: str, user_id: Optional[str] = None):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            task_id: Task ID it was subscribed to
            user_id: Optional user ID
        """
        # Remove from task subscribers
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

        # Remove from user subscribers
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"🔌 WebSocket disconnected - Task: {task_id[:8]}...")

    async def connect_agent(self, websocket: WebSocket, agent_id: str):
        """Accept a WebSocket connection for an agent presence channel"""
        await websocket.accept()
        if agent_id not in self.agent_connections:
            self.agent_connections[agent_id] = set()
        self.agent_connections[agent_id].add(websocket)
        logger.info(f"🤖 Agent connected: {agent_id}")

    def disconnect_agent(self, websocket: WebSocket, agent_id: str):
        """Remove an agent WebSocket connection"""
        if agent_id in self.agent_connections:
            self.agent_connections[agent_id].discard(websocket)
            if not self.agent_connections[agent_id]:
                del self.agent_connections[agent_id]
        logger.info(f"🤖 Agent disconnected: {agent_id}")

    async def send_to_agent(self, agent_id: str, event: Dict[str, Any]):
        """Send event to all sockets for a specific agent"""
        if agent_id not in self.agent_connections:
            return
        if "timestamp" not in event:
            from datetime import datetime, timezone
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
        disconnected = []
        for connection in self.agent_connections[agent_id]:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.error(f"❌ Failed to send to agent socket: {e}")
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect_agent(connection, agent_id)

    async def send_to_task(self, task_id: str, event: Dict[str, Any]):
        """
        Send event to all clients subscribed to a specific task.
        If no clients are connected, buffer the event for later delivery.

        Args:
            task_id: Task ID
            event: Event data (will be JSON serialized)
        """
        # Add timestamp if not present
        if "timestamp" not in event:
            from datetime import datetime, timezone
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        # If no active connections, buffer the message
        if task_id not in self.active_connections or not self.active_connections[task_id]:
            logger.info(f"📦 Buffering message for task {task_id[:8]}... (no active connections)")
            if task_id not in self.message_buffer:
                self.message_buffer[task_id] = []
            self.message_buffer[task_id].append(event)
            return

        # Broadcast to all connections
        disconnected = []
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.error(f"❌ Failed to send to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, task_id)

    async def send_to_user(self, user_id: str, event: Dict[str, Any]):
        """
        Send event to all connections for a specific user.

        Args:
            user_id: User ID
            event: Event data
        """
        if user_id not in self.user_connections:
            return

        # Add timestamp
        if "timestamp" not in event:
            from datetime import datetime, timezone
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Broadcast
        disconnected = []
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.error(f"❌ Failed to send to user WebSocket: {e}")
                disconnected.append(connection)

        # Cleanup
        for connection in disconnected:
            # Find which task this connection belongs to
            for task_id, connections in self.active_connections.items():
                if connection in connections:
                    self.disconnect(connection, task_id, user_id)
                    break

    async def broadcast(self, event: Dict):
        """
        Broadcast event to ALL connected clients.

        Args:
            event: Event data
        """
        # Add timestamp
        if "timestamp" not in event:
            from datetime import datetime
            event["timestamp"] = datetime.utcnow().isoformat()

        # Send to all tasks
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)

        disconnected = []
        for connection in all_connections:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.error(f"❌ Broadcast failed: {e}")
                disconnected.append(connection)

        # Cleanup
        for connection in disconnected:
            for task_id, connections in list(self.active_connections.items()):
                if connection in connections:
                    self.disconnect(connection, task_id)

    def get_connection_count(self, task_id: str = None) -> int:
        """
        Get number of active connections.

        Args:
            task_id: Optional task ID to get count for specific task

        Returns:
            Number of connections
        """
        if task_id:
            return len(self.active_connections.get(task_id, set()))
        else:
            # Total connections across all tasks
            all_connections = set()
            for connections in self.active_connections.values():
                all_connections.update(connections)
            return len(all_connections)

    def get_stats(self) -> Dict:
        """Get WebSocket statistics"""
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        total_agent_conns = sum(len(conns) for conns in self.agent_connections.values())
        total_workflow_conns = sum(len(conns) for conns in self.workflow_connections.values())

        return {
            "total_connections": total_connections,
            "total_agent_connections": total_agent_conns,
            "total_workflow_connections": total_workflow_conns,
            "active_tasks": len(self.active_connections),
            "active_users": len(self.user_connections),
            "active_agents": len(self.agent_connections),
            "active_workflows": len(self.workflow_connections),
            "tasks": {
                task_id[:8] + "...": len(conns)
                for task_id, conns in self.active_connections.items()
            },
            "agents": {
                agent_id: len(conns)
                for agent_id, conns in self.agent_connections.items()
            },
            "workflows": {
                workflow_id[:8] + "...": len(conns)
                for workflow_id, conns in self.workflow_connections.items()
            }
        }

    async def connect_workflow(self, websocket: WebSocket, workflow_run_id: str):
        """Accept a WebSocket connection for workflow run updates (Sprint 5)"""
        await websocket.accept()
        if workflow_run_id not in self.workflow_connections:
            self.workflow_connections[workflow_run_id] = set()
        self.workflow_connections[workflow_run_id].add(websocket)
        logger.info(f"🔄 Workflow run connected: {workflow_run_id[:8]}...")

    def disconnect_workflow(self, websocket: WebSocket, workflow_run_id: str):
        """Remove a workflow WebSocket connection"""
        if workflow_run_id in self.workflow_connections:
            self.workflow_connections[workflow_run_id].discard(websocket)
            if not self.workflow_connections[workflow_run_id]:
                del self.workflow_connections[workflow_run_id]
        logger.info(f"🔄 Workflow run disconnected: {workflow_run_id[:8]}...")

    async def broadcast_to_workflow(self, workflow_run_id: str, event: Dict[str, Any]):
        """
        Send event to all clients subscribed to a workflow run.
        
        Args:
            workflow_run_id: Workflow run ID
            event: Event data (will be JSON serialized)
        """
        if workflow_run_id not in self.workflow_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in event:
            from datetime import datetime, timezone
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Broadcast to all connections
        disconnected = []
        for connection in self.workflow_connections[workflow_run_id]:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.error(f"❌ Failed to send to workflow WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect_workflow(connection, workflow_run_id)


# Global connection manager instance
manager = ConnectionManager()
