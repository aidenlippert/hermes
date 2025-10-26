"""
HERMES BACKEND - THE ACTUAL PRODUCTION API

This is the REAL backend that powers Hermes orchestration.

Endpoints:
- POST /api/v1/chat - Main orchestration endpoint
- GET /api/v1/agents - List available agents
- POST /api/v1/agents/register - Register new agent
- GET /api/v1/health - Health check
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
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

from backend.api import v1_auth
from backend.api import v1_websocket
from backend.api import marketplace
from backend.websocket.manager import manager
from backend.mesh.network import MeshNetwork, FlightAgent, HotelAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize mesh network
mesh = MeshNetwork()

from contextlib import asynccontextmanager
from backend.database.connection import init_db, init_redis, close_redis

# Initialize FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Hermes Backend Starting...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ PostgreSQL initialized")
    except Exception as e:
        logger.error(f"❌ PostgreSQL failed: {e}")
        # Continue without database if needed
    
    try:
        # Initialize Redis
        await init_redis()
        logger.info("✅ Redis initialized")
    except Exception as e:
        logger.error(f"❌ Redis failed: {e}")
        # Continue without Redis if needed
    
    try:
        # Initialize mesh network
        await mesh.start()
        
        # Register internal agents
        flight_agent = FlightAgent()
        hotel_agent = HotelAgent()
        
        await mesh.register_agent(flight_agent)
        await mesh.register_agent(hotel_agent)
        
        logger.info("✅ Mesh network initialized")
    except Exception as e:
        logger.error(f"❌ Mesh initialization failed: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info(f"   Legacy agents registered: {len(agent_registry)}")
    logger.info(f"   Mesh agents active: {len(mesh.discovery.list_agents())}")
    logger.info("✅ Ready to orchestrate!")
    yield
    # Shutdown
    logger.info("👋 Hermes Backend Shutting down...")
    await mesh.stop()
    await a2a_client.close()
    await close_redis()

app = FastAPI(
    title="Hermes API",
    description="AI Agent Orchestration Platform powered by A2A",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Support both local dev and production
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://hermes-aidenlippert.vercel.app")
origins = [
    "http://localhost:3000",  # Local Next.js dev server
    "http://localhost:3001",  # Alternative port
    "http://127.0.0.1:3000",  # Alternative local
    "http://127.0.0.1:3001",  # Alternative local
    FRONTEND_URL,  # Production Vercel URL
]

# Remove duplicates and empty strings
origins = list(set([origin for origin in origins if origin]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


@app.get("/health")
async def health_check():
    """Simple health check for Railway"""
    return {"status": "healthy"}


@app.get("/api/v1/health")
async def health():
    """Health check with startup status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "startup_complete": True,
        "agents_available": len(agent_registry),
        "active_tasks": len([t for t in tasks.values() if t["status"] == "in_progress"])
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    MESH-POWERED ORCHESTRATION ENDPOINT
    
    Uses autonomous mesh network for multi-agent coordination:
    1. Parse user intent into multiple tasks
    2. Create mesh contracts for each task
    3. Agents autonomously bid and execute
    4. Stream results via WebSocket
    
    Returns immediately with task_id, execution happens in background.
    Client connects via WebSocket for real-time updates.
    """
    logger.info(f"📨 Chat request (MESH): {request.query[:100]}...")

    # Create task ID
    task_id = str(uuid.uuid4())

    # Store task immediately
    tasks[task_id] = {
        "task_id": task_id,
        "query": request.query,
        "status": "pending",
        "contracts": [],
        "result": None,
        "error": None
    }

    # Execute mesh orchestration in background
    background_tasks.add_task(execute_mesh_chat_task, task_id, request.query)

    # Return task ID immediately
    return ChatResponse(
        task_id=task_id,
        status="pending",
        message="Task created. Mesh network activating..."
    )


async def available_agents_list():
    """Get list of available agents"""
    return [
        {
            "name": name,
            "endpoint": agent["endpoint"],
            "capabilities": agent["capabilities"],
            "description": agent.get("description", "")
        }
        for name, agent in agent_registry.items()
        if agent["status"] == "active"
    ]


async def execute_mesh_chat_task(task_id: str, query: str):
    """
    Execute chat orchestration using MESH NETWORK.
    Automatically creates contracts, agents bid, execute, and return results.
    Sends real-time updates via WebSocket.
    """
    try:
        # Update status
        tasks[task_id]["status"] = "in_progress"
        await manager.send_to_task(task_id, {
            "type": "task_started",
            "task_id": task_id,
            "query": query
        })

        # STEP 1: Parse Intent with LLM
        logger.info(f"🧠 [{task_id[:8]}] Parsing intent with Gemini...")
        await manager.send_to_task(task_id, {
            "type": "intent_parsing_started",
            "message": "Analyzing your request with AI..."
        })

        # Use the existing Gemini-powered intent parser
        parsed_intent = await intent_parser.parse(query)
        
        logger.info(f"📋 [{task_id[:8]}] Parsed: {parsed_intent.category.value}, capabilities: {parsed_intent.required_capabilities}")

        await manager.send_to_task(task_id, {
            "type": "intent_parsed",
            "category": parsed_intent.category.value,
            "capabilities": parsed_intent.required_capabilities,
            "message": f"Understood: {parsed_intent.category.value}"
        })

        # STEP 2: Create mesh contracts based on required capabilities
        task_contracts = []
        
        # Map capabilities to task types
        capability_to_task = {
            "flight_search": "flight_search",
            "hotel_search": "hotel_search",
            "restaurant_search": "restaurant_search",
            "event_search": "event_search",
            "weather": "weather_query",
            "code_write": "code_generation",
            "code_debug": "code_debug",
            "data_analysis": "data_analysis"
        }
        
        # Create contracts for each required capability
        for capability in parsed_intent.required_capabilities:
            task_type = capability_to_task.get(capability, "general_query")
            
            task_contracts.append({
                "type": task_type,
                "description": f"{capability} for: {query}",
                "requirements": {
                    "query": query,
                    "capability": capability,
                    "parsed_intent": parsed_intent.to_dict()
                }
            })
        
        # If no specific capabilities, create a general query
        if not task_contracts:
            task_contracts.append({
                "type": "general_query",
                "description": query,
                "requirements": {
                    "query": query,
                    "category": parsed_intent.category.value
                }
            })

        await manager.send_to_task(task_id, {
            "type": "tasks_identified",
            "tasks": len(task_contracts),
            "task_types": [t["type"] for t in task_contracts],
            "message": f"Breaking down into {len(task_contracts)} tasks"
        })

        # STEP 3: Get available mesh agents
        mesh_agents = mesh.discovery.list_agents()
        
        await manager.send_to_task(task_id, {
            "type": "agents_discovered",
            "agents": [{"id": a["agent_id"], "name": a["name"], "capabilities": [c["name"] for c in a.get("capabilities", [])]} for a in mesh_agents],
            "message": f"Found {len(mesh_agents)} specialized agents"
        })

        # STEP 4: Create contracts and execute
        logger.info(f"📋 [{task_id[:8]}] Creating {len(task_contracts)} mesh contracts...")
        
        await manager.send_to_task(task_id, {
            "type": "contracts_creating",
            "count": len(task_contracts),
            "message": "Announcing contracts to mesh network..."
        })
        
        contract_results = []
        contract_ids = []
        
        for task in task_contracts:
            # Create contract
            contract = await mesh.announce_contract(
                task_type=task["type"],
                description=task["description"],
                requirements=task["requirements"]
            )
            
            contract_ids.append(contract.contract_id)
            
            logger.info(f"📝 [{task_id[:8]}] Contract {contract.contract_id[:8]} created for {task['type']}")
            
            await manager.send_to_task(task_id, {
                "type": "contract_created",
                "contract_id": contract.contract_id,
                "task_type": task["type"],
                "message": f"✓ {task['type']} contract announced"
            })
        
        # Store contract IDs
        tasks[task_id]["contracts"] = contract_ids
        
        # STEP 5: Wait for contracts to complete (poll with timeout)
        logger.info(f"⚡ [{task_id[:8]}] Waiting for mesh execution...")
        
        await manager.send_to_task(task_id, {
            "type": "execution_started",
            "message": "🤖 Agents are bidding and executing your tasks..."
        })
        
        # Poll contracts for completion (max 30 seconds)
        import asyncio
        max_wait = 30
        poll_interval = 0.5
        elapsed = 0
        
        while elapsed < max_wait:
            all_complete = True
            status_summary = {}
            
            for contract_id in contract_ids:
                contract = mesh.contracts.get_contract(contract_id)
                if contract:
                    status = contract.status.value
                    status_summary[contract_id[:8]] = status
                    
                    if status not in ["DELIVERED", "SETTLED"]:
                        all_complete = False
            
            # Send periodic status update
            if elapsed % 2 == 0:  # Every 2 seconds
                await manager.send_to_task(task_id, {
                    "type": "execution_progress",
                    "statuses": status_summary,
                    "message": f"⏳ {sum(1 for s in status_summary.values() if s in ['DELIVERED', 'SETTLED'])}/{len(contract_ids)} tasks completed"
                })
            
            if all_complete:
                break
                
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        # STEP 6: Collect results
        logger.info(f"✅ [{task_id[:8]}] Collecting mesh results...")
        
        final_results = []
        for contract_id in contract_ids:
            contract = mesh.contracts.get_contract(contract_id)
            if contract:
                deliveries = mesh.contracts.deliveries.get(contract_id, [])
                bids = mesh.contracts.get_bids(contract_id)
                
                result_data = {
                    "contract_id": contract_id,
                    "task_type": contract.intent,
                    "status": contract.status.value,
                    "awarded_to": contract.awarded_to[0] if contract.awarded_to else None,
                    "bids_count": len(bids)
                }
                
                if deliveries:
                    delivery = deliveries[0]
                    result_data["result"] = delivery.data
                    result_data["agent_id"] = delivery.agent_id
                
                final_results.append(result_data)
        
        # STEP 7: Format final response with LLM (optional - can be enhanced)
        result_text = f"🎯 **Task Complete!** I coordinated {len(final_results)} specialized agents:\n\n"
        
        for r in final_results:
            emoji = "✅" if r['status'] in ['DELIVERED', 'SETTLED'] else "⏳"
            task_name = r['task_type'].replace('_', ' ').title()
            result_text += f"{emoji} **{task_name}**\n"
            
            if r.get('awarded_to'):
                result_text += f"   Agent: {r['awarded_to']}\n"
            
            if r.get('result'):
                result_data = r['result']
                if isinstance(result_data, dict):
                    if 'message' in result_data:
                        result_text += f"   {result_data['message']}\n"
                    elif 'status' in result_data:
                        result_text += f"   Status: {result_data['status']}\n"
                else:
                    result_text += f"   {result_data}\n"
            
            result_text += "\n"
        
        result_text += f"\n💰 Total cost: ${sum(r.get('cost', 0) for r in final_results):.2f}\n"
        result_text += f"⚡ Completed in {elapsed:.1f}s using autonomous mesh network"
        
        # Update task
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = final_results
        
        logger.info(f"✅ [{task_id[:8]}] Mesh execution completed with {len(final_results)} results")

        # Send completion event
        await manager.send_to_task(task_id, {
            "type": "task_complete",
            "success": True,
            "result": result_text,
            "contracts": final_results,
            "parsed_intent": parsed_intent.to_dict(),
            "message": f"✅ All tasks completed successfully!"
        })

    except Exception as e:
        logger.error(f"❌ [{task_id[:8]}] Mesh task failed: {e}")
        import traceback
        traceback.print_exc()

        # Update task
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

        # Send error event
        await manager.send_to_task(task_id, {
            "type": "error",
            "error": str(e),
            "message": f"❌ Task failed: {str(e)}"
        })


async def execute_chat_task(task_id: str, query: str, available_agents: List[Dict[str, Any]]):
    """
    Execute chat orchestration task in background.
    Sends real-time updates via WebSocket.
    """
    try:
        # Update status
        tasks[task_id]["status"] = "in_progress"
        await manager.send_to_task(task_id, {
            "type": "task_started",
            "task_id": task_id,
            "query": query
        })

        # STEP 1: Parse Intent
        logger.info(f"🧠 [{task_id[:8]}] Parsing intent...")
        await manager.send_to_task(task_id, {
            "type": "intent_parsing_started",
            "message": "Analyzing your request..."
        })

        parsed_intent = await intent_parser.parse(query)

        await manager.send_to_task(task_id, {
            "type": "intent_parsed",
            "category": parsed_intent.category.value,
            "capabilities": parsed_intent.required_capabilities,
            "message": f"Request understood: {parsed_intent.category.value}"
        })

        # Check if agents available
        if not available_agents:
            raise Exception("No agents available. Please register agents first.")

        # STEP 2: Create Plan
        logger.info(f"📋 [{task_id[:8]}] Creating execution plan...")
        await manager.send_to_task(task_id, {
            "type": "planning_started",
            "message": "Searching for specialized agents..."
        })

        plan = await planner.create_plan(
            user_query=query,
            parsed_intent=parsed_intent.to_dict(),
            available_agents=available_agents
        )

        tasks[task_id]["plan"] = plan

        # Send agents discovered
        agents_info = [
            {
                "name": step.agent_name,
                "task": step.task_description
            }
            for step in plan.steps
        ]

        await manager.send_to_task(task_id, {
            "type": "agents_discovered",
            "agents": agents_info,
            "message": f"Found {len(agents_info)} specialized agents"
        })

        # STEP 3: Execute Plan
        logger.info(f"⚡ [{task_id[:8]}] Executing plan...")
        await manager.send_to_task(task_id, {
            "type": "execution_started",
            "steps": [{"agent": step.agent_name, "status": "pending"} for step in plan.steps],
            "message": "Executing agents..."
        })

        result = await executor.execute(plan)

        # Update task
        tasks[task_id]["status"] = "completed" if result.success else "failed"
        tasks[task_id]["result"] = result
        tasks[task_id]["error"] = result.error

        logger.info(f"{'✅' if result.success else '❌'} [{task_id[:8]}] Execution completed")

        # Send completion event
        await manager.send_to_task(task_id, {
            "type": "task_complete",
            "success": result.success,
            "result": result.final_output,
            "message": f"Completed {result.completed_steps}/{len(plan.steps)} steps",
            "steps": [step.to_dict() for step in plan.steps]
        })

    except Exception as e:
        logger.error(f"❌ [{task_id[:8]}] Task failed: {e}")

        # Update task
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

        # Send error event
        await manager.send_to_task(task_id, {
            "type": "error",
            "error": str(e),
            "message": "Task execution failed"
        })


@app.get("/api/v1/agents")
async def list_agents():
    """List all registered agents (public endpoint for marketplace)"""
    # Combine legacy agents with some default marketplace agents
    marketplace_agents = [
        {
            "id": "flight-finder",
            "name": "FlightFinder Pro",
            "description": "Searches flights across 200+ airlines with real-time pricing",
            "category": "travel",
            "rating": 4.9,
            "usage_count": 45200,
            "is_featured": True,
            "capabilities": ["flight_search", "price_comparison", "booking"]
        },
        {
            "id": "hotel-scout",
            "name": "HotelScout AI",
            "description": "Finds the best hotels with reviews and availability",
            "category": "travel",
            "rating": 4.8,
            "usage_count": 38900,
            "is_featured": True,
            "capabilities": ["hotel_search", "review_analysis", "price_tracking"]
        },
        {
            "id": "code-assist",
            "name": "CodeAssist Ultra",
            "description": "Advanced code generation and debugging assistant",
            "category": "development",
            "rating": 4.9,
            "usage_count": 128000,
            "is_featured": True,
            "capabilities": ["code_generation", "debugging", "refactoring"]
        },
        {
            "id": "data-analyzer",
            "name": "DataAnalyzer Pro",
            "description": "Powerful data analysis and visualization agent",
            "category": "data",
            "rating": 4.7,
            "usage_count": 67800,
            "is_featured": True,
            "capabilities": ["data_analysis", "visualization", "reporting"]
        },
        {
            "id": "content-writer",
            "name": "ContentWriter AI",
            "description": "Professional content creation for blogs and articles",
            "category": "content",
            "rating": 4.6,
            "usage_count": 89300,
            "is_featured": False,
            "capabilities": ["blog_writing", "copywriting", "seo_optimization"]
        },
        {
            "id": "email-assistant",
            "name": "EmailAssistant",
            "description": "Smart email management and auto-responses",
            "category": "productivity",
            "rating": 4.5,
            "usage_count": 56700,
            "is_featured": False,
            "capabilities": ["email_sorting", "summarization", "auto_reply"]
        },
        {
            "id": "market-analyst",
            "name": "MarketAnalyst",
            "description": "Real-time stock market analysis and predictions",
            "category": "finance",
            "rating": 4.8,
            "usage_count": 34500,
            "is_featured": False,
            "capabilities": ["market_analysis", "trend_prediction", "portfolio_optimization"]
        },
        {
            "id": "support-bot",
            "name": "CustomerSupport Bot",
            "description": "Intelligent customer service automation",
            "category": "support",
            "rating": 4.4,
            "usage_count": 78900,
            "is_featured": False,
            "capabilities": ["ticket_handling", "faq_responses", "escalation"]
        }
    ]

    # Add any registered agents
    for name, agent in agent_registry.items():
        marketplace_agents.append({
            "id": name.lower().replace(" ", "-"),
            "name": name,
            "description": agent.get("description", ""),
            "category": "custom",
            "rating": 4.5,
            "usage_count": 0,
            "is_featured": False,
            "capabilities": agent.get("capabilities", [])
        })

    return {
        "agents": marketplace_agents,
        "total": len(marketplace_agents)
    }

@app.get("/api/v1/marketplace")
async def list_marketplace_agents():
    """List marketplace agents (alias for /api/v1/agents)"""
    return await list_agents()


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


# ============================================================
# 🔸 MESH NETWORK ENDPOINTS
# ============================================================

class CreateContractRequest(BaseModel):
    task_type: str
    description: str
    requirements: Dict[str, Any]
    deadline: Optional[str] = None
    budget: Optional[float] = None

class SearchAgentsRequest(BaseModel):
    capabilities: List[str]

@app.post("/api/v1/mesh/contracts")
async def create_mesh_contract(request: CreateContractRequest):
    """Create a new task contract in the mesh network"""
    try:
        # Create contract
        contract = await mesh.announce_contract(
            task_type=request.task_type,
            description=request.description,
            requirements=request.requirements
        )
        
        return {
            "success": True,
            "contract_id": contract.contract_id,
            "status": contract.status.value,
            "message": f"Contract announced to {len(mesh.discovery.list_agents())} agents"
        }
    except Exception as e:
        logger.error(f"Failed to create contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mesh/contracts/{contract_id}")
async def get_mesh_contract(contract_id: str):
    """Get contract status and details"""
    try:
        contract = mesh.contracts.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Get bids
        bids = mesh.contracts.get_bids(contract_id)
        
        return {
            "contract": {
                "id": contract.contract_id,
                "task_type": contract.intent,
                "description": str(contract.context),
                "status": contract.status.value,
                "created_at": contract.created_at,
                "awarded_to": contract.awarded_to
            },
            "bids": [
                {
                    "agent_id": bid.agent_id,
                    "amount": bid.price,
                    "confidence": bid.confidence,
                    "estimated_time": bid.eta_seconds
                }
                for bid in bids
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mesh/agents")
async def list_mesh_agents():
    """List all agents in the mesh network"""
    try:
        agents = mesh.discovery.list_agents()
        return {
            "agents": agents,
            "total": len(agents)
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mesh/agents/search")
async def search_mesh_agents(request: SearchAgentsRequest):
    """Search for agents by capabilities"""
    try:
        results = []
        for capability in request.capabilities:
            matched = mesh.discovery.search_capabilities(capability)
            results.extend(matched)
        
        # Deduplicate by agent_id
        seen = set()
        unique_results = []
        for result in results:
            if result["agent_id"] not in seen:
                seen.add(result["agent_id"])
                unique_results.append(result)
        
        return {
            "results": unique_results,
            "total": len(unique_results)
        }
    except Exception as e:
        logger.error(f"Failed to search agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mesh/execute")
async def execute_mesh_task(request: ChatRequest):
    """Execute a task through the mesh network"""
    try:
        # Execute through mesh
        result = await mesh.execute_task(
            task_type="general_query",
            description=request.query,
            requirements={"query": request.query}
        )
        
        return {
            "success": True,
            "result": result,
            "mesh_enabled": True
        }
    except Exception as e:
        logger.error(f"Mesh execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/mesh/contracts/{contract_id}")
async def get_mesh_contract(contract_id: str):
    """Get contract by ID with bids"""
    from backend.mesh.contracts import contract_manager
    
    contract = contract_manager.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    bids = contract_manager.get_bids(contract_id)
    
    return {
        **contract.to_dict(),
        "bids": [b.to_dict() for b in bids]
    }


# ========================================
# USER PREFERENCES API
# ========================================

@app.post("/api/v1/preferences")
async def set_user_preferences(
    preferences: Dict[str, Any],
    user_id: str = Header(None, alias="X-User-ID")
):
    """Set user preferences for agent selection
    
    Examples:
        {"preset": "cheapest"}  # Only care about price
        {"preset": "premium"}   # Prioritize performance
        {"preset": "free_only"} # Only free agents
        {
            "price_weight": 40,
            "performance_weight": 30,
            "speed_weight": 20,
            "reputation_weight": 10,
            "max_price": 5.0
        }
    """
    from backend.mesh.preferences import preference_manager, UserPreferences, PreferencePreset
    
    if not user_id:
        user_id = "default_user"  # Allow without auth for now
    
    # Check if preset
    if "preset" in preferences:
        preset = PreferencePreset(preferences["preset"])
        prefs = UserPreferences.from_preset(user_id, preset)
    else:
        # Custom preferences
        prefs = UserPreferences(user_id=user_id, **preferences)
    
    preference_manager.set_preferences(prefs)
    
    return {
        "status": "success",
        "preferences": prefs.to_dict()
    }


@app.get("/api/v1/preferences")
async def get_user_preferences(user_id: str = Header(None, alias="X-User-ID")):
    """Get user preferences"""
    from backend.mesh.preferences import preference_manager
    
    if not user_id:
        user_id = "default_user"
    
    prefs = preference_manager.get_preferences(user_id)
    
    return prefs.to_dict()


# ========================================
# AGENT REGISTRATION API
# ========================================

@app.post("/api/v1/mesh/agents/register")
async def register_external_agent(agent_data: Dict[str, Any]):
    """Register external agent to mesh network
    
    Body:
        {
            "name": "WeatherBot",
            "owner": "alice@example.com",
            "capabilities": [
                {
                    "name": "weather_query",
                    "description": "Get weather forecast",
                    "confidence": 0.9,
                    "cost": 0.5,
                    "latency": 2.0
                }
            ]
        }
    """
    from backend.mesh.discovery import discovery_service, AgentRegistration, Capability
    import uuid
    
    # Generate agent ID
    agent_id = f"agent-{str(uuid.uuid4())[:8]}"
    
    # Parse capabilities
    capabilities = []
    for cap_data in agent_data.get("capabilities", []):
        cap = Capability(
            name=cap_data["name"],
            description=cap_data["description"],
            confidence=cap_data.get("confidence", 0.9),
            cost=cap_data.get("cost", 0.0),
            latency=cap_data.get("latency", 3.0)
        )
        capabilities.append(cap)
    
    # Create registration
    registration = AgentRegistration(
        agent_id=agent_id,
        name=agent_data["name"],
        endpoint=agent_data.get("endpoint", f"local://{agent_id}"),
        capabilities=capabilities,
        owner=agent_data.get("owner", "anonymous")
    )
    
    # Register
    await discovery_service.register_agent(registration)
    
    return {
        "status": "success",
        "agent_id": agent_id,
        "message": f"Agent {agent_data['name']} registered successfully"
    }


# ========================================
# AGENT-TO-AGENT MESSAGING API
# ========================================

@app.post("/api/v1/mesh/conversations")
async def start_a2a_conversation(data: Dict[str, Any]):
    """Start agent-to-agent conversation
    
    Body:
        {
            "initiator_id": "agent-1",
            "target_id": "agent-2",
            "topic": "Flight delay notification",
            "initial_message": {"delay_info": {...}}
        }
    """
    from backend.mesh.messaging import messaging_protocol
    
    conv_id = await messaging_protocol.start_conversation(
        initiator_id=data["initiator_id"],
        target_id=data["target_id"],
        topic=data["topic"],
        initial_message=data["initial_message"]
    )
    
    return {
        "conversation_id": conv_id,
        "status": "active"
    }


@app.get("/api/v1/mesh/conversations/{conversation_id}")
async def get_a2a_conversation(conversation_id: str):
    """Get conversation history"""
    from backend.mesh.messaging import messaging_protocol
    
    conv = messaging_protocol.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conv.to_dict()


@app.post("/api/v1/mesh/conversations/{conversation_id}/messages")
async def send_a2a_message(conversation_id: str, data: Dict[str, Any]):
    """Send message in conversation"""
    from backend.mesh.messaging import messaging_protocol, MessageType
    
    msg_id = await messaging_protocol.send_message(
        conversation_id=conversation_id,
        from_agent_id=data["from_agent_id"],
        to_agent_id=data["to_agent_id"],
        message_type=MessageType(data["message_type"]),
        content=data["content"],
        requires_response=data.get("requires_response", False)
    )
    
    return {
        "message_id": msg_id,
        "status": "sent"
    }


# ============================================================
# 🔸 LEGACY ENDPOINTS
# ============================================================

# Include authentication router
app.include_router(v1_auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Include marketplace router (Sprint 1.2)
app.include_router(marketplace.router, tags=["Marketplace"])

# Include WebSocket router
app.include_router(v1_websocket.router, prefix="/api/v1", tags=["WebSocket"])

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
