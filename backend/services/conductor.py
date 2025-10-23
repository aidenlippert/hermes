"""
Conductor Service - The Intelligent Agent Orchestrator

This conductor:
1. Analyzes user requests
2. Finds relevant agents from the database
3. Examines agent cards to understand requirements
4. Asks follow-up questions if information is missing
5. Coordinates agent execution with real-time updates
6. Handles price discovery and agent selection
"""

import logging
import httpx
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.agent_registry import AgentRegistry
from backend.services.llm_provider import get_llm_provider
from backend.database.models import Agent

logger = logging.getLogger(__name__)


class ConductorService:
    """
    The Conductor orchestrates multi-agent workflows with intelligence.

    It acts as the intermediary between the user and specialized agents,
    gathering requirements, coordinating execution, and synthesizing results.
    """

    @staticmethod
    async def fetch_agent_card(endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Fetch agent card from /.well-known/agent-card.json

        Args:
            endpoint: Agent endpoint URL

        Returns:
            Agent card dictionary or None if failed
        """
        try:
            agent_card_url = f"{endpoint}/.well-known/agent-card.json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(agent_card_url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch agent card from {endpoint}: {e}")
            return None

    @staticmethod
    async def analyze_information_requirements(
        user_query: str,
        agent_cards: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze what information is needed to execute the user's request.

        This examines agent cards to understand required inputs and determines
        if we have enough information or need to ask follow-up questions.

        Args:
            user_query: Original user request
            agent_cards: List of agent card dictionaries
            conversation_history: Previous messages for context

        Returns:
            {
                "has_sufficient_info": bool,
                "missing_info": List[str],
                "follow_up_questions": List[str],
                "extracted_info": Dict[str, Any]
            }
        """
        llm = get_llm_provider()

        # Build analysis prompt
        agent_requirements = []
        for card in agent_cards:
            agent_name = card.get("name", "Unknown")
            skills = card.get("skills", [])
            agent_requirements.append(f"- {agent_name}: {skills}")

        agent_requirements_text = "\n".join(agent_requirements)

        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nConversation History:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                conversation_context += f"{msg['role']}: {msg['content']}\n"

        prompt = f"""You are analyzing a user's request to determine if you have enough information to proceed with agent execution.

User Request: "{user_query}"

Available Agents and Their Capabilities:
{agent_requirements_text}
{conversation_context}

Analyze the request and determine:

1. For TRAVEL requests specifically, check if you have:
   - Destination (where are they going?)
   - Departure location (where are they leaving from?)
   - Travel dates (when are they going and returning?)
   - Number of travelers (how many people?)
   - Budget/price range (what's their budget?)
   - Special requirements (dietary restrictions, accessibility needs, activity preferences, etc.)

2. What information is EXPLICITLY provided in the user's request or conversation history?

3. What CRITICAL information is missing that prevents agent execution?

4. What follow-up questions should we ask to gather missing information?

Respond in JSON format:
{{
    "has_sufficient_info": false,
    "missing_info": ["departure_location", "travel_dates", "number_of_travelers", "budget"],
    "follow_up_questions": [
        "Where will you be departing from?",
        "What are your travel dates?",
        "How many people will be traveling?",
        "What's your budget for this trip?"
    ],
    "extracted_info": {{
        "destination": "extracted value or null"
    }}
}}

Be conversational and friendly in your follow-up questions. Keep them concise and grouped logically."""

        try:
            response = await llm.chat_completion([
                {"role": "user", "content": prompt}
            ])

            # Parse JSON from response
            import json
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)

            logger.info(f"📋 Information analysis complete")
            logger.info(f"   Sufficient info: {result.get('has_sufficient_info', False)}")
            logger.info(f"   Missing: {result.get('missing_info', [])}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to analyze information requirements: {e}")
            return {
                "has_sufficient_info": False,
                "missing_info": ["unknown"],
                "follow_up_questions": ["Could you provide more details about your request?"],
                "extracted_info": {}
            }

    @staticmethod
    async def discover_agents(
        db: AsyncSession,
        user_query: str,
        parsed_intent: Dict[str, Any]
    ) -> List[Agent]:
        """
        Discover relevant agents for the user's request.

        Uses capability matching and semantic search to find agents.

        Args:
            db: Database session
            user_query: Original user request
            parsed_intent: Parsed intent from IntentParser

        Returns:
            List of relevant Agent objects
        """
        logger.info("🔍 Discovering agents...")

        # First try capability-based search
        required_capabilities = parsed_intent.get("required_capabilities", [])
        agents = []

        if required_capabilities:
            logger.info(f"   Searching by capabilities: {required_capabilities}")
            agents = await AgentRegistry.search_by_capabilities(
                db, required_capabilities, limit=10
            )

        # If no agents found, try semantic search
        if not agents:
            logger.info(f"   Trying semantic search for: '{user_query}'")
            agents = await AgentRegistry.semantic_search(db, user_query, limit=10)

        # If still no agents for travel queries, search explicitly
        if not agents and parsed_intent.get("category") == "travel":
            logger.info("   Trying explicit travel agent search...")
            agents = await AgentRegistry.semantic_search(db, "travel flight hotel restaurant", limit=10)

        logger.info(f"   ✅ Found {len(agents)} relevant agents")
        for agent in agents:
            logger.info(f"      - {agent.name}: {agent.description[:60]}...")

        return agents

    @staticmethod
    async def generate_conversational_response(
        user_query: str,
        analysis: Dict[str, Any],
        agents: List[Agent]
    ) -> str:
        """
        Generate a friendly conversational response that asks for missing information.

        Args:
            user_query: Original user request
            analysis: Information requirement analysis
            agents: Discovered agents

        Returns:
            Conversational response string
        """
        llm = get_llm_provider()

        agent_list = "\n".join([f"- {agent.name}" for agent in agents])
        follow_up_questions = analysis.get("follow_up_questions", [])
        extracted_info = analysis.get("extracted_info", {})

        prompt = f"""You are Hermes, an AI assistant that coordinates specialized travel agents to help users plan trips.

User said: "{user_query}"

You've discovered these agents that can help:
{agent_list}

You've extracted this information:
{extracted_info}

But you need to ask these follow-up questions:
{follow_up_questions}

Generate a friendly, conversational response that:
1. Acknowledges what they want to do
2. Mentions which agents you'll use to help them
3. Asks for the missing information in a natural way
4. Keep it concise and friendly

Example:
"Great! I can help you plan your trip to Cancun. I'll coordinate with FlightBooker, HotelBooker, RestaurantFinder, and EventsFinder to create the perfect itinerary.

To get started, I need a few details:
- Where will you be departing from?
- What are your travel dates?
- How many people will be traveling?
- What's your budget for this trip?
- Any dietary restrictions or special activity preferences?"

Now generate your response:"""

        try:
            response = await llm.chat_completion([
                {"role": "user", "content": prompt}
            ])
            return response.strip()
        except Exception as e:
            logger.error(f"❌ Failed to generate response: {e}")
            # Fallback to basic response
            questions = "\n".join([f"- {q}" for q in follow_up_questions])
            return f"I can help you with that! I found these agents: {agent_list}\n\nTo proceed, I need some information:\n{questions}"

    @staticmethod
    async def orchestrate_request(
        db: AsyncSession,
        user_query: str,
        parsed_intent: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Main orchestration method that coordinates the entire flow.

        This is called from the chat endpoint and handles:
        1. Agent discovery
        2. Agent card analysis
        3. Information requirement analysis
        4. Follow-up question generation OR execution

        Args:
            db: Database session
            user_query: User's request
            parsed_intent: Parsed intent
            conversation_history: Previous messages

        Returns:
            Tuple of (response_message, execution_plan or None)
            If execution_plan is None, we need more info from user
            If execution_plan is provided, we can proceed with execution
        """
        # Step 1: Discover relevant agents
        agents = await ConductorService.discover_agents(db, user_query, parsed_intent)

        if not agents:
            return (
                "I couldn't find any specialized agents to help with your request. "
                "Let me try to help you directly with what I know.",
                None
            )

        # Step 2: Fetch agent cards
        agent_cards = []
        for agent in agents:
            card = await ConductorService.fetch_agent_card(agent.endpoint)
            if card:
                agent_cards.append(card)

        if not agent_cards:
            logger.warning("⚠️ No agent cards could be fetched, proceeding without them")
            agent_cards = [
                {
                    "name": agent.name,
                    "skills": agent.capabilities,
                    "description": agent.description
                }
                for agent in agents
            ]

        # Step 3: Analyze information requirements
        analysis = await ConductorService.analyze_information_requirements(
            user_query,
            agent_cards,
            conversation_history
        )

        # Step 4: Check if we have enough information
        if not analysis.get("has_sufficient_info", False):
            # Need more information - ask follow-up questions
            response = await ConductorService.generate_conversational_response(
                user_query,
                analysis,
                agents
            )

            return (response, None)

        # Step 5: We have enough info - create execution plan
        execution_plan = {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "endpoint": agent.endpoint,
                    "capabilities": agent.capabilities
                }
                for agent in agents
            ],
            "extracted_info": analysis.get("extracted_info", {}),
            "ready_for_execution": True
        }

        return (
            f"Perfect! I have all the information I need. Let me coordinate with "
            f"{', '.join([a.name for a in agents])} to help you.",
            execution_plan
        )
