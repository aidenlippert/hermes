"""
A2A-Powered Orchestrator with Groq Intelligence

Combines Groq AI (FREE 70B model) with A2A Protocol for agent orchestration:
1. Agent Discovery: Query database + mesh network for available agents
2. Intent Parsing: Use Groq to understand user intent
3. Task Execution: Coordinate agents via A2A protocol
4. Multi-Agent Workflows: Automatic agent-to-agent coordination
"""

import os
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class A2AOrchestrator:
    """Intelligent orchestrator combining Groq AI with A2A Protocol"""

    def __init__(self):
        """Initialize orchestrator with Groq client"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.groq_client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        logger.info("🤖 A2A Orchestrator initialized with Groq AI")

    async def handle_agent_discovery(self, query: str, agent_registry: Dict, mesh_network) -> Dict[str, Any]:
        """
        Handle queries about available agents

        Args:
            query: User query like "what agents are there?"
            agent_registry: Legacy agent registry
            mesh_network: Mesh network with A2A agents

        Returns:
            Response with agent list and details
        """
        logger.info(f"🔍 Handling agent discovery query: {query}")

        # Get all available agents
        all_agents = []

        # Legacy agents
        for agent_id, agent_data in agent_registry.items():
            all_agents.append({
                "id": agent_id,
                "name": agent_data.get("name", agent_id),
                "description": agent_data.get("description", ""),
                "capabilities": agent_data.get("capabilities", []),
                "type": "legacy",
                "status": agent_data.get("status", "unknown")
            })

        # Mesh agents
        try:
            mesh_agents = mesh_network.discovery.list_agents()
            for agent in mesh_agents:
                all_agents.append({
                    "id": agent.get("id", agent.get("name", "unknown")),
                    "name": agent.get("name", "Unknown"),
                    "description": agent.get("description", ""),
                    "capabilities": agent.get("capabilities", []),
                    "type": "mesh",
                    "status": "active"
                })
        except Exception as e:
            logger.warning(f"Failed to get mesh agents: {e}")

        # Format agent list
        if not all_agents:
            response_text = "No agents are currently available on the network."
        else:
            response_lines = ["**Available Agents on Astraeus Network:**\n"]
            for agent in all_agents:
                caps = ", ".join(agent["capabilities"][:3]) if agent["capabilities"] else "General AI"
                response_lines.append(
                    f"• **{agent['name']}** ({agent['type']})\n"
                    f"  └─ {agent['description']}\n"
                    f"  └─ Capabilities: {caps}\n"
                )
            response_text = "\n".join(response_lines)
            response_text += f"\n\n*Total: {len(all_agents)} agents available*"

        return {
            "type": "agent_list",
            "agents": all_agents,
            "result": response_text
        }

    async def detect_intent(self, query: str) -> Dict[str, Any]:
        """
        Use Groq AI to detect user intent

        Returns:
            {
                "intent": "agent_discovery" | "task_execution" | "question",
                "requires_agents": bool,
                "confidence": float
            }
        """
        logger.info(f"🎯 Detecting intent for: {query[:100]}")

        system_prompt = """You are an intent classifier for an AI agent orchestration system.

Classify the user's query into ONE of these intents:
1. "agent_discovery" - User asking about available agents, capabilities, or agent details
2. "task_execution" - User requesting to perform a task (translate, code, search, etc.)
3. "question" - General question not requiring agent coordination

Examples:
- "what agents are there?" → agent_discovery
- "translate hello to spanish" → task_execution
- "search for AI news" → task_execution
- "what can you do?" → agent_discovery
- "how does this work?" → question

Respond with ONLY JSON: {"intent": "...", "requires_agents": true/false, "confidence": 0.0-1.0}"""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=100
            )

            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ Intent detected: {result['intent']} (confidence: {result['confidence']})")
            return result

        except Exception as e:
            logger.error(f"❌ Intent detection failed: {e}")
            # Default to question intent
            return {
                "intent": "question",
                "requires_agents": False,
                "confidence": 0.5
            }

    async def answer_question(self, query: str) -> str:
        """
        Use Groq to answer general questions
        """
        logger.info(f"💬 Answering question: {query[:100]}")

        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are Hermes, an AI agent orchestration assistant. Be helpful, clear, and concise."
                },
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=1024
        )

        return response.choices[0].message.content
