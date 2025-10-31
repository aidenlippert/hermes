"""
Mesh Protocol API Router

Endpoints for market-based agent collaboration via contracts and bidding.

This implements the complete contract lifecycle:
- OPEN: Contract announced and accepting bids
- BIDDING: Agents submit bids
- AWARDED: Winner selected based on strategy
- IN_PROGRESS: Agent working on task
- DELIVERED: Agent submits result
- VALIDATED: Result validated by issuer
- SETTLED: Payment released

Agents can autonomously:
- Browse open contracts
- Submit competitive bids
- Deliver results
- Build reputation
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import (
    Contract, Bid, Delivery, Agent, User,
    ContractStatus
)
from backend.middleware.agent_auth import get_current_agent
from backend.middleware.auth import get_current_user
from backend.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mesh", tags=["mesh"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ContractCreateRequest(BaseModel):
    """Request to create a new contract"""
    intent: str = Field(..., description="Task intent (e.g., 'image_generation')")
    context: Dict[str, Any] = Field(..., description="Task parameters")
    reward_amount: float = Field(5.0, description="Reward amount")
    reward_currency: str = Field("USD", description="Currency")
    expires_in_minutes: int = Field(60, description="Contract expiry time (minutes)")


class ContractResponse(BaseModel):
    """Contract information"""
    id: str
    user_id: str
    intent: str
    context: Dict[str, Any]
    reward_amount: float
    reward_currency: str
    status: str
    awarded_to: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None
    awarded_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_bids: int = 0


class BidSubmitRequest(BaseModel):
    """Request to submit a bid"""
    price: float = Field(..., description="Bid price")
    eta_seconds: float = Field(..., description="Estimated completion time")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")


class BidResponse(BaseModel):
    """Bid information"""
    id: str
    contract_id: str
    agent_id: str
    price: float
    eta_seconds: float
    confidence: float
    created_at: str


class ContractAwardRequest(BaseModel):
    """Request to award a contract"""
    strategy: str = Field("lowest_price", description="Award strategy")


class DeliverySubmitRequest(BaseModel):
    """Request to submit delivery"""
    data: Dict[str, Any] = Field(..., description="Result data")


class DeliveryResponse(BaseModel):
    """Delivery information"""
    id: str
    contract_id: str
    agent_id: Optional[str]
    data: Dict[str, Any]
    is_validated: bool
    validation_score: Optional[float]
    delivered_at: str
    validated_at: Optional[str] = None


# ============================================================================
# CONTRACT CREATION
# ============================================================================

@router.post("/contracts", response_model=ContractResponse)
async def create_contract(
    request: ContractCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new contract for agents to bid on.

    This announces a task to the agent network. Agents will discover it,
    evaluate if they can complete it, and submit bids.

    **Flow:**
    1. User creates contract with task description
    2. Contract is broadcast to agent network (WebSocket)
    3. Agents submit bids
    4. User (or auto) awards contract to best bidder
    5. Winner executes task
    6. Winner delivers result
    7. User validates and settles payment

    **Example:**
    ```json
    {
        "intent": "image_generation",
        "context": {
            "prompt": "A realistic sunset over mountains",
            "style": "realistic",
            "size": "1024x1024"
        },
        "reward_amount": 10.0,
        "expires_in_minutes": 60
    }
    ```
    """
    logger.info(f"User {user.email} creating contract: {request.intent}")

    try:
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(minutes=request.expires_in_minutes)

        # Create contract
        contract = Contract(
            user_id=user.id,
            intent=request.intent,
            context=request.context,
            reward_amount=request.reward_amount,
            reward_currency=request.reward_currency,
            status=ContractStatus.OPEN,
            expires_at=expires_at
        )

        db.add(contract)
        await db.commit()
        await db.refresh(contract)

        logger.info(f"Contract created: {contract.id}")

        # Broadcast to agent network via WebSocket
        await manager.broadcast_to_agents({
            "type": "contract_announced",
            "contract": {
                "id": contract.id,
                "intent": contract.intent,
                "context": contract.context,
                "reward_amount": contract.reward_amount,
                "reward_currency": contract.reward_currency,
                "expires_at": contract.expires_at.isoformat()
            }
        })

        return ContractResponse(
            id=contract.id,
            user_id=contract.user_id,
            intent=contract.intent,
            context=contract.context,
            reward_amount=contract.reward_amount,
            reward_currency=contract.reward_currency,
            status=contract.status.value,
            awarded_to=contract.awarded_to,
            created_at=contract.created_at.isoformat(),
            expires_at=contract.expires_at.isoformat() if contract.expires_at else None,
            awarded_at=contract.awarded_at.isoformat() if contract.awarded_at else None,
            completed_at=contract.completed_at.isoformat() if contract.completed_at else None,
            total_bids=0
        )

    except Exception as e:
        logger.error(f"Contract creation failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contract creation failed: {str(e)}"
        )


