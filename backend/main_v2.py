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
from backend.websocket.manager import manager
from backend.api import v1_websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Include WebSocket router
app.include_router(v1_websocket.router, prefix="/api/v1", tags=["WebSocket"])

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

        # STEP 2: Get Available Agents from Database
        logger.info("🔍 Finding agents...")

        if parsed_intent.required_capabilities:
            agents = await AgentRegistry.search_by_capabilities(
                db, parsed_intent.required_capabilities, limit=5
            )
        else:
            # Semantic search as fallback
            agents = await AgentRegistry.semantic_search(db, request.query, limit=5)

        if not agents:
            # No agents - respond directly with LLM
            logger.info("⚠️ No agents found, responding directly with LLM")

            from backend.services.llm_provider import get_llm_provider
            llm = get_llm_provider()

            # Get conversation history for context
            conversation_messages = await ConversationService.get_messages(db, conversation_id)
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation_messages[-10:]  # Last 10 messages for context
            ]

            # Generate response
            response_text = await llm.chat_completion(messages)

            # Update task
            await TaskService.complete_task(db, task.id, final_output=response_text)

            # Add assistant message
            await ConversationService.add_message(
                db, conversation_id, "assistant", response_text, task.id
            )

            logger.info("✅ Direct LLM response sent")

            return ChatResponse(
                task_id=task.id,
                conversation_id=conversation_id,
                status="completed",
                message="Responded with direct LLM",
                result=response_text,
                steps=[]
            )

        # Convert to format planner expects
        available_agents = [
            {
                "name": agent.name,
                "endpoint": agent.endpoint,
                "capabilities": agent.capabilities,
                "description": agent.description
            }
            for agent in agents
        ]

        # STEP 3: Create Plan
        logger.info("📋 Creating execution plan...")
        plan = await planner.create_plan(
            user_query=request.query,
            parsed_intent=parsed_intent.to_dict(),
            available_agents=available_agents
        )

        await TaskService.update_task_plan(db, task.id, plan.to_dict(), len(plan.steps))

        # STEP 4: Execute Plan (with real-time WebSocket streaming!)
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


# ============================================================================
# AGENT MARKETPLACE ENDPOINTS
# ============================================================================

@app.get("/api/v1/marketplace")
async def list_agents(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all active agents"""
    agents = await AgentRegistry.list_agents(db, skip, limit, category)

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
                "cost_per_request": agent.cost_per_request
            }
            for agent in agents
        ],
        "total": len(agents)
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
    """Health check - simple version for Railway"""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize everything on startup"""
    logger.info("🚀 Hermes Platform Starting...")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ PostgreSQL initialized")
    except Exception as e:
        logger.error(f"❌ PostgreSQL init failed: {e}")

    # Initialize Redis
    try:
        await init_redis()
        logger.info("✅ Redis initialized")
    except Exception as e:
        logger.error(f"❌ Redis init failed: {e}")

    logger.info("✅ Hermes Platform Ready!")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("👋 Hermes Platform Shutting down...")
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
