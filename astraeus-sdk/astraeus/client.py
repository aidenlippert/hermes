"""
ASTRAEUS Client - Discover and communicate with agents on the network
"""

import httpx
from typing import List, Dict, Any, Optional


class AstraeusClient:
    """
    Client for discovering and calling agents on the ASTRAEUS network

    Example:
        client = AstraeusClient(api_key="astraeus_xxxxx")

        # Search for translation agents
        agents = await client.search_agents(capability="translate")

        # Call an agent
        result = await client.call_agent(
            agent_id="agent-xyz",
            capability="translate",
            input={"text": "Hello", "target_lang": "es"}
        )
    """

    def __init__(
        self,
        api_key: str,
        astraeus_url: str = "https://web-production-3df46.up.railway.app"
    ):
        self.api_key = api_key
        self.astraeus_url = astraeus_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

    async def search_agents(
        self,
        capability: Optional[str] = None,
        framework: Optional[str] = None,
        min_trust_score: float = 0.0,
        limit: int = 10,
        sort_by: str = "trust_score"
    ) -> List[Dict[str, Any]]:
        """
        Search for agents on the network with smart ranking

        Args:
            capability: Filter by capability name (e.g., "translate", "analyze_data")
            framework: Filter by framework (e.g., "langchain", "crewai", "custom")
            min_trust_score: Minimum trust score (0.0-1.0)
            limit: Maximum number of results
            sort_by: Sort by "trust_score", "cost", "speed", or "smart" (default: trust_score)

        Returns:
            List of agent dictionaries ranked by quality
        """
        params = {"limit": limit * 2}

        if capability:
            params["capability"] = capability
        if framework:
            params["framework"] = framework
        if min_trust_score > 0:
            params["min_trust_score"] = min_trust_score

        response = await self.client.get(
            f"{self.astraeus_url}/api/v1/mesh/agents",
            params=params
        )
        response.raise_for_status()

        agents = response.json()

        if sort_by == "trust_score":
            agents.sort(key=lambda a: -a.get('trust_score', 0))
        elif sort_by == "cost":
            agents.sort(key=lambda a: a.get('base_cost_per_call', 0))
        elif sort_by == "speed":
            agents.sort(key=lambda a: a.get('avg_latency_ms', 99999))
        elif sort_by == "smart":
            agents = self._smart_rank_agents(agents)

        return agents[:limit]

    def _smart_rank_agents(self, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Smart ranking algorithm that balances trust, cost, and speed

        Scoring:
        - Trust Score (60%): Reputation and reliability
        - Cost Efficiency (20%): Lower cost is better
        - Speed (20%): Lower latency is better
        """
        def calculate_score(agent):
            trust = agent.get('trust_score', 0)
            cost = agent.get('base_cost_per_call', 0)
            latency = agent.get('avg_latency_ms', 1000)

            max_cost = max([a.get('base_cost_per_call', 0) for a in agents] or [1])
            max_latency = max([a.get('avg_latency_ms', 1000) for a in agents] or [1000])

            cost_score = 1.0 - (cost / max_cost if max_cost > 0 else 0)
            speed_score = 1.0 - (latency / max_latency if max_latency > 0 else 0)

            return trust * 0.6 + cost_score * 0.2 + speed_score * 0.2

        agents_with_scores = [(agent, calculate_score(agent)) for agent in agents]
        agents_with_scores.sort(key=lambda x: -x[1])

        return [agent for agent, score in agents_with_scores]

    async def find_best_agent(
        self,
        capability: str,
        max_cost: Optional[float] = None,
        min_trust_score: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Find the single best agent for a capability

        Args:
            capability: Required capability
            max_cost: Maximum acceptable cost per call
            min_trust_score: Minimum required trust score

        Returns:
            Best agent or None if no suitable agent found
        """
        agents = await self.search_agents(
            capability=capability,
            min_trust_score=min_trust_score,
            sort_by="smart",
            limit=10
        )

        if max_cost:
            agents = [a for a in agents if a.get('base_cost_per_call', 0) <= max_cost]

        return agents[0] if agents else None

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific agent

        Args:
            agent_id: The unique agent identifier

        Returns:
            Agent information including capabilities, stats, and metadata
        """
        response = await self.client.get(
            f"{self.astraeus_url}/api/v1/mesh/agents/{agent_id}"
        )
        response.raise_for_status()

        return response.json()

    async def get_agent_card(self, agent_id: str) -> Dict[str, Any]:
        """
        Get A2A Protocol Agent Card from agent endpoint

        Args:
            agent_id: The unique agent identifier

        Returns:
            A2A Agent Card with capabilities
        """
        agent = await self.get_agent(agent_id)
        endpoint = agent.get("endpoint")

        if not endpoint:
            raise ValueError(f"Agent {agent_id} has no endpoint")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{endpoint}/.well-known/agent.json")
            response.raise_for_status()
            return response.json()

    async def call_agent(
        self,
        agent_id: str,
        capability: str,
        input: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Call an agent's capability

        Args:
            agent_id: The agent to call
            capability: The capability name
            input: Input parameters for the capability
            timeout: Request timeout in seconds

        Returns:
            Result from the agent

        Example:
            result = await client.call_agent(
                agent_id="agent-abc123",
                capability="translate",
                input={"text": "Hello", "target_lang": "es"}
            )
            # result: {"success": True, "result": {"translation": "Hola"}}
        """
        agent = await self.get_agent(agent_id)
        endpoint = agent.get("endpoint")

        if not endpoint:
            raise ValueError(f"Agent {agent_id} has no endpoint")

        payload = {
            "capability": capability,
            "input": input
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{endpoint}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def create_conversation(
        self,
        target_agent_id: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Start a conversation with another agent

        Args:
            target_agent_id: Agent to start conversation with
            topic: Optional conversation topic

        Returns:
            Conversation ID
        """
        response = await self.client.post(
            f"{self.astraeus_url}/api/v1/mesh/conversations",
            json={
                "target_agent_id": target_agent_id,
                "topic": topic
            }
        )
        response.raise_for_status()

        data = response.json()
        return data.get("conversation_id")

    async def send_message(
        self,
        conversation_id: str,
        content: Dict[str, Any],
        message_type: str = "request",
        requires_response: bool = True
    ) -> Dict[str, Any]:
        """
        Send a message in a conversation

        Args:
            conversation_id: The conversation ID
            content: Message content (JSON)
            message_type: Type of message (request, response, event, notification)
            requires_response: Whether this message expects a response

        Returns:
            Message metadata
        """
        response = await self.client.post(
            f"{self.astraeus_url}/api/v1/mesh/conversations/{conversation_id}/messages",
            json={
                "content": content,
                "message_type": message_type,
                "requires_response": requires_response
            }
        )
        response.raise_for_status()

        return response.json()

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        since_message_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of messages
            since_message_id: Only get messages after this ID

        Returns:
            List of messages
        """
        params = {"limit": limit}
        if since_message_id:
            params["since"] = since_message_id

        response = await self.client.get(
            f"{self.astraeus_url}/api/v1/mesh/conversations/{conversation_id}/messages",
            params=params
        )
        response.raise_for_status()

        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
