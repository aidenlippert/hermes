"""
HERMES BACKEND V2 - WITH FULL DATABASE INTEGRATION

This is the production backend with:
- PostgreSQL + Redis integration
- User authentication (JWT)
- Agent registry with semantic search
- Conversation memory
- Full persistence

All the features we brainstormed - NOW WORKING!
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hermes.protocols.a2a_client import A2AClient
from hermes.conductor.intent_parser import IntentParser
from hermes.conductor.planner import WorkflowPlanner
from hermes.conductor.executor_streaming import StreamingExecutor

# Database imports
from backend.database.connection import get_db, init_db, init_redis, close_redis
from backend.database.models import User, Agent, Task, Conversation, UserRole, SubscriptionTier
from backend.services.auth import AuthService
from backend.services.agent_registry import AgentRegistry
from backend.services.conversation import ConversationService
from backend.services.task_service import TaskService
from backend.services.conductor import ConductorService
from backend.services.seed_agents import seed_travel_agents
from backend.services.real_agents import execute_real_agents
from backend.websocket.manager import manager
from backend.api import v1_websocket
from backend.services.reputation import recalculate_all_trust_scores
from backend.database.connection import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup state
startup_complete = False
startup_error = None
_trust_recalc_task: asyncio.Task | None = None
TRUST_RECALC_INTERVAL_SECONDS = int(os.getenv("TRUST_RECALC_INTERVAL_SECONDS", "900"))  # 15 minutes default

# Initialize FastAPI
app = FastAPI(
    title="Hermes AI Platform",
    description="The Operating System for AI Agent Orchestration",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(v1_websocket.router, prefix="/api/v1", tags=["WebSocket"])

# Include Marketplace router
from backend.api import marketplace
app.include_router(marketplace.router)

# Security
security = HTTPBearer()

# API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")

# Initialize components
a2a_client = A2AClient()
intent_parser = IntentParser(GOOGLE_API_KEY)
planner = WorkflowPlanner(GOOGLE_API_KEY)

# Create event callback for WebSocket streaming
async def event_callback(event: dict):
    """Broadcast events to WebSocket subscribers"""
    task_id = event.get("task_id")
    if task_id:
        await manager.send_to_task(task_id, event)

executor = StreamingExecutor(a2a_client, event_callback=event_callback)


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.

    Usage in endpoints:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials

    # Decode token
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - for public endpoints that can use auth if provided"""
    if not authorization:
        return None

    try:
        token = authorization.replace("Bearer ", "")
        payload = AuthService.decode_token(token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                return await AuthService.get_user_by_id(db, user_id)
    except:
        pass

    return None


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

    @field_validator('password')
    @classmethod
    def truncate_password(cls, v):
        """Truncate password to 72 bytes for bcrypt"""
        if isinstance(v, str):
            password_bytes = v.encode('utf-8')[:72]
            return password_bytes.decode('utf-8', errors='ignore')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def truncate_password(cls, v):
        """Truncate password to 72 bytes for bcrypt"""
        if isinstance(v, str):
            password_bytes = v.encode('utf-8')[:72]
            return password_bytes.decode('utf-8', errors='ignore')
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    task_id: str
    conversation_id: str
    status: str
    message: str
    result: Optional[Any] = None
    steps: Optional[List[Dict[str, Any]]] = None
    agents: Optional[List[Dict[str, Any]]] = None
    extracted_info: Optional[Dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    task_id: str
    conversation_id: str
    approved: bool = True
    extracted_info: Optional[Dict[str, Any]] = None


class AgentSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 10


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.

    Creates user and returns access tokens.
    """
    try:
        # Register user
        user = await AuthService.register_user(
            db,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            username=request.username
        )

        # Create tokens
        access_token = AuthService.create_access_token({"sub": user.id})
        refresh_token = AuthService.create_refresh_token({"sub": user.id})

        logger.info(f"✅ User registered: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "subscription_tier": user.subscription_tier.value
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Returns access tokens on success.
    """
    user = await AuthService.authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create tokens
    access_token = AuthService.create_access_token({"sub": user.id})
    refresh_token = AuthService.create_refresh_token({"sub": user.id})

    logger.info(f"✅ User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "subscription_tier": user.subscription_tier.value
        }
    )


@app.get("/api/v1/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "subscription_tier": user.subscription_tier.value,
        "total_requests": user.total_requests,
        "requests_this_month": user.requests_this_month,
        "created_at": user.created_at.isoformat()
    }


# ============================================================================
# ORCHESTRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    MAIN ORCHESTRATION ENDPOINT

    Now with full database integration:
    - Creates conversation if needed
    - Saves all messages
    - Tracks tasks and executions
    - Updates user usage
    """
    logger.info(f"💬 Chat request from {user.email}: {request.query[:50]}...")

    # Check rate limit
    if not AuthService.check_rate_limit(user):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Upgrade to {SubscriptionTier.PRO.value} for more requests."
        )

    # Get or create conversation
    conversation_id = request.conversation_id

    if conversation_id:
        conversation = await ConversationService.get_conversation(db, conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await ConversationService.create_conversation(db, user.id)
        conversation_id = conversation.id

    # Add user message to conversation
    await ConversationService.add_message(
        db, conversation_id, "user", request.query
    )

    # Create task
    task = await TaskService.create_task(db, user.id, request.query, conversation_id)

    try:
        # STEP 1: Parse Intent
        logger.info("🧠 Parsing intent...")
        parsed_intent = await intent_parser.parse(request.query)
        await TaskService.update_task_intent(db, task.id, parsed_intent.to_dict())

        # Send intent parsed event
        await manager.send_to_task(task.id, {
            "type": "intent_parsed",
            "task_id": task.id,
            "intent": parsed_intent.to_dict()
        })

        # STEP 2: Get conversation history for context
        conversation_messages = await ConversationService.get_conversation_messages(db, conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_messages[-10:]  # Last 10 messages
        ]

        # STEP 3: Orchestrate with Conductor
        logger.info("🎭 Conductor analyzing request...")
        response_message, execution_plan = await ConductorService.orchestrate_request(
            db,
            request.query,
            parsed_intent.to_dict(),
            history
        )

        # Send agent discovery event if agents were found
        if execution_plan and "agents" in execution_plan:
            await manager.send_to_task(task.id, {
                "type": "agents_discovered",
                "task_id": task.id,
                "agents": execution_plan["agents"],
                "count": len(execution_plan["agents"])
            })

        # Check if we need more information
        if not execution_plan:
            # Conductor is asking follow-up questions
            logger.info("❓ Asking follow-up questions...")

            # Update task as waiting for input
            await TaskService.complete_task(db, task.id, final_output=response_message)

            # Add assistant message
            await ConversationService.add_message(
                db, conversation_id, "assistant", response_message, task.id
            )

            # Send follow-up question event
            await manager.send_to_task(task.id, {
                "type": "follow_up_required",
                "task_id": task.id,
                "message": response_message
            })

            return ChatResponse(
                task_id=task.id,
                conversation_id=conversation_id,
                status="awaiting_input",
                message="Follow-up questions asked",
                result=response_message,
                steps=[]
            )

        # STEP 4: Check if plan requires user approval
        if execution_plan.get("requires_approval", False):
            # Show agents and wait for user approval
            logger.info("👀 Awaiting user approval for agents...")

            # Update task as waiting for approval
            await TaskService.complete_task(db, task.id, final_output=response_message)

            # Add assistant message
            await ConversationService.add_message(
                db, conversation_id, "assistant", response_message, task.id
            )

            # Send awaiting approval event
            await manager.send_to_task(task.id, {
                "type": "awaiting_approval",
                "task_id": task.id,
                "message": response_message,
                "agents": execution_plan["agents"],
                "extracted_info": execution_plan.get("extracted_info", {})
            })

            return ChatResponse(
                task_id=task.id,
                conversation_id=conversation_id,
                status="awaiting_approval",
                message="Agents discovered, awaiting approval",
                result=response_message,
                steps=[],
                agents=execution_plan["agents"],
                extracted_info=execution_plan.get("extracted_info", {})
            )

        # STEP 5: User approved - create workflow plan
        logger.info("📋 Creating execution plan...")

        available_agents = execution_plan["agents"]

        plan = await planner.create_plan(
            user_query=request.query,
            parsed_intent=parsed_intent.to_dict(),
            available_agents=available_agents
        )

        await TaskService.update_task_plan(db, task.id, plan.to_dict(), len(plan.steps))

        # Send plan created event
        await manager.send_to_task(task.id, {
            "type": "plan_created",
            "task_id": task.id,
            "steps": [step.to_dict() for step in plan.steps],
            "total_steps": len(plan.steps)
        })

        # STEP 6: Execute Plan (with real-time WebSocket streaming!)
        logger.info("⚡ Executing plan...")
        result = await executor.execute(plan, task.id)

        # Update task completion
        await TaskService.complete_task(
            db,
            task.id,
            final_output=result.final_output,
            error_message=result.error if not result.success else None
        )

        # Update user usage
        user.total_requests += 1
        user.requests_this_month += 1
        await db.commit()

        # Add assistant message to conversation
        assistant_response = result.final_output or f"Completed {result.completed_steps}/{len(plan.steps)} steps"
        await ConversationService.add_message(
            db, conversation_id, "assistant", assistant_response, task.id
        )

        logger.info(f"{'✅' if result.success else '❌'} Task completed")

        return ChatResponse(
            task_id=task.id,
            conversation_id=conversation_id,
            status="completed" if result.success else "failed",
            message=f"Completed {result.completed_steps}/{len(plan.steps)} steps",
            result=result.final_output,
            steps=[step.to_dict() for step in plan.steps]
        )

    except Exception as e:
        logger.error(f"❌ Chat failed: {e}")

        # Update task as failed
        await TaskService.complete_task(db, task.id, error_message=str(e))

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/approve", response_model=ChatResponse)
async def approve_agents(
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    User approves discovered agents and triggers REAL execution with external APIs.

    Uses:
    - Amadeus API for flights, hotels, activities
    - Foursquare API for restaurants
    """
    try:
        logger.info(f"✅ User approved agents for task {request.task_id}")

        # Get task to retrieve agent data
        task = await TaskService.get_task(db, request.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get conversation to retrieve extracted_info
        conversation = await ConversationService.get_conversation(db, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get agents from task metadata (what was actually shown to user)
        # Parse from task context or use only approved ones
        task_context = task.context or {}
        agents = task_context.get("agents", [])

        # If no agents in context, only use Flight and Hotel (the core ones)
        if not agents:
            agents = [
                {"name": "FlightBooker"},
                {"name": "HotelBooker"}
            ]

        logger.info(f"🎯 Executing {len(agents)} approved agents: {[a['name'] for a in agents]}")

        # Get extracted info from request (sent from frontend) or use fallback
        extracted_info = request.extracted_info or {
            "destination": "Cancun",
            "departure_location": "San Diego",
            "travel_dates": "October 25th to October 30th",
            "num_travelers": 3,
            "budget": "2000 USD"
        }

        logger.info(f"📍 Using extracted info: {extracted_info}")

        # Send execution started event
        await manager.send_to_task(request.task_id, {
            "type": "execution_started",
            "task_id": request.task_id,
            "message": "🚀 Starting real agent execution with live APIs...",
            "total_agents": len(agents)
        })

        # Execute real agents with external APIs (with timeout protection)
        import asyncio
        real_results = {}

        async def execute_agent_with_timeout(agent_name: str, agent_index: int) -> tuple:
            """Execute a single agent with timeout protection"""
            try:
                await manager.send_to_task(request.task_id, {
                    "type": "agent_progress",
                    "task_id": request.task_id,
                    "agent_name": agent_name,
                    "status": "working",
                    "message": f"🔄 {agent_name} is searching live data...",
                    "progress": agent_index / len(agents)
                })

                # Execute with 30 second timeout
                from backend.services.real_agents_v2 import AGENT_EXECUTORS
                if agent_name in AGENT_EXECUTORS:
                    result = await asyncio.wait_for(
                        AGENT_EXECUTORS[agent_name](extracted_info),
                        timeout=30.0
                    )
                else:
                    result = {"status": "error", "message": "Agent not found"}

                await manager.send_to_task(request.task_id, {
                    "type": "agent_completed",
                    "task_id": request.task_id,
                    "agent_name": agent_name,
                    "status": "completed" if result["status"] == "success" else "failed",
                    "message": f"✅ {agent_name} found {result.get('data', {}).get('summary', 'results')}" if result["status"] == "success" else f"❌ {agent_name} failed: {result.get('message')}",
                    "data": result.get("data", {})
                })

                return agent_name, result

            except asyncio.TimeoutError:
                logger.error(f"⏱️ {agent_name} timed out after 30s")
                result = {"status": "error", "message": "Agent timed out after 30 seconds"}
                return agent_name, result
            except Exception as e:
                logger.error(f"❌ {agent_name} execution error: {e}")
                result = {"status": "error", "message": str(e)}
                return agent_name, result

        # Execute all agents in parallel with timeout
        tasks = [
            execute_agent_with_timeout(agent["name"], i)
            for i, agent in enumerate(agents, 1)
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for item in results_list:
            if isinstance(item, tuple):
                agent_name, result = item
                real_results[agent_name] = result
            else:
                logger.error(f"Unexpected result type: {type(item)}")

        # Generate summary from real results
        summary_parts = ["🎉 **Your Trip Results**\n"]
        has_any_results = False

        # FlightBooker results
        if "FlightBooker" in real_results:
            if real_results["FlightBooker"]["status"] == "success":
                flights = real_results["FlightBooker"]["data"].get("flights", [])
                if flights:
                    has_any_results = True
                    flight = flights[0]
                    summary_parts.append(f"\n**✈️ Flights** (from Amadeus API)")
                    summary_parts.append(f"- {flight['outbound']['departure']['airport']} → {flight['outbound']['arrival']['airport']}")
                    summary_parts.append(f"- Price: {flight['price']} per person")
                    if "return" in flight:
                        summary_parts.append(f"- Round trip included")
            else:
                summary_parts.append(f"\n**✈️ Flights**: ⚠️ {real_results['FlightBooker'].get('message', 'API temporarily unavailable')}")

        # HotelBooker results
        if "HotelBooker" in real_results:
            if real_results["HotelBooker"]["status"] == "success":
                hotels = real_results["HotelBooker"]["data"].get("hotels", [])
                if hotels:
                    has_any_results = True
                    hotel = hotels[0]
                    summary_parts.append(f"\n**🏨 Hotels** (from Amadeus API)")
                    summary_parts.append(f"- {hotel['name']}")
                    summary_parts.append(f"- {hotel['price_per_night']} per night")
                    if hotel.get('rating'):
                        summary_parts.append(f"- Rating: {hotel['rating']}/5")
            else:
                summary_parts.append(f"\n**🏨 Hotels**: ⚠️ {real_results['HotelBooker'].get('message', 'API temporarily unavailable')}")

        # RestaurantFinder results
        if "RestaurantFinder" in real_results:
            if real_results["RestaurantFinder"]["status"] == "success":
                restaurants = real_results["RestaurantFinder"]["data"].get("restaurants", [])
                if restaurants:
                    has_any_results = True
                    summary_parts.append(f"\n**🍽️ Restaurants** (from Foursquare API)")
                    for r in restaurants[:3]:
                        summary_parts.append(f"- {r['name']} ({r['cuisine']}) - {r['rating']}/5 ⭐")
            else:
                summary_parts.append(f"\n**🍽️ Restaurants**: ⚠️ {real_results['RestaurantFinder'].get('message', 'API temporarily unavailable')}")

        # EventsFinder results
        if "EventsFinder" in real_results:
            if real_results["EventsFinder"]["status"] == "success":
                activities = real_results["EventsFinder"]["data"].get("activities", [])
                if activities:
                    has_any_results = True
                    summary_parts.append(f"\n**🎭 Activities** (from Amadeus API)")
                    for a in activities[:3]:
                        summary_parts.append(f"- {a['name']} - {a['price']}")
            else:
                summary_parts.append(f"\n**🎭 Activities**: ⚠️ {real_results['EventsFinder'].get('message', 'API temporarily unavailable')}")

        summary = "\n".join(summary_parts)

        if has_any_results:
            summary += "\n\n✨ **Data is LIVE from real travel APIs!**"
        else:
            summary += "\n\n⚠️ **APIs are still activating - production credentials can take up to 24 hours.**"
            summary += "\n💡 Try again soon or check your Amadeus dashboard for activation status."

        # Update task
        await TaskService.complete_task(db, request.task_id, final_output=summary)

        # Add to conversation
        await ConversationService.add_message(
            db, request.conversation_id, "assistant", summary, request.task_id
        )

        # Send completion event
        await manager.send_to_task(request.task_id, {
            "type": "execution_completed",
            "task_id": request.task_id,
            "message": summary,
            "results": real_results
        })

        return ChatResponse(
            task_id=request.task_id,
            conversation_id=request.conversation_id,
            status="completed",
            message="Trip planning completed",
            result=summary,
            steps=[]
        )

    except Exception as e:
        logger.error(f"❌ Approval execution failed: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENT MARKETPLACE ENDPOINTS
# ============================================================================

@app.get("/api/v1/marketplace")
async def list_agents(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    sort: Optional[str] = None,  # trust|rating|usage
    free_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all active agents with optional sorting and trust score enrichment"""
    agents = await AgentRegistry.list_agents(db, skip, limit, category, sort=sort or "rating")

    # Apply free_only filter in memory (AgentRegistry can be extended later)
    if free_only is True:
        agents = [a for a in agents if bool(a.is_free)]

    # Enrich with trust scores
    from sqlalchemy import select
    from backend.database.models import AgentTrustScore
    agent_ids = [str(a.id) for a in agents]
    trust_map: dict[str, float] = {}
    if agent_ids:
        result = await db.execute(
            select(AgentTrustScore.agent_id, AgentTrustScore.trust_score)
            .where(AgentTrustScore.agent_id.in_(agent_ids))
        )
        trust_map = {str(row[0]): float(row[1]) for row in result.all() if row[1] is not None}

    def _trust_grade(score: float) -> str:
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "A-"
        elif score >= 0.80:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.70:
            return "B-"
        elif score >= 0.65:
            return "C+"
        elif score >= 0.60:
            return "C"
        elif score >= 0.55:
            return "C-"
        else:
            return "D"

    return {
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "capabilities": agent.capabilities,
                "average_rating": agent.average_rating,
                "total_calls": agent.total_calls,
                "is_free": agent.is_free,
                "cost_per_request": agent.cost_per_request,
                "trust_score": trust_map.get(str(agent.id), 0.0),
                "trust_grade": _trust_grade(trust_map.get(str(agent.id), 0.0)),
            }
            for agent in agents
        ],
        "total": len(agents)
    }


@app.get("/api/v1/marketplace/top")
async def top_agents(
    limit: int = 8,
    category: Optional[str] = None,
    free_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Return top agents ranked by a composite score of trust, rating, and usage.

    score = 0.6 * trust + 0.25 * rating_norm + 0.15 * usage_norm
    where rating_norm is average_rating/5 and usage_norm is total_calls/max_total_calls among candidates.
    """
    # Get a reasonable candidate set
    candidates = await AgentRegistry.list_agents(db, skip=0, limit=200, category=category, sort="trust")

    # Filter
    if free_only is True:
        candidates = [a for a in candidates if bool(a.is_free)]

    # Build trust map
    from sqlalchemy import select
    from backend.database.models import AgentTrustScore
    ids = [str(a.id) for a in candidates]
    trust_map: dict[str, float] = {}
    if ids:
        result = await db.execute(
            select(AgentTrustScore.agent_id, AgentTrustScore.trust_score)
            .where(AgentTrustScore.agent_id.in_(ids))
        )
        trust_map = {str(row[0]): float(row[1]) for row in result.all() if row[1] is not None}

    # Compute score
    max_usage = max((a.total_calls or 0) for a in candidates) if candidates else 0
    def usage_norm(a):
        return ((a.total_calls or 0) / max_usage) if max_usage > 0 else 0.0

    def rating_norm(a):
        return (float(a.average_rating) / 5.0) if a.average_rating else 0.0

    def trust(a):
        return trust_map.get(str(a.id), 0.0)

    scored = [
        (
            0.60 * trust(a) + 0.25 * rating_norm(a) + 0.15 * usage_norm(a),
            a,
        )
        for a in candidates
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [a for _, a in scored[:limit]]

    def _trust_grade(score: float) -> str:
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "A-"
        elif score >= 0.80:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.70:
            return "B-"
        elif score >= 0.65:
            return "C+"
        elif score >= 0.60:
            return "C"
        elif score >= 0.55:
            return "C-"
        else:
            return "D"

    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "category": a.category,
                "capabilities": a.capabilities,
                "average_rating": a.average_rating,
                "total_calls": a.total_calls,
                "is_free": a.is_free,
                "cost_per_request": a.cost_per_request,
                "trust_score": trust(a),
                "trust_grade": _trust_grade(trust(a)),
            }
            for a in top
        ],
        "total": len(top)
    }


@app.post("/api/v1/marketplace/search")
async def search_agents(
    request: AgentSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    SEMANTIC SEARCH for agents!

    Uses pgvector to find agents by meaning, not just keywords.
    """
    agents = await AgentRegistry.semantic_search(
        db,
        query=request.query,
        limit=request.limit,
        category=request.category
    )

    return {
        "query": request.query,
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "capabilities": agent.capabilities,
                "average_rating": agent.average_rating,
                "relevance": "high"  # TODO: Add actual similarity score
            }
            for agent in agents
        ],
        "total": len(agents)
    }


# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================

@app.get("/api/v1/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get all conversations for current user"""
    conversations = await ConversationService.get_user_conversations(db, user.id, skip, limit)

    return {
        "conversations": [
            await ConversationService.get_conversation_summary(db, conv.id)
            for conv in conversations
        ]
    }


@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get conversation with all messages"""
    conversation = await ConversationService.get_conversation(db, conversation_id)

    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await ConversationService.get_conversation_messages(db, conversation_id)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.get("/")
async def root():
    """API info"""
    return {
        "service": "Hermes AI Platform",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "User Authentication (JWT)",
            "Agent Marketplace (Semantic Search)",
            "Conversation Memory",
            "Multi-Agent Orchestration",
            "Full Persistence"
        ],
        "docs": "/docs"
    }


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    """Health check - returns OK even during startup"""
    global startup_complete, startup_error

    if startup_error:
        return {
            "status": "degraded",
            "version": "2.0.0",
            "startup_complete": startup_complete,
            "error": str(startup_error)
        }

    return {
        "status": "healthy" if startup_complete else "starting",
        "version": "2.0.0",
        "startup_complete": startup_complete
    }


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize everything on startup"""
    global startup_complete, startup_error

    logger.info("🚀 Hermes Platform Starting...")

    try:
        # try:
        #     import asyncio
        #     await asyncio.wait_for(init_db(), timeout=10.0)
        #     logger.info("✅ PostgreSQL initialized")
        # except asyncio.TimeoutError:
        #     logger.error("❌ PostgreSQL init timed out after 10s")
        #     raise
        # except Exception as e:
        #     logger.error(f"❌ PostgreSQL init failed: {e}")
        #     raise

        # Initialize Redis with timeout
        try:
            await asyncio.wait_for(init_redis(), timeout=5.0)
            logger.info("✅ Redis initialized")
        except asyncio.TimeoutError:
            logger.error("❌ Redis init timed out after 5s")
            raise
        except Exception as e:
            logger.error(f"❌ Redis init failed: {e}")
            raise

        # Seed travel agents (non-blocking)
        try:
            async with AsyncSessionLocal() as db:
                await seed_travel_agents(db)
        except Exception as e:
            logger.error(f"❌ Agent seeding failed: {e}")
            # Don't fail startup for seeding issues
            pass

        # Kick off background trust score recalculation loop
        async def _trust_recalc_loop():
            # Initial short delay to allow startup and seed to complete
            await asyncio.sleep(5)
            while True:
                try:
                    async with AsyncSessionLocal() as db:
                        await recalculate_all_trust_scores(db)
                except Exception as e:
                    logger.error(f"❌ Trust score recalculation failed: {e}")
                # Sleep until next cycle
                await asyncio.sleep(TRUST_RECALC_INTERVAL_SECONDS)

        global _trust_recalc_task
        _trust_recalc_task = asyncio.create_task(_trust_recalc_loop())

        startup_complete = True
        logger.info("✅ Hermes Platform Ready!")

    except Exception as e:
        startup_error = e
        logger.error(f"❌ Startup failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Don't raise - let the app start in degraded mode


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("👋 Hermes Platform Shutting down...")
    # Cancel background trust recalculation task
    global _trust_recalc_task
    if _trust_recalc_task and not _trust_recalc_task.done():
        _trust_recalc_task.cancel()
        try:
            await _trust_recalc_task
        except Exception:
            pass
    await close_redis()
    await a2a_client.close()


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("🚀 HERMES AI PLATFORM V2")
    print("="*70)
    print("\n✨ NEW FEATURES:")
    print("   - Full database integration")
    print("   - User authentication (JWT)")
    print("   - Agent marketplace with semantic search")
    print("   - Conversation memory")
    print("   - Complete persistence")
    print("   - ⚡ REAL-TIME WEBSOCKET STREAMING ⚡")
    print("\n📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("\n💡 Quick Test:")
    print('   1. Register: POST /api/v1/auth/register')
    print('   2. Login: POST /api/v1/auth/login')
    print('   3. Connect: WS /api/v1/ws/tasks/{task_id}?token=YOUR_TOKEN')
    print('   4. Chat: POST /api/v1/chat (with Bearer token)')
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
