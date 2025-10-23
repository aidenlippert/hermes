"""
Intent Parser - Understanding What Users REALLY Want

Uses Gemini to parse natural language into structured intent.

Input: "Book me a flight to NYC and a hotel for 3 nights"
Output: {
    "intent": "travel_booking",
    "entities": {
        "destination": "NYC",
        "services": ["flight", "hotel"],
        "duration": "3 nights"
    },
    "required_capabilities": ["flight_search", "hotel_booking"],
    "complexity": 0.7
}
"""

import google.generativeai as genai
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """High-level categories of user intent"""
    CODE_GENERATION = "code_generation"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    RESEARCH = "research"
    TRAVEL = "travel"
    COMMUNICATION = "communication"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Structured representation of user intent"""
    original_query: str
    category: IntentCategory
    entities: Dict[str, Any]
    required_capabilities: List[str]
    complexity: float  # 0.0 (simple) to 1.0 (very complex)
    confidence: float  # 0.0 (uncertain) to 1.0 (very confident)
    suggested_agents: List[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "category": self.category.value,
            "entities": self.entities,
            "required_capabilities": self.required_capabilities,
            "complexity": self.complexity,
            "confidence": self.confidence,
            "suggested_agents": self.suggested_agents or [],
            "metadata": self.metadata or {}
        }


class IntentParser:
    """
    Gemini-powered intent parser.

    This is the FIRST step in Hermes orchestration:
    1. User says something in natural language
    2. We figure out what they REALLY want
    3. We identify which capabilities are needed
    4. We pass this to the Planner
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize intent parser with Gemini.

        Args:
            api_key: Google AI Studio API key
            model_name: Which Gemini model to use (flash is fast & cheap)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        # System prompt that defines how to parse intent
        self.system_prompt = """You are an intent parser for Hermes, an AI agent orchestrator.

Your job: Parse user requests into structured JSON that identifies:
1. What they want to accomplish (intent category)
2. Key entities (destinations, dates, topics, etc.)
3. What capabilities are needed (search, write, analyze, etc.)
4. Complexity (0.0 = simple, 1.0 = very complex multi-step)
5. Confidence (0.0 = unclear, 1.0 = crystal clear)

Intent Categories:
- code_generation: Write, debug, or explain code
- content_creation: Write articles, blogs, social posts
- data_analysis: Analyze data, create insights, visualize
- automation: Schedule, book, automate tasks
- research: Find information, summarize, investigate
- travel: Book flights, hotels, plan trips
- communication: Send emails, messages, make calls
- unknown: Can't determine intent

Capabilities (what agents can do):
- code_write, code_debug, code_review, code_test
- content_write, content_edit, content_translate
- data_analyze, data_visualize, data_clean
- schedule_meeting, book_flight, book_hotel
- search_web, summarize_text, answer_question
- send_email, send_message

Response Format (JSON only, no markdown):
{
    "category": "intent_category",
    "entities": {
        "key1": "value1",
        "key2": "value2"
    },
    "required_capabilities": ["capability1", "capability2"],
    "complexity": 0.5,
    "confidence": 0.9,
    "reasoning": "Brief explanation of your analysis"
}

Examples:

Input: "Write me a Python function to calculate fibonacci"
Output:
{
    "category": "code_generation",
    "entities": {
        "language": "Python",
        "task": "function",
        "topic": "fibonacci"
    },
    "required_capabilities": ["code_write"],
    "complexity": 0.3,
    "confidence": 1.0,
    "reasoning": "Single, well-defined coding task"
}

Input: "Book me a flight to NYC tomorrow and find a hotel near Times Square for 3 nights"
Output:
{
    "category": "travel",
    "entities": {
        "destination": "NYC",
        "flight_date": "tomorrow",
        "hotel_location": "Times Square",
        "duration": "3 nights"
    },
    "required_capabilities": ["book_flight", "book_hotel"],
    "complexity": 0.7,
    "confidence": 0.9,
    "reasoning": "Multi-step travel booking with dependencies"
}

Now parse the user's request."""

        logger.info(f"✅ Intent Parser initialized with {model_name}")

    async def parse(self, user_query: str) -> ParsedIntent:
        """
        Parse user query into structured intent.

        Args:
            user_query: What the user said

        Returns:
            ParsedIntent with all the structured information
        """
        logger.info(f"🧠 Parsing intent: '{user_query[:100]}...'")

        try:
            # Call Gemini
            response = self.model.generate_content(
                f"{self.system_prompt}\n\nUser Query: {user_query}"
            )

            # Parse JSON from response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            result = json.loads(response_text)

            # Create ParsedIntent
            intent = ParsedIntent(
                original_query=user_query,
                category=IntentCategory(result.get("category", "unknown")),
                entities=result.get("entities", {}),
                required_capabilities=result.get("required_capabilities", []),
                complexity=float(result.get("complexity", 0.5)),
                confidence=float(result.get("confidence", 0.5)),
                metadata={
                    "reasoning": result.get("reasoning", ""),
                    "model": self.model.model_name
                }
            )

            logger.info(f"✅ Intent parsed: {intent.category.value}")
            logger.info(f"   Capabilities needed: {intent.required_capabilities}")
            logger.info(f"   Complexity: {intent.complexity:.2f}")
            logger.info(f"   Confidence: {intent.confidence:.2f}")

            return intent

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from Gemini: {e}")
            logger.error(f"   Raw response: {response_text}")

            # Return a fallback intent
            return ParsedIntent(
                original_query=user_query,
                category=IntentCategory.UNKNOWN,
                entities={},
                required_capabilities=[],
                complexity=0.5,
                confidence=0.0,
                metadata={"error": "JSON parse failed", "raw": response_text}
            )

        except Exception as e:
            logger.error(f"❌ Intent parsing failed: {e}")

            # Return error intent
            return ParsedIntent(
                original_query=user_query,
                category=IntentCategory.UNKNOWN,
                entities={},
                required_capabilities=[],
                complexity=0.5,
                confidence=0.0,
                metadata={"error": str(e)}
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test_intent_parser():
        """Test the intent parser"""

        # You need to set your API key
        api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")

        if not api_key or api_key == "your_key_here":
            print("❌ Set GOOGLE_API_KEY environment variable")
            return

        parser = IntentParser(api_key)

        print("\n" + "="*60)
        print("🧪 Testing Intent Parser")
        print("="*60)

        test_queries = [
            "Write me a Python function to calculate fibonacci",
            "Book a flight to NYC and a hotel for 3 nights",
            "Analyze this sales data and create a visualization",
            "Help me debug this code",
            "Something random and unclear"
        ]

        for query in test_queries:
            print(f"\n📝 Query: {query}")
            intent = await parser.parse(query)
            print(f"   Category: {intent.category.value}")
            print(f"   Capabilities: {intent.required_capabilities}")
            print(f"   Complexity: {intent.complexity:.2f}")
            print(f"   Confidence: {intent.confidence:.2f}")
            if intent.metadata.get("reasoning"):
                print(f"   Reasoning: {intent.metadata['reasoning']}")

        print("\n✅ Intent Parser is working!")

    asyncio.run(test_intent_parser())
