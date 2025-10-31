"""
Credit Service

Internal credit system for platform currency.

Sprint 3: Economic System & Payments
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models_payments import Credit

logger = logging.getLogger(__name__)


class CreditService:
    """Internal credit management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_credits(
        self,
        user_id: str,
        amount: Decimal,
        transaction_type: str,
        description: Optional[str] = None,
        payment_id: Optional[str] = None,
        contract_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Credit:
        """
        Add credits to user account.

        Args:
            user_id: User ID
            amount: Credit amount (positive)
            transaction_type: Transaction type (purchase, refund, reward, etc.)
            description: Transaction description
            payment_id: Related payment ID
            contract_id: Related contract ID
            expires_at: Expiration date (for promotional credits)

        Returns:
            Credit transaction
        """
        if amount <= 0:
            raise ValueError("Amount must be positive for adding credits")

        # Get current balance
        current_balance = await self.get_balance(user_id)
        new_balance = current_balance + amount

        # Create credit transaction
        credit = Credit(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            transaction_type=transaction_type,
            description=description,
            payment_id=payment_id,
            contract_id=contract_id,
            expires_at=expires_at
        )

        self.db.add(credit)
        await self.db.commit()
        await self.db.refresh(credit)

        logger.info(f"Added {amount} credits to user {user_id} (balance: {new_balance})")

        return credit

    async def deduct_credits(
        self,
        user_id: str,
        amount: Decimal,
        description: str,
        payment_id: Optional[str] = None,
        contract_id: Optional[str] = None
    ) -> Credit:
        """
        Deduct credits from user account.

        Args:
            user_id: User ID
            amount: Credit amount to deduct (positive)
            description: Transaction description
            payment_id: Related payment ID
            contract_id: Related contract ID

        Returns:
            Credit transaction

        Raises:
            ValueError: If insufficient balance
        """
        if amount <= 0:
            raise ValueError("Amount must be positive for deducting credits")

        # Get current balance
        current_balance = await self.get_balance(user_id)

        if current_balance < amount:
            raise ValueError(
                f"Insufficient credits. Balance: {current_balance}, Required: {amount}"
            )

        new_balance = current_balance - amount

        # Create debit transaction (negative amount)
        credit = Credit(
            user_id=user_id,
            amount=-amount,  # Negative for debit
            balance_after=new_balance,
            transaction_type="usage",
            description=description,
            payment_id=payment_id,
            contract_id=contract_id
        )

        self.db.add(credit)
        await self.db.commit()
        await self.db.refresh(credit)

        logger.info(f"Deducted {amount} credits from user {user_id} (balance: {new_balance})")

        return credit

    async def get_balance(self, user_id: str) -> Decimal:
        """
        Get current credit balance for user.

        Returns the balance_after from the most recent transaction,
        or 0 if no transactions exist.

        Args:
            user_id: User ID

        Returns:
            Current balance
        """
        result = await self.db.execute(
            select(Credit.balance_after)
            .where(Credit.user_id == user_id)
            .order_by(Credit.created_at.desc())
            .limit(1)
        )

        balance = result.scalar_one_or_none()
        return Decimal(balance or 0)

    async def get_transactions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> List[Credit]:
        """
        Get credit transaction history.

        Args:
            user_id: User ID
            limit: Max number of transactions
            offset: Pagination offset
            transaction_type: Filter by transaction type

        Returns:
            List of credit transactions
        """
        query = select(Credit).where(Credit.user_id == user_id)

        if transaction_type:
            query = query.where(Credit.transaction_type == transaction_type)

        query = query.order_by(Credit.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def purchase_credits(
        self,
        user_id: str,
        amount: Decimal,
        payment_id: str
    ) -> Credit:
        """
        Purchase credits via payment.

        Args:
            user_id: User ID
            amount: Credit amount
            payment_id: Completed payment ID

        Returns:
            Credit transaction
        """
        return await self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type="purchase",
            description=f"Purchased {amount} credits",
            payment_id=payment_id
        )

    async def award_credits(
        self,
        user_id: str,
        amount: Decimal,
        reason: str,
        expires_in_days: Optional[int] = None
    ) -> Credit:
        """
        Award promotional credits.

        Args:
            user_id: User ID
            amount: Credit amount
            reason: Award reason
            expires_in_days: Days until expiration

        Returns:
            Credit transaction
        """
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        return await self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type="reward",
            description=reason,
            expires_at=expires_at
        )

    async def refund_credits(
        self,
        user_id: str,
        amount: Decimal,
        reason: str,
        payment_id: Optional[str] = None
    ) -> Credit:
        """
        Refund credits to user.

        Args:
            user_id: User ID
            amount: Credit amount
            reason: Refund reason
            payment_id: Related payment ID

        Returns:
            Credit transaction
        """
        return await self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type="refund",
            description=reason,
            payment_id=payment_id
        )

    async def expire_credits(self):
        """
        Expire promotional credits past their expiration date.

        This should be run as a periodic background task.
        """
        # Find expired credits that haven't been processed
        result = await self.db.execute(
            select(Credit).where(
                Credit.expires_at.isnot(None),
                Credit.expires_at < datetime.utcnow(),
                Credit.amount > 0  # Only promotional credits (positive amounts)
            ).order_by(Credit.user_id, Credit.created_at)
        )

        expired_credits = result.scalars().all()

        # Group by user and deduct expired amounts
        user_expirations = {}
        for credit in expired_credits:
            user_id = credit.user_id
            if user_id not in user_expirations:
                user_expirations[user_id] = Decimal(0)
            user_expirations[user_id] += credit.amount

        # Create expiration transactions
        for user_id, amount in user_expirations.items():
            try:
                await self.deduct_credits(
                    user_id=user_id,
                    amount=amount,
                    description=f"Expired promotional credits: {amount}"
                )
                logger.info(f"Expired {amount} credits for user {user_id}")
            except ValueError as e:
                logger.error(f"Failed to expire credits for user {user_id}: {e}")

        await self.db.commit()

        return len(user_expirations)

    async def get_credit_stats(self, user_id: str) -> dict:
        """
        Get credit statistics for user.

        Returns:
            {
                "current_balance": Decimal,
                "total_purchased": Decimal,
                "total_earned": Decimal,
                "total_spent": Decimal,
                "pending_expiration": Decimal
            }
        """
        # Current balance
        balance = await self.get_balance(user_id)

        # Total purchased
        result = await self.db.execute(
            select(func.sum(Credit.amount)).where(
                Credit.user_id == user_id,
                Credit.transaction_type == "purchase"
            )
        )
        total_purchased = result.scalar_one_or_none() or Decimal(0)

        # Total earned (rewards)
        result = await self.db.execute(
            select(func.sum(Credit.amount)).where(
                Credit.user_id == user_id,
                Credit.transaction_type == "reward"
            )
        )
        total_earned = result.scalar_one_or_none() or Decimal(0)

        # Total spent
        result = await self.db.execute(
            select(func.sum(Credit.amount)).where(
                Credit.user_id == user_id,
                Credit.transaction_type == "usage",
                Credit.amount < 0
            )
        )
        total_spent = abs(result.scalar_one_or_none() or Decimal(0))

        # Pending expiration
        result = await self.db.execute(
            select(func.sum(Credit.amount)).where(
                Credit.user_id == user_id,
                Credit.expires_at.isnot(None),
                Credit.expires_at > datetime.utcnow(),
                Credit.amount > 0
            )
        )
        pending_expiration = result.scalar_one_or_none() or Decimal(0)

        return {
            "current_balance": balance,
            "total_purchased": total_purchased,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "pending_expiration": pending_expiration
        }
