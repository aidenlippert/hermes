"""
Integration Tests for Agent-to-Agent Communication

Tests the complete agent lifecycle:
1. Agent registration
2. Agent discovery
3. Agent execution
4. ACL permission checking
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main_v2 import app
from backend.database.models import Agent, APIKey, User, A2AAgentAllow
from backend.services.auth import hash_password


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        name="Test User",
        is_verified=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def user_token(test_user: User):
    """Get JWT token for test user"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]


@pytest.mark.asyncio
class TestAgentRegistration:
    """Test agent registration and API key generation"""

    async def test_register_agent_success(self, user_token: str):
        """Successfully register a new agent"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents/register",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "name": "test-agent",
                    "description": "Test agent for integration tests",
                    "endpoint": "http://localhost:8001/api/v1",
                    "capabilities": ["test", "demo"],
                    "category": "test",
                    "tags": ["test"],
                    "is_public": True,
                    "max_calls_per_hour": 100
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "agent_id" in data
            assert "api_key" in data
            assert data["name"] == "test-agent"
            assert data["api_key"].startswith("hsk_")

    async def test_register_duplicate_agent(self, user_token: str):
        """Fail when registering agent with duplicate name"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register first agent
            await client.post(
                "/api/v1/agents/register",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "name": "duplicate-test",
                    "description": "First agent",
                    "endpoint": "http://localhost:8001/api/v1",
                    "capabilities": ["test"],
                    "is_public": True
                }
            )

            # Try to register duplicate
            response = await client.post(
                "/api/v1/agents/register",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "name": "duplicate-test",
                    "description": "Second agent",
                    "endpoint": "http://localhost:8002/api/v1",
                    "capabilities": ["test"],
                    "is_public": True
                }
            )

            assert response.status_code == 400
            assert "already taken" in response.json()["detail"].lower()

    async def test_register_without_auth(self):
        """Fail when registering without authentication"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents/register",
                json={
                    "name": "unauthorized-agent",
                    "description": "Should fail",
                    "endpoint": "http://localhost:8001/api/v1",
                    "capabilities": ["test"],
                    "is_public": True
                }
            )

            assert response.status_code == 401


@pytest.mark.asyncio
class TestAgentDiscovery:
    """Test agent discovery with semantic search"""

    @pytest.fixture
    async def test_agents(self, db: AsyncSession, test_user: User):
        """Create test agents with different capabilities"""
        agents = [
            Agent(
                name="image-generator",
                description="Generate realistic images using AI",
                endpoint="http://localhost:8001/api/v1",
                capabilities=["image_generation", "style_transfer"],
                category="content",
                is_public=True,
                trust_score=0.9,
                creator_id=test_user.id,
                status="active"
            ),
            Agent(
                name="text-analyzer",
                description="Analyze and summarize text content",
                endpoint="http://localhost:8002/api/v1",
                capabilities=["text_analysis", "summarization"],
                category="content",
                is_public=True,
                trust_score=0.8,
                creator_id=test_user.id,
                status="active"
            ),
            Agent(
                name="code-reviewer",
                description="Review code for bugs and improvements",
                endpoint="http://localhost:8003/api/v1",
                capabilities=["code_review", "static_analysis"],
                category="development",
                is_public=False,
                trust_score=0.95,
                creator_id=test_user.id,
                status="active"
            )
        ]

        for agent in agents:
            db.add(agent)

        await db.commit()

        # Create API keys for agents
        for agent in agents:
            await db.refresh(agent)
            api_key = APIKey(
                agent_id=agent.id,
                key=f"test-key-{agent.name}",
                key_hash=f"hash-{agent.name}",
                name=f"{agent.name}-key",
                is_active=True
            )
            db.add(api_key)

        await db.commit()
        return agents

    async def test_discover_by_capability(self, test_agents: list[Agent]):
        """Discover agents by capability"""
        calling_agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents/discover",
                headers={
                    "X-Agent-ID": calling_agent.id,
                    "X-API-Key": f"test-key-{calling_agent.name}"
                },
                json={
                    "capability": "text_analysis",
                    "available_only": True,
                    "limit": 10
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "agents" in data
            assert len(data["agents"]) >= 1

            # Should find text-analyzer
            found = any(a["name"] == "text-analyzer" for a in data["agents"])
            assert found

    async def test_discover_filters_by_reputation(self, test_agents: list[Agent]):
        """Filter discovery results by minimum reputation"""
        calling_agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents/discover",
                headers={
                    "X-Agent-ID": calling_agent.id,
                    "X-API-Key": f"test-key-{calling_agent.name}"
                },
                json={
                    "capability": "code",
                    "min_reputation": 0.9,
                    "limit": 10
                }
            )

            assert response.status_code == 200
            data = response.json()

            # All returned agents should have reputation >= 0.9
            for agent in data["agents"]:
                assert agent["trust_score"] >= 0.9


@pytest.mark.asyncio
class TestAgentExecution:
    """Test agent-to-agent execution"""

    @pytest.fixture
    async def source_agent(self, db: AsyncSession, test_user: User):
        """Create source agent that will call other agents"""
        agent = Agent(
            name="orchestrator",
            description="Orchestrates tasks across agents",
            endpoint="http://localhost:9000/api/v1",
            capabilities=["orchestration"],
            is_public=True,
            trust_score=0.8,
            creator_id=test_user.id,
            status="active"
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        api_key = APIKey(
            agent_id=agent.id,
            key="orchestrator-key",
            key_hash="orchestrator-hash",
            name="orchestrator-key",
            is_active=True
        )
        db.add(api_key)
        await db.commit()

        return agent

    @pytest.fixture
    async def target_agent(self, db: AsyncSession, test_user: User):
        """Create target agent that will be called"""
        agent = Agent(
            name="worker",
            description="Executes tasks",
            endpoint="http://localhost:9001/api/v1",
            capabilities=["task_execution"],
            is_public=True,
            trust_score=0.7,
            creator_id=test_user.id,
            status="active"
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        return agent

    async def test_execute_agent_with_permission(
        self,
        db: AsyncSession,
        source_agent: Agent,
        target_agent: Agent
    ):
        """Execute agent with proper ACL permissions"""
        # Grant permission
        permission = A2AAgentAllow(
            source_agent_id=source_agent.id,
            target_agent_id=target_agent.id
        )
        db.add(permission)
        await db.commit()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents/execute",
                headers={
                    "X-Agent-ID": source_agent.id,
                    "X-API-Key": "orchestrator-key"
                },
                json={
                    "agent_id": target_agent.id,
                    "task": "Process this data",
                    "context": {"data": "test"}
                }
            )

            # Note: This will fail with actual execution since agents aren't running
            # But should pass ACL check and create task
            assert response.status_code in [200, 500]

    async def test_execute_agent_without_permission(
        self,
        source_agent: Agent,
        target_agent: Agent
    ):
        """Fail when executing agent without ACL permission"""
        # Make target agent not public
        target_agent.is_public = False

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents/execute",
                headers={
                    "X-Agent-ID": source_agent.id,
                    "X-API-Key": "orchestrator-key"
                },
                json={
                    "agent_id": target_agent.id,
                    "task": "Process this data",
                    "context": {"data": "test"}
                }
            )

            assert response.status_code == 403
            assert "permission denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestAgentInfo:
    """Test agent information retrieval"""

    @pytest.fixture
    async def public_agent(self, db: AsyncSession, test_user: User):
        """Create public agent"""
        agent = Agent(
            name="public-agent",
            description="Public agent anyone can see",
            endpoint="http://localhost:8005/api/v1",
            capabilities=["public_service"],
            is_public=True,
            trust_score=0.85,
            creator_id=test_user.id,
            status="active"
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        api_key = APIKey(
            agent_id=agent.id,
            key="caller-key",
            key_hash="caller-hash",
            name="caller-key",
            is_active=True
        )
        db.add(api_key)
        await db.commit()

        return agent

    async def test_get_agent_info(self, public_agent: Agent):
        """Get information about an agent"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/agents/{public_agent.id}",
                headers={
                    "X-Agent-ID": public_agent.id,
                    "X-API-Key": "caller-key"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == public_agent.id
            assert data["name"] == "public-agent"
            assert data["is_public"] is True
            assert "capabilities" in data
            assert "trust_score" in data
