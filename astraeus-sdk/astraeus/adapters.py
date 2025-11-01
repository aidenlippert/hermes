"""
Framework Adapters - Wrap existing agents from LangChain, CrewAI, etc.
"""

import asyncio
import uuid
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx


class LangChainAdapter:
    """
    Adapter for LangChain agents to publish on ASTRAEUS network

    Example:
        from langchain.agents import create_openai_agent
        from langchain.tools import Tool
        from astraeus.adapters import LangChainAdapter

        # Your existing LangChain agent
        tools = [Tool(name="search", func=search_fn)]
        langchain_agent = create_openai_agent(tools=tools)

        # Wrap for ASTRAEUS
        astraeus_agent = LangChainAdapter(
            agent=langchain_agent,
            name="LangChain-Assistant",
            description="AI assistant powered by LangChain",
            api_key="astraeus_xxxxx",
            cost_per_call=0.03
        )

        astraeus_agent.serve(port=8000)
    """

    def __init__(
        self,
        agent: Any,
        name: str,
        description: str,
        api_key: str,
        cost_per_call: float = 0.0,
        owner: str = "anonymous",
        version: str = "1.0.0",
        astraeus_url: str = "https://web-production-3df46.up.railway.app"
    ):
        self.agent = agent
        self.name = name
        self.description = description
        self.api_key = api_key
        self.cost_per_call = cost_per_call
        self.owner = owner
        self.version = version
        self.astraeus_url = astraeus_url
        self.agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        self.app = FastAPI(title=self.name, description=self.description)
        self._setup_routes()

    def _setup_routes(self):
        """Setup A2A Protocol routes"""

        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            """A2A Protocol: Agent Card"""
            return {
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "agent_id": self.agent_id,
                "capabilities": [
                    {
                        "name": "execute",
                        "description": "Execute LangChain agent with query",
                        "cost_per_call": self.cost_per_call,
                        "timeout": 60
                    }
                ],
                "endpoint": f"http://localhost:8000/execute",
                "protocol": "A2A",
                "framework": "langchain",
                "supported_modalities": ["text"]
            }

        @self.app.post("/execute")
        async def execute_capability(request: Request):
            """Execute LangChain agent"""
            data = await request.json()

            capability = data.get("capability")
            input_data = data.get("input", {})
            task_id = data.get("task_id", str(uuid.uuid4()))

            if capability != "execute":
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": f"Capability '{capability}' not found. Use 'execute'.",
                        "available": ["execute"]
                    }
                )

            try:
                query = input_data.get("query") or input_data.get("input")

                if not query:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": "Missing 'query' or 'input' in request"
                        }
                    )

                if asyncio.iscoroutinefunction(self.agent.invoke):
                    result = await self.agent.invoke(query)
                else:
                    result = await asyncio.to_thread(self.agent.invoke, query)

                return {
                    "success": True,
                    "task_id": task_id,
                    "capability": capability,
                    "result": {"output": result},
                    "cost": self.cost_per_call,
                    "agent_id": self.agent_id
                }

            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "task_id": task_id,
                        "error": str(e),
                        "capability": capability
                    }
                )

        @self.app.get("/health")
        async def health():
            """Health check"""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "framework": "langchain"
            }

    async def register_to_network(self):
        """Register to ASTRAEUS network"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.astraeus_url}/api/v1/mesh/agents/register",
                json={
                    "name": self.name,
                    "owner": self.owner,
                    "framework": "langchain",
                    "capabilities": [
                        {
                            "name": "execute",
                            "description": self.description,
                            "confidence": 0.9,
                            "cost": self.cost_per_call,
                            "latency": 60
                        }
                    ]
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                self.agent_id = data.get("agent_id", self.agent_id)
                print(f"✅ LangChain agent registered: {self.name} ({self.agent_id})")
                return data
            else:
                print(f"❌ Registration failed: {response.text}")
                return None

    def serve(self, host: str = "0.0.0.0", port: int = 8000, register: bool = True):
        """Start the agent server"""
        print(f"\n🚀 Starting LangChain agent: {self.name}")
        print(f"📍 Endpoint: http://{host}:{port}")
        print(f"💰 Cost per call: ${self.cost_per_call}")

        if register:
            try:
                asyncio.run(self.register_to_network())
            except Exception as e:
                print(f"⚠️  Registration failed: {e}")
                print(f"   Agent will run locally only")

        print(f"\n✨ Agent ready! Try:")
        print(f'   curl -X POST http://{host}:{port}/execute \\')
        print(f'        -d \'{{"capability": "execute", "input": {{"query": "Hello"}}}}\'')
        print()

        uvicorn.run(self.app, host=host, port=port, log_level="info")


class CrewAIAdapter:
    """
    Adapter for CrewAI crews to publish on ASTRAEUS network

    Example:
        from crewai import Crew, Agent, Task
        from astraeus.adapters import CrewAIAdapter

        # Your existing CrewAI setup
        researcher = Agent(role="Researcher", ...)
        writer = Agent(role="Writer", ...)
        crew = Crew(agents=[researcher, writer], tasks=[...])

        # Publish to ASTRAEUS
        astraeus_crew = CrewAIAdapter(
            crew=crew,
            name="Research-Crew",
            description="Research and content creation team",
            api_key="astraeus_xxxxx",
            cost_per_call=0.15
        )

        astraeus_crew.serve(port=8001)
    """

    def __init__(
        self,
        crew: Any,
        name: str,
        description: str,
        api_key: str,
        cost_per_call: float = 0.0,
        owner: str = "anonymous",
        version: str = "1.0.0",
        astraeus_url: str = "https://web-production-3df46.up.railway.app"
    ):
        self.crew = crew
        self.name = name
        self.description = description
        self.api_key = api_key
        self.cost_per_call = cost_per_call
        self.owner = owner
        self.version = version
        self.astraeus_url = astraeus_url
        self.agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        self.app = FastAPI(title=self.name, description=self.description)
        self._setup_routes()

    def _setup_routes(self):
        """Setup A2A Protocol routes"""

        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            """A2A Protocol: Agent Card"""
            return {
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "agent_id": self.agent_id,
                "capabilities": [
                    {
                        "name": "kickoff",
                        "description": "Start crew execution with inputs",
                        "cost_per_call": self.cost_per_call,
                        "timeout": 300
                    }
                ],
                "endpoint": f"http://localhost:8001/execute",
                "protocol": "A2A",
                "framework": "crewai",
                "supported_modalities": ["text"]
            }

        @self.app.post("/execute")
        async def execute_capability(request: Request):
            """Execute CrewAI crew"""
            data = await request.json()

            capability = data.get("capability")
            input_data = data.get("input", {})
            task_id = data.get("task_id", str(uuid.uuid4()))

            if capability != "kickoff":
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": f"Capability '{capability}' not found. Use 'kickoff'.",
                        "available": ["kickoff"]
                    }
                )

            try:
                if asyncio.iscoroutinefunction(self.crew.kickoff):
                    result = await self.crew.kickoff(inputs=input_data)
                else:
                    result = await asyncio.to_thread(self.crew.kickoff, inputs=input_data)

                return {
                    "success": True,
                    "task_id": task_id,
                    "capability": capability,
                    "result": {"output": str(result)},
                    "cost": self.cost_per_call,
                    "agent_id": self.agent_id
                }

            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "task_id": task_id,
                        "error": str(e),
                        "capability": capability
                    }
                )

        @self.app.get("/health")
        async def health():
            """Health check"""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "framework": "crewai"
            }

    async def register_to_network(self):
        """Register to ASTRAEUS network"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.astraeus_url}/api/v1/mesh/agents/register",
                json={
                    "name": self.name,
                    "owner": self.owner,
                    "framework": "crewai",
                    "capabilities": [
                        {
                            "name": "kickoff",
                            "description": self.description,
                            "confidence": 0.9,
                            "cost": self.cost_per_call,
                            "latency": 300
                        }
                    ]
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                self.agent_id = data.get("agent_id", self.agent_id)
                print(f"✅ CrewAI crew registered: {self.name} ({self.agent_id})")
                return data
            else:
                print(f"❌ Registration failed: {response.text}")
                return None

    def serve(self, host: str = "0.0.0.0", port: int = 8001, register: bool = True):
        """Start the crew server"""
        print(f"\n🚀 Starting CrewAI crew: {self.name}")
        print(f"📍 Endpoint: http://{host}:{port}")
        print(f"💰 Cost per call: ${self.cost_per_call}")

        if register:
            try:
                asyncio.run(self.register_to_network())
            except Exception as e:
                print(f"⚠️  Registration failed: {e}")
                print(f"   Crew will run locally only")

        print(f"\n✨ Crew ready! Try:")
        print(f'   curl -X POST http://{host}:{port}/execute \\')
        print(f'        -d \'{{"capability": "kickoff", "input": {{"topic": "AI"}}}}\'')
        print()

        uvicorn.run(self.app, host=host, port=port, log_level="info")
