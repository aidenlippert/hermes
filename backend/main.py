"""
HERMES BACKEND - THE ACTUAL PRODUCTION API

This is the REAL backend that powers Hermes orchestration.

Endpoints:
- POST /api/v1/chat - Main orchestration endpoint
- GET /api/v1/agents - List available agents
- POST /api/v1/agents/register - Register new agent
- GET /api/v1/health - Health check
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
import sys
from pathlib import Path
import uuid

# Add parent to path to import hermes modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hermes.protocols.a2a_client import A2AClient
from hermes.conductor.intent_parser import IntentParser
from hermes.conductor.planner import WorkflowPlanner
from hermes.conductor.executor import Executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Hermes API",
    description="AI Agent Orchestration Platform powered by A2A",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")

# Initialize core components
a2a_client = A2AClient()
intent_parser = IntentParser(GOOGLE_API_KEY)
planner = WorkflowPlanner(GOOGLE_API_KEY)
executor = Executor(a2a_client)

# In-memory agent registry (will move to PostgreSQL later)
agent_registry: Dict[str, Dict[str, Any]] = {
    "CodeGenerator": {
        "name": "CodeGenerator",
        "endpoint": "http://localhost:10001/a2a",
        "capabilities": ["code_write", "code_debug", "code_explain"],
        "description": "Generates code in any programming language",
        "status": "active"
    }
}

# In-memory task storage (will move to PostgreSQL later)
tasks: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class ChatRequest(BaseModel):
    """Request to orchestrate agents"""
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response from orchestration"""
    task_id: str
    status: str
    message: str
    result: Optional[Any] = None
    steps: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class RegisterAgentRequest(BaseModel):
    """Request to register a new agent"""
    name: str
    endpoint: str
    capabilities: List[str]
    description: Optional[str] = None


# API Endpoints

@app.get("/")
async def root():
    """API info"""
    return {
        "service": "Hermes AI Orchestration",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/api/v1/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "agents_available": len(agent_registry),
        "active_tasks": len([t for t in tasks.values() if t["status"] == "in_progress"])
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    MAIN ORCHESTRATION ENDPOINT

    This is where the magic happens:
    1. Parse user intent (Gemini)
    2. Create execution plan (Gemini)
    3. Execute via A2A agents
    4. Return results

    For now: Synchronous (wait for completion)
    Later: Async with WebSocket streaming
    """
    logger.info(f"📨 Chat request: {request.query[:100]}...")

    # Create task ID
    task_id = str(uuid.uuid4())

    try:
        # STEP 1: Parse Intent
        logger.info("🧠 Parsing intent...")
        parsed_intent = await intent_parser.parse(request.query)

        logger.info(f"   Category: {parsed_intent.category.value}")
        logger.info(f"   Capabilities: {parsed_intent.required_capabilities}")

        # STEP 2: Get Available Agents
        available_agents = [
            {
                "name": name,
                "endpoint": agent["endpoint"],
                "capabilities": agent["capabilities"],
                "description": agent.get("description", "")
            }
            for name, agent in agent_registry.items()
            if agent["status"] == "active"
        ]

        if not available_agents:
            raise HTTPException(
                status_code=503,
                detail="No agents available. Please register agents first."
            )

        # STEP 3: Create Plan
        logger.info("📋 Creating execution plan...")
        plan = await planner.create_plan(
            user_query=request.query,
            parsed_intent=parsed_intent.to_dict(),
            available_agents=available_agents
        )

        logger.info(f"   Plan: {len(plan.steps)} steps")

        # Store task
        tasks[task_id] = {
            "task_id": task_id,
            "query": request.query,
            "status": "in_progress",
            "plan": plan,
            "result": None,
            "error": None
        }

        # STEP 4: Execute Plan
        logger.info("⚡ Executing plan...")
        result = await executor.execute(plan)

        # Update task
        tasks[task_id]["status"] = "completed" if result.success else "failed"
        tasks[task_id]["result"] = result
        tasks[task_id]["error"] = result.error

        logger.info(f"{'✅' if result.success else '❌'} Execution completed")

        # Return response
        return ChatResponse(
            task_id=task_id,
            status="completed" if result.success else "failed",
            message=f"Completed {result.completed_steps}/{len(plan.steps)} steps",
            result=result.final_output,
            steps=[step.to_dict() for step in plan.steps],
            error=result.error
        )

    except Exception as e:
        logger.error(f"❌ Chat request failed: {e}")

        # Store error
        tasks[task_id] = {
            "task_id": task_id,
            "query": request.query,
            "status": "failed",
            "error": str(e)
        }

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents")
async def list_agents():
    """List all registered agents"""
    return {
        "agents": list(agent_registry.values()),
        "total": len(agent_registry)
    }


@app.post("/api/v1/agents/register")
async def register_agent(request: RegisterAgentRequest):
    """
    Register a new agent

    The agent must be A2A-compliant (expose /.well-known/agent.json)
    """
    logger.info(f"📝 Registering agent: {request.name}")

    try:
        # Discover the agent via A2A
        agent_card = await a2a_client.discover_agent(request.endpoint.split("/a2a")[0])

        # Add to registry
        agent_registry[request.name] = {
            "name": request.name,
            "endpoint": request.endpoint,
            "capabilities": request.capabilities,
            "description": request.description or agent_card.description,
            "status": "active",
            "agent_card": agent_card.raw_card
        }

        logger.info(f"✅ Agent registered: {request.name}")

        return {
            "success": True,
            "message": f"Agent '{request.name}' registered successfully",
            "agent": agent_registry[request.name]
        }

    except Exception as e:
        logger.error(f"❌ Failed to register agent: {e}")
        raise HTTPException(status_code=400, detail=f"Agent registration failed: {str(e)}")


@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status and results"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    return {
        "task_id": task_id,
        "status": task["status"],
        "query": task.get("query"),
        "result": task.get("result"),
        "error": task.get("error")
    }


# Startup/Shutdown
@app.on_event("startup")
async def startup():
    logger.info("🚀 Hermes Backend Starting...")
    logger.info(f"   Agents registered: {len(agent_registry)}")
    logger.info("✅ Ready to orchestrate!")


@app.on_event("shutdown")
async def shutdown():
    logger.info("👋 Hermes Backend Shutting down...")
    await a2a_client.close()


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("🚀 HERMES BACKEND - PRODUCTION API")
    print("="*70)
    print("\n📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("\n💡 Try it:")
    print('   curl -X POST http://localhost:8000/api/v1/chat \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"query": "Write me a Python function"}\'')
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
