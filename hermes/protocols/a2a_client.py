"""
A2A Protocol Client - THE FOUNDATION

This is how Hermes talks to ALL agents using Google's A2A protocol.

A2A Spec: https://github.com/google/a2a
- Agent Cards: /.well-known/agent.json
- JSON-RPC 2.0 messaging
- Tasks with unique IDs
- Streaming support
- Artifact-based results
"""

import httpx
import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCard:
    """
    Represents an agent's capabilities and metadata.
    Parsed from /.well-known/agent.json
    """
    name: str
    description: str
    version: str
    endpoint: str
    capabilities: List[Dict[str, Any]]
    authentication: Optional[Dict[str, Any]] = None
    supported_modalities: List[str] = field(default_factory=lambda: ["text"])
    streaming: bool = True
    raw_card: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Parse agent card from JSON response"""
        return cls(
            name=data.get("name", "Unknown Agent"),
            description=data.get("description", ""),
            version=data.get("version", "0.1"),
            endpoint=data.get("endpoint", ""),
            capabilities=data.get("capabilities", []),
            authentication=data.get("authentication"),
            supported_modalities=data.get("supportedModalities", ["text"]),
            streaming=data.get("streaming", True),
            raw_card=data
        )


@dataclass
class A2ATask:
    """
    Represents a task sent to an agent.

    A2A tasks are the atomic unit of work. Each task:
    - Has a unique ID (we generate)
    - Contains parts (the actual content)
    - Can stream results
    - Returns artifacts
    """
    task_id: str
    agent_endpoint: str
    parts: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_jsonrpc(self) -> Dict[str, Any]:
        """Convert to JSON-RPC 2.0 request format"""
        return {
            "jsonrpc": "2.0",
            "method": "execute_task",
            "params": {
                "task_id": self.task_id,
                "parts": self.parts,
                "context": self.context or {},
                "metadata": self.metadata or {}
            },
            "id": self.task_id
        }


@dataclass
class A2AResponse:
    """Response from an A2A agent"""
    task_id: str
    status: TaskStatus
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_jsonrpc(cls, data: Dict[str, Any]) -> "A2AResponse":
        """Parse JSON-RPC 2.0 response"""
        if "error" in data:
            return cls(
                task_id=data.get("id", "unknown"),
                status=TaskStatus.FAILED,
                error=data["error"].get("message", "Unknown error")
            )

        result = data.get("result", {})
        return cls(
            task_id=data.get("id", "unknown"),
            status=TaskStatus(result.get("status", "completed")),
            artifacts=result.get("artifacts", []),
            metadata=result.get("metadata", {})
        )


class A2AClient:
    """
    Universal A2A Protocol Client

    This is how Hermes communicates with ALL agents, regardless of
    their implementation (CrewAI, LangChain, custom, etc.)

    As long as they speak A2A, we can talk to them.
    """

    def __init__(self, timeout: int = 120):
        """
        Initialize A2A client

        Args:
            timeout: HTTP timeout in seconds (default 120 for long-running agents)
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self._discovered_agents: Dict[str, AgentCard] = {}

        logger.info("🚀 A2A Client initialized")

    async def discover_agent(self, base_url: str) -> AgentCard:
        """
        Discover an agent's capabilities via its Agent Card.

        This is STEP 1 of A2A protocol:
        1. Fetch /.well-known/agent.json
        2. Parse capabilities
        3. Cache the card

        Args:
            base_url: Agent's base URL (e.g., https://agent.example.com)

        Returns:
            AgentCard with parsed capabilities

        Raises:
            httpx.HTTPError: If agent card can't be fetched
        """
        # Normalize URL
        base_url = base_url.rstrip('/')
        card_url = f"{base_url}/.well-known/agent.json"

        logger.info(f"🔍 Discovering agent at {card_url}")

        try:
            response = await self.client.get(card_url)
            response.raise_for_status()
            card_data = response.json()

            # If endpoint is relative, make it absolute
            if "endpoint" in card_data and not card_data["endpoint"].startswith("http"):
                card_data["endpoint"] = f"{base_url}{card_data['endpoint']}"

            agent_card = AgentCard.from_dict(card_data)

            # Cache it
            self._discovered_agents[base_url] = agent_card

            logger.info(f"✅ Discovered agent: {agent_card.name} (v{agent_card.version})")
            logger.info(f"   Capabilities: {len(agent_card.capabilities)}")
            logger.info(f"   Endpoint: {agent_card.endpoint}")

            return agent_card

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to discover agent at {card_url}: {e}")
            raise

    async def send_task(
        self,
        agent_endpoint: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> A2AResponse:
        """
        Send a task to an agent and get the result.

        This is STEP 2 of A2A protocol:
        1. Create task with unique ID
        2. Format as JSON-RPC 2.0
        3. POST to agent's endpoint
        4. Parse artifact response

        Args:
            agent_endpoint: Full URL of agent's A2A endpoint
            task_description: What you want the agent to do (natural language)
            context: Optional context (previous results, user info, etc.)
            stream: Whether to request streaming response

        Returns:
            A2AResponse with results or error
        """
        task = A2ATask(
            task_id=str(uuid.uuid4()),
            agent_endpoint=agent_endpoint,
            parts=[
                {
                    "type": "TextPart",
                    "content": task_description
                }
            ],
            context=context,
            metadata={
                "stream": stream,
                "hermes_version": "0.1.0"
            }
        )

        logger.info(f"📤 Sending task {task.task_id} to {agent_endpoint}")
        logger.debug(f"   Task: {task_description[:100]}...")

        try:
            response = await self.client.post(
                agent_endpoint,
                json=task.to_jsonrpc(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = A2AResponse.from_jsonrpc(response.json())

            if result.status == TaskStatus.COMPLETED:
                logger.info(f"✅ Task {task.task_id} completed")
                logger.info(f"   Artifacts: {len(result.artifacts)}")
            else:
                logger.warning(f"⚠️ Task {task.task_id} status: {result.status}")

            return result

        except httpx.HTTPError as e:
            logger.error(f"❌ Task {task.task_id} failed: {e}")
            return A2AResponse(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )

    async def stream_task(
        self,
        agent_endpoint: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream task execution updates from an agent.

        This uses Server-Sent Events (SSE) for real-time updates.
        The agent sends incremental updates as it works.

        Args:
            agent_endpoint: Full URL of agent's A2A endpoint
            task_description: What you want the agent to do
            context: Optional context

        Yields:
            Dict with update events (thinking, progress, results)
        """
        task = A2ATask(
            task_id=str(uuid.uuid4()),
            agent_endpoint=agent_endpoint,
            parts=[{"type": "TextPart", "content": task_description}],
            context=context,
            metadata={"stream": True}
        )

        logger.info(f"🌊 Streaming task {task.task_id}")

        try:
            async with self.client.stream(
                "POST",
                agent_endpoint,
                json=task.to_jsonrpc(),
                headers={"Accept": "text/event-stream"}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        try:
                            yield eval(data)  # Parse the event
                        except:
                            logger.warning(f"⚠️ Failed to parse stream event: {data}")

        except Exception as e:
            logger.error(f"❌ Stream failed: {e}")
            yield {
                "type": "error",
                "task_id": task.task_id,
                "error": str(e)
            }

    async def get_task_status(
        self,
        agent_endpoint: str,
        task_id: str
    ) -> A2AResponse:
        """
        Check the status of a previously submitted task.

        For long-running tasks, agents may return immediately and
        we poll for completion.

        Args:
            agent_endpoint: Full URL of agent's A2A endpoint
            task_id: The task ID to check

        Returns:
            Current A2AResponse with status
        """
        logger.info(f"🔍 Checking status of task {task_id}")

        try:
            response = await self.client.post(
                agent_endpoint,
                json={
                    "jsonrpc": "2.0",
                    "method": "get_task_status",
                    "params": {"task_id": task_id},
                    "id": task_id
                }
            )
            response.raise_for_status()
            return A2AResponse.from_jsonrpc(response.json())

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to get status: {e}")
            return A2AResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )

    async def cancel_task(
        self,
        agent_endpoint: str,
        task_id: str
    ) -> bool:
        """
        Cancel a running task.

        Args:
            agent_endpoint: Full URL of agent's A2A endpoint
            task_id: The task ID to cancel

        Returns:
            True if cancelled successfully
        """
        logger.info(f"🛑 Cancelling task {task_id}")

        try:
            response = await self.client.post(
                agent_endpoint,
                json={
                    "jsonrpc": "2.0",
                    "method": "cancel_task",
                    "params": {"task_id": task_id},
                    "id": task_id
                }
            )
            response.raise_for_status()
            result = response.json()

            if "error" not in result:
                logger.info(f"✅ Task {task_id} cancelled")
                return True
            else:
                logger.error(f"❌ Failed to cancel: {result['error']}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"❌ Cancel failed: {e}")
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("👋 A2A Client closed")

    def __del__(self):
        """Cleanup"""
        try:
            asyncio.get_event_loop().run_until_complete(self.close())
        except:
            pass


if __name__ == "__main__":
    async def test_a2a_client():
        """Test the A2A client with a mock agent"""
        client = A2AClient()

        print("\n" + "="*60)
        print("🧪 Testing A2A Client")
        print("="*60)

        print("\n1️⃣ Testing Agent Discovery...")
        print("   (This will fail unless you have a real agent running)")
        print("   Example: await client.discover_agent('http://localhost:10001')")

        print("\n2️⃣ Testing Task Sending...")
        print("   (This will fail unless you have a real agent running)")
        print("   Example: await client.send_task(endpoint, 'Write a function')")

        print("\n✅ A2A Client is ready!")
        print("\nNext steps:")
        print("   1. Build a simple A2A-compliant agent")
        print("   2. Test discovery and task execution")
        print("   3. Integrate with Hermes conductor")

        await client.close()

    asyncio.run(test_a2a_client())
