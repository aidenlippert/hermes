"""
Simple Backend Startup - No Database Required
Runs backend with mock data for testing frontend integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ASTRAEUS API (Mock)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

@app.post("/api/v1/auth/login")
async def login(req: LoginRequest):
    return {
        "access_token": "mock_token_" + req.email,
        "refresh_token": "mock_refresh",
        "token_type": "bearer",
        "user": {
            "id": "user_123",
            "email": req.email,
            "username": req.email.split("@")[0],
            "full_name": "Test User",
            "role": "developer",
            "subscription_tier": "pro"
        }
    }

@app.post("/api/v1/auth/register")
async def register(req: RegisterRequest):
    return {
        "access_token": "mock_token_" + req.email,
        "refresh_token": "mock_refresh",
        "token_type": "bearer",
        "user": {
            "id": "user_new",
            "email": req.email,
            "username": req.email.split("@")[0],
            "full_name": req.full_name or "New User",
            "role": "developer",
            "subscription_tier": "free"
        }
    }

@app.get("/api/v1/marketplace")
async def list_agents():
    return {
        "agents": [
            {
                "id": "agent_1",
                "name": "Translation Bot",
                "description": "Translates text between 50+ languages",
                "category": "translation",
                "capabilities": ["translate", "detect_language"],
                "average_rating": 4.8,
                "total_calls": 1543,
                "is_free": False,
                "cost_per_request": 0.05
            },
            {
                "id": "agent_2",
                "name": "Free Summarizer",
                "description": "Summarizes long text into key points",
                "category": "text_processing",
                "capabilities": ["summarize", "extract_keywords"],
                "average_rating": 4.5,
                "total_calls": 892,
                "is_free": True,
                "cost_per_request": 0
            }
        ],
        "total": 2
    }

@app.get("/api/v1/agents/owned")
async def list_owned_agents():
    return {
        "agents": [
            {
                "id": "my_agent_1",
                "name": "My Translation Service",
                "description": "Premium translation with context awareness",
                "category": "translation",
                "capabilities": ["translate", "context_aware"],
                "average_rating": 4.9,
                "total_calls": 234,
                "is_free": False,
                "cost_per_request": 0.10,
                "is_active": True,
                "is_public": True,
                "total_revenue": 23.40,
                "api_endpoint": "http://localhost:8001"
            }
        ]
    }

@app.get("/api/v1/payments/credits/balance")
async def get_balance():
    return {"balance": 150.00}

@app.get("/api/v1/payments/credits/transactions")
async def get_transactions():
    return {
        "transactions": [
            {
                "id": "tx_1",
                "transaction_type": "purchase",
                "amount": 50.0,
                "balance_after": 150.0,
                "description": "Credit purchase - 50 credits",
                "created_at": "2025-01-15T10:30:00Z",
                "status": "completed"
            },
            {
                "id": "tx_2",
                "transaction_type": "usage",
                "amount": -0.05,
                "balance_after": 100.0,
                "description": "Agent execution - Translation Bot",
                "created_at": "2025-01-14T15:20:00Z",
                "status": "completed"
            }
        ]
    }

@app.get("/api/v1/contracts")
async def list_contracts():
    return {
        "contracts": [
            {
                "id": "contract_1",
                "title": "Website Translation Project",
                "description": "Translate entire website to 5 languages",
                "budget": 500.0,
                "escrow_amount": 500.0,
                "status": "active",
                "client_id": "user_123",
                "developer_id": "dev_456",
                "agent_id": "agent_1",
                "created_at": "2025-01-10T09:00:00Z",
                "updated_at": "2025-01-10T09:00:00Z"
            }
        ]
    }

@app.get("/api/v1/contracts/{contract_id}")
async def get_contract(contract_id: str):
    return {
        "id": contract_id,
        "title": "Website Translation Project",
        "description": "Translate entire website to 5 languages",
        "budget": 500.0,
        "escrow_amount": 300.0,
        "status": "active",
        "client_id": "user_123",
        "developer_id": "dev_456",
        "agent_id": "agent_1",
        "created_at": "2025-01-10T09:00:00Z",
        "updated_at": "2025-01-15T14:30:00Z",
        "milestones": [
            {
                "id": "m1",
                "title": "Homepage Translation",
                "description": "Translate homepage to all languages",
                "amount": 100.0,
                "status": "completed",
                "due_date": "2025-01-15T00:00:00Z"
            }
        ],
        "timeline": [
            {
                "id": "t1",
                "event_type": "created",
                "description": "Contract created",
                "timestamp": "2025-01-10T09:00:00Z",
                "user_id": "user_123"
            },
            {
                "id": "t2",
                "event_type": "funded",
                "description": "Escrow funded with $500",
                "timestamp": "2025-01-10T09:05:00Z",
                "user_id": "user_123"
            }
        ]
    }

@app.get("/api/v1/analytics/agent/{agent_id}")
async def get_agent_analytics(agent_id: str):
    return {
        "total_calls": 234,
        "success_rate": 98.5,
        "average_response_time": 250,
        "average_rating": 4.9,
        "total_reviews": 45,
        "total_revenue": 23.40,
        "average_per_call": 0.10,
        "call_volume_trend": [
            {"date": "2025-01-14", "calls": 45, "revenue": 4.50},
            {"date": "2025-01-15", "calls": 52, "revenue": 5.20}
        ],
        "top_users": [
            {"user_id": "user_abc", "calls": 23, "revenue": 2.30},
            {"user_id": "user_xyz", "calls": 18, "revenue": 1.80}
        ],
        "top_clients": [
            {"user_id": "user_abc", "calls": 23, "revenue": 2.30}
        ],
        "error_distribution": [],
        "reviews": [
            {
                "user_id": "user_abc",
                "rating": 5,
                "comment": "Excellent translation quality!",
                "created_at": "2025-01-14T10:00:00Z"
            }
        ],
        "transactions": [],
        "payout_history": [],
        "revenue_trend": []
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "mode": "mock"}

if __name__ == "__main__":
    logger.info("🚀 Starting ASTRAEUS Mock Backend...")
    logger.info("   Mode: Simple (No Database)")
    logger.info("   Mock agents: 4 running on ports 8001-8004")
    logger.info("   API URL: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
