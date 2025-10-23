"""
Multi-Agent Planner - The Orchestration Brain

Takes parsed intent and creates an execution plan using available agents.

Input: ParsedIntent + Available Agents
Output: ExecutionPlan (ordered steps, which agents to use, dependencies)

This is where the magic happens - figuring out HOW to coordinate
multiple agents to accomplish complex tasks.
"""

import google.generativeai as genai
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a single step in the plan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """
    A single step in the execution plan.

    Steps are executed in order, with optional dependencies.
    """
    step_number: int
    agent_name: str
    agent_endpoint: str
    task_description: str
    depends_on: List[int] = field(default_factory=list)  # Step numbers
    input_from_step: Optional[int] = None  # Get input from this step's output
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "agent_name": self.agent_name,
            "agent_endpoint": self.agent_endpoint,
            "task_description": self.task_description,
            "depends_on": self.depends_on,
            "input_from_step": self.input_from_step,
            "status": self.status.value,
            "result": self.result,
            "error": self.error
        }


@dataclass
class ExecutionPlan:
    """
    Complete execution plan for a user request.

    This is the "sheet music" for the conductor.
    """
    original_query: str
    steps: List[ExecutionStep]
    estimated_duration: float  # seconds
    total_cost: float = 0.0  # estimated cost in USD
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "steps": [step.to_dict() for step in self.steps],
            "estimated_duration": self.estimated_duration,
            "total_cost": self.total_cost,
            "metadata": self.metadata
        }

    def get_next_step(self) -> Optional[ExecutionStep]:
        """Get the next step that's ready to execute"""
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue

            # Check if dependencies are met
            if step.depends_on:
                all_deps_met = all(
                    self.steps[dep_num - 1].status == StepStatus.COMPLETED
                    for dep_num in step.depends_on
                )
                if not all_deps_met:
                    continue

            return step

        return None


class WorkflowPlanner:
    """
    Gemini-powered workflow planner.

    This is STEP 2 in Hermes orchestration:
    1. Intent Parser figures out WHAT user wants
    2. Workflow Planner figures out HOW to do it (THIS)
    3. Executor runs the plan
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize planner with Gemini.

        Args:
            api_key: Google AI Studio API key
            model_name: Which Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        # System prompt for planning
        self.system_prompt = """You are a multi-agent workflow planner for Hermes.

Your job: Create an optimal execution plan using available agents.

You will receive:
1. User's request
2. Parsed intent (what they want)
3. Available agents (what each can do)

You must create:
1. Ordered list of steps
2. Which agent to use for each step
3. Dependencies between steps
4. Task description for each agent

Rules:
- Steps execute in order (unless they have no dependencies)
- Each step uses ONE agent
- Steps can depend on previous steps' outputs
- Optimize for: speed, cost, reliability
- If multiple agents can do something, pick the best one
- If no suitable agent exists, create a step saying "Need agent for X"

Response Format (JSON only):
{
    "steps": [
        {
            "step_number": 1,
            "agent_name": "AgentName",
            "task_description": "Specific instruction for this agent",
            "depends_on": [],
            "input_from_step": null
        }
    ],
    "estimated_duration": 30.0,
    "reasoning": "Why this plan is optimal"
}

Example:

User: "Book me a flight to NYC and a hotel near Times Square"

Available Agents:
- FlightBooker: Can search and book flights
- HotelFinder: Can search hotels by location
- PaymentProcessor: Can handle payments

Plan:
{
    "steps": [
        {
            "step_number": 1,
            "agent_name": "FlightBooker",
            "task_description": "Search for flights to NYC for [dates from user]",
            "depends_on": [],
            "input_from_step": null
        },
        {
            "step_number": 2,
            "agent_name": "HotelFinder",
            "task_description": "Find hotels near Times Square, NYC",
            "depends_on": [],
            "input_from_step": null
        },
        {
            "step_number": 3,
            "agent_name": "PaymentProcessor",
            "task_description": "Process payment for flight and hotel",
            "depends_on": [1, 2],
            "input_from_step": null
        }
    ],
    "estimated_duration": 45.0,
    "reasoning": "Steps 1 and 2 can run in parallel. Step 3 waits for both."
}

Now create a plan."""

        logger.info(f"✅ Workflow Planner initialized with {model_name}")

    async def create_plan(
        self,
        user_query: str,
        parsed_intent: Dict[str, Any],
        available_agents: List[Dict[str, Any]]
    ) -> ExecutionPlan:
        """
        Create an execution plan.

        Args:
            user_query: Original user request
            parsed_intent: Output from IntentParser
            available_agents: List of available agents with their capabilities

        Returns:
            ExecutionPlan ready to execute
        """
        logger.info(f"📋 Creating execution plan for: '{user_query[:100]}...'")
        logger.info(f"   Available agents: {len(available_agents)}")

        # Build the planning prompt
        planning_context = f"""User Request: {user_query}

Parsed Intent:
{json.dumps(parsed_intent, indent=2)}

