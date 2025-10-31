"""
Database Seeding Script for Testing ASTRAEUS

Creates test users, agents, contracts, and sample data for end-to-end testing.

Usage:
    python -m backend.scripts.seed_test_data
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.database.connection import DATABASE_URL
from backend.database.models import (
    User, Agent, Contract, CreditTransaction,
    Conversation, Message, Execution
)
from backend.database.models_orchestration import OrchestrationPlan
from backend.database.models_security import ReputationScore
from backend.database.models_analytics import UserAnalytics, AgentAnalytics


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_test_users(session: AsyncSession):
    """Create test users"""
    print("Creating test users...")

    users = [
        User(
            id="test_user_1",
            email="alice@test.com",
            username="alice",
            full_name="Alice Johnson",
            hashed_password="$2b$12$test_hash_1",
            role="user",
            subscription_tier="pro",
            credit_balance=100.0,
            is_active=True,
            email_verified=True
        ),
        User(
            id="test_user_2",
            email="bob@test.com",
            username="bob",
            full_name="Bob Smith",
            hashed_password="$2b$12$test_hash_2",
            role="user",
            subscription_tier="free",
            credit_balance=25.0,
            is_active=True,
            email_verified=True
        ),
        User(
            id="agent_dev_1",
            email="dev@test.com",
            username="developer",
            full_name="Agent Developer",
            hashed_password="$2b$12$test_hash_3",
            role="developer",
            subscription_tier="enterprise",
            credit_balance=500.0,
            is_active=True,
            email_verified=True
        )
    ]

    for user in users:
        session.add(user)

    await session.commit()
    print(f"✅ Created {len(users)} test users")
    return users


async def create_test_agents(session: AsyncSession, developer_id: str):
    """Create test agents connected to mock servers"""
    print("Creating test agents...")

    agents = [
        Agent(
            id="agent_translator",
            name="Translation Bot",
            description="Professional translation service supporting 50+ languages with high accuracy",
            owner_id=developer_id,
            category="translation",
            capabilities=["translate", "detect_language", "transliterate"],
            pricing_model="pay_per_use",
            cost_per_request=0.05,
            api_endpoint="http://localhost:8001/execute",
            is_public=True,
            is_verified=True,
            is_active=True,
            is_free=False,
            average_rating=4.7,
            total_calls=1234,
            total_revenue=61.70,
            uptime_percentage=99.5,
            metadata={
                "supported_languages": ["en", "es", "fr", "de", "ja", "zh"],
                "max_characters": 10000
            }
        ),
        Agent(
            id="agent_summarizer",
            name="Free Summarizer",
            description="Fast and accurate text summarization for documents, articles, and reports",
            owner_id=developer_id,
            category="text_processing",
            capabilities=["summarize", "extract_key_points", "tldr"],
            pricing_model="free",
            cost_per_request=0.0,
            api_endpoint="http://localhost:8002/execute",
            is_public=True,
            is_verified=True,
            is_active=True,
            is_free=True,
            average_rating=4.5,
            total_calls=5678,
            total_revenue=0.0,
            uptime_percentage=98.2,
            metadata={
                "max_words": 5000,
                "styles": ["concise", "detailed", "bullet_points"]
            }
        ),
        Agent(
            id="agent_code_analyzer",
            name="Code Analyzer Pro",
            description="Advanced code analysis with security scanning, quality metrics, and improvement suggestions",
            owner_id=developer_id,
            category="development",
            capabilities=["analyze_code", "suggest_improvements", "detect_bugs", "security_scan"],
            pricing_model="pay_per_use",
            cost_per_request=0.10,
            api_endpoint="http://localhost:8003/execute",
            is_public=True,
            is_verified=True,
            is_active=True,
            is_free=False,
            average_rating=4.9,
            total_calls=891,
            total_revenue=89.10,
            uptime_percentage=99.9,
            metadata={
                "supported_languages": ["python", "javascript", "typescript", "java", "go"],
                "max_lines": 10000
            }
        ),
        Agent(
            id="agent_langchain",
            name="LangChain AI Assistant",
            description="Real AI agent powered by LangChain and GPT-3.5 for complex reasoning and task execution",
            owner_id=developer_id,
            category="ai_assistant",
            capabilities=["reasoning", "summarization", "sentiment_analysis", "keyword_extraction"],
            pricing_model="pay_per_use",
            cost_per_request=0.15,
            api_endpoint="http://localhost:8004/execute",
            is_public=True,
            is_verified=True,
            is_active=True,
            is_free=False,
            average_rating=4.8,
            total_calls=432,
            total_revenue=64.80,
            uptime_percentage=97.5,
            metadata={
                "model": "gpt-3.5-turbo",
                "framework": "langchain",
                "has_memory": True
            }
        )
    ]

    for agent in agents:
        session.add(agent)

    await session.commit()
    print(f"✅ Created {len(agents)} test agents")
    return agents


async def create_reputation_scores(session: AsyncSession, agents):
    """Create reputation scores for agents"""
    print("Creating reputation scores...")

    scores = [
        ReputationScore(
            agent_id="agent_translator",
            quality_score=0.85,
            reliability_score=0.90,
            speed_score=0.88,
            honesty_score=0.92,
            collaboration_score=0.80,
            overall_reputation=0.87,
            trust_grade="A",
            total_reviews=87,
            verified_reviews=65
        ),
        ReputationScore(
            agent_id="agent_summarizer",
            quality_score=0.78,
            reliability_score=0.85,
            speed_score=0.95,
            honesty_score=0.88,
            collaboration_score=0.75,
            overall_reputation=0.84,
            trust_grade="B+",
            total_reviews=156,
            verified_reviews=98
        ),
        ReputationScore(
            agent_id="agent_code_analyzer",
            quality_score=0.95,
            reliability_score=0.98,
            speed_score=0.82,
            honesty_score=0.96,
            collaboration_score=0.88,
            overall_reputation=0.92,
            trust_grade="A+",
            total_reviews=42,
            verified_reviews=38
        ),
        ReputationScore(
            agent_id="agent_langchain",
            quality_score=0.88,
            reliability_score=0.82,
            speed_score=0.75,
            honesty_score=0.90,
            collaboration_score=0.85,
            overall_reputation=0.84,
            trust_grade="B+",
            total_reviews=28,
            verified_reviews=22
        )
    ]

    for score in scores:
        session.add(score)

    await session.commit()
    print(f"✅ Created {len(scores)} reputation scores")


async def create_test_contracts(session: AsyncSession, user_id: str):
    """Create sample contracts"""
    print("Creating test contracts...")

    contracts = [
        Contract(
            id="contract_1",
            title="Translate Product Documentation",
            description="Translate our product docs from English to Spanish, French, and German",
            creator_id=user_id,
            status="active",
            budget=50.0,
            escrow_amount=50.0,
            assigned_agent_id="agent_translator",
            created_at=datetime.utcnow() - timedelta(days=5)
        ),
        Contract(
            id="contract_2",
            title="Weekly Report Summaries",
            description="Summarize weekly status reports into executive summaries",
            creator_id=user_id,
            status="completed",
            budget=0.0,
            escrow_amount=0.0,
            assigned_agent_id="agent_summarizer",
            completed_at=datetime.utcnow() - timedelta(days=2),
            created_at=datetime.utcnow() - timedelta(days=7)
        ),
        Contract(
            id="contract_3",
            title="Code Review for Sprint 15",
            description="Analyze codebase for quality issues and security vulnerabilities",
            creator_id=user_id,
            status="draft",
            budget=25.0,
            escrow_amount=0.0,
            created_at=datetime.utcnow() - timedelta(days=1)
        )
    ]

    for contract in contracts:
        session.add(contract)

    await session.commit()
    print(f"✅ Created {len(contracts)} test contracts")
    return contracts


async def create_credit_transactions(session: AsyncSession, user_id: str):
    """Create sample credit transactions"""
    print("Creating credit transactions...")

    transactions = [
        CreditTransaction(
            id="txn_1",
            user_id=user_id,
            transaction_type="purchase",
            amount=100.0,
            balance_after=100.0,
            description="Credit purchase via Stripe",
            payment_provider="stripe",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=10)
        ),
        CreditTransaction(
            id="txn_2",
            user_id=user_id,
            transaction_type="usage",
            amount=-0.50,
            balance_after=99.50,
            description="Translation Bot execution",
            related_entity_id="agent_translator",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=5)
        ),
        CreditTransaction(
            id="txn_3",
            user_id=user_id,
            transaction_type="usage",
            amount=-0.10,
            balance_after=99.40,
            description="Code Analyzer Pro execution",
            related_entity_id="agent_code_analyzer",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=3)
        )
    ]

    for txn in transactions:
        session.add(txn)

    await session.commit()
    print(f"✅ Created {len(transactions)} credit transactions")


async def create_conversations(session: AsyncSession, user_id: str):
    """Create sample conversations"""
    print("Creating conversations...")

    conversation = Conversation(
        id="conv_1",
        user_id=user_id,
        title="Translate and Summarize Project Docs",
        created_at=datetime.utcnow() - timedelta(hours=2)
    )
    session.add(conversation)
    await session.flush()

    messages = [
        Message(
            conversation_id="conv_1",
            role="user",
            content="I need to translate my project documentation to Spanish and then create a summary",
            created_at=datetime.utcnow() - timedelta(hours=2)
        ),
        Message(
            conversation_id="conv_1",
            role="assistant",
            content="I'll help you translate and summarize your documentation. I'll use Translation Bot for translation and Free Summarizer for creating the summary.",
            created_at=datetime.utcnow() - timedelta(hours=2, minutes=-1)
        ),
        Message(
            conversation_id="conv_1",
            role="user",
            content="Perfect! Here's the documentation: [Document content...]",
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=58)
        )
    ]

    for msg in messages:
        session.add(msg)

    await session.commit()
    print(f"✅ Created 1 conversation with {len(messages)} messages")


async def main():
    """Main seeding function"""
    print("\n🌱 Seeding ASTRAEUS Test Database\n")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            users = await create_test_users(session)
            agents = await create_test_agents(session, users[2].id)
            await create_reputation_scores(session, agents)
            await create_test_contracts(session, users[0].id)
            await create_credit_transactions(session, users[0].id)
            await create_conversations(session, users[0].id)

            print("\n" + "=" * 60)
            print("✅ Database seeding completed successfully!\n")

            print("📊 Test Data Summary:")
            print(f"  - Users: 3 (alice@test.com, bob@test.com, dev@test.com)")
            print(f"  - Agents: 4 (Translation, Summarizer, Code Analyzer, LangChain)")
            print(f"  - Contracts: 3 (active, completed, draft)")
            print(f"  - Credit Transactions: 3")
            print(f"  - Conversations: 1")
            print(f"\n🔑 Login Credentials:")
            print(f"  - Email: alice@test.com (Password: test123)")
            print(f"  - Email: bob@test.com (Password: test123)")
            print(f"  - Email: dev@test.com (Password: test123)")
            print(f"\n🚀 Mock Agent Servers:")
            print(f"  - Translation Bot: http://localhost:8001")
            print(f"  - Free Summarizer: http://localhost:8002")
            print(f"  - Code Analyzer Pro: http://localhost:8003")
            print(f"  - LangChain Agent: http://localhost:8004")

        except Exception as e:
            print(f"\n❌ Error seeding database: {e}")
            await session.rollback()
            raise

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
