"""
Database Initialization Script

Run this to set up the database with initial data.

Usage:
    python scripts/init_database.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import init_db, init_redis, close_redis, AsyncSessionLocal
from backend.services.auth import AuthService
from backend.services.agent_registry import AgentRegistry


async def seed_database():
    """Seed database with initial data"""
    print("\n" + "="*70)
    print("🌱 SEEDING DATABASE")
    print("="*70)

    async with AsyncSessionLocal() as db:
        # Create admin user
        print("\n1️⃣ Creating admin user...")
        try:
            admin = await AuthService.register_user(
                db,
                email="admin@hermes.ai",
                password="admin123",  # CHANGE THIS IN PRODUCTION!
                full_name="Hermes Admin",
                username="admin"
            )
            print(f"   ✅ Admin user created: {admin.email}")
        except ValueError as e:
            print(f"   ⚠️ Admin user already exists: {e}")

        # Create test user
        print("\n2️⃣ Creating test user...")
        try:
            test_user = await AuthService.register_user(
                db,
                email="test@example.com",
                password="test123",
                full_name="Test User",
                username="testuser"
            )
            print(f"   ✅ Test user created: {test_user.email}")

            # Create API key for test user
            api_key = await AuthService.create_api_key(
                db,
                user_id=test_user.id,
                name="Test API Key"
            )
            print(f"   ✅ API key created: {api_key.key}")
            print(f"   💡 Save this key for testing!")

        except ValueError as e:
            print(f"   ⚠️ Test user already exists: {e}")

        # Register default agents
        print("\n3️⃣ Registering default agents...")

        agents_to_register = [
            {
                "name": "CodeGenerator",
                "description": "Generates code in any programming language using Gemini AI. Can write functions, classes, entire applications. Specializes in Python, JavaScript, and more.",
                "endpoint": "http://localhost:10001/a2a",
                "capabilities": ["code_write", "code_debug", "code_explain", "code_review"],
                "category": "code"
            },
            {
                "name": "ContentWriter",
                "description": "Professional content writer that creates blog posts, articles, social media content, and marketing copy. Specializes in engaging, well-structured written content.",
                "endpoint": "http://localhost:10002/a2a",
                "capabilities": ["content_write", "blog_write", "article_write", "social_media", "marketing_copy", "documentation"],
                "category": "content"
            },
            {
                "name": "DataAnalyzer",
                "description": "Intelligent data analysis agent that processes CSV/JSON data, identifies patterns, performs statistical analysis, and provides actionable insights.",
                "endpoint": "http://localhost:10003/a2a",
                "capabilities": ["data_analysis", "csv_analysis", "json_analysis", "statistical_analysis", "pattern_detection", "data_insights"],
                "category": "data"
            },
            {
                "name": "WebSearcher",
                "description": "Web search and research agent that finds current information, aggregates news, and provides fact-checked summaries from the web.",
                "endpoint": "http://localhost:10004/a2a",
                "capabilities": ["web_search", "research", "news_aggregation", "fact_checking", "current_events", "information_retrieval"],
                "category": "research"
            }
        ]

        for agent_data in agents_to_register:
            try:
                agent = await AgentRegistry.register_agent(
                    db,
                    name=agent_data["name"],
                    description=agent_data["description"],
                    endpoint=agent_data["endpoint"],
                    capabilities=agent_data["capabilities"],
                    category=agent_data.get("category")
                )
                print(f"   ✅ Agent registered: {agent.name}")
            except Exception as e:
                print(f"   ⚠️ Agent {agent_data['name']} failed: {e}")

    print("\n" + "="*70)
    print("✅ DATABASE SEEDED SUCCESSFULLY!")
    print("="*70)
    print("\n📝 Default Credentials:")
    print("   Admin: admin@hermes.ai / admin123")
    print("   Test:  test@example.com / test123")
    print("\n⚠️ CHANGE THESE IN PRODUCTION!")
    print()


async def main():
    """Main initialization flow"""
    print("\n" + "="*70)
    print("🚀 HERMES DATABASE INITIALIZATION")
    print("="*70)

    print("\n⚠️ Prerequisites:")
    print("   - Docker running: docker-compose up -d")
    print("   - PostgreSQL accessible on localhost:5432")
    print("   - Redis accessible on localhost:6379")
    print()

    input("Press Enter to continue...")

    # Initialize PostgreSQL
    print("\n1️⃣ Initializing PostgreSQL...")
    try:
        await init_db()
        print("   ✅ PostgreSQL initialized")
    except Exception as e:
        print(f"   ❌ PostgreSQL init failed: {e}")
        print("\n   Make sure Docker is running:")
        print("   docker-compose up -d")
        return

    # Initialize Redis
    print("\n2️⃣ Initializing Redis...")
    try:
        await init_redis()
        print("   ✅ Redis initialized")
    except Exception as e:
        print(f"   ❌ Redis init failed: {e}")
        return

    # Seed database
    await seed_database()

    # Cleanup
    await close_redis()

    print("\n" + "="*70)
    print("🎉 INITIALIZATION COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("   1. Start backend: python backend/main.py")
    print("   2. Start test agent: python test_agent_code_generator.py")
    print("   3. Test the API: python test_backend.py")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
