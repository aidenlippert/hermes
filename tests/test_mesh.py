"""
Integration Tests for Mesh Protocol

Tests the complete contract lifecycle:
1. Contract creation
2. Agent bidding
3. Contract award
4. Result delivery
5. Validation and settlement
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from backend.main_v2 import app
from backend.database.models import (
    Agent, APIKey, User, Contract, Bid, Delivery,
    ContractStatus
)
from backend.services.auth import hash_password


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user"""
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("testpass123"),
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
                "email": "testuser@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]


@pytest.fixture
async def test_agents(db: AsyncSession, test_user: User):
    """Create test agents for bidding"""
    agents = []

    for i in range(3):
        agent = Agent(
            name=f"test-agent-{i}",
            description=f"Test agent {i}",
            endpoint=f"http://localhost:900{i}/api/v1",
            capabilities=["image_generation"],
            is_public=True,
            trust_score=0.8 + (i * 0.05),
            creator_id=test_user.id,
            status="active"
        )
        db.add(agent)
        await db.flush()

        # Create API key
        api_key = APIKey(
            agent_id=agent.id,
            key=f"test-key-agent-{i}",
            key_hash=f"hash-agent-{i}",
            name=f"agent-{i}-key",
            is_active=True
        )
        db.add(api_key)
        agents.append(agent)

    await db.commit()

    for agent in agents:
        await db.refresh(agent)

    return agents


@pytest.mark.asyncio
class TestContractCreation:
    """Test contract creation"""

    async def test_create_contract_success(self, user_token: str):
        """Successfully create a new contract"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/mesh/contracts",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "intent": "image_generation",
                    "context": {
                        "prompt": "A beautiful sunset",
                        "style": "realistic"
                    },
                    "reward_amount": 10.0,
                    "reward_currency": "USD",
                    "expires_in_minutes": 60
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "id" in data
            assert data["intent"] == "image_generation"
            assert data["reward_amount"] == 10.0
            assert data["status"] == "open"

    async def test_create_contract_without_auth(self):
        """Fail when creating contract without authentication"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/mesh/contracts",
                json={
                    "intent": "test",
                    "context": {},
                    "reward_amount": 5.0
                }
            )

            assert response.status_code == 401


@pytest.mark.asyncio
class TestBidding:
    """Test bidding on contracts"""

    @pytest.fixture
    async def test_contract(self, db: AsyncSession, test_user: User):
        """Create a test contract"""
        contract = Contract(
            user_id=test_user.id,
            intent="image_generation",
            context={"prompt": "Test image"},
            reward_amount=10.0,
            reward_currency="USD",
            status=ContractStatus.OPEN,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract

    async def test_submit_bid_success(self, test_contract: Contract, test_agents: list[Agent]):
        """Successfully submit a bid"""
        agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{test_contract.id}/bid",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": f"test-key-agent-0"
                },
                json={
                    "price": 8.0,
                    "eta_seconds": 30.0,
                    "confidence": 0.9
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["contract_id"] == test_contract.id
            assert data["agent_id"] == agent.id
            assert data["price"] == 8.0
            assert data["confidence"] == 0.9

    async def test_submit_bid_twice_fails(self, test_contract: Contract, test_agents: list[Agent]):
        """Fail when agent bids twice"""
        agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            # First bid
            await client.post(
                f"/api/v1/mesh/contracts/{test_contract.id}/bid",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": f"test-key-agent-0"
                },
                json={
                    "price": 8.0,
                    "eta_seconds": 30.0,
                    "confidence": 0.9
                }
            )

            # Second bid (should fail)
            response = await client.post(
                f"/api/v1/mesh/contracts/{test_contract.id}/bid",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": f"test-key-agent-0"
                },
                json={
                    "price": 7.0,
                    "eta_seconds": 25.0,
                    "confidence": 0.95
                }
            )

            assert response.status_code == 400
            assert "already bid" in response.json()["detail"].lower()

    async def test_submit_bid_to_nonexistent_contract(self, test_agents: list[Agent]):
        """Fail when bidding on nonexistent contract"""
        agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/mesh/contracts/nonexistent-id/bid",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": f"test-key-agent-0"
                },
                json={
                    "price": 8.0,
                    "eta_seconds": 30.0,
                    "confidence": 0.9
                }
            )

            assert response.status_code == 404


