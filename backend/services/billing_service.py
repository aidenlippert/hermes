"""
Billing and Invoicing Service

Sprint 3: Economic System & Payments
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models_payments import Invoice, InvoiceStatus, UsageRecord

logger = logging.getLogger(__name__)


class BillingService:
    """Billing and invoicing service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invoice(
        self,
        user_id: str,
        line_items: List[Dict],
        tax_rate: float = 0.0,
        due_in_days: int = 30
    ) -> Invoice:
        """Create invoice"""
        # Calculate totals
        amount = sum(Decimal(str(item["total"])) for item in line_items)
        tax_amount = amount * Decimal(str(tax_rate))
        total_amount = amount + tax_amount

        # Generate invoice number
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        invoice = Invoice(
            invoice_number=invoice_number,
            user_id=user_id,
            amount=amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            line_items=line_items,
            status=InvoiceStatus.DRAFT,
            due_date=datetime.utcnow() + timedelta(days=due_in_days)
        )

        self.db.add(invoice)
        await self.db.commit()

        return invoice

    async def record_usage(
        self,
        user_id: str,
        resource_type: str,
        quantity: int,
        unit_price: Optional[Decimal] = None,
        contract_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> UsageRecord:
        """Record usage for billing"""
        total_cost = None
        if unit_price:
            total_cost = Decimal(str(quantity)) * unit_price

        # Current billing period (monthly)
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = period_start + timedelta(days=32)
        period_end = next_month.replace(day=1) - timedelta(seconds=1)

        usage = UsageRecord(
            user_id=user_id,
            resource_type=resource_type,
            quantity=quantity,
            unit_price=unit_price,
            total_cost=total_cost,
            contract_id=contract_id,
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end
        )

        self.db.add(usage)
        await self.db.commit()

        return usage
