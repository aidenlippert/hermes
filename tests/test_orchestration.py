"""
Tests for Sprint 2: Orchestration & Intelligence

Tests for:
- Intent analysis and task decomposition
- Dependency resolution and topological sorting
- Agent selection and scoring
- Collaboration patterns (sequential, parallel, vote, debate, swarm, consensus)
- Result synthesis
- Chat endpoint with orchestration routing
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from backend.main_v2 import app
from backend.database.connection import Base, engine
from backend.database.models import User, Agent, AgentStatus
from backend.database.models_orchestration import (
    CollaborationPattern,
    OrchestrationPlan,
    OrchestrationStatus,
    AgentCollaboration
)
from backend.services.orchestrator import (
    IntentAnalyzer,
    DependencyResolver,
    AgentSelector,
    OrchestratorAgent
)
from backend.services.collaboration import (
    CollaborationEngine,
    ResultSynthesizer,
    CollaborationFactory
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user"""
    user = User(
        email="test@orchestration.com",
        username="orchestrator",
        hashed_password="hashed_password",
        role="user",
        subscription_tier="pro"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_agents(db_session: AsyncSession) -> List[Agent]:
    """Create test agents with different capabilities"""
    agents = [
        Agent(
            name="SearchAgent",
            description="Searches for information",
            endpoint="http://localhost:8001/search",
            capabilities=["search", "query", "find"],
            status=AgentStatus.ACTIVE,
            trust_score=0.9,
            successful_calls=100,
            total_calls=110,
            cost_per_request=0.01
        ),
        Agent(
            name="AnalyzerAgent",
            description="Analyzes and evaluates data",
            endpoint="http://localhost:8002/analyze",
            capabilities=["analyze", "evaluate", "assess"],
            status=AgentStatus.ACTIVE,
            trust_score=0.85,
            successful_calls=80,
            total_calls=100,
            cost_per_request=0.02
        ),
        Agent(
            name="GeneratorAgent",
            description="Generates content and text",
            endpoint="http://localhost:8003/generate",
            capabilities=["generate", "create", "write"],
            status=AgentStatus.ACTIVE,
            trust_score=0.88,
            successful_calls=90,
            total_calls=100,
            cost_per_request=0.015
        ),
    ]

    for agent in agents:
        db_session.add(agent)

    await db_session.commit()

    for agent in agents:
        await db_session.refresh(agent)

    return agents


# ============================================================================
# INTENT ANALYSIS TESTS
# ============================================================================

@pytest.mark.asyncio
class TestIntentAnalyzer:
    """Tests for intent analysis and task decomposition"""

    async def test_simple_intent(self):
        """Test simple single-intent query"""
        analyzer = IntentAnalyzer()
        result = await analyzer.analyze("Search for hotels in Paris")

        assert result["main_intent"] == "Search for hotels in Paris"
        assert len(result["sub_intents"]) >= 1
        assert result["complexity"] >= 0.0
        assert isinstance(result["requires_orchestration"], bool)

    async def test_sequential_intent(self):
        """Test sequential query with 'then' keyword"""
        analyzer = IntentAnalyzer()
        result = await analyzer.analyze("Search for flights and then book a hotel")

        assert result["suggested_pattern"] == CollaborationPattern.SEQUENTIAL
        assert result["requires_orchestration"] is True
        assert len(result["sub_intents"]) >= 2

    async def test_parallel_intent(self):
        """Test parallel query with 'and' keyword"""
        analyzer = IntentAnalyzer()
        result = await analyzer.analyze("Search for flights and hotels")

        assert result["requires_orchestration"] is True
        assert len(result["sub_intents"]) >= 2

    async def test_comparison_intent(self):
        """Test comparison query"""
        analyzer = IntentAnalyzer()
        result = await analyzer.analyze("Compare hotel prices versus Airbnb")

        assert result["suggested_pattern"] in [CollaborationPattern.VOTE, CollaborationPattern.PARALLEL]
        assert result["requires_orchestration"] is True

    async def test_complexity_scoring(self):
        """Test complexity scoring"""
        analyzer = IntentAnalyzer()

        simple = await analyzer.analyze("Search")
        complex_query = await analyzer.analyze(
            "Search for all hotels and compare prices and analyze reviews and then book the best one"
        )

        assert complex_query["complexity"] > simple["complexity"]


# ============================================================================
# DEPENDENCY RESOLUTION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestDependencyResolver:
    """Tests for dependency resolution and graph building"""

    async def test_build_sequential_graph(self):
        """Test building sequential dependency graph"""
        resolver = DependencyResolver()

        sub_tasks = [
            {"description": "Task 1", "required_capabilities": ["search"]},
            {"description": "Task 2", "required_capabilities": ["analyze"]},
            {"description": "Task 3", "required_capabilities": ["generate"]},
        ]

        graph = resolver.build_graph(sub_tasks)

        assert len(graph["nodes"]) == 3
        assert len(graph["edges"]) == 2  # Sequential: 1→2, 2→3
        assert len(graph["execution_order"]) >= 1

    async def test_topological_sort(self):
        """Test topological sorting"""
        resolver = DependencyResolver()

        sub_tasks = [
            {"description": "Task A", "required_capabilities": []},
            {"description": "Task B", "required_capabilities": []},
            {"description": "Task C", "required_capabilities": []},
        ]

        graph = resolver.build_graph(sub_tasks)
        execution_order = graph["execution_order"]

        # Should have at least one level
        assert len(execution_order) > 0

        # All tasks should be present
        all_tasks = [task for level in execution_order for task in level]
        assert len(all_tasks) == len(sub_tasks)


# ============================================================================
# AGENT SELECTION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestAgentSelector:
    """Tests for agent selection and scoring"""

    async def test_select_agent_by_capability(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test selecting agent based on capabilities"""
        selector = AgentSelector(db_session)

        agents = await selector.select_agents(
            task_description="Search for information",
            required_capabilities=["search"],
            count=1
        )

        assert len(agents) == 1
        assert "search" in agents[0].capabilities

    async def test_select_multiple_agents(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test selecting multiple agents"""
        selector = AgentSelector(db_session)

        agents = await selector.select_agents(
            task_description="Analyze data",
            required_capabilities=["analyze"],
            count=2
        )

        assert len(agents) <= 2

    async def test_agent_scoring(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test agent scoring considers multiple factors"""
        selector = AgentSelector(db_session)

        # Score should consider capability match, trust score, success rate, cost
        score = await selector._score_agent(
            agent=test_agents[0],
            required_capabilities=["search"],
            task_description="Search task"
        )

        assert 0.0 <= score <= 1.0


# ============================================================================
# COLLABORATION PATTERN TESTS
# ============================================================================

@pytest.mark.asyncio
class TestCollaborationEngine:
    """Tests for collaboration patterns"""

    async def test_sequential_pattern(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test sequential collaboration"""
        engine = CollaborationEngine(db_session)

        result = await engine.sequential(
            agents=test_agents,
            task="Sequential task",
            config={}
        )

        assert result["pattern"] == "sequential"
        assert len(result["results"]) == len(test_agents)
        assert result["final_output"] is not None

    async def test_parallel_pattern(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test parallel collaboration"""
        engine = CollaborationEngine(db_session)

        result = await engine.parallel(
            agents=test_agents,
            task="Parallel task",
            config={}
        )

        assert result["pattern"] == "parallel"
        assert len(result["results"]) == len(test_agents)
        assert "synthesized" in result

    async def test_vote_pattern(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test voting collaboration"""
        engine = CollaborationEngine(db_session)

        result = await engine.vote(
            agents=test_agents,
            task="Vote task",
            config={}
        )

        assert result["pattern"] == "vote"
        assert "synthesized" in result
        assert result["synthesized"]["type"] == "vote"

    async def test_debate_pattern(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test debate collaboration"""
        engine = CollaborationEngine(db_session)

        result = await engine.debate(
            agents=test_agents,
            task="Debate task",
            config={"rounds": 2}
        )

        assert result["pattern"] == "debate"
        assert len(result["rounds"]) == 2
        assert result["synthesized"]["type"] == "debate_winner"

    async def test_swarm_pattern(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test swarm intelligence"""
        engine = CollaborationEngine(db_session)

        result = await engine.swarm(
            agents=test_agents,
            task="Swarm task",
            config={"iterations": 2}
        )

        assert result["pattern"] == "swarm"
        assert len(result["iterations"]) == 2

    async def test_consensus_pattern(self, db_session: AsyncSession, test_agents: List[Agent]):
        """Test consensus pattern"""
        engine = CollaborationEngine(db_session)

        result = await engine.consensus(
            agents=test_agents,
            task="Consensus task",
            config={"threshold": 0.66, "max_rounds": 3}
        )

        assert result["pattern"] == "consensus"
        assert "converged" in result


# ============================================================================
# RESULT SYNTHESIS TESTS
# ============================================================================

@pytest.mark.asyncio
class TestResultSynthesizer:
    """Tests for result synthesis"""

    def test_merge(self):
        """Test merging results"""
        synthesizer = ResultSynthesizer()

        results = [
            {"agent": "Agent1", "result": "Result 1", "confidence": 0.9},
            {"agent": "Agent2", "result": "Result 2", "confidence": 0.8},
        ]

        merged = synthesizer.merge(results)

        assert merged["type"] == "merged"
        assert len(merged["sources"]) == 2
        assert len(merged["outputs"]) == 2
        assert 0.8 <= merged["confidence"] <= 0.9

    def test_vote(self):
        """Test voting synthesis"""
        synthesizer = ResultSynthesizer()

        results = [
            {"result": "Option A"},
            {"result": "Option A"},
            {"result": "Option B"},
        ]

        vote_result = synthesizer.vote(results)

        assert vote_result["type"] == "vote"
        assert vote_result["winner"] == "Option A"
        assert vote_result["confidence"] > 0.5

    def test_weighted_vote(self):
        """Test weighted voting"""
        synthesizer = ResultSynthesizer()

        results = [
            {"result": "Option A"},
            {"result": "Option B"},
        ]

        weights = [0.7, 0.3]
        vote_result = synthesizer.vote(results, weights)

        assert vote_result["winner"] == "Option A"


# ============================================================================
# ORCHESTRATOR INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestOrchestratorAgent:
    """Tests for end-to-end orchestration"""

    async def test_simple_orchestration(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_agents: List[Agent]
    ):
        """Test simple orchestration flow"""
        orchestrator = OrchestratorAgent(db_session)

        result = await orchestrator.orchestrate(
            user_id=test_user.id,
            query="Search for information",
            context={}
        )

        assert "plan_id" in result
        assert result["status"] == OrchestrationStatus.COMPLETED.value
        assert "execution_summary" in result

    async def test_sequential_orchestration(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_agents: List[Agent]
    ):
        """Test sequential orchestration"""
        orchestrator = OrchestratorAgent(db_session)

        result = await orchestrator.orchestrate(
            user_id=test_user.id,
            query="Search for hotels and then analyze the results",
            context={}
        )

        assert result["status"] == OrchestrationStatus.COMPLETED.value
        assert result["execution_summary"]["pattern"] == CollaborationPattern.SEQUENTIAL.value

    async def test_parallel_orchestration(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_agents: List[Agent]
    ):
        """Test parallel orchestration"""
        orchestrator = OrchestratorAgent(db_session)

        result = await orchestrator.orchestrate(
            user_id=test_user.id,
            query="Search for hotels and flights",
            context={}
        )

        assert result["status"] == OrchestrationStatus.COMPLETED.value


# ============================================================================
# CHAT ENDPOINT TESTS
# ============================================================================

@pytest.mark.asyncio
class TestChatEndpoint:
    """Tests for chat endpoint with orchestration"""

    async def test_simple_chat(self, user_token: str):
        """Test simple chat without orchestration"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/message",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"message": "Hello"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "conversation_id" in data
            assert isinstance(data["orchestration_used"], bool)

    async def test_chat_with_orchestration(self, user_token: str):
        """Test chat that triggers orchestration"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/message",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "message": "Search for hotels and then book a room",
                    "use_orchestration": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["orchestration_used"] is True
            assert data["orchestration_details"] is not None

    async def test_direct_orchestration_endpoint(self, user_token: str):
        """Test direct orchestration endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/orchestrate",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "query": "Analyze data",
                    "pattern": "parallel"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "plan_id" in data
            assert "status" in data

    async def test_conversation_list(self, user_token: str):
        """Test listing conversations"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a conversation first
            await client.post(
                "/api/v1/chat/message",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"message": "Test"}
            )

            # List conversations
            response = await client.get(
                "/api/v1/chat/conversations",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "conversations" in data
            assert isinstance(data["conversations"], list)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestOrchestrationPerformance:
    """Performance tests for orchestration"""

    async def test_parallel_faster_than_sequential(
        self,
        db_session: AsyncSession,
        test_agents: List[Agent]
    ):
        """Test that parallel execution is faster than sequential"""
        engine = CollaborationEngine(db_session)

        # Sequential execution
        start = datetime.utcnow()
        await engine.sequential(test_agents, "Task", {})
        sequential_time = (datetime.utcnow() - start).total_seconds()

        # Parallel execution
        start = datetime.utcnow()
        await engine.parallel(test_agents, "Task", {})
        parallel_time = (datetime.utcnow() - start).total_seconds()

        # Parallel should be faster (or at least not significantly slower)
        assert parallel_time <= sequential_time * 1.5


# ============================================================================
# CONFTEST FIXTURES
# ============================================================================

@pytest.fixture
async def db_session():
    """Create test database session"""
    from backend.database.connection import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def user_token(test_user: User) -> str:
    """Generate JWT token for test user"""
    from backend.services.auth import AuthService

    auth_service = AuthService()
    token = auth_service.create_access_token(test_user.id)
    return token
