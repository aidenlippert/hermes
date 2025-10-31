"""
Payment API Endpoints

Sprint 3: Economic System & Payments
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.models import User
from backend.database.models_payments import PaymentProvider
from backend.auth import get_current_user
from backend.services.payment_service import PaymentService
from backend.services.escrow_service import EscrowService
from backend.services.credit_service import CreditService
from backend.services.pricing_engine import PricingEngine
from backend.services.billing_service import BillingService

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    provider: PaymentProvider
    description: Optional[str] = None
    contract_id: Optional[str] = None


class CreateEscrowRequest(BaseModel):
    contract_id: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"


class PurchaseCreditsRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    provider: PaymentProvider


@router.post("/create")
async def create_payment(
    request: CreatePaymentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create payment"""
    service = PaymentService(db)

    payment = await service.create_payment(
        user_id=user.id,
        amount=request.amount,
        currency=request.currency,
        provider=request.provider,
        description=request.description,
        contract_id=request.contract_id
    )

    return {
        "payment_id": payment.id,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "status": payment.status.value,
        "provider_data": payment.provider_metadata
    }


@router.post("/credits/purchase")
async def purchase_credits(
    request: PurchaseCreditsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Purchase credits"""
    payment_service = PaymentService(db)
    credit_service = CreditService(db)

    # Create payment
    payment = await payment_service.create_payment(
        user_id=user.id,
        amount=request.amount,
        currency="USD",
        provider=request.provider,
        description=f"Purchase {request.amount} credits"
    )

    # Add credits after payment completes
    if payment.status.value == "completed":
        await credit_service.purchase_credits(
            user_id=user.id,
            amount=request.amount,
            payment_id=payment.id
        )

    return {
        "payment_id": payment.id,
        "credits": str(request.amount),
        "status": payment.status.value
    }


@router.get("/credits/balance")
async def get_credit_balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get credit balance"""
    service = CreditService(db)
    balance = await service.get_balance(user.id)
    stats = await service.get_credit_stats(user.id)

    return {
        "balance": str(balance),
        "stats": {k: str(v) for k, v in stats.items()}
    }


@router.post("/escrow/create")
async def create_escrow(
    request: CreateEscrowRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create escrow"""
    service = EscrowService(db)

    escrow = await service.create_escrow(
        contract_id=request.contract_id,
        amount=request.amount,
        currency=request.currency,
        payer_id=user.id
    )

    return {
        "escrow_id": escrow.id,
        "amount": str(escrow.amount),
        "status": escrow.status.value
    }


@router.get("/pricing/{agent_id}")
async def get_pricing(
    agent_id: str,
    base_price: Decimal,
    db: AsyncSession = Depends(get_db)
):
    """Get dynamic pricing"""
    service = PricingEngine(db)

    pricing = await service.calculate_price(
        agent_id=agent_id,
        base_price=base_price
    )

    return {
        "base_price": str(pricing["base_price"]),
        "adjusted_price": str(pricing["adjusted_price"]),
        "multiplier": pricing["multiplier"],
        "adjustments": pricing["adjustments"]
    }