Available Agents:
{json.dumps(available_agents, indent=2)}

Create an optimal execution plan."""

        try:
            # Call Gemini
            response = self.model.generate_content(
                f"{self.system_prompt}\n\n{planning_context}"
            )

            # Parse response
            response_text = response.text.strip()

            # Remove markdown if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            plan_data = json.loads(response_text)

            # Create ExecutionSteps
            steps = []
            for step_data in plan_data.get("steps", []):
                # Find the agent's endpoint
                agent_name = step_data["agent_name"]
                agent_endpoint = self._find_agent_endpoint(agent_name, available_agents)

                step = ExecutionStep(
                    step_number=step_data["step_number"],
                    agent_name=agent_name,
                    agent_endpoint=agent_endpoint or "UNKNOWN",
                    task_description=step_data["task_description"],
                    depends_on=step_data.get("depends_on", []),
                    input_from_step=step_data.get("input_from_step")
                )
                steps.append(step)

            # Create ExecutionPlan
            plan = ExecutionPlan(
                original_query=user_query,
                steps=steps,
                estimated_duration=float(plan_data.get("estimated_duration", 60.0)),
                metadata={
                    "reasoning": plan_data.get("reasoning", ""),
                    "model": self.model.model_name,
                    "agents_considered": len(available_agents)
                }
            )

            logger.info(f"✅ Plan created with {len(steps)} steps")
            logger.info(f"   Estimated duration: {plan.estimated_duration}s")
            if plan.metadata.get("reasoning"):
                logger.info(f"   Reasoning: {plan.metadata['reasoning']}")

            return plan

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse plan JSON: {e}")
            logger.error(f"   Raw response: {response_text}")

            # Return a fallback plan
            return self._create_fallback_plan(user_query, parsed_intent)

        except Exception as e:
            logger.error(f"❌ Planning failed: {e}")
            return self._create_fallback_plan(user_query, parsed_intent)

    def _find_agent_endpoint(
        self,
        agent_name: str,
        available_agents: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Find an agent's endpoint by name"""
        for agent in available_agents:
            if agent.get("name") == agent_name:
                return agent.get("endpoint")
        return None

    def _create_fallback_plan(
        self,
        user_query: str,
        parsed_intent: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create a simple fallback plan when Gemini fails.

        This ensures we always return something executable.
        """
        logger.warning("⚠️ Creating fallback plan")

        # Simple single-step plan
        step = ExecutionStep(
            step_number=1,
            agent_name="GenericAssistant",
            agent_endpoint="UNKNOWN",
            task_description=user_query,
            depends_on=[],
            input_from_step=None
        )

        return ExecutionPlan(
            original_query=user_query,
            steps=[step],
            estimated_duration=30.0,
            metadata={
                "fallback": True,
                "reason": "Planning failed, using generic approach"
            }
        )


if __name__ == "__main__":
    import asyncio
    import os

    async def test_planner():
        """Test the workflow planner"""

        api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")

        if not api_key or api_key == "your_key_here":
            print("❌ Set GOOGLE_API_KEY environment variable")
            return

        planner = WorkflowPlanner(api_key)

        print("\n" + "="*60)
        print("🧪 Testing Workflow Planner")
        print("="*60)

        # Mock data
        user_query = "Book me a flight to NYC tomorrow and find a hotel near Times Square"

        parsed_intent = {
            "category": "travel",
            "entities": {
                "destination": "NYC",
                "flight_date": "tomorrow",
                "hotel_location": "Times Square"
            },
            "required_capabilities": ["book_flight", "book_hotel"],
            "complexity": 0.7,
            "confidence": 0.9
        }

        available_agents = [
            {
                "name": "FlightBooker",
                "endpoint": "http://localhost:10001",
                "capabilities": ["search_flight", "book_flight"],
                "description": "Searches and books flights"
            },
            {
                "name": "HotelFinder",
                "endpoint": "http://localhost:10002",
                "capabilities": ["search_hotel", "book_hotel"],
                "description": "Finds and books hotels"
            },
            {
                "name": "PaymentProcessor",
                "endpoint": "http://localhost:10003",
                "capabilities": ["process_payment"],
                "description": "Handles payments"
            }
        ]

        print(f"\n📝 Query: {user_query}")
        print(f"\n🤖 Available agents: {[a['name'] for a in available_agents]}")

        plan = await planner.create_plan(user_query, parsed_intent, available_agents)

        print(f"\n✅ Plan created with {len(plan.steps)} steps:")
        for step in plan.steps:
            print(f"\n   Step {step.step_number}: {step.agent_name}")
            print(f"      Task: {step.task_description}")
            if step.depends_on:
                print(f"      Depends on: {step.depends_on}")

        print(f"\n⏱️ Estimated duration: {plan.estimated_duration}s")
        if plan.metadata.get("reasoning"):
            print(f"💡 Reasoning: {plan.metadata['reasoning']}")

    asyncio.run(test_planner())