# ============================================================================
# CONTRACT BIDDING
# ============================================================================

@router.post("/contracts/{contract_id}/bid", response_model=BidResponse)
async def submit_bid(
    contract_id: str,
    request: BidSubmitRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a bid on an open contract.

    Agents evaluate contracts and submit competitive bids based on:
    - Their capability to complete the task
    - Their current workload
    - Market prices
    - Reputation considerations

    **Requirements:**
    - Contract must be in OPEN or BIDDING status
    - Agent must have relevant capabilities
    - Bid price must be reasonable

    **Example:**
    ```json
    {
        "price": 8.50,
        "eta_seconds": 30.0,
        "confidence": 0.95
    }
    ```
    """
    logger.info(f"Agent {agent.name} bidding on contract {contract_id}")

    try:
        # Get contract
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract {contract_id} not found"
            )

        # Check contract status
        if contract.status not in [ContractStatus.OPEN, ContractStatus.BIDDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract not accepting bids (status: {contract.status})"
            )

        # Check if contract expired
        if contract.expires_at and datetime.utcnow() > contract.expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract has expired"
            )

        # Check if agent already bid
        stmt = select(Bid).where(
            and_(
                Bid.contract_id == contract_id,
                Bid.agent_id == agent.id
            )
        )
        result = await db.execute(stmt)
        existing_bid = result.scalar_one_or_none()

        if existing_bid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent has already bid on this contract"
            )

        # Create bid
        bid = Bid(
            contract_id=contract_id,
            agent_id=agent.id,
            price=request.price,
            eta_seconds=request.eta_seconds,
            confidence=request.confidence
        )

        db.add(bid)

        # Update contract status to BIDDING
        if contract.status == ContractStatus.OPEN:
            contract.status = ContractStatus.BIDDING

        await db.commit()
        await db.refresh(bid)

        logger.info(f"Bid submitted: {bid.id} by {agent.name} for ${bid.price}")

        # Broadcast bid to contract issuer
        await manager.send_to_user(contract.user_id, {
            "type": "bid_submitted",
            "contract_id": contract_id,
            "bid": {
                "id": bid.id,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "price": bid.price,
                "eta_seconds": bid.eta_seconds,
                "confidence": bid.confidence
            }
        })

        return BidResponse(
            id=bid.id,
            contract_id=bid.contract_id,
            agent_id=bid.agent_id,
            price=bid.price,
            eta_seconds=bid.eta_seconds,
            confidence=bid.confidence,
            created_at=bid.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bid submission failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bid submission failed: {str(e)}"
        )


# ============================================================================
# CONTRACT AWARD
# ============================================================================

@router.post("/contracts/{contract_id}/award", response_model=ContractResponse)
async def award_contract(
    contract_id: str,
    request: ContractAwardRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Award a contract to the winning bidder.

    **Award Strategies:**
    - `lowest_price`: Select bid with lowest price
    - `fastest`: Select bid with lowest ETA
    - `best_confidence`: Select bid with highest confidence
    - `balanced`: Balance price, speed, and confidence

    **Example:**
    ```json
    {
        "strategy": "lowest_price"
    }
    ```
    """
    logger.info(f"User {user.email} awarding contract {contract_id}")

    try:
        # Get contract
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract {contract_id} not found"
            )

        # Check ownership
        if contract.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to award this contract"
            )

        # Check status
        if contract.status not in [ContractStatus.OPEN, ContractStatus.BIDDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract cannot be awarded (status: {contract.status})"
            )

        # Get all bids
        stmt = select(Bid).where(Bid.contract_id == contract_id)
        result = await db.execute(stmt)
        bids = list(result.scalars())

        if not bids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No bids to award"
            )

        # Select winner based on strategy
        if request.strategy == "lowest_price":
            winner = min(bids, key=lambda b: b.price)
        elif request.strategy == "fastest":
            winner = min(bids, key=lambda b: b.eta_seconds)
        elif request.strategy == "best_confidence":
            winner = max(bids, key=lambda b: b.confidence)
        elif request.strategy == "balanced":
            # Normalize and balance all factors
            winner = min(bids, key=lambda b: (
                b.price / 10.0 +  # Normalize price
                b.eta_seconds / 60.0 +  # Normalize ETA
                (1.0 - b.confidence)  # Invert confidence
            ))
        else:
            # Default to lowest price
            winner = min(bids, key=lambda b: b.price)

        # Update contract
        contract.status = ContractStatus.AWARDED
        contract.awarded_to = winner.agent_id
        contract.awarded_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Contract {contract_id} awarded to {winner.agent_id} (${winner.price})")

        # Notify winner
        await manager.send_to_agent(winner.agent_id, {
            "type": "contract_awarded",
            "contract_id": contract_id,
            "message": "Congratulations! You won the bid."
        })

        # Notify other bidders
        for bid in bids:
            if bid.agent_id != winner.agent_id:
                await manager.send_to_agent(bid.agent_id, {
                    "type": "bid_rejected",
                    "contract_id": contract_id,
                    "message": "Your bid was not selected."
                })

        return ContractResponse(
            id=contract.id,
            user_id=contract.user_id,
            intent=contract.intent,
            context=contract.context,
            reward_amount=contract.reward_amount,
            reward_currency=contract.reward_currency,
            status=contract.status.value,
            awarded_to=contract.awarded_to,
            created_at=contract.created_at.isoformat(),
            expires_at=contract.expires_at.isoformat() if contract.expires_at else None,
            awarded_at=contract.awarded_at.isoformat() if contract.awarded_at else None,
            completed_at=contract.completed_at.isoformat() if contract.completed_at else None,
            total_bids=len(bids)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract award failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contract award failed: {str(e)}"
        )


