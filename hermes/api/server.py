"""
Hermes API Server

FastAPI-based REST API that exposes Hermes to the world.
This is how users interact with Hermes.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
from pathlib import Path

# Add parent directory to path so we can import hermes modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from hermes.conductor.core import HermesConductor

app = FastAPI(
    title="Hermes API",
    description="The AI Agent Orchestrator - Messenger of the Gods",
    version="0.1.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the conductor
conductor = HermesConductor()

# Register default agents for demo
conductor.register_agent(
    name="CodeWizard",
    endpoint="localhost:10001",
    capabilities=["code", "debug", "program", "function", "create"]
)

conductor.register_agent(
    name="WritingPro",
    endpoint="localhost:10002",
    capabilities=["write", "article", "blog", "content", "create"]
)

conductor.register_agent(
    name="DataAnalyst",
    endpoint="localhost:10003",
    capabilities=["analyze", "research", "investigate", "study", "data"]
)


# Request/Response Models
class OrchestrateRequest(BaseModel):
    query: str
    context: Optional[Dict] = None


class OrchestrateResponse(BaseModel):
    success: bool
    message: str
    agents_selected: Optional[List[str]] = None
    intent: Optional[Dict] = None
    next_steps: Optional[List[str]] = None
    suggestion: Optional[str] = None


class RegisterAgentRequest(BaseModel):
    name: str
    endpoint: str
    capabilities: List[str]


# API Endpoints
@app.get("/")
async def root():
    """Welcome message and API info."""
    return {
        "message": "🚀 Welcome to Hermes - The AI Agent Orchestrator",
        "tagline": "Messenger of the Gods, Now for AI Agents",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "/status"
    }


@app.get("/status")
async def get_status():
    """Get current system status."""
    return conductor.get_status()


@app.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(request: OrchestrateRequest):
    """
    Main orchestration endpoint.

    Send a natural language query and Hermes will:
    1. Figure out what you want
    2. Find the right agents
    3. Coordinate their work
    4. Return unified results
    """
    try:
        result = conductor.orchestrate(request.query)
        return OrchestrateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/register")
async def register_agent(request: RegisterAgentRequest):
    """Register a new agent with Hermes."""
    try:
        conductor.register_agent(
            name=request.name,
            endpoint=request.endpoint,
            capabilities=request.capabilities
        )
        return {
            "success": True,
            "message": f"Agent '{request.name}' registered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    return {
        "agents": conductor.agents,
        "count": len(conductor.agents)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "hermes-api"}


# For local development
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Hermes API Server")
    print("="*60)
    print("\n📍 API will be available at: http://localhost:8000")
    print("📚 Interactive docs at: http://localhost:8000/docs")
    print("\n💡 Try it out:")
    print('   curl -X POST http://localhost:8000/orchestrate \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"query": "Write me a Python function"}\'')
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
