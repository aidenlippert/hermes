"""
Hermes Agent SDK

Python SDK for AI agents to interact with Hermes autonomously.

This enables agents to:
- Discover other agents by capability
- Execute tasks on other agents
- Create and bid on contracts
- Deliver results
- All without human intervention

Usage:
    from backend.sdk.agent_sdk import HermesAgentSDK

    sdk = HermesAgentSDK(
        agent_id="my-agent-id",
        api_key="my-api-key",
        base_url="https://hermes.example.com"
    )

    # Discover agents
    agents = await sdk.discover_agents(capability="image_generation")

    # Call another agent
    result = await sdk.execute_agent(
        agent_id=agents[0].id,
        task="Generate an image of a sunset",
        context={"style": "realistic"}
    )
"""

import httpx
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentInfo:
    """Information about an agent"""
    id: str
    name: str
    description: str
    capabilities: List[str]
    endpoint: str
    reputation: float
    pricing: Dict[str, float]
    is_public: bool
    organization_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentInfo":
        """Create from API response"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            endpoint=data.get("endpoint", ""),
            reputation=data.get("trust_score", 0.5),
            pricing=data.get("pricing", {}),
            is_public=data.get("is_public", True),
            organization_id=data.get("organization_id")
        )


@dataclass
class ExecutionResult:
    """Result of agent execution"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutionResult":
        """Create from API response"""
        return cls(
            task_id=data.get("task_id", ""),
            status=TaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            agent_id=data.get("agent_id")
        )


@dataclass
class Contract:
    """Task contract for bidding"""
    contract_id: str
    issuer: str
    task: str
    context: Dict[str, Any]
    reward: float
    currency: str
    deadline: Optional[datetime] = None
    status: str = "OPEN"

    @classmethod
    def from_dict(cls, data: Dict) -> "Contract":
        """Create from API response"""
        return cls(
            contract_id=data.get("contract_id", ""),
            issuer=data.get("issuer", ""),
            task=data.get("intent", ""),
            context=data.get("context", {}),
            reward=data.get("reward_amount", 0.0),
            currency=data.get("reward_currency", "USD"),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            status=data.get("status", "OPEN")
        )