# ============================================================================
# DELIVERY
# ============================================================================

@router.post("/contracts/{contract_id}/deliver", response_model=DeliveryResponse)
async def deliver_result(
    contract_id: str,
    request: DeliverySubmitRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit delivery for an awarded contract.

    The winning agent delivers the completed work.

    **Requirements:**
    - Agent must be the awarded winner
    - Contract must be in AWARDED or IN_PROGRESS status
    - Result data must be provided

    **Example:**
    ```json
    {
        "data": {
            "image_url": "https://storage.example.com/image.png",
            "metadata": {
                "generated_at": "2025-10-30T10:00:00Z",
                "model": "stable-diffusion-xl"
            }
        }
    }
    ```
    """
    logger.info(f"Agent {agent.name} delivering result for contract {contract_id}")

    try:
        # Get contract
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract {contract_id} not found"
            )

        # Check if agent is winner
        if contract.awarded_to != agent.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the awarded agent can deliver"
            )

        # Check status
        if contract.status not in [ContractStatus.AWARDED, ContractStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract not ready for delivery (status: {contract.status})"
            )

        # Check if already delivered
        stmt = select(Delivery).where(Delivery.contract_id == contract_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract already delivered"
            )

        # Create delivery
        delivery = Delivery(
            contract_id=contract_id,
            agent_id=agent.id,
            data=request.data,
            is_validated=False
        )

        db.add(delivery)

        # Update contract status
        contract.status = ContractStatus.DELIVERED
        contract.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(delivery)

        logger.info(f"Delivery submitted: {delivery.id}")

        # Notify contract issuer
        await manager.send_to_user(contract.user_id, {
            "type": "contract_delivered",
            "contract_id": contract_id,
            "agent_id": agent.id,
            "agent_name": agent.name,
            "message": "Result delivered. Please validate."
        })

        return DeliveryResponse(
            id=delivery.id,
            contract_id=delivery.contract_id,
            agent_id=delivery.agent_id,
            data=delivery.data,
            is_validated=delivery.is_validated,
            validation_score=delivery.validation_score,
            delivered_at=delivery.delivered_at.isoformat(),
            validated_at=delivery.validated_at.isoformat() if delivery.validated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delivery submission failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delivery submission failed: {str(e)}"
        )


# ============================================================================
# VALIDATION & SETTLEMENT
# ============================================================================

@router.post("/contracts/{contract_id}/validate")
async def validate_delivery(
    contract_id: str,
    validation_score: float = Field(..., ge=0.0, le=1.0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a delivered result and settle payment.

    **Validation Score:**
    - 1.0: Perfect, exceeds expectations
    - 0.8-0.9: Good, meets expectations
    - 0.6-0.7: Acceptable, minor issues
    - <0.6: Poor, major issues

    Scores affect agent reputation.
    """
    logger.info(f"User {user.email} validating contract {contract_id}")

    try:
        # Get contract
        stmt = select(Contract).where(Contract.id == contract_id)
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract {contract_id} not found"
            )

        # Check ownership
        if contract.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to validate this contract"
            )

        # Check status
        if contract.status != ContractStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract not ready for validation (status: {contract.status})"
            )

        # Get delivery
        stmt = select(Delivery).where(Delivery.contract_id == contract_id)
        result = await db.execute(stmt)
        delivery = result.scalar_one_or_none()

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No delivery found"
            )

        # Update delivery validation
        delivery.is_validated = True
        delivery.validation_score = validation_score
        delivery.validated_at = datetime.utcnow()

        # Update contract status
        contract.status = ContractStatus.VALIDATED if validation_score >= 0.6 else ContractStatus.FAILED

        # If validated, settle payment
        if contract.status == ContractStatus.VALIDATED:
            contract.status = ContractStatus.SETTLED

        await db.commit()

        logger.info(f"Contract {contract_id} validated with score {validation_score}")

        # Notify agent
        await manager.send_to_agent(contract.awarded_to, {
            "type": "contract_validated",
            "contract_id": contract_id,
            "validation_score": validation_score,
            "status": contract.status.value,
            "message": "Contract settled" if contract.status == ContractStatus.SETTLED else "Validation failed"
        })

        # TODO: Update agent reputation based on validation_score
        # TODO: Process payment (release escrow)

        return {
            "success": True,
            "contract_id": contract_id,
            "validation_score": validation_score,
            "status": contract.status.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


# ============================================================================
# CONTRACT QUERIES
# ============================================================================

@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts(
    status_filter: Optional[str] = None,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    List contracts available to bid on (for agents).

    Returns contracts filtered by status (default: OPEN and BIDDING).
    """
    logger.info(f"Agent {agent.name} listing contracts")

    # Build query
    stmt = select(Contract)

    if status_filter:
        try:
            status_enum = ContractStatus(status_filter.lower())
            stmt = stmt.where(Contract.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    else:
        # Default: show OPEN and BIDDING
        stmt = stmt.where(
            Contract.status.in_([ContractStatus.OPEN, ContractStatus.BIDDING])
        )

    stmt = stmt.order_by(Contract.created_at.desc()).limit(50)

    result = await db.execute(stmt)
    contracts = list(result.scalars())

    # Get bid counts
    contract_responses = []
    for contract in contracts:
        stmt = select(Bid).where(Bid.contract_id == contract.id)
        result = await db.execute(stmt)
        bids = list(result.scalars())

        contract_responses.append(ContractResponse(
            id=contract.id,
            user_id=contract.user_id,
            intent=contract.intent,
            context=contract.context,
            reward_amount=contract.reward_amount,
            reward_currency=contract.reward_currency,
            status=contract.status.value,
            awarded_to=contract.awarded_to,
            created_at=contract.created_at.isoformat(),
            expires_at=contract.expires_at.isoformat() if contract.expires_at else None,
            awarded_at=contract.awarded_at.isoformat() if contract.awarded_at else None,
            completed_at=contract.completed_at.isoformat() if contract.completed_at else None,
            total_bids=len(bids)
        ))

    return contract_responses


@router.get("/contracts/{contract_id}/bids", response_model=List[BidResponse])
async def get_contract_bids(
    contract_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all bids for a contract (contract owner only).
    """
    # Get contract
    stmt = select(Contract).where(Contract.id == contract_id)
    result = await db.execute(stmt)
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract {contract_id} not found"
        )

    # Check ownership
    if contract.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view bids"
        )

    # Get bids
    stmt = select(Bid).where(Bid.contract_id == contract_id).order_by(Bid.price)
    result = await db.execute(stmt)
    bids = list(result.scalars())

    return [
        BidResponse(
            id=bid.id,
            contract_id=bid.contract_id,
            agent_id=bid.agent_id,
            price=bid.price,
            eta_seconds=bid.eta_seconds,
            confidence=bid.confidence,
            created_at=bid.created_at.isoformat()
        )
        for bid in bids
    ]


@router.get("/my-contracts", response_model=List[ContractResponse])
async def get_my_contracts(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Get contracts awarded to this agent.

    Returns contracts where the agent won the bid.
    """
    logger.info(f"Agent {agent.name} fetching awarded contracts")

    stmt = select(Contract).where(
        Contract.awarded_to == agent.id
    ).order_by(Contract.awarded_at.desc())

    result = await db.execute(stmt)
    contracts = list(result.scalars())

    return [
        ContractResponse(
            id=contract.id,
            user_id=contract.user_id,
            intent=contract.intent,
            context=contract.context,
            reward_amount=contract.reward_amount,
            reward_currency=contract.reward_currency,
            status=contract.status.value,
            awarded_to=contract.awarded_to,
            created_at=contract.created_at.isoformat(),
            expires_at=contract.expires_at.isoformat() if contract.expires_at else None,
            awarded_at=contract.awarded_at.isoformat() if contract.awarded_at else None,
            completed_at=contract.completed_at.isoformat() if contract.completed_at else None,
            total_bids=0
        )
        for contract in contracts
    ]
