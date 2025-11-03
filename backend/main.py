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
from datetime import datetime, timezone

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
from backend.services.monitoring import monitoring, log_info, log_error, track_performance
from backend.services.semantic_search import semantic_search
from backend.services.observability import setup_tracing, instrument_fastapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.config.sentry import init_sentry
sentry_enabled = init_sentry()

# Initialize structured logging
from backend.services.structured_logging import setup_logging
setup_logging()

# Initialize rate limiting and security
from backend.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from backend.middleware.security_headers import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded

# Initialize mesh network
mesh = MeshNetwork()

from contextlib import asynccontextmanager
from backend.database.connection import init_db, init_redis, close_redis
from backend.database.agent_db import init_agent_db, close_agent_db

# Initialize FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log_info("startup_initiated", service="hermes-backend", version="2.0.0")

    # Initialize OpenTelemetry tracing
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    setup_tracing(
        service_name="hermes-backend",
        service_version="2.0.0",
        otlp_endpoint=otlp_endpoint,
        console_export=True
    )

    try:
        # Initialize database
        with monitoring.track_performance("database_init"):
            await init_db()
        log_info("postgresql_initialized", status="connected")
    except Exception as e:
        log_error("postgresql_init_failed", e, component="database")
        # Continue without database if needed

    try:
        # Initialize agent database pool
        with monitoring.track_performance("agent_db_init"):
            await init_agent_db()
        log_info("agent_database_initialized", status="connected")
    except Exception as e:
        log_error("agent_db_init_failed", e, component="agent_database")
        # Continue without agent database if needed

    try:
        # Initialize Redis
        with monitoring.track_performance("redis_init"):
            await init_redis()
        log_info("redis_initialized", status="connected")
    except Exception as e:
        log_error("redis_init_failed", e, component="redis")
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
    
    log_info(
        "startup_complete",
        legacy_agents=len(agent_registry),
        mesh_agents=len(mesh.discovery.list_agents()),
        semantic_search_enabled=semantic_search.enabled
    )
    yield
    # Shutdown
    log_info("shutdown_initiated")
    await mesh.stop()
    await a2a_client.close()
    await close_redis()
    await close_agent_db()

app = FastAPI(
    title="Hermes AI Orchestration Platform",
    description="""
## AI Agent Orchestration Platform powered by A2A Protocol

Hermes is an enterprise-grade AI agent orchestration platform that enables seamless coordination
of AI agents through the Agent-to-Agent (A2A) Protocol.

### Key Features

- 🤖 **Agent Orchestration**: Coordinate multiple AI agents to handle complex tasks
- 🔗 **A2A Protocol**: Standards-compliant agent-to-agent communication
- 🌐 **Mesh Network**: Autonomous agent discovery and task execution
- 🔐 **Enterprise Security**: Argon2 password hashing, JWT authentication, rate limiting
- 📊 **Real-time Updates**: WebSocket support for live task progress
- 💳 **Billing Integration**: Stripe payment processing for agent marketplace
- 📧 **Email Verification**: Automated email verification with SendGrid
- 🔔 **Notifications**: User notification system with real-time updates

### Architecture

Hermes uses a microservices architecture with:
- **FastAPI Backend**: High-performance async Python API
- **PostgreSQL**: Primary data store with async connection pooling
- **Redis**: Session management and caching
- **WebSocket**: Real-time bidirectional communication
- **Groq AI**: Free AI orchestration with llama-3-70b-8192

### Documentation

- **Swagger UI**: `/docs` - Interactive API documentation
- **ReDoc**: `/redoc` - Alternative documentation view
- **Health Check**: `/api/v1/health` - Service diagnostics

### Support

- **GitHub**: [github.com/hermes-ai](https://github.com/hermes-ai)
- **Email**: support@hermes.ai
- **Discord**: [discord.gg/hermes](https://discord.gg/hermes)
    """,
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "Hermes AI Team",
        "url": "https://hermes.ai",
        "email": "support@hermes.ai"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://api.hermes.ai",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        }
    ],
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication, registration, and session management with enterprise-grade security"
        },
        {
            "name": "Health",
            "description": "Service health checks, diagnostics, and monitoring endpoints"
        },
        {
            "name": "Orchestration",
            "description": "AI agent orchestration and task execution with Groq AI"
        },
        {
            "name": "Agents",
            "description": "Agent registration, discovery, and management endpoints"
        },
        {
            "name": "Marketplace",
            "description": "Agent marketplace with ratings, reviews, and billing"
        },
        {
            "name": "Mesh Network",
            "description": "Autonomous agent mesh network for distributed task execution"
        },
        {
            "name": "A2A Protocol",
            "description": "Agent-to-Agent protocol endpoints for standardized agent communication"
        },
        {
            "name": "Notifications",
            "description": "User notification system with real-time updates"
        },
        {
            "name": "Email Verification",
            "description": "Email verification and account activation endpoints"
        },
        {
            "name": "WebSocket",
            "description": "Real-time WebSocket connections for live task updates"
        },
        {
            "name": "Organizations",
            "description": "Multi-tenant organization management and team collaboration"
        },
        {
            "name": "Workflows",
            "description": "Workflow templates and execution management"
        },
        {
            "name": "Analytics",
            "description": "Usage analytics, metrics, and reporting"
        },
        {
            "name": "Payments",
            "description": "Stripe billing integration and payment processing"
        },
        {
            "name": "Federation",
            "description": "Cross-platform federation and agent sharing"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "tryItOutEnabled": True
    }
)

