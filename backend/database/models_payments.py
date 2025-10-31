"""
Payment and Economic System Models

Advanced payment processing, escrow, and economic models for Sprint 3.

Tables:
- payments: Payment transactions with multi-provider support
- escrows: Secure escrow for contracts
- credits: Internal credit system
- invoices: Billing and invoicing
- subscriptions: User subscription management
- payment_methods: Stored payment methods
- payouts: Agent payouts and earnings
- disputes: Payment disputes and resolutions
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, Index, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid

from .connection import Base


class PaymentProvider(str, Enum):
    """Payment provider types"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    CREDITS = "credits"


class PaymentStatus(str, Enum):
    """Payment transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class EscrowStatus(str, Enum):
    """Escrow status"""
    CREATED = "created"
    FUNDED = "funded"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class DisputeStatus(str, Enum):
    """Dispute status"""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class InvoiceStatus(str, Enum):
    """Invoice status"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PayoutStatus(str, Enum):
    """Payout status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Payment(Base):
    """Payment transactions with multi-provider support"""
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)  # Precise decimal for money
    currency = Column(String, default="USD", nullable=False)
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)

    # Provider-specific data
    provider_payment_id = Column(String, nullable=True, index=True)  # Stripe charge ID, PayPal transaction ID, etc.
    provider_metadata = Column(JSON, default=dict)

    # Purpose
    description = Column(Text, nullable=True)
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_id = Column(String, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)

    # Payment method
    payment_method_id = Column(String, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    escrow = relationship("Escrow", back_populates="payment", uselist=False)

    def __repr__(self):
        return f"<Payment {self.id[:8]}... - ${self.amount} {self.status.value}>"


class Escrow(Base):
    """Secure escrow for contract-based payments"""
    __tablename__ = "escrows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    payment_id = Column(String, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)

    # Escrow details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(SQLEnum(EscrowStatus), default=EscrowStatus.CREATED, nullable=False, index=True)

    # Parties
    payer_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    payee_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True)  # Agent receiving payment

    # Release conditions
    requires_signatures = Column(Integer, default=1)  # Multi-signature support
    current_signatures = Column(JSON, default=list)  # List of user IDs who signed
    auto_release_on_validation = Column(Boolean, default=True)
    validation_threshold = Column(Float, default=0.6)  # Minimum validation score for auto-release

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    funded_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    payment = relationship("Payment", back_populates="escrow")
    disputes = relationship("Dispute", back_populates="escrow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Escrow {self.id[:8]}... - ${self.amount} {self.status.value}>"


class Credit(Base):
    """Internal credit system for platform currency"""
    __tablename__ = "credits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Credit details
    amount = Column(Numeric(10, 2), nullable=False)  # Can be negative for debits
    balance_after = Column(Numeric(10, 2), nullable=False)  # Running balance

    # Transaction type
    transaction_type = Column(String, nullable=False, index=True)  # purchase, refund, reward, usage, payout
    description = Column(Text, nullable=True)

    # References
    payment_id = Column(String, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For promotional credits

    # Index for balance queries
    __table_args__ = (
        Index('ix_credits_user_balance', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Credit {self.transaction_type} - ${self.amount}>"


class Invoice(Base):
    """Billing and invoicing"""
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Invoice details
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)

    # Status
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)

    # Line items
    line_items = Column(JSON, default=list)  # [{description, quantity, unit_price, total}]

    # Dates
    issue_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_date = Column(DateTime(timezone=True), nullable=True)

    # Billing details
    billing_address = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - ${self.total_amount}>"


class Subscription(Base):
    """User subscription management"""
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Subscription details
    tier = Column(String, nullable=False)  # free, pro, enterprise
    status = Column(String, default="active", nullable=False)  # active, cancelled, expired, past_due

    # Pricing
    price_per_month = Column(Numeric(10, 2), default=0)
    currency = Column(String, default="USD")

    # Provider integration
    provider = Column(SQLEnum(PaymentProvider), nullable=True)
    provider_subscription_id = Column(String, nullable=True, index=True)
    provider_customer_id = Column(String, nullable=True)

    # Billing cycle
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Subscription {self.tier} - {self.status}>"


class PaymentMethod(Base):
    """Stored payment methods"""
    __tablename__ = "payment_methods"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Payment method details
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    provider_method_id = Column(String, nullable=True)  # Stripe payment method ID, etc.

    # Card details (last 4 digits, brand, expiry)
    card_last4 = Column(String, nullable=True)
    card_brand = Column(String, nullable=True)  # visa, mastercard, amex
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)

    # Billing details
    billing_email = Column(String, nullable=True)
    billing_address = Column(JSON, nullable=True)

    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PaymentMethod {self.card_brand} ****{self.card_last4}>"


class Payout(Base):
    """Agent payouts and earnings"""
    __tablename__ = "payouts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Payout details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(SQLEnum(PayoutStatus), default=PayoutStatus.PENDING, nullable=False, index=True)

    # Provider integration
    provider = Column(SQLEnum(PaymentProvider), nullable=True)
    provider_payout_id = Column(String, nullable=True)

    # Earnings breakdown
    contracts_included = Column(JSON, default=list)  # List of contract IDs
    earnings_period_start = Column(DateTime(timezone=True), nullable=True)
    earnings_period_end = Column(DateTime(timezone=True), nullable=True)

    # Recipient details (for agent owner)
    recipient_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recipient_email = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Payout {self.id[:8]}... - ${self.amount} {self.status.value}>"


class Dispute(Base):
    """Payment disputes and resolutions"""
    __tablename__ = "disputes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    escrow_id = Column(String, ForeignKey("escrows.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Dispute details
    raised_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, default=list)  # URLs to evidence files

    # Status
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False, index=True)

    # Resolution
    resolution = Column(Text, nullable=True)
    resolved_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin/moderator
    resolution_action = Column(String, nullable=True)  # refund, release, partial_refund
    resolution_amount = Column(Numeric(10, 2), nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    escrow = relationship("Escrow", back_populates="disputes")

    def __repr__(self):
        return f"<Dispute {self.id[:8]}... - {self.reason}>"


class PricingRule(Base):
    """Dynamic pricing rules"""
    __tablename__ = "pricing_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Rule details
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Rule type
    rule_type = Column(String, nullable=False)  # surge, discount, reputation_based, bulk

    # Conditions (JSON expression)
    conditions = Column(JSON, nullable=False)  # {demand_threshold: 0.8, time_of_day: "peak"}

    # Pricing adjustments
    multiplier = Column(Float, default=1.0)  # Price multiplier
    fixed_adjustment = Column(Numeric(10, 2), default=0)  # Fixed price adjustment

    # Applicability
    applies_to_agents = Column(JSON, default=list)  # Agent IDs or "all"
    applies_to_capabilities = Column(JSON, default=list)  # Capability types

    # Status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority rules apply first

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PricingRule {self.name} - {self.rule_type}>"


class UsageRecord(Base):
    """Track usage for billing"""
    __tablename__ = "usage_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Usage details
    resource_type = Column(String, nullable=False, index=True)  # api_call, agent_execution, storage
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 4), nullable=True)
    total_cost = Column(Numeric(10, 2), nullable=True)

    # References
    contract_id = Column(String, ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # Billing period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for billing queries
    __table_args__ = (
        Index('ix_usage_user_period', 'user_id', 'period_start', 'period_end'),
    )

    def __repr__(self):
        return f"<UsageRecord {self.resource_type} - {self.quantity} units>"
