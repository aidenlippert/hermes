"""
Security and Trust Models

Advanced security, reputation, fraud detection, and compliance models for Sprint 4.

Tables:
- reputation_scores: Multi-dimensional agent reputation
- fraud_alerts: Fraud detection alerts
- security_events: Security event logging
- compliance_records: GDPR/SOC2 compliance tracking
- data_access_logs: Data access audit trail
- trust_metrics: Historical trust metrics
- verification_records: Agent verification history
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from .connection import Base


class FraudType(str, Enum):
    """Types of fraud detected"""
    SYBIL_ATTACK = "sybil_attack"  # Multiple fake identities
    COLLUSION = "collusion"  # Agents working together to game system
    DELIVERY_FRAUD = "delivery_fraud"  # Fake/poor quality deliveries
    RATING_MANIPULATION = "rating_manipulation"  # Fake reviews
    PRICE_MANIPULATION = "price_manipulation"  # Artificial price inflation
    IDENTITY_THEFT = "identity_theft"  # Stolen credentials


class FraudSeverity(str, Enum):
    """Fraud alert severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(str, Enum):
    """Security event types"""
    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class ComplianceFramework(str, Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


class DataAccessPurpose(str, Enum):
    """Purpose of data access"""
    USER_REQUEST = "user_request"
    ANALYTICS = "analytics"
    SUPPORT = "support"
    COMPLIANCE = "compliance"
    FRAUD_INVESTIGATION = "fraud_investigation"
    SYSTEM_MAINTENANCE = "system_maintenance"


class ReputationScore(Base):
    """Multi-dimensional agent reputation scores"""
    __tablename__ = "reputation_scores"

    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)

    # Core reputation dimensions (0.0 - 1.0)
    quality_score = Column(Float, default=0.5, nullable=False)  # Delivery quality
    reliability_score = Column(Float, default=0.5, nullable=False)  # Uptime and consistency
    speed_score = Column(Float, default=0.5, nullable=False)  # Response time
    honesty_score = Column(Float, default=0.5, nullable=False)  # Accuracy of estimates
    collaboration_score = Column(Float, default=0.5, nullable=False)  # Works well with others

    # Composite scores
    overall_reputation = Column(Float, default=0.5, nullable=False, index=True)
    trust_grade = Column(String, default="C", nullable=False)  # A+, A, B, C, D, F

    # Statistics
    total_contracts = Column(Integer, default=0)
    successful_contracts = Column(Integer, default=0)
    failed_contracts = Column(Integer, default=0)
    disputed_contracts = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_earnings = Column(Float, default=0.0)

    # Fraud indicators
    fraud_score = Column(Float, default=0.0)  # 0.0 = clean, 1.0 = highly suspicious
    is_flagged = Column(Boolean, default=False, index=True)
    flag_reason = Column(Text, nullable=True)

    # Metadata
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    calculation_count = Column(Integer, default=0)

    # Relationships
    metrics = relationship("TrustMetric", back_populates="reputation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ReputationScore {self.agent_id} - {self.trust_grade} ({self.overall_reputation:.2f})>"


class TrustMetric(Base):
    """Historical trust metrics for trend analysis"""
    __tablename__ = "trust_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Snapshot of scores at this time
    quality_score = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    speed_score = Column(Float, nullable=False)
    honesty_score = Column(Float, nullable=False)
    collaboration_score = Column(Float, nullable=False)
    overall_reputation = Column(Float, nullable=False)

    # Context
    contracts_at_time = Column(Integer, default=0)
    successful_at_time = Column(Integer, default=0)

    # Metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    reputation = relationship("ReputationScore", back_populates="metrics")

    # Index for time-series queries
    __table_args__ = (
        Index('ix_trust_metrics_time_series', 'agent_id', 'recorded_at'),
    )

    def __repr__(self):
        return f"<TrustMetric {self.agent_id} - {self.overall_reputation:.2f}>"


class FraudAlert(Base):
    """Fraud detection alerts"""
    __tablename__ = "fraud_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Target
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # Alert details
    fraud_type = Column(SQLEnum(FraudType), nullable=False, index=True)
    severity = Column(SQLEnum(FraudSeverity), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # ML model confidence (0.0-1.0)

    # Description
    description = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)  # Evidence data

    # Related entities
    related_agents = Column(JSON, default=list)  # For collusion detection
    related_contracts = Column(JSON, default=list)

    # Status
    is_reviewed = Column(Boolean, default=False, index=True)
    reviewed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(Text, nullable=True)
    action_taken = Column(String, nullable=True)  # ban, warn, monitor, dismiss

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FraudAlert {self.fraud_type.value} - {self.severity.value}>"


class SecurityEvent(Base):
    """Security event logging for audit trail"""
    __tablename__ = "security_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Event details
    event_type = Column(SQLEnum(SecurityEventType), nullable=False, index=True)
    severity = Column(String, default="info", nullable=False)  # info, warning, error, critical

    # Actor
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Details
    description = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)

    # Outcome
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Index for security monitoring
    __table_args__ = (
        Index('ix_security_events_monitoring', 'event_type', 'severity', 'created_at'),
        Index('ix_security_events_user', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<SecurityEvent {self.event_type.value} - {self.severity}>"


class ComplianceRecord(Base):
    """GDPR/SOC2 compliance tracking"""
    __tablename__ = "compliance_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Framework
    framework = Column(SQLEnum(ComplianceFramework), nullable=False, index=True)
    control_id = Column(String, nullable=False)  # e.g., "GDPR-7.3", "SOC2-CC6.1"
    control_name = Column(String, nullable=False)

    # Subject
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # Status
    is_compliant = Column(Boolean, default=True, nullable=False)
    compliance_date = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Details
    description = Column(Text, nullable=True)
    evidence = Column(JSON, default=dict)
    notes = Column(Text, nullable=True)

    # Verification
    verified_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ComplianceRecord {self.framework.value} - {self.control_id}>"


class DataAccessLog(Base):
    """Audit trail for data access (GDPR requirement)"""
    __tablename__ = "data_access_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Subject
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Accessor
    accessed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    access_method = Column(String, nullable=False)  # api, admin_panel, support, system

    # Access details
    purpose = Column(SQLEnum(DataAccessPurpose), nullable=False)
    data_types = Column(JSON, default=list)  # ["profile", "payments", "contracts"]
    action = Column(String, nullable=False)  # read, update, delete, export

    # Legal basis (GDPR)
    legal_basis = Column(String, nullable=True)  # consent, contract, legitimate_interest, etc.

    # Context
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Metadata
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Index for GDPR queries
    __table_args__ = (
        Index('ix_data_access_subject_time', 'user_id', 'accessed_at'),
    )

    def __repr__(self):
        return f"<DataAccessLog {self.action} - {self.purpose.value}>"


class VerificationRecord(Base):
    """Agent verification history"""
    __tablename__ = "verification_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Verification type
    verification_type = Column(String, nullable=False)  # identity, endpoint, capability, security
    status = Column(String, nullable=False)  # pending, approved, rejected, expired

    # Verification details
    verified_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verification_method = Column(String, nullable=True)  # manual, automated, third_party
    verification_data = Column(JSON, default=dict)

    # Results
    is_verified = Column(Boolean, default=False)
    verification_score = Column(Float, nullable=True)  # 0.0-1.0
    notes = Column(Text, nullable=True)

    # Validity
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<VerificationRecord {self.verification_type} - {self.status}>"


class AnomalyDetection(Base):
    """ML-powered anomaly detection for agent behavior"""
    __tablename__ = "anomaly_detections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Anomaly details
    anomaly_type = Column(String, nullable=False)  # response_time, quality, pricing, availability
    severity = Column(Float, nullable=False)  # 0.0-1.0
    description = Column(Text, nullable=False)

    # Baseline vs observed
    baseline_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    deviation = Column(Float, nullable=True)  # How many standard deviations

    # ML model info
    model_version = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    # Status
    is_investigated = Column(Boolean, default=False)
    investigation_notes = Column(Text, nullable=True)

    # Metadata
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AnomalyDetection {self.anomaly_type} - severity {self.severity:.2f}>"
