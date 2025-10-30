"""
Database Initialization Script
Run this to create all tables in the database
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database.connection import engine
from backend.database.models import Base
# Import workflow models so SQLAlchemy knows about them
from backend.database.models_workflows import (
    Workflow, WorkflowNode, WorkflowEdge, WorkflowRun, 
    NodeRun, WorkflowTemplate, WorkflowPermission
)
from backend.services.agent_registry import AgentRegistry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database tables and seed initial data"""
    try:
        logger.info("Creating database tables...")

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables created successfully!")

        # Initialize agent registry with sample agents
        logger.info("Initializing agent registry...")

        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with AsyncSessionLocal() as session:
            registry = AgentRegistry(session)

            # Register sample agents
            sample_agents = [
                {
                    "name": "FlightFinder Pro",
                    "description": "Searches flights across 200+ airlines with real-time pricing and availability",
                    "category": "travel",
                    "capabilities": ["flight_search", "price_comparison", "booking_assistance"],
                    "is_free": True,
                    "is_featured": True,
                },
                {
                    "name": "HotelScout AI",
                    "description": "Finds the best hotels with reviews, amenities, and real-time availability",
                    "category": "travel",
                    "capabilities": ["hotel_search", "review_analysis", "price_tracking"],
                    "is_free": True,
                    "is_featured": True,
                },
                {
                    "name": "CodeAssist Ultra",
                    "description": "Advanced AI coding assistant for debugging, code generation, and refactoring",
                    "category": "development",
                    "capabilities": ["code_generation", "debugging", "refactoring", "code_review"],
                    "is_free": True,
                    "is_featured": True,
                },
                {
                    "name": "DataAnalyzer Pro",
                    "description": "Powerful data analysis and visualization agent for business intelligence",
                    "category": "data",
                    "capabilities": ["data_analysis", "visualization", "reporting", "predictive_analytics"],
                    "is_free": False,
                    "cost_per_request": 0.10,
                    "is_featured": True,
                },
                {
                    "name": "ContentWriter AI",
                    "description": "Professional content creation for blogs, articles, and marketing copy",
                    "category": "content",
                    "capabilities": ["blog_writing", "copywriting", "seo_optimization", "content_planning"],
                    "is_free": True,
                    "is_featured": False,
                },
                {
                    "name": "EmailAssistant",
                    "description": "Smart email management with categorization, summarization, and auto-responses",
                    "category": "productivity",
                    "capabilities": ["email_sorting", "summarization", "auto_reply", "scheduling"],
                    "is_free": True,
                    "is_featured": False,
                },
                {
                    "name": "MarketAnalyst",
                    "description": "Real-time stock market analysis with trend prediction and portfolio optimization",
                    "category": "finance",
                    "capabilities": ["market_analysis", "trend_prediction", "portfolio_optimization", "risk_assessment"],
                    "is_free": False,
                    "cost_per_request": 0.25,
                    "is_featured": False,
                },
                {
                    "name": "CustomerSupport Bot",
                    "description": "Intelligent customer service automation with multi-language support",
                    "category": "support",
                    "capabilities": ["ticket_handling", "faq_responses", "escalation_management", "sentiment_analysis"],
                    "is_free": True,
                    "is_featured": False,
                },
            ]

            for agent_data in sample_agents:
                try:
                    await registry.register_agent(
                        agent_id=agent_data["name"].lower().replace(" ", "-"),
                        **agent_data
                    )
                    logger.info(f"  ✓ Registered agent: {agent_data['name']}")
                except Exception as e:
                    logger.warning(f"  ⚠ Failed to register {agent_data['name']}: {e}")

            await session.commit()

        logger.info("✅ Agent registry initialized!")
        logger.info("\n🎉 Database initialization complete!")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())