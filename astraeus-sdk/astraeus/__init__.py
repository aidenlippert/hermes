"""
ASTRAEUS SDK - Build and publish AI agents to the ASTRAEUS Network

Example:
    from astraeus import Agent, capability

    agent = Agent(
        name="DataAnalyzer",
        description="Analyzes data and generates insights",
        api_key="your_api_key"
    )

    @agent.capability("analyze_csv", cost=0.05)
    async def analyze(file_url: str) -> dict:
        # Your agent logic
        return {"summary": "..."}

    agent.serve()
"""

__version__ = "1.0.0"

from .agent import Agent, capability
from .client import AstraeusClient
from .adapters import LangChainAdapter, CrewAIAdapter
from .autonomous import AutonomousAgent
from .validator import AgentCardValidator

__all__ = [
    "Agent",
    "capability",
    "AstraeusClient",
    "LangChainAdapter",
    "CrewAIAdapter",
    "AutonomousAgent",
    "AgentCardValidator",
]
