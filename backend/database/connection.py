"""
Database Connection Management

Handles PostgreSQL and Redis connections with async support.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
import os
import logging

logger = logging.getLogger(__name__)

# Database URLs
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hermes:hermes_dev_password@localhost:5432/hermes"
)

# Railway provides postgresql:// or postgres:// but we need postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://:hermes_dev_password@localhost:6379/0"
)

# SQLAlchemy Base
Base = declarative_base()

# Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    pool_pre_ping=True,
    poolclass=NullPool,  # For serverless environments
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Redis client (will be initialized on startup)
redis_client = None


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database:
    1. Create all tables
    2. Install pgvector extension
    """
    logger.info("🔧 Initializing database...")

    async with engine.begin() as conn:
        # Install pgvector extension
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("✅ pgvector extension installed")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created")


async def init_redis():
    """Initialize Redis connection"""
    global redis_client

    logger.info("🔧 Initializing Redis...")

    redis_client = await redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

    # Test connection
    await redis_client.ping()
    logger.info("✅ Redis connected")


async def close_redis():
    """Close Redis connection"""
    if redis_client:
        await redis_client.close()
        logger.info("👋 Redis connection closed")


async def get_redis():
    """
    Dependency for FastAPI to get Redis client.

    Usage:
        @app.get("/cache")
        async def get_cache(redis = Depends(get_redis)):
            ...
    """
    return redis_client


# Cache utilities
class Cache:
    """Redis cache utilities"""

    @staticmethod
    async def get(key: str):
        """Get value from cache"""
        if redis_client:
            return await redis_client.get(key)
        return None

    @staticmethod
    async def set(key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL (seconds)"""
        if redis_client:
            await redis_client.setex(key, ttl, value)

    @staticmethod
    async def delete(key: str):
        """Delete key from cache"""
        if redis_client:
            await redis_client.delete(key)

    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists"""
        if redis_client:
            return await redis_client.exists(key) > 0
        return False


if __name__ == "__main__":
    import asyncio

    async def test_connection():
        """Test database and Redis connections"""
        print("\n" + "="*60)
        print("🧪 Testing Database Connections")
        print("="*60)

        # Test PostgreSQL
        print("\n1️⃣ Testing PostgreSQL...")
        try:
            await init_db()
            print("   ✅ PostgreSQL connected and initialized")
        except Exception as e:
            print(f"   ❌ PostgreSQL failed: {e}")

        # Test Redis
        print("\n2️⃣ Testing Redis...")
        try:
            await init_redis()

            # Test cache operations
            await Cache.set("test_key", "test_value", ttl=10)
            value = await Cache.get("test_key")

            if value == "test_value":
                print("   ✅ Redis connected and working")
            else:
                print("   ⚠️ Redis connected but cache not working")

            await Cache.delete("test_key")
            await close_redis()

        except Exception as e:
            print(f"   ❌ Redis failed: {e}")

        print("\n" + "="*60)
        print("✅ Connection tests complete!")
        print("\nMake sure Docker is running:")
        print("   docker-compose up -d")
        print()

    asyncio.run(test_connection())
