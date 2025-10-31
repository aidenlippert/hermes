"""
Simple Example Agent

This demonstrates how to create an agent that uses the Hermes Agent SDK
to discover and collaborate with other agents.

This agent:
1. Registers itself with Hermes
2. Discovers other agents by capability
3. Calls another agent to execute a task
4. Responds to incoming requests via A2A protocol

Usage:
    python examples/simple_agent.py
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request
from pydantic import BaseModel

from backend.sdk.agent_sdk import HermesAgentSDK

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleAgent:
    """
    Example agent that demonstrates autonomous agent behavior.

    This agent can:
    - Discover other agents with specific capabilities
    - Execute tasks on other agents
    - Receive and respond to tasks from other agents
    """

    def __init__(self, agent_id: str, api_key: str, base_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.api_key = api_key
        self.base_url = base_url

        # Initialize SDK
        self.sdk = HermesAgentSDK(
            agent_id=agent_id,
            api_key=api_key,
            base_url=base_url
        )

        # Create FastAPI app for receiving requests
        self.app = FastAPI(title=f"Agent: {agent_id}")
        self._setup_routes()

        logger.info(f"✨ Agent initialized: {agent_id}")

    def _setup_routes(self):
        """Set up A2A protocol endpoints"""

        @self.app.post("/api/v1/task")
        async def receive_task(request: Request):
            """
            Handle incoming task requests from other agents.

            This follows the A2A protocol specification.
            """
            data = await request.json()
            task_description = data.get("task", "")
            context = data.get("context", {})

            logger.info(f"📥 Received task: {task_description}")

            # Process the task
            result = await self.process_task(task_description, context)

            return {
                "status": "completed",
                "result": result
            }

    async def process_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming task.

        In a real agent, this would do actual work like:
        - Generate images
        - Analyze data
        - Process text
        - Make API calls
        etc.
        """
        logger.info(f"🔄 Processing task: {task}")

        # Simulate some work
        await asyncio.sleep(1)

        # Return result
        return {
            "message": f"Task completed: {task}",
            "processed_by": self.agent_id,
            "context_received": context
        }

    async def discover_collaborators(self, capability: str):
        """
        Discover other agents that can help with a specific capability.

        Example capabilities:
        - "image_generation"
        - "data_analysis"
        - "text_summarization"
        - "code_generation"
        """
        logger.info(f"🔍 Discovering agents with capability: {capability}")

        agents = await self.sdk.discover_agents(
            capability=capability,
            min_reputation=0.5,
            available_only=True,
            limit=5
        )

        logger.info(f"✅ Found {len(agents)} agents")
        for agent in agents:
            logger.info(f"  - {agent.name}: {agent.description}")

        return agents

    async def call_agent(self, agent_id: str, task: str, context: Dict[str, Any] = None):
        """
        Execute a task on another agent.

        This demonstrates agent-to-agent collaboration.
        """
        logger.info(f"📞 Calling agent {agent_id} with task: {task}")

        result = await self.sdk.execute_agent(
            agent_id=agent_id,
            task=task,
            context=context or {}
        )

        if result.status.value == "completed":
            logger.info(f"✅ Task completed successfully")
            logger.info(f"   Result: {result.result}")
        else:
            logger.error(f"❌ Task failed: {result.error}")

        return result

    async def autonomous_workflow(self):
        """
        Example of an autonomous multi-agent workflow.

        This demonstrates:
        1. Discovering agents with needed capabilities
        2. Calling multiple agents to complete a complex task
        3. Combining results from multiple agents
        """
        logger.info("🤖 Starting autonomous workflow...")

        # Step 1: Discover image generation agents
        image_agents = await self.discover_collaborators("image_generation")

        if not image_agents:
            logger.warning("No image generation agents found")
            return

        # Step 2: Call the best image generation agent
        best_agent = image_agents[0]  # Highest reputation

        image_result = await self.call_agent(
            agent_id=best_agent.id,
            task="Generate a realistic sunset image",
            context={
                "style": "realistic",
                "size": "1024x1024",
                "format": "png"
            }
        )

        # Step 3: Discover text analysis agents
        text_agents = await self.discover_collaborators("text_analysis")

        if text_agents:
            # Step 4: Analyze the image generation result
            analysis_result = await self.call_agent(
                agent_id=text_agents[0].id,
                task="Analyze the quality of this generated image",
                context={
                    "image_data": image_result.result
                }
            )

            logger.info("🎉 Workflow completed successfully!")
            logger.info(f"   Image: {image_result.result}")
            logger.info(f"   Analysis: {analysis_result.result}")

        return {
            "image": image_result.result,
            "analysis": analysis_result.result if text_agents else None
        }

    async def close(self):
        """Clean up resources"""
        await self.sdk.close()


async def main():
    """
    Main entry point for the example agent.

    To use this:
    1. Register your agent via the Hermes API to get an agent_id and api_key
    2. Set those values below
    3. Run this script
    4. The agent will discover and call other agents autonomously
    """

    # TODO: Replace with your actual agent credentials
    # These are obtained by calling POST /api/v1/agents/register
    AGENT_ID = "your-agent-id-here"
    API_KEY = "hsk_your-api-key-here"
    BASE_URL = "http://localhost:8000"

    if AGENT_ID == "your-agent-id-here":
        logger.error("❌ Please register your agent first and update AGENT_ID and API_KEY")
        logger.info("   1. Start the Hermes server")
        logger.info("   2. Create a user account")
        logger.info("   3. Call POST /api/v1/agents/register to register your agent")
        logger.info("   4. Update this script with your agent_id and api_key")
        return

    # Create agent
    agent = SimpleAgent(
        agent_id=AGENT_ID,
        api_key=API_KEY,
        base_url=BASE_URL
    )

    try:
        # Run autonomous workflow
        await agent.autonomous_workflow()

        # Keep agent running to receive requests
        logger.info("🎧 Agent is now listening for incoming requests...")
        logger.info("   Press Ctrl+C to stop")

        # In production, you'd run the FastAPI app with uvicorn:
        # uvicorn examples.simple_agent:app --host 0.0.0.0 --port 8001

        # For this example, just keep it alive
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("👋 Shutting down agent...")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
