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
        logger.info("📋 Analyzing information requirements...")
        logger.info(f"   Current query: '{user_query[:100]}'")
        if conversation_history:
            logger.info(f"   Conversation history: {len(conversation_history)} messages")
            for i, msg in enumerate(conversation_history[-3:]):
                logger.info(f"      [{i}] {msg.get('role')}: {msg.get('content', '')[:80]}")

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

        prompt = f"""You are analyzing if we have enough information to book a trip.

Current Request: "{user_query}"
{conversation_context}

EXTRACTION RULES:
1. Look in BOTH current request AND conversation history - MERGE information across messages
2. "just me" = 1 traveler, "solo" = 1 traveler, "two of us" = 2
3. "sfo" = San Francisco, "lax" = Los Angeles, "san" = likely San Diego/San Francisco (ask if unclear)
4. "25th to 31st" = valid dates, "cot" = "oct" (typo), "dec" = December
5. "$1000" or "1000 dollars" = valid budget
6. FIX TYPOS: "cot 25" → "October 25", "nov 3rd" → "November 3rd"
7. INCOMPLETE CITIES: "san" alone could be San Diego, San Francisco, or San Jose - ASK FOR CLARIFICATION
8. If user sends JUST a city name (like "san diego") after being asked a question, UPDATE the previous incomplete field

EXAMPLES:
❌ WRONG: User said "departing from sfo" → you say "missing departure_location"
✅ RIGHT: User said "departing from sfo" → "departure_location": "San Francisco"

❌ WRONG: User said "from san to seattle" → "departure_location": "San"
✅ RIGHT: User said "from san to seattle" → ASK "Did you mean San Diego, San Francisco, or San Jose?"

❌ WRONG: Previous msg: "from san", Current msg: "san diego" → you ignore context
✅ RIGHT: Previous msg: "from san", Current msg: "san diego" → UPDATE "departure_location": "San Diego"

❌ WRONG: User said "just me" → you say "missing num_travelers"
✅ RIGHT: User said "just me" → "num_travelers": 1

❌ WRONG: User said "1000 dollars usd" → you say "missing budget"
✅ RIGHT: User said "1000 dollars usd" → "budget": "1000 USD"

❌ WRONG: User said "cot 25 to 31" → "travel_dates": "cot 25 to 31"
✅ RIGHT: User said "cot 25 to 31" → "travel_dates": "October 25 to 31"

Now extract from the ENTIRE conversation history:
- destination: city/country name (ask if ambiguous like "san")
- departure_location: where user is flying FROM (ask if ambiguous like "san")
- travel_dates: any dates mentioned (ask if invalid/unclear)
- num_travelers: number of people ("just me"=1, "3 people"=3, "solo"=1)
- budget: dollar amount mentioned

Return JSON:
{{
    "has_sufficient_info": true/false,
    "missing_info": ["only if TRULY missing"],
    "follow_up_questions": ["only for missing"],
    "extracted_info": {{
        "destination": "extracted city",
        "departure_location": "extracted city",
        "travel_dates": "extracted dates",
        "num_travelers": number,
        "budget": "extracted budget"
    }}
}}

If user provided ALL 5 items → set "has_sufficient_info": true"""

        try:
            response = await llm.chat_completion([
                {"role": "user", "content": prompt}
            ])

            # Parse JSON from response - handle various formats
            import json
            import re

            response_text = response.strip()
            logger.info(f"   Raw LLM response: {response_text[:200]}...")

            # Remove markdown code blocks
            if "```" in response_text:
                # Extract content between ```json and ``` or between ``` and ```
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if match:
                    response_text = match.group(1)
                else:
                    # Fallback: take content after first ```
                    parts = response_text.split("```")
                    if len(parts) >= 2:
                        response_text = parts[1]
                        if response_text.startswith("json"):
                            response_text = response_text[4:]

            # Try to find JSON object if there's surrounding text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            response_text = response_text.strip()
            logger.info(f"   Cleaned JSON: {response_text[:200]}...")

            result = json.loads(response_text)

            logger.info(f"📋 Information analysis complete")
            logger.info(f"   Sufficient info: {result.get('has_sufficient_info', False)}")
            logger.info(f"   Missing: {result.get('missing_info', [])}")
            logger.info(f"   Extracted: {result.get('extracted_info', {})}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to analyze information requirements: {e}")
            logger.error(f"   Response was: {response_text if 'response_text' in locals() else 'N/A'}")
            return {
                "has_sufficient_info": False,
                "missing_info": ["departure_location", "travel_dates", "num_travelers", "budget"],
                "follow_up_questions": [
                    "Where will you be departing from?",
                    "What are your travel dates?",
                    "How many people will be traveling?",
                    "What's your budget for this trip?"
                ],
                "extracted_info": {"destination": "Cancun"}
            }

    @staticmethod
    async def discover_agents(
        db: AsyncSession,
        user_query: str,
        parsed_intent: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Agent]:
        """
        Discover relevant agents for the user's request.

        Uses capability matching and semantic search to find agents.
        Checks conversation history to maintain context.

        Args:
            db: Database session
            user_query: Original user request
            parsed_intent: Parsed intent from IntentParser
            conversation_history: Previous conversation messages

        Returns:
            List of relevant Agent objects
        """
        logger.info("🔍 Discovering agents...")

        # Check if this is a continuation of a previous travel request
        is_travel_continuation = False
        if conversation_history:
            # Look at recent messages to see if we're in a travel conversation
            recent_messages = conversation_history[-5:]
            for msg in recent_messages:
                content_lower = msg.get("content", "").lower()
                if any(keyword in content_lower for keyword in ["trip", "travel", "flight", "hotel", "book", "cancun", "vacation"]):
                    is_travel_continuation = True
                    logger.info("   📍 Detected travel conversation continuation")
                    break

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

        # If still no agents and this is a travel conversation, search for travel agents
        if not agents and (parsed_intent.get("category") == "travel" or is_travel_continuation):
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
        agents = await ConductorService.discover_agents(db, user_query, parsed_intent, conversation_history)

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
                    "capabilities": agent.capabilities,
                    "description": agent.description
                }
                for agent in agents
            ],
            "extracted_info": analysis.get("extracted_info", {}),
            "ready_for_execution": True,
            "requires_approval": True  # User must approve agents before execution
        }

        extracted = analysis.get("extracted_info", {})
        info_summary = []
        if extracted.get("destination"):
            info_summary.append(f"📍 Destination: {extracted['destination']}")
        if extracted.get("departure_location"):
            info_summary.append(f"🛫 Departing from: {extracted['departure_location']}")
        if extracted.get("travel_dates"):
            info_summary.append(f"📅 Dates: {extracted['travel_dates']}")
        if extracted.get("num_travelers"):
            info_summary.append(f"👥 Travelers: {extracted['num_travelers']}")
        if extracted.get("budget"):
            info_summary.append(f"💰 Budget: {extracted['budget']}")

        summary_text = "\n".join(info_summary) if info_summary else "Planning your trip"

        return (
            f"Perfect! I found {len(agents)} specialized agents to help plan your trip:\n\n"
            f"{summary_text}\n\n"
            f"I'll use {', '.join([a.name for a in agents])} to find the best options. "
            f"Review the agents below and let me know if you'd like to proceed!",
            execution_plan
        )
