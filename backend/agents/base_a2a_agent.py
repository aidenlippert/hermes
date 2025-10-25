"""
Base A2A Agent Framework

This is the foundation for all A2A-compliant agents in Hermes.
Every agent should inherit from this base class.
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class A2AAgent(ABC):
    """
    Base class for A2A-compliant agents.

    This provides:
    - Agent card generation
    - JSON-RPC 2.0 handling
    - Task management
    - Error handling
    - Streaming support
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        port: int = 8000
    ):
        self.name = name
        self.description = description
        self.version = version
        self.port = port
        self.app = FastAPI(title=name, version=version)
        self.tasks = {}  # Track running tasks

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup A2A protocol routes"""

        @self.app.get("/.well-known/agent.json")
        async def agent_card():
            """Return A2A-compliant agent card"""
            return self.get_agent_card()

        @self.app.post("/a2a")
        async def handle_a2a_request(request: Request):
            """Handle A2A JSON-RPC 2.0 requests"""
            try:
                body = await request.json()
                return await self.handle_jsonrpc(body)
            except Exception as e:
                logger.error(f"Error handling A2A request: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": str(e)
                        },
                        "id": body.get("id") if "body" in locals() else None
                    }
                )

        @self.app.post("/a2a/stream")
        async def handle_stream_request(request: Request):
            """Handle streaming A2A requests"""
            body = await request.json()
            return StreamingResponse(
                self.stream_task(body),
                media_type="text/event-stream"
            )

    def get_agent_card(self) -> Dict[str, Any]:
        """
        Generate A2A-compliant agent card.

        Override this to customize your agent's capabilities.
        """
        return {
            "name": self.name,
            "description": self.description,
            "url": f"http://localhost:{self.port}/a2a",
            "version": self.version,
            "capabilities": {
                "streaming": True,
                "pushNotifications": False
            },
            "default_input_modes": ["text/plain", "application/json"],
            "default_output_modes": ["text/plain", "application/json"],
            "skills": self.get_skills(),
            "authentication": {
                "type": "none"
            }
        }

    @abstractmethod
    def get_skills(self) -> List[Dict[str, Any]]:
        """
        Define your agent's skills.

        Must return a list of skill objects with:
        - id: unique identifier
        - name: human-readable name
        - description: what the skill does
        - tags: list of tags
        - examples: list of example uses
        """
        pass

    async def handle_jsonrpc(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC 2.0 requests"""

        # Validate JSON-RPC format
        if body.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                },
                "id": body.get("id")
            }

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        # Route to appropriate handler
        if method == "task":
            return await self.handle_task(params, request_id)
        elif method == "task_status":
            return await self.get_task_status(params.get("task_id"), request_id)
        elif method == "task_cancel":
            return await self.cancel_task(params.get("task_id"), request_id)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }

    async def handle_task(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle task execution request"""

        # Extract task details
        messages = params.get("messages", [])
        context = params.get("context", {})
        metadata = params.get("metadata", {})

        if not messages:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params: messages required"
                },
                "id": request_id
            }

        # Get user message
        user_message = None
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break

        if not user_message:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "No user message found"
                },
                "id": request_id
            }

        # Create task
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "status": "in_progress",
            "created_at": datetime.utcnow().isoformat()
        }

        # Execute the task (agent-specific logic)
        try:
            result = await self.execute(user_message, context, metadata)

            # Update task status
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = result

            return {
                "jsonrpc": "2.0",
                "result": {
                    "task_id": task_id,
                    "status": "completed",
                    "artifacts": result if isinstance(result, list) else [result]
                },
                "id": request_id
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}")

            # Update task status
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = str(e)

            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Task execution failed",
                    "data": str(e)
                },
                "id": request_id
            }

    @abstractmethod
    async def execute(self, message: str, context: Dict, metadata: Dict) -> Any:
        """
        Execute the agent's main logic.

        This is where you implement your agent's functionality.

        Args:
            message: The user's request
            context: Context from previous interactions
            metadata: Additional metadata

        Returns:
            The result (will be wrapped in artifacts)
        """
        pass

    async def get_task_status(self, task_id: str, request_id: str) -> Dict[str, Any]:
        """Get status of a running task"""

        task = self.tasks.get(task_id)

        if not task:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": f"Task not found: {task_id}"
                },
                "id": request_id
            }

        return {
            "jsonrpc": "2.0",
            "result": {
                "task_id": task_id,
                "status": task["status"],
                "created_at": task["created_at"],
                "result": task.get("result"),
                "error": task.get("error")
            },
            "id": request_id
        }

    async def cancel_task(self, task_id: str, request_id: str) -> Dict[str, Any]:
        """Cancel a running task"""

        task = self.tasks.get(task_id)

        if not task:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": f"Task not found: {task_id}"
                },
                "id": request_id
            }

        # Mark as cancelled
        task["status"] = "cancelled"

        return {
            "jsonrpc": "2.0",
            "result": {
                "task_id": task_id,
                "status": "cancelled"
            },
            "id": request_id
        }

    async def stream_task(self, body: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream task execution updates"""

        # Parse request
        params = body.get("params", {})
        messages = params.get("messages", [])

        # Get user message
        user_message = None
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break

        if not user_message:
            yield f"data: {json.dumps({'error': 'No user message found'})}\n\n"
            return

        # Stream updates
        yield f"data: {json.dumps({'status': 'starting', 'message': 'Processing request...'})}\n\n"
        await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'status': 'thinking', 'message': 'Analyzing...'})}\n\n"
        await asyncio.sleep(1)

        # Execute
        try:
            result = await self.execute(user_message, {}, {})
            yield f"data: {json.dumps({'status': 'completed', 'result': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    def run(self):
        """Start the agent server"""
        import uvicorn
        logger.info(f"🚀 Starting {self.name} on port {self.port}")
        logger.info(f"   Agent card: http://localhost:{self.port}/.well-known/agent.json")
        logger.info(f"   A2A endpoint: http://localhost:{self.port}/a2a")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)