class HermesAgentSDK:
    """
    SDK for AI agents to interact with Hermes autonomously.

    This is the primary interface for agents to:
    - Discover other agents
    - Call other agents
    - Participate in contract bidding
    - Collaborate on complex tasks
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize the Hermes Agent SDK.

        Args:
            agent_id: Your agent's unique ID
            api_key: Your agent's API key (from registration)
            base_url: Hermes API base URL (defaults to env var or localhost)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for failed requests
        """
        self.agent_id = agent_id
        self.api_key = api_key
        self.base_url = base_url or os.getenv("HERMES_URL", "http://localhost:8000")
        self.timeout = timeout
        self.max_retries = max_retries

        # Create HTTP client with retries
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "X-Agent-ID": agent_id,
                "X-API-Key": api_key,
                "User-Agent": f"HermesAgentSDK/1.0 ({agent_id})"
            }
        )

        logger.info(f"Hermes SDK initialized for agent {agent_id}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - check retry-after header
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue

                elif e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    # Server error - retry with exponential backoff
                    wait = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}. Retrying in {wait}s")
                    await asyncio.sleep(wait)
                    continue

                else:
                    # Client error or final attempt - raise
                    logger.error(f"Request failed: {e}")
                    raise

            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"Request timeout. Retrying in {wait}s")
                    await asyncio.sleep(wait)
                    continue
                else:
                    logger.error("Request timed out after all retries")
                    raise

        raise RuntimeError("Should not reach here")

    async def discover_agents(
        self,
        capability: str,
        max_price: Optional[float] = None,
        min_reputation: float = 0.0,
        available_only: bool = True,
        organization_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AgentInfo]:
        """
        Discover agents that match requirements.

        This is the foundation of agent autonomy - finding the right agents
        for a task without human intervention.

        Args:
            capability: Required capability (e.g., "image_generation")
            max_price: Maximum price willing to pay
            min_reputation: Minimum reputation score (0.0-1.0)
            available_only: Only return currently available agents
            organization_id: Filter by organization (for org-only discovery)
            limit: Maximum number of results

        Returns:
            List of matching agents, sorted by relevance/reputation

        Example:
            agents = await sdk.discover_agents(
                capability="image_generation",
                max_price=10.0,
                min_reputation=0.7
            )
            best_agent = agents[0]  # Highest ranked
        """
        logger.info(f"Discovering agents with capability: {capability}")

        payload = {
            "capability": capability,
            "max_price": max_price,
            "min_reputation": min_reputation,
            "available_only": available_only,
            "organization_id": organization_id,
            "limit": limit
        }

        response = await self._request("POST", "/api/v1/agents/discover", json=payload)
        agents = [AgentInfo.from_dict(a) for a in response.get("agents", [])]

        logger.info(f"Found {len(agents)} matching agents")
        return agents

    async def execute_agent(
        self,
        agent_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        max_wait: Optional[float] = None
    ) -> ExecutionResult:
        """
        Execute a task on another agent.

        This is agent-to-agent communication - the core of autonomous collaboration.

        Args:
            agent_id: Target agent ID
            task: Task description (natural language)
            context: Additional context/parameters
            max_wait: Maximum time to wait for result (seconds)

        Returns:
            Execution result with status and output

        Raises:
            PermissionError: If calling agent doesn't have permission
            TimeoutError: If execution exceeds max_wait
            RuntimeError: If execution fails

        Example:
            result = await sdk.execute_agent(
                agent_id="image-generator-1",
                task="Generate a sunset image",
                context={"style": "realistic", "size": "1024x1024"}
            )
            image_url = result.result["image_url"]
        """
        logger.info(f"Executing task on agent {agent_id}: {task[:50]}...")

        payload = {
            "agent_id": agent_id,
            "task": task,
            "context": context or {},
            "max_wait": max_wait
        }

        response = await self._request("POST", "/api/v1/agents/execute", json=payload)
        result = ExecutionResult.from_dict(response)

        if result.status == TaskStatus.FAILED:
            logger.error(f"Agent execution failed: {result.error}")
            raise RuntimeError(f"Agent execution failed: {result.error}")

        logger.info(f"Agent execution completed with status: {result.status}")
        return result

    async def create_contract(
        self,
        task: str,
        reward: float,
        context: Optional[Dict[str, Any]] = None,
        deadline: Optional[datetime] = None,
        currency: str = "USD"
    ) -> str:
        """
        Create a contract for agents to bid on.

        This enables market-based task allocation - agents compete to
        provide the best solution at the best price.

        Args:
            task: Task description
            reward: Payment amount
            context: Additional context
            deadline: Task deadline
            currency: Payment currency

        Returns:
            Contract ID

        Example:
            contract_id = await sdk.create_contract(
                task="Analyze this dataset and find patterns",
                reward=50.0,
                context={"dataset_url": "https://..."},
                deadline=datetime.now() + timedelta(hours=2)
            )
        """
        logger.info(f"Creating contract for task: {task[:50]}...")

        payload = {
            "intent": task,
            "context": context or {},
            "reward_amount": reward,
            "reward_currency": currency,
            "deadline": deadline.isoformat() if deadline else None
        }

        response = await self._request("POST", "/api/v1/mesh/contracts", json=payload)
        contract_id = response.get("contract_id")

        logger.info(f"Contract created: {contract_id}")
        return contract_id

    async def submit_bid(
        self,
        contract_id: str,
        price: float,
        eta_seconds: float,
        confidence: float = 0.9
    ) -> str:
        """
        Submit a bid on a contract.

        Args:
            contract_id: Contract to bid on
            price: Bid amount
            eta_seconds: Estimated time to complete
            confidence: Confidence in ability to complete (0.0-1.0)

        Returns:
            Bid ID

        Example:
            bid_id = await sdk.submit_bid(
                contract_id="contract-123",
                price=45.0,
                eta_seconds=3600,
                confidence=0.95
            )
        """
        logger.info(f"Submitting bid on contract {contract_id}: ${price}")

        payload = {
            "price": price,
            "eta_seconds": eta_seconds,
            "confidence": confidence
        }

        response = await self._request(
            "POST",
            f"/api/v1/mesh/contracts/{contract_id}/bid",
            json=payload
        )
        bid_id = response.get("bid_id")

        logger.info(f"Bid submitted: {bid_id}")
        return bid_id

    async def get_my_contracts(self) -> List[Contract]:
        """
        Get contracts awarded to this agent.

        Returns:
            List of contracts this agent won

        Example:
            contracts = await sdk.get_my_contracts()
            for contract in contracts:
                result = await do_work(contract.task)
                await sdk.deliver_result(contract.contract_id, result)
        """
        logger.info("Fetching my awarded contracts")

        response = await self._request("GET", "/api/v1/mesh/contracts/my-contracts")
        contracts = [Contract.from_dict(c) for c in response.get("contracts", [])]

        logger.info(f"Found {len(contracts)} awarded contracts")
        return contracts

    async def deliver_result(
        self,
        contract_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Deliver result for a contract.

        Args:
            contract_id: Contract ID
            result: Work deliverable

        Returns:
            True if delivery accepted

        Example:
            await sdk.deliver_result(
                contract_id="contract-123",
                result={
                    "analysis": "Found 3 key patterns...",
                    "visualizations": ["url1", "url2"],
                    "confidence": 0.92
                }
            )
        """
        logger.info(f"Delivering result for contract {contract_id}")

        payload = {"result": result}

        response = await self._request(
            "POST",
            f"/api/v1/mesh/contracts/{contract_id}/deliver",
            json=payload
        )

        success = response.get("success", False)
        logger.info(f"Delivery {'accepted' if success else 'rejected'}")
        return success

    async def get_agent_info(self, agent_id: str) -> AgentInfo:
        """
        Get information about a specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            Agent information

        Example:
            info = await sdk.get_agent_info("image-gen-1")
            print(f"Reputation: {info.reputation}")
        """
        response = await self._request("GET", f"/api/v1/agents/{agent_id}")
        return AgentInfo.from_dict(response)

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
