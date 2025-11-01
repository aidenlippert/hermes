"""
Core Agent class for ASTRAEUS SDK
"""

import asyncio
import uuid
from typing import Callable, Dict, Any, Optional, List
from functools import wraps
import inspect

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn


def capability(name: str, cost: float = 0.0, description: str = "", timeout: int = 30):
    """
    Decorator to mark a function as an agent capability

    Example:
        @agent.capability("translate", cost=0.02, description="Translate text")
        async def translate_text(text: str, target_lang: str) -> dict:
            return {"translation": translated}
    """
    def decorator(func):
        func._is_capability = True
        func._capability_name = name
        func._capability_cost = cost
        func._capability_description = description or func.__doc__
        func._capability_timeout = timeout
        return func
    return decorator


class Agent:
    """
    ASTRAEUS Agent - Publish your AI agent to the network

    Example:
        agent = Agent(
            name="DataAnalyzer",
            description="Analyze datasets",
            api_key="astraeus_xxxxx"
        )

        @agent.capability("analyze_csv", cost=0.05)
        async def analyze(file_url: str) -> dict:
            # Your logic here
            return {"summary": "..."}

        agent.serve(host="0.0.0.0", port=8000)
    """

    def __init__(
        self,
        name: str,
        description: str,
        api_key: str,
        owner: str = "anonymous",
        version: str = "1.0.0",
        astraeus_url: str = "https://web-production-3df46.up.railway.app"
    ):
        self.name = name
        self.description = description
        self.api_key = api_key
        self.owner = owner
        self.version = version
        self.astraeus_url = astraeus_url
        self.agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        self.capabilities: Dict[str, Callable] = {}
        self.app = FastAPI(title=self.name, description=self.description)

        self._setup_routes()

    def capability(self, name: str, cost: float = 0.0, description: str = "", timeout: int = 30):
        """Decorator to register capability"""
        def decorator(func):
            # Store capability
            self.capabilities[name] = {
                "function": func,
                "cost": cost,
                "description": description or func.__doc__ or "",
                "timeout": timeout
            }

            # Mark function
            func._is_capability = True
            func._capability_name = name

            return func
        return decorator

    def _setup_routes(self):
        """Setup FastAPI routes for A2A Protocol"""

        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            """A2A Protocol: Agent Card discovery"""
            return {
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "agent_id": self.agent_id,
                "capabilities": [
                    {
                        "name": name,
                        "description": cap["description"],
                        "cost_per_call": cap["cost"],
                        "timeout": cap["timeout"]
                    }
                    for name, cap in self.capabilities.items()
                ],
                "endpoint": f"http://localhost:8000/execute",
                "protocol": "A2A",
                "supported_modalities": ["text"]
            }

        @self.app.post("/execute")
        async def execute_capability(request: Request):
            """Execute agent capability"""
            data = await request.json()

            capability_name = data.get("capability")
            input_data = data.get("input", {})
            task_id = data.get("task_id", str(uuid.uuid4()))

            if capability_name not in self.capabilities:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": f"Capability '{capability_name}' not found",
                        "available": list(self.capabilities.keys())
                    }
                )

            try:
                # Execute capability
                cap = self.capabilities[capability_name]
                func = cap["function"]

                # Call function
                if inspect.iscoroutinefunction(func):
                    result = await func(**input_data)
                else:
                    result = func(**input_data)

                return {
                    "success": True,
                    "task_id": task_id,
                    "capability": capability_name,
                    "result": result,
                    "cost": cap["cost"],
                    "agent_id": self.agent_id
                }

            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "task_id": task_id,
                        "error": str(e),
                        "capability": capability_name
                    }
                )

        @self.app.get("/health")
        async def health():
            """Health check"""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "capabilities": len(self.capabilities)
            }

    async def register_to_network(self):
        """Register this agent to ASTRAEUS network"""
        import httpx

        agent_card = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [
                {
                    "name": name,
                    "description": cap["description"],
                    "confidence": 0.9,
                    "cost": cap["cost"],
                    "latency": cap["timeout"]
                }
                for name, cap in self.capabilities.items()
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.astraeus_url}/api/v1/mesh/agents/register",
                json={
                    "name": self.name,
                    "owner": self.owner,
                    "capabilities": agent_card["capabilities"]
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                self.agent_id = data.get("agent_id", self.agent_id)
                print(f"✅ Agent registered: {self.name} ({self.agent_id})")
                return data
            else:
                print(f"❌ Registration failed: {response.text}")
                return None

    def serve(self, host: str = "0.0.0.0", port: int = 8000, register: bool = True):
        """
        Start the agent server

        Args:
            host: Host to bind to
            port: Port to listen on
            register: Auto-register to ASTRAEUS network
        """
        print(f"\n🚀 Starting {self.name} agent...")
        print(f"📍 Endpoint: http://{host}:{port}")
        print(f"🔧 Capabilities: {len(self.capabilities)}")

        for name, cap in self.capabilities.items():
            print(f"   - {name}: ${cap['cost']} per call")

        # Register to network
        if register:
            try:
                asyncio.run(self.register_to_network())
            except Exception as e:
                print(f"⚠️  Registration failed: {e}")
                print(f"   Agent will run locally only")

        print(f"\n✨ Agent ready! Try:")
        print(f"   curl -X POST http://{host}:{port}/execute \\")
        print(f'        -d \'{{"capability": "{list(self.capabilities.keys())[0]}", "input": {{}}}}\'')
        print()

        uvicorn.run(self.app, host=host, port=port, log_level="info")
