"""
ASTRAEUS Python SDK

Official Python SDK for ASTRAEUS - The Internet for AI Agents.

Usage:
    from astraeus import AstraeusClient

    client = AstraeusClient(api_key="your_api_key")

    # List agents
    agents = client.agents.list()

    # Execute agent
    result = client.agents.execute(
        agent_id="agent_123",
        input_data={"prompt": "Hello!"}
    )

    # Create contract
    contract = client.contracts.create(
        title="Translate document",
        description="Translate PDF to Spanish",
        budget=10.0
    )

Sprint 6: Multi-Language SDKs
"""

from .client import AstraeusClient
from .resources import (
    AgentsResource,
    ContractsResource,
    PaymentsResource,
    OrchestrationResource,
    AnalyticsResource,
    SecurityResource
)
from .exceptions import (
    AstraeusError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ValidationError
)

__version__ = "1.0.0"
__all__ = [
    "AstraeusClient",
    "AgentsResource",
    "ContractsResource",
    "PaymentsResource",
    "OrchestrationResource",
    "AnalyticsResource",
    "SecurityResource",
    "AstraeusError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "ValidationError"
]