@pytest.mark.asyncio
class TestContractAward:
    """Test contract awarding"""

    @pytest.fixture
    async def contract_with_bids(
        self,
        db: AsyncSession,
        test_user: User,
        test_agents: list[Agent]
    ):
        """Create contract with multiple bids"""
        # Create contract
        contract = Contract(
            user_id=test_user.id,
            intent="image_generation",
            context={"prompt": "Test image"},
            reward_amount=10.0,
            reward_currency="USD",
            status=ContractStatus.BIDDING,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(contract)
        await db.flush()

        # Create bids
        bids = [
            Bid(
                contract_id=contract.id,
                agent_id=test_agents[0].id,
                price=8.0,
                eta_seconds=30.0,
                confidence=0.9
            ),
            Bid(
                contract_id=contract.id,
                agent_id=test_agents[1].id,
                price=6.0,  # Lowest price
                eta_seconds=45.0,
                confidence=0.85
            ),
            Bid(
                contract_id=contract.id,
                agent_id=test_agents[2].id,
                price=9.0,
                eta_seconds=20.0,  # Fastest
                confidence=0.95  # Best confidence
            )
        ]

        for bid in bids:
            db.add(bid)

        await db.commit()
        await db.refresh(contract)
        return contract

    async def test_award_lowest_price(
        self,
        contract_with_bids: Contract,
        test_agents: list[Agent],
        user_token: str
    ):
        """Award contract to lowest price bid"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{contract_with_bids.id}/award",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"strategy": "lowest_price"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "awarded"
            # Should be agent-1 (price=6.0)
            assert data["awarded_to"] == test_agents[1].id
            assert data["total_bids"] == 3

    async def test_award_fastest(
        self,
        contract_with_bids: Contract,
        test_agents: list[Agent],
        user_token: str
    ):
        """Award contract to fastest bid"""
        # Reset contract status for new award
        contract_with_bids.status = ContractStatus.BIDDING
        contract_with_bids.awarded_to = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{contract_with_bids.id}/award",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"strategy": "fastest"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should be agent-2 (eta=20.0)
            assert data["awarded_to"] == test_agents[2].id

    async def test_award_without_ownership(
        self,
        db: AsyncSession,
        contract_with_bids: Contract
    ):
        """Fail when non-owner tries to award"""
        # Create different user
        other_user = User(
            email="other@example.com",
            password_hash=hash_password("password123"),
            name="Other User",
            is_verified=True
        )
        db.add(other_user)
        await db.commit()

        # Get token for other user
        async with AsyncClient(app=app, base_url="http://test") as client:
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "other@example.com",
                    "password": "password123"
                }
            )
            other_token = login_response.json()["access_token"]

            # Try to award
            response = await client.post(
                f"/api/v1/mesh/contracts/{contract_with_bids.id}/award",
                headers={"Authorization": f"Bearer {other_token}"},
                json={"strategy": "lowest_price"}
            )

            assert response.status_code == 403


@pytest.mark.asyncio
class TestDelivery:
    """Test result delivery"""

    @pytest.fixture
    async def awarded_contract(
        self,
        db: AsyncSession,
        test_user: User,
        test_agents: list[Agent]
    ):
        """Create awarded contract"""
        contract = Contract(
            user_id=test_user.id,
            intent="image_generation",
            context={"prompt": "Test image"},
            reward_amount=10.0,
            reward_currency="USD",
            status=ContractStatus.AWARDED,
            awarded_to=test_agents[0].id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract

    async def test_deliver_result_success(
        self,
        awarded_contract: Contract,
        test_agents: list[Agent]
    ):
        """Successfully deliver result"""
        agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{awarded_contract.id}/deliver",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": "test-key-agent-0"
                },
                json={
                    "data": {
                        "image_url": "https://example.com/image.png",
                        "metadata": {"model": "stable-diffusion"}
                    }
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["contract_id"] == awarded_contract.id
            assert data["agent_id"] == agent.id
            assert data["is_validated"] is False
            assert "image_url" in data["data"]

    async def test_deliver_by_wrong_agent_fails(
        self,
        awarded_contract: Contract,
        test_agents: list[Agent]
    ):
        """Fail when non-winner tries to deliver"""
        wrong_agent = test_agents[1]  # Not the winner

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{awarded_contract.id}/deliver",
                headers={
                    "X-Agent-ID": wrong_agent.id,
                    "X-API-Key": "test-key-agent-1"
                },
                json={
                    "data": {"image_url": "https://example.com/image.png"}
                }
            )

            assert response.status_code == 403
            assert "awarded agent" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestValidation:
    """Test delivery validation"""

    @pytest.fixture
    async def delivered_contract(
        self,
        db: AsyncSession,
        test_user: User,
        test_agents: list[Agent]
    ):
        """Create contract with delivery"""
        contract = Contract(
            user_id=test_user.id,
            intent="image_generation",
            context={"prompt": "Test image"},
            reward_amount=10.0,
            reward_currency="USD",
            status=ContractStatus.DELIVERED,
            awarded_to=test_agents[0].id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(contract)
        await db.flush()

        delivery = Delivery(
            contract_id=contract.id,
            agent_id=test_agents[0].id,
            data={"image_url": "https://example.com/image.png"},
            is_validated=False
        )
        db.add(delivery)
        await db.commit()
        await db.refresh(contract)
        return contract

    async def test_validate_success(
        self,
        delivered_contract: Contract,
        user_token: str
    ):
        """Successfully validate delivery"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{delivered_contract.id}/validate",
                headers={"Authorization": f"Bearer {user_token}"},
                params={"validation_score": 0.9}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["validation_score"] == 0.9
            assert data["status"] == "settled"

    async def test_validate_poor_quality(
        self,
        delivered_contract: Contract,
        user_token: str
    ):
        """Validate with poor score marks as failed"""
        # Reset status
        delivered_contract.status = ContractStatus.DELIVERED

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/mesh/contracts/{delivered_contract.id}/validate",
                headers={"Authorization": f"Bearer {user_token}"},
                params={"validation_score": 0.4}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "failed"
            assert data["validation_score"] == 0.4


@pytest.mark.asyncio
class TestContractQueries:
    """Test contract listing and querying"""

    async def test_list_open_contracts(
        self,
        db: AsyncSession,
        test_user: User,
        test_agents: list[Agent]
    ):
        """List open contracts for agents"""
        # Create some contracts
        for i in range(3):
            contract = Contract(
                user_id=test_user.id,
                intent=f"task-{i}",
                context={"data": i},
                reward_amount=10.0 + i,
                status=ContractStatus.OPEN if i < 2 else ContractStatus.AWARDED
            )
            db.add(contract)
        await db.commit()

        agent = test_agents[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/mesh/contracts",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": "test-key-agent-0"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should only return OPEN contracts (2 of them)
            assert len(data) >= 2
            for contract in data:
                assert contract["status"] in ["open", "bidding"]

    async def test_get_my_contracts(
        self,
        db: AsyncSession,
        test_user: User,
        test_agents: list[Agent]
    ):
        """Get contracts awarded to agent"""
        agent = test_agents[0]

        # Create contracts awarded to agent
        for i in range(2):
            contract = Contract(
                user_id=test_user.id,
                intent=f"my-task-{i}",
                context={"data": i},
                reward_amount=10.0,
                status=ContractStatus.AWARDED,
                awarded_to=agent.id
            )
            db.add(contract)
        await db.commit()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/mesh/my-contracts",
                headers={
                    "X-Agent-ID": agent.id,
                    "X-API-Key": "test-key-agent-0"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should return contracts awarded to this agent
            assert len(data) >= 2
            for contract in data:
                assert contract["awarded_to"] == agent.id
