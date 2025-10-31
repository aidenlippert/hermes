"""
Escrow Service

Secure escrow management for contract-based payments with multi-signature support.

Sprint 3: Economic System & Payments
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Contract, ContractStatus, User
from backend.database.models_payments import (
    Escrow,
    EscrowStatus,
    Payment,
    PaymentStatus,
    Dispute,
    DisputeStatus
)
from backend.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class EscrowService:
    """Escrow service for secure contract payments"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_service = PaymentService(db)

    async def create_escrow(
        self,
        contract_id: str,
        amount: Decimal,
        currency: str = "USD",
        payer_id: str = None,
        payee_id: str = None,
        requires_signatures: int = 1,
        auto_release_on_validation: bool = True,
        validation_threshold: float = 0.6
    ) -> Escrow:
        """
        Create escrow for a contract.

        Args:
            contract_id: Contract ID
            amount: Escrow amount
            currency: Currency code
            payer_id: User ID paying into escrow
            payee_id: Agent ID receiving payment
            requires_signatures: Number of signatures needed for release
            auto_release_on_validation: Auto-release when validation score meets threshold
            validation_threshold: Minimum validation score for auto-release (0.0-1.0)

        Returns:
            Escrow object
        """
        # Check if escrow already exists
        existing = await self.db.execute(
            select(Escrow).where(Escrow.contract_id == contract_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Escrow already exists for this contract")

        # Create escrow
        escrow = Escrow(
            contract_id=contract_id,
            amount=amount,
            currency=currency,
            status=EscrowStatus.CREATED,
            payer_id=payer_id,
            payee_id=payee_id,
            requires_signatures=requires_signatures,
            current_signatures=[],
            auto_release_on_validation=auto_release_on_validation,
            validation_threshold=validation_threshold
        )

        self.db.add(escrow)
        await self.db.commit()
        await self.db.refresh(escrow)

        logger.info(f"Created escrow {escrow.id} for contract {contract_id}")

        return escrow

    async def fund_escrow(
        self,
        escrow_id: str,
        payment_id: str
    ) -> Escrow:
        """
        Fund escrow with a completed payment.

        Args:
            escrow_id: Escrow ID
            payment_id: Completed payment ID

        Returns:
            Updated escrow
        """
        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")

        if escrow.status != EscrowStatus.CREATED:
            raise ValueError(f"Escrow must be in CREATED status, got {escrow.status}")

        # Verify payment
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("Payment must be completed")

        if payment.amount < escrow.amount:
            raise ValueError(f"Payment amount ${payment.amount} is less than escrow amount ${escrow.amount}")

        # Fund escrow
        escrow.payment_id = payment_id
        escrow.status = EscrowStatus.FUNDED
        escrow.funded_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Funded escrow {escrow_id} with payment {payment_id}")

        return escrow

    async def add_signature(
        self,
        escrow_id: str,
        signer_user_id: str
    ) -> Escrow:
        """
        Add signature to escrow release.

        Args:
            escrow_id: Escrow ID
            signer_user_id: User ID signing

        Returns:
            Updated escrow
        """
        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")

        if escrow.status != EscrowStatus.FUNDED:
            raise ValueError("Can only sign funded escrows")

        # Check if already signed
        if signer_user_id in escrow.current_signatures:
            raise ValueError("User has already signed")

        # Add signature
        signatures = escrow.current_signatures or []
        signatures.append(signer_user_id)
        escrow.current_signatures = signatures

        # Check if we have enough signatures
        if len(signatures) >= escrow.requires_signatures:
            await self._release_escrow(escrow)

        await self.db.commit()

        logger.info(f"Added signature to escrow {escrow_id} ({len(signatures)}/{escrow.requires_signatures})")

        return escrow

    async def release_escrow(
        self,
        escrow_id: str,
        validation_score: Optional[float] = None
    ) -> Escrow:
        """
        Release escrow to payee.

        Args:
            escrow_id: Escrow ID
            validation_score: Optional validation score (for auto-release)

        Returns:
            Updated escrow
        """
        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")

        if escrow.status != EscrowStatus.FUNDED:
            raise ValueError("Escrow must be funded to release")

        # Check validation score if auto-release is enabled
        if escrow.auto_release_on_validation and validation_score is not None:
            if validation_score < escrow.validation_threshold:
                raise ValueError(
                    f"Validation score {validation_score} is below threshold {escrow.validation_threshold}"
                )

        await self._release_escrow(escrow)
        await self.db.commit()

        return escrow

    async def _release_escrow(self, escrow: Escrow):
        """Internal escrow release logic"""
        # In production, this would transfer funds to the payee
        # For now, we just update the status

        escrow.status = EscrowStatus.RELEASED
        escrow.released_at = datetime.utcnow()

        # Update contract status
        contract = await self.db.get(Contract, escrow.contract_id)
        if contract:
            contract.status = ContractStatus.SETTLED

        logger.info(f"Released escrow {escrow.id}")

    async def refund_escrow(
        self,
        escrow_id: str,
        reason: Optional[str] = None
    ) -> Escrow:
        """
        Refund escrow to payer.

        Args:
            escrow_id: Escrow ID
            reason: Refund reason

        Returns:
            Updated escrow
        """
        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")

        if escrow.status not in [EscrowStatus.FUNDED, EscrowStatus.DISPUTED]:
            raise ValueError("Can only refund funded or disputed escrows")

        # Refund payment
        if escrow.payment_id:
            await self.payment_service.refund_payment(
                payment_id=escrow.payment_id,
                reason=reason or "Escrow refund"
            )

        escrow.status = EscrowStatus.REFUNDED
        await self.db.commit()

        logger.info(f"Refunded escrow {escrow_id}")

        return escrow

    async def create_dispute(
        self,
        escrow_id: str,
        raised_by: str,
        reason: str,
        description: str,
        evidence: Optional[List[str]] = None
    ) -> Dispute:
        """
        Create dispute for escrow.

        Args:
            escrow_id: Escrow ID
            raised_by: User ID raising dispute
            reason: Dispute reason
            description: Detailed description
            evidence: List of evidence URLs

        Returns:
            Dispute object
        """
        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")

        if escrow.status != EscrowStatus.FUNDED:
            raise ValueError("Can only dispute funded escrows")

        # Create dispute
        dispute = Dispute(
            escrow_id=escrow_id,
            contract_id=escrow.contract_id,
            raised_by=raised_by,
            reason=reason,
            description=description,
            evidence=evidence or [],
            status=DisputeStatus.OPEN
        )

        self.db.add(dispute)

        # Update escrow status
        escrow.status = EscrowStatus.DISPUTED

        await self.db.commit()

        logger.info(f"Created dispute {dispute.id} for escrow {escrow_id}")

        return dispute

    async def resolve_dispute(
        self,
        dispute_id: str,
        resolved_by: str,
        resolution: str,
        action: str,
        amount: Optional[Decimal] = None
    ) -> Dispute:
        """
        Resolve dispute.

        Args:
            dispute_id: Dispute ID
            resolved_by: User ID resolving (admin/moderator)
            resolution: Resolution description
            action: Resolution action (refund, release, partial_refund)
            amount: Amount for partial refund

        Returns:
            Updated dispute
        """
        dispute = await self.db.get(Dispute, dispute_id)
        if not dispute:
            raise ValueError("Dispute not found")

        if dispute.status not in [DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]:
            raise ValueError("Dispute already resolved")

        escrow = await self.db.get(Escrow, dispute.escrow_id)

        # Execute resolution action
        if action == "refund":
            await self.refund_escrow(
                escrow_id=dispute.escrow_id,
                reason=f"Dispute resolved: {resolution}"
            )
        elif action == "release":
            await self._release_escrow(escrow)
        elif action == "partial_refund":
            if not amount:
                raise ValueError("Amount required for partial refund")
            # Partial refund logic
            await self.payment_service.refund_payment(
                payment_id=escrow.payment_id,
                amount=amount,
                reason=f"Partial refund: {resolution}"
            )

        # Update dispute
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = resolution
        dispute.resolved_by = resolved_by
        dispute.resolution_action = action
        dispute.resolution_amount = amount
        dispute.resolved_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Resolved dispute {dispute_id} with action: {action}")

        return dispute

    async def check_auto_release(
        self,
        contract_id: str,
        validation_score: float
    ):
        """
        Check if escrow should be auto-released based on validation score.

        Called after contract delivery is validated.

        Args:
            contract_id: Contract ID
            validation_score: Validation score (0.0-1.0)
        """
        result = await self.db.execute(
            select(Escrow).where(Escrow.contract_id == contract_id)
        )
        escrow = result.scalar_one_or_none()

        if not escrow:
            logger.warning(f"No escrow found for contract {contract_id}")
            return

        if escrow.status != EscrowStatus.FUNDED:
            logger.info(f"Escrow {escrow.id} not in funded status, skipping auto-release")
            return

        if not escrow.auto_release_on_validation:
            logger.info(f"Auto-release disabled for escrow {escrow.id}")
            return

        if validation_score >= escrow.validation_threshold:
            logger.info(f"Auto-releasing escrow {escrow.id} (score: {validation_score})")
            await self._release_escrow(escrow)
            await self.db.commit()
        else:
            logger.info(
                f"Validation score {validation_score} below threshold {escrow.validation_threshold}, "
                f"not releasing escrow {escrow.id}"
            )

    async def get_escrow_by_contract(self, contract_id: str) -> Optional[Escrow]:
        """Get escrow for a contract"""
        result = await self.db.execute(
            select(Escrow).where(Escrow.contract_id == contract_id)
        )
        return result.scalar_one_or_none()

    async def get_user_escrows(
        self,
        user_id: str,
        status: Optional[EscrowStatus] = None
    ) -> List[Escrow]:
        """Get all escrows for a user (as payer)"""
        query = select(Escrow).where(Escrow.payer_id == user_id)

        if status:
            query = query.where(Escrow.status == status)

        result = await self.db.execute(query.order_by(Escrow.created_at.desc()))
        return list(result.scalars().all())

    async def get_agent_escrows(
        self,
        agent_id: str,
        status: Optional[EscrowStatus] = None
    ) -> List[Escrow]:
        """Get all escrows for an agent (as payee)"""
        query = select(Escrow).where(Escrow.payee_id == agent_id)

        if status:
            query = query.where(Escrow.status == status)

        result = await self.db.execute(query.order_by(Escrow.created_at.desc()))
        return list(result.scalars().all())