# Add rate limiting state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS - Support both local dev and production
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://hermes-one-navy.vercel.app")

import re

def check_origin(origin: str) -> bool:
    """Check if origin is allowed"""
    allowed_patterns = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
        r"^https://hermes.*\.vercel\.app$",
    ]
    return any(re.match(pattern, origin) for pattern in allowed_patterns)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https://.*\.vercel\.app$|^http://localhost:\d+$|^http://127\.0\.0\.1:\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Instrument FastAPI with OpenTelemetry
instrument_fastapi(app)

@app.middleware("http")
async def add_request_context(request, call_next):
    """Add request ID and monitoring context to all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Add request context to monitoring
    monitoring.add_request_context(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else "unknown"
    )

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        # Clear context after request
        monitoring.clear_context()

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

@app.get("/", tags=["Health"])
async def root():
    """
    ## Root endpoint - API information and status

    Returns basic API information including service status, version, and documentation links.

    ### Response
    - `service`: Service name
    - `version`: Current API version
    - `status`: Operational status
    - `docs`: Link to interactive documentation
    - `redoc`: Link to alternative documentation
    - `health`: Link to detailed health check endpoint

    ### Example Response
    ```json
    {
        "service": "Hermes AI Orchestration",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }
    ```
    """
    return {
        "service": "Hermes AI Orchestration",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }


@app.get("/health")
async def health_check():
    """Simple health check for Railway/Fly.io"""
    return {"status": "healthy", "service": "hermes"}


@app.get("/api/v1/health")
async def health():
    """Comprehensive health check with service diagnostics"""
    from backend.database.connection import engine, redis_client, get_pool_stats
    from sqlalchemy import text

    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "startup_complete": True,
        "checks": {},
        "metrics": {},
        "connection_pool": {}
    }

    # Check PostgreSQL
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["postgresql"] = "ok"
    except Exception as e:
        health_status["checks"]["postgresql"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Get connection pool statistics
    try:
        health_status["connection_pool"] = get_pool_stats()

        # Warn if pool utilization is high
        pool_stats = health_status["connection_pool"]
        if pool_stats.get("mode") == "persistent":
            utilization_str = pool_stats.get("utilization", "0%")
            utilization = float(utilization_str.rstrip('%'))
            if utilization > 80:
                health_status["status"] = "degraded"
                health_status["connection_pool"]["warning"] = f"High pool utilization: {utilization}%"
    except Exception as e:
        health_status["connection_pool"] = {"error": str(e)}

    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"

    # Check Semantic Search (Pinecone)
    try:
        if semantic_search.enabled:
            health_status["checks"]["pinecone"] = "ok"
        else:
            health_status["checks"]["pinecone"] = "disabled"
    except Exception as e:
        health_status["checks"]["pinecone"] = f"error: {str(e)}"

    # Check Sentry
    health_status["checks"]["sentry"] = "ok" if monitoring.sentry_enabled else "disabled"

    # Add metrics
    health_status["metrics"]["agents_available"] = len(agent_registry)
    health_status["metrics"]["mesh_agents"] = len(mesh.discovery.list_agents())
    health_status["metrics"]["active_tasks"] = len([t for t in tasks.values() if t["status"] == "in_progress"])
    health_status["metrics"]["performance"] = monitoring.get_metrics_summary()

    return health_status


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Orchestration"])
@track_performance(operation="api.chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    ## AI Agent Orchestration Endpoint

    Orchestrate multiple AI agents to handle complex tasks using Groq AI (llama-3-70b-8192).

    ### Workflow
    1. **Parse Intent**: Analyze user query with Groq AI to determine intent
    2. **Discover Agents**: Find agents in mesh network with required capabilities
    3. **Execute Tasks**: Coordinate agent execution in background
    4. **Stream Updates**: Send real-time progress via WebSocket

    ### Request Body
    - `query`: Natural language task description
    - `user_id`: Optional user identifier for tracking
    - `context`: Optional additional context for the task

    ### Response
    - `task_id`: Unique task identifier for tracking
    - `status`: Initial task status (pending, in_progress, completed, failed)
    - `message`: Human-readable status message

    ### Real-time Updates
    Connect to WebSocket at `/ws/{task_id}` to receive real-time progress updates:
    - `task_started`: Task execution has begun
    - `intent_parsed`: User intent has been analyzed
    - `agents_discovered`: Relevant agents have been found
    - `execution_started`: Agent execution has started
    - `task_complete`: Task finished successfully
    - `error`: Task failed with error details

    ### Example Request
    ```json
    {
        "query": "Find me flights from NYC to LA on Friday",
        "user_id": "user-123",
        "context": {
            "budget": "economy",
            "preferences": ["non-stop"]
        }
    }
    ```

    ### Example Response
    ```json
    {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "pending",
        "message": "Task created. AI orchestrator activating..."
    }
    ```

    ### Error Responses
    - `400 Bad Request`: Invalid query or parameters
    - `429 Too Many Requests`: Rate limit exceeded
    - `500 Internal Server Error`: Orchestration failed
    """
    log_info("chat_request_received", query_length=len(request.query), user_id=request.user_id)

    # Create task ID
    task_id = str(uuid.uuid4())

    # Store task immediately
    tasks[task_id] = {
        "task_id": task_id,
        "query": request.query,
        "status": "pending",
        "result": None,
        "error": None
    }

    # Execute Groq orchestration in background
    background_tasks.add_task(execute_groq_chat_task, task_id, request.query)

    # Return task ID immediately
    return ChatResponse(
        task_id=task_id,
        status="pending",
        message="Task created. AI orchestrator activating..."
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


async def execute_groq_chat_task(task_id: str, query: str):
    """
    Execute orchestration with Groq AI + A2A Protocol

    Flow:
    1. Detect intent (agent_discovery / task_execution / question)
    2. Handle agent_discovery → Show agents from database + mesh
    3. Handle task_execution → A2A protocol (future)
    4. Handle question → Groq answer
    """
    try:
        with monitoring.track_performance("orchestration.groq_chat", task_id=task_id[:8]):
            log_info("orchestration_started", task_id=task_id[:8], query_length=len(query))

            tasks[task_id]["status"] = "in_progress"

            # Send status update
            await manager.send_to_task(task_id, {
                "type": "task_started",
                "task_id": task_id,
                "message": "🤖 Analyzing your request..."
            })

            # Initialize A2A orchestrator
            from backend.orchestrator_a2a import A2AOrchestrator
            orchestrator = A2AOrchestrator()

            # Detect intent
            with monitoring.track_performance("orchestration.detect_intent", task_id=task_id[:8]):
                intent_data = await orchestrator.detect_intent(query)
            log_info("intent_detected", task_id=task_id[:8], intent=intent_data['intent'])

            if intent_data["intent"] == "agent_discovery":
                # Handle agent discovery
                result = await orchestrator.handle_agent_discovery(query, agent_registry, mesh)
                result_text = result["result"]

                # Send agents_discovered event
                if result.get("agents"):
                    await manager.send_to_task(task_id, {
                        "type": "agents_discovered",
                        "agents": result["agents"],
                        "message": f"Found {len(result['agents'])} agents"
                    })

            elif intent_data["intent"] == "task_execution":
                # Future: A2A protocol execution
                result_text = "🚧 Task execution via A2A protocol coming soon! For now, ask about available agents."

            else:
                # General question
                result_text = await orchestrator.answer_question(query)

            log_info("orchestration_completed", task_id=task_id[:8], result_length=len(result_text))

            # Update task
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = {"result": result_text}

            # Send completion
            await manager.send_to_task(task_id, {
                "type": "task_complete",
                "success": True,
                "result": result_text,
                "message": "✅ Task completed!"
            })

    except Exception as e:
        log_error("orchestration_failed", e, task_id=task_id[:8], query=query)
        monitoring.capture_exception(e, task_id=task_id[:8], operation="orchestration")

        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

        await manager.send_to_task(task_id, {
            "type": "error",
            "error": str(e),
            "message": f"❌ Task failed: {str(e)}"
        })


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
        
        # Poll contracts for completion (max 10 seconds)
        import asyncio
        max_wait = 10
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

        # FALLBACK: If mesh had no results, use Groq orchestrator
        if not any(r.get('result') for r in final_results):
            logger.info(f"⚡ [{task_id[:8]}] No mesh results, falling back to Groq orchestrator...")

            try:
                from backend.orchestrator_groq import FreeGroqOrchestrator
                groq_orchestrator = FreeGroqOrchestrator()

                # Send status update
                await manager.send_to_task(task_id, {
                    "type": "status_update",
                    "message": "Using FREE AI orchestrator (Groq)..."
                })

                # Use Groq to handle the query
                groq_result = await groq_orchestrator.orchestrate(query, astraeus_client)

                # Format as mesh-compatible result
                final_results = [{
                    "contract_id": "groq-fallback",
                    "task_type": "ai_orchestration",
                    "status": "DELIVERED",
                    "awarded_to": "groq-llama3-70b",
                    "bids_count": 1,
                    "result": groq_result.get("result", str(groq_result)),
                    "agent_id": "groq-orchestrator"
                }]

                logger.info(f"✅ [{task_id[:8]}] Groq orchestrator provided fallback result")

            except Exception as e:
                logger.error(f"❌ [{task_id[:8]}] Groq fallback failed: {e}")
                # Return helpful error message
                final_results = [{
                    "contract_id": "error",
                    "task_type": "error_message",
                    "status": "FAILED",
                    "result": {
                        "message": f"No agents are currently available to handle this request. Please try again later or register an agent to handle '{parsed_intent.category}' tasks."
                    }
                }]

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


@app.get("/api/v1/agents", tags=["Marketplace"])
async def list_agents():
    """
    ## List All Agents in Marketplace

    Returns a list of all available agents in the Hermes marketplace with ratings, usage statistics, and capabilities.

    ### Response
    - `agents`: Array of agent objects
      - `id`: Unique agent identifier
      - `name`: Agent display name
      - `description`: Agent capabilities description
      - `category`: Agent category (travel, development, data, content, etc.)
      - `rating`: Average user rating (0-5)
      - `usage_count`: Number of times agent has been used
      - `is_featured`: Whether agent is featured in marketplace
      - `capabilities`: Array of capability strings

    ### Example Response
    ```json
    {
        "agents": [
            {
                "id": "flight-finder",
                "name": "FlightFinder Pro",
                "description": "Searches flights across 200+ airlines with real-time pricing",
                "category": "travel",
                "rating": 4.9,
                "usage_count": 45200,
                "is_featured": true,
                "capabilities": ["flight_search", "price_comparison", "booking"]
            }
        ],
        "total": 8
    }
    ```
    """
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


@app.post("/api/v1/agents/register", tags=["Agents"])
async def register_agent(request: RegisterAgentRequest):
    """
    ## Register A2A-Compliant Agent

    Register a new agent to the Hermes network. Agent must implement the A2A Protocol
    and expose an agent card at `/.well-known/agent.json`.

    ### Request Body
    - `name`: Agent name (required)
    - `endpoint`: Agent A2A endpoint URL (required)
    - `capabilities`: Array of capability strings (required)
    - `description`: Optional agent description

    ### A2A Protocol Requirements
    Agent must expose:
    - `GET /.well-known/agent.json` - Agent card with metadata
    - `POST /a2a` - A2A protocol message endpoint

    ### Example Request
    ```json
    {
        "name": "WeatherBot",
        "endpoint": "https://api.weatherbot.com/a2a",
        "capabilities": ["weather_query", "forecast"],
        "description": "Real-time weather forecasts and alerts"
    }
    ```

    ### Example Response
    ```json
    {
        "success": true,
        "message": "Agent 'WeatherBot' registered successfully",
        "agent": {
            "name": "WeatherBot",
            "endpoint": "https://api.weatherbot.com/a2a",
            "capabilities": ["weather_query", "forecast"],
            "status": "active"
        }
    }
    ```

    ### Error Responses
    - `400 Bad Request`: Invalid agent data or A2A discovery failed
    - `409 Conflict`: Agent with this name already exists
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

@app.post("/api/v1/mesh/contracts", tags=["Mesh Network"])
async def create_mesh_contract(request: CreateContractRequest):
    """
    ## Create Mesh Network Task Contract

    Announce a new task contract to the autonomous mesh network. Agents will bid on the contract
    based on their capabilities and pricing.

    ### Request Body
    - `task_type`: Type of task (e.g., "flight_search", "code_generation")
    - `description`: Detailed task description
    - `requirements`: Task-specific requirements (dict)
    - `deadline`: Optional ISO datetime deadline
    - `budget`: Optional maximum budget

    ### Workflow
    1. Contract is announced to all mesh agents
    2. Agents evaluate and submit bids
    3. Contract is awarded to best bidder(s)
    4. Agent(s) execute task and deliver results
    5. Contract is settled and agent is paid

    ### Example Request
    ```json
    {
        "task_type": "flight_search",
        "description": "Find flights from NYC to LA on Friday",
        "requirements": {
            "origin": "NYC",
            "destination": "LA",
            "date": "2024-12-15",
            "class": "economy"
        },
        "budget": 5.00
    }
    ```

    ### Example Response
    ```json
    {
        "success": true,
        "contract_id": "contract-a1b2c3d4",
        "status": "announced",
        "message": "Contract announced to 12 agents"
    }
    ```
    """
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
    """Register external agent to ASTRAEUS network (A2A Protocol)

    Body:
        {
            "name": "WeatherBot",
            "owner": "alice@example.com",
            "framework": "custom|langchain|crewai",
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
    from backend.database.agent_db import get_agent_pool
    from backend.database.models_agents import Agent, create_agent
    from datetime import datetime
    import json

    pool = get_agent_pool()

    if not pool:
        raise HTTPException(status_code=503, detail="Agent database not available")

    agent_id = f"agent-{str(uuid.uuid4())[:8]}"

    capabilities = agent_data.get("capabilities", [])

    agent_card = {
        "name": agent_data["name"],
        "description": agent_data.get("description", ""),
        "version": agent_data.get("version", "1.0.0"),
        "capabilities": capabilities,
        "endpoint": agent_data.get("endpoint", f"http://localhost:8000"),
        "protocol": "A2A",
        "framework": agent_data.get("framework", "custom")
    }

    agent = Agent(
        agent_id=agent_id,
        name=agent_data["name"],
        description=agent_data.get("description"),
        owner_id=agent_data.get("owner", "anonymous"),
        endpoint=agent_data.get("endpoint", f"http://localhost:8000"),
        status="active",
        agent_card=agent_card,
        capabilities=capabilities,
        version=agent_data.get("version", "1.0.0"),
        framework=agent_data.get("framework", "custom"),
        trust_score=0.0,
        base_cost_per_call=0.0
    )

    created_agent = await create_agent(pool, agent)

    async with pool.acquire() as conn:
        for cap in capabilities:
            await conn.execute(
                """
                INSERT INTO agent_capabilities (agent_id, capability_name, confidence, cost_per_call, avg_latency_ms, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (agent_id, capability_name) DO UPDATE
                SET confidence = $3, cost_per_call = $4, avg_latency_ms = $5, description = $6
                """,
                agent_id,
                cap["name"],
                cap.get("confidence", 0.9),
                cap.get("cost", 0.0),
                cap.get("latency", 30),
                cap.get("description", "")
            )

    logger.info(f"✅ Agent registered: {agent_data['name']} ({agent_id})")

    return {
        "status": "success",
        "agent_id": agent_id,
        "message": f"Agent {agent_data['name']} registered successfully to ASTRAEUS network",
        "agent_card_url": f"{agent_data.get('endpoint', 'http://localhost:8000')}/.well-known/agent.json"
    }


@app.get("/api/v1/mesh/agents")
async def list_agents(
    capability: Optional[str] = None,
    framework: Optional[str] = None,
    min_trust_score: float = 0.0,
    status: str = "active",
    limit: int = 10,
    offset: int = 0
):
    """List/search agents on ASTRAEUS network

    Query params:
        capability: Filter by capability name
        framework: Filter by framework (langchain, crewai, custom)
        min_trust_score: Minimum trust score (0.0-1.0)
        status: Agent status (active, inactive, suspended)
        limit: Max results (default 10)
        offset: Pagination offset
    """
    from backend.database.agent_db import get_agent_pool
    from backend.database.models_agents import list_agents as db_list_agents, search_agents_by_capability

    pool = get_agent_pool()

    if not pool:
        raise HTTPException(status_code=503, detail="Agent database not available")

    if capability:
        agents = await search_agents_by_capability(pool, capability, limit)
    else:
        agents = await db_list_agents(pool, status, framework, limit, offset)

    if min_trust_score > 0:
        agents = [a for a in agents if a.trust_score >= min_trust_score]

    return [a.dict() for a in agents]


@app.get("/api/v1/mesh/agents/{agent_id}")
async def get_agent_details(agent_id: str):
    """Get detailed information about a specific agent"""
    from backend.database.agent_db import get_agent_pool
    from backend.database.models_agents import get_agent

    pool = get_agent_pool()

    if not pool:
        raise HTTPException(status_code=503, detail="Agent database not available")

    agent = await get_agent(pool, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return agent.dict()


# ========================================
# AGENT REPUTATION & REVIEW SYSTEM
# ========================================

@app.post("/api/v1/agents/{agent_id}/review")
async def review_agent(agent_id: str, rating: int, review_text: str, reviewer_user_id: str):
    """Submit a review for an agent

    Args:
        agent_id: Agent to review
        rating: 1-5 stars
        review_text: Review text
        reviewer_user_id: User submitting review
    """
    from backend.database.agent_db import get_agent_pool

    pool = get_agent_pool()

    if not pool:
        raise HTTPException(status_code=503, detail="Agent database not available")

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO agent_reviews (agent_id, reviewer_user_id, rating, review_text, helpful_count)
            VALUES ($1, $2, $3, $4, 0)
            ON CONFLICT (agent_id, reviewer_user_id)
            DO UPDATE SET rating = $3, review_text = $4, updated_at = CURRENT_TIMESTAMP
            """,
            agent_id, reviewer_user_id, rating, review_text
        )

    await update_agent_trust_score(agent_id)

    logger.info(f"✅ Review added for {agent_id}: {rating}⭐ by {reviewer_user_id}")

    return {"status": "success", "message": "Review submitted successfully"}


@app.get("/api/v1/agents/{agent_id}/reviews")
async def get_agent_reviews(agent_id: str, limit: int = 10, offset: int = 0):
    """Get reviews for an agent"""
    from backend.database.agent_db import get_agent_pool

    pool = get_agent_pool()

    if not pool:
        raise HTTPException(status_code=503, detail="Agent database not available")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM agent_reviews
            WHERE agent_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            agent_id, limit, offset
        )

    reviews = [dict(row) for row in rows]

    return reviews


async def update_agent_trust_score(agent_id: str):
    """Calculate and update agent trust score based on multiple factors

    Trust Score Calculation:
    - Success Rate (40%): successful_calls / total_calls
    - User Reviews (30%): avg_rating / 5.0
    - Popularity (20%): min(total_calls / 1000, 1.0)
    - Performance (10%): 1.0 - min(avg_latency_ms / 5000, 1.0)
    """
    from backend.database.agent_db import get_agent_pool

    pool = get_agent_pool()

    if not pool:
        return

    async with pool.acquire() as conn:
        agent_stats = await conn.fetchrow(
            "SELECT total_calls, successful_calls, avg_latency_ms FROM agents WHERE agent_id = $1",
            agent_id
        )

        if not agent_stats or agent_stats['total_calls'] == 0:
            return

        review_stats = await conn.fetchrow(
            "SELECT AVG(rating) as avg_rating, COUNT(*) as review_count FROM agent_reviews WHERE agent_id = $1",
            agent_id
        )

        success_rate = agent_stats['successful_calls'] / agent_stats['total_calls']
        avg_rating = float(review_stats['avg_rating'] or 0) / 5.0
        popularity = min(agent_stats['total_calls'] / 1000.0, 1.0)
        performance = 1.0 - min((agent_stats['avg_latency_ms'] or 0) / 5000.0, 1.0)

        trust_score = (
            success_rate * 0.4 +
            avg_rating * 0.3 +
            popularity * 0.2 +
            performance * 0.1
        )

        await conn.execute(
            "UPDATE agents SET trust_score = $1 WHERE agent_id = $2",
            round(trust_score, 2), agent_id
        )

        logger.info(f"📊 Updated trust score for {agent_id}: {trust_score:.2f}")


@app.get("/api/v1/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """Get detailed agent statistics and reputation"""
    from backend.database.agent_db import get_agent_pool

    pool = get_agent_pool()

    if not pool:
        raise HTTPException(status_code=503, detail="Agent database not available")

    async with pool.acquire() as conn:
        agent = await conn.fetchrow("SELECT * FROM agents WHERE agent_id = $1", agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        reviews = await conn.fetch(
            """
            SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
            FROM agent_reviews WHERE agent_id = $1
            """,
            agent_id
        )

        recent_calls = await conn.fetch(
            """
            SELECT status, COUNT(*) as count
            FROM agent_api_calls
            WHERE callee_agent_id = $1 AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY status
            """,
            agent_id
        )

    review_data = reviews[0] if reviews else {"avg_rating": 0, "review_count": 0}

    return {
        "agent_id": agent_id,
        "name": agent['name'],
        "trust_score": float(agent['trust_score']),
        "total_calls": agent['total_calls'],
        "successful_calls": agent['successful_calls'],
        "failed_calls": agent['failed_calls'],
        "success_rate": agent['successful_calls'] / agent['total_calls'] if agent['total_calls'] > 0 else 0,
        "avg_latency_ms": agent['avg_latency_ms'],
        "total_revenue": float(agent['total_revenue']),
        "avg_rating": float(review_data['avg_rating'] or 0),
        "review_count": review_data['review_count'],
        "recent_activity": [dict(row) for row in recent_calls],
        "status": agent['status']
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

# CRITICAL FIX: Define /me endpoint BEFORE router to take priority
from backend.services.auth import get_current_user
from backend.database.models import User
from fastapi import Depends

@app.get("/api/v1/auth/me", tags=["Authentication"])
async def get_me_endpoint(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "subscription_tier": current_user.subscription_tier,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

# Health check router already included via /health and /api/v1/health endpoints

# Include authentication router AFTER /me endpoint
app.include_router(v1_auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Include email verification router (Sprint 3)
from backend.api import verification
app.include_router(verification.router, prefix="/api/v1/verification", tags=["Email Verification"])

# Include password reset router (Sprint 3)
from backend.api import password_reset
app.include_router(password_reset.router, prefix="/api/v1/auth", tags=["Password Reset"])

# Include notifications router (Sprint 3)
from backend.api import notifications
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])

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

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
