"""
Payment Service

Multi-provider payment processing with Stripe, PayPal, and Credits support.

Sprint 3: Economic System & Payments
"""

import os
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User
from backend.database.models_payments import (
    Payment,
    PaymentMethod,
    PaymentProvider,
    PaymentStatus
)

logger = logging.getLogger(__name__)


class StripeProvider:
    """Stripe payment provider integration"""

    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not configured")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe payment intent.

        In production, this would use the Stripe SDK:
        import stripe
        stripe.api_key = self.api_key
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency.lower(),
            metadata=metadata or {}
        )
        """
        if not self.api_key:
            raise ValueError("Stripe not configured")

        # Stub implementation
        payment_intent_id = f"pi_stub_{datetime.utcnow().timestamp()}"

        logger.info(f"Created Stripe payment intent: {payment_intent_id}")

        return {
            "id": payment_intent_id,
            "client_secret": f"{payment_intent_id}_secret",
            "status": "requires_payment_method",
            "amount": int(amount * 100),
            "currency": currency
        }

    async def confirm_payment(
        self,
        payment_intent_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Confirm Stripe payment.

        In production:
        intent = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method=payment_method_id
        )
        """
        logger.info(f"Confirmed Stripe payment: {payment_intent_id}")

        return {
            "id": payment_intent_id,
            "status": "succeeded",
            "amount_received": 1000
        }

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Create refund.

        In production:
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=int(amount * 100) if amount else None
        )
        """
        logger.info(f"Created Stripe refund: {payment_intent_id}")

        return {
            "id": f"re_stub_{datetime.utcnow().timestamp()}",
            "status": "succeeded",
            "amount": int((amount or 0) * 100)
        }

    async def create_payment_method(
        self,
        card_token: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create payment method from card token.

        In production:
        method = stripe.PaymentMethod.create(
            type="card",
            card={"token": card_token}
        )
        if customer_id:
            stripe.PaymentMethod.attach(method.id, customer=customer_id)
        """
        method_id = f"pm_stub_{datetime.utcnow().timestamp()}"

        return {
            "id": method_id,
            "type": "card",
            "card": {
                "last4": "4242",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2025
            }
        }

    async def create_customer(
        self,
        email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe customer.

        In production:
        customer = stripe.Customer.create(
            email=email,
            metadata=metadata or {}
        )
        """
        customer_id = f"cus_stub_{datetime.utcnow().timestamp()}"

        return {
            "id": customer_id,
            "email": email
        }


class PayPalProvider:
    """PayPal payment provider integration"""

    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        if not self.client_id:
            logger.warning("PAYPAL credentials not configured")

    async def create_order(
        self,
        amount: Decimal,
        currency: str
    ) -> Dict[str, Any]:
        """
        Create PayPal order.

        In production, use PayPal SDK or REST API.
        """
        if not self.client_id:
            raise ValueError("PayPal not configured")

        order_id = f"PAYPAL_{datetime.utcnow().timestamp()}"

        logger.info(f"Created PayPal order: {order_id}")

        return {
            "id": order_id,
            "status": "CREATED",
            "amount": str(amount),
            "currency": currency,
            "approval_url": f"https://paypal.com/checkoutnow?token={order_id}"
        }

    async def capture_order(
        self,
        order_id: str
    ) -> Dict[str, Any]:
        """Capture PayPal order after user approval"""
        logger.info(f"Captured PayPal order: {order_id}")

        return {
            "id": order_id,
            "status": "COMPLETED",
            "capture_id": f"CAP_{order_id}"
        }


class CryptoProvider:
    """Cryptocurrency payment provider (placeholder)"""

    async def create_payment_address(
        self,
        amount: Decimal,
        currency: str = "BTC"
    ) -> Dict[str, Any]:
        """Generate crypto payment address"""
        address = f"bc1q{datetime.utcnow().timestamp()}"

        return {
            "address": address,
            "amount": str(amount),
            "currency": currency,
            "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?data={address}"
        }


class PaymentService:
    """Main payment service coordinating all providers"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stripe = StripeProvider()
        self.paypal = PayPalProvider()
        self.crypto = CryptoProvider()

    async def create_payment(
        self,
        user_id: str,
        amount: Decimal,
        currency: str,
        provider: PaymentProvider,
        description: Optional[str] = None,
        contract_id: Optional[str] = None,
        payment_method_id: Optional[str] = None
    ) -> Payment:
        """
        Create payment transaction.

        Args:
            user_id: User making the payment
            amount: Payment amount
            currency: Currency code (USD, EUR, etc.)
            provider: Payment provider to use
            description: Payment description
            contract_id: Optional contract reference
            payment_method_id: Stored payment method ID

        Returns:
            Payment object
        """
        # Create payment record
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            provider=provider,
            status=PaymentStatus.PENDING,
            description=description,
            contract_id=contract_id,
            payment_method_id=payment_method_id
        )
        self.db.add(payment)
        await self.db.flush()

        try:
            # Process with provider
            if provider == PaymentProvider.STRIPE:
                result = await self._process_stripe_payment(payment)
            elif provider == PaymentProvider.PAYPAL:
                result = await self._process_paypal_payment(payment)
            elif provider == PaymentProvider.CRYPTO:
                result = await self._process_crypto_payment(payment)
            elif provider == PaymentProvider.CREDITS:
                result = await self._process_credits_payment(payment)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Update payment with provider details
            payment.provider_payment_id = result.get("id")
            payment.provider_metadata = result

            await self.db.commit()

            return payment

        except Exception as e:
            logger.error(f"Payment creation failed: {e}")
            payment.status = PaymentStatus.FAILED
            await self.db.commit()
            raise

    async def _process_stripe_payment(self, payment: Payment) -> Dict[str, Any]:
        """Process Stripe payment"""
        # Create payment intent
        intent = await self.stripe.create_payment_intent(
            amount=payment.amount,
            currency=payment.currency,
            metadata={
                "payment_id": payment.id,
                "user_id": payment.user_id,
                "contract_id": payment.contract_id
            }
        )

        payment.status = PaymentStatus.PROCESSING

        return intent

    async def _process_paypal_payment(self, payment: Payment) -> Dict[str, Any]:
        """Process PayPal payment"""
        order = await self.paypal.create_order(
            amount=payment.amount,
            currency=payment.currency
        )

        payment.status = PaymentStatus.PROCESSING

        return order

    async def _process_crypto_payment(self, payment: Payment) -> Dict[str, Any]:
        """Process crypto payment"""
        payment_address = await self.crypto.create_payment_address(
            amount=payment.amount,
            currency="BTC"
        )

        payment.status = PaymentStatus.PROCESSING

        return payment_address

    async def _process_credits_payment(self, payment: Payment) -> Dict[str, Any]:
        """Process credits payment (internal)"""
        from backend.services.credit_service import CreditService

        credit_service = CreditService(self.db)

        # Deduct credits
        await credit_service.deduct_credits(
            user_id=payment.user_id,
            amount=payment.amount,
            description=payment.description or "Payment",
            payment_id=payment.id
        )

        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()

        return {"status": "completed"}

    async def confirm_payment(
        self,
        payment_id: str,
        provider_confirmation_data: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """
        Confirm payment completion.

        Called after user completes payment flow (e.g., returns from PayPal, confirms Stripe).
        """
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status == PaymentStatus.COMPLETED:
            return payment

        try:
            if payment.provider == PaymentProvider.STRIPE:
                # Confirm with Stripe
                await self.stripe.confirm_payment(
                    payment_intent_id=payment.provider_payment_id,
                    payment_method_id=provider_confirmation_data.get("payment_method_id")
                )

            elif payment.provider == PaymentProvider.PAYPAL:
                # Capture PayPal order
                await self.paypal.capture_order(
                    order_id=payment.provider_payment_id
                )

            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()

            await self.db.commit()

            return payment

        except Exception as e:
            logger.error(f"Payment confirmation failed: {e}")
            payment.status = PaymentStatus.FAILED
            await self.db.commit()
            raise

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Payment:
        """
        Refund a payment (full or partial).

        Args:
            payment_id: Payment to refund
            amount: Optional partial refund amount
            reason: Refund reason

        Returns:
            Updated payment object
        """
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("Can only refund completed payments")

        refund_amount = amount or payment.amount

        try:
            if payment.provider == PaymentProvider.STRIPE:
                await self.stripe.create_refund(
                    payment_intent_id=payment.provider_payment_id,
                    amount=refund_amount
                )

            elif payment.provider == PaymentProvider.CREDITS:
                from backend.services.credit_service import CreditService
                credit_service = CreditService(self.db)
                await credit_service.add_credits(
                    user_id=payment.user_id,
                    amount=refund_amount,
                    transaction_type="refund",
                    description=f"Refund: {reason or 'Payment refunded'}",
                    payment_id=payment.id
                )

            payment.status = PaymentStatus.REFUNDED
            await self.db.commit()

            return payment

        except Exception as e:
            logger.error(f"Refund failed: {e}")
            raise

    async def save_payment_method(
        self,
        user_id: str,
        provider: PaymentProvider,
        card_token: str,
        set_as_default: bool = False
    ) -> PaymentMethod:
        """
        Save payment method for future use.

        Args:
            user_id: User ID
            provider: Payment provider
            card_token: Card token from provider
            set_as_default: Set as default payment method

        Returns:
            PaymentMethod object
        """
        # Get or create Stripe customer
        user = await self.db.get(User, user_id)

        if provider == PaymentProvider.STRIPE:
            # Create payment method with Stripe
            method_data = await self.stripe.create_payment_method(
                card_token=card_token
            )

            payment_method = PaymentMethod(
                user_id=user_id,
                provider=provider,
                provider_method_id=method_data["id"],
                card_last4=method_data["card"]["last4"],
                card_brand=method_data["card"]["brand"],
                card_exp_month=method_data["card"]["exp_month"],
                card_exp_year=method_data["card"]["exp_year"],
                billing_email=user.email,
                is_default=set_as_default
            )

            self.db.add(payment_method)

            # Unset other default methods if this is default
            if set_as_default:
                result = await self.db.execute(
                    select(PaymentMethod).where(
                        PaymentMethod.user_id == user_id,
                        PaymentMethod.is_default == True,
                        PaymentMethod.id != payment_method.id
                    )
                )
                for method in result.scalars():
                    method.is_default = False

            await self.db.commit()

            return payment_method

        raise ValueError(f"Unsupported provider: {provider}")

    async def get_payment_methods(self, user_id: str) -> List[PaymentMethod]:
        """Get all payment methods for a user"""
        result = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.user_id == user_id,
                PaymentMethod.is_active == True
            ).order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        )
        return list(result.scalars().all())
