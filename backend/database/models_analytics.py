"""
Analytics and Observability Models

Time-series analytics, metrics, monitoring, and observability for Sprint 5.

Tables:
- user_analytics: User behavior and engagement metrics
- agent_analytics: Agent performance and availability metrics
- platform_metrics: System-wide platform metrics
- metric_events: Time-series event tracking
- health_checks: Service health monitoring
- alert_rules: Alerting configuration
- alert_incidents: Alert incident tracking
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, Index, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from .connection import Base


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"  # Incremental count
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution
    TIMER = "timer"  # Duration measurement


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class UserAnalytics(Base):
    """User behavior and engagement analytics"""
    __tablename__ = "user_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String, nullable=False)  # hour, day, week, month

    # Activity metrics
    sessions = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    actions = Column(Integer, default=0)
    active_time_seconds = Column(Integer, default=0)

    # Contract metrics
    contracts_created = Column(Integer, default=0)
    contracts_completed = Column(Integer, default=0)
    contracts_cancelled = Column(Integer, default=0)

    # Financial metrics
    credits_purchased = Column(Float, default=0.0)
    credits_spent = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)

    # Engagement metrics
    agents_used = Column(Integer, default=0)
    unique_agents = Column(JSON, default=list)
    orchestrations_run = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for time-series queries
    __table_args__ = (
        Index('ix_user_analytics_time_series', 'user_id', 'period_start'),
        Index('ix_user_analytics_period', 'period_type', 'period_start'),
    )

    def __repr__(self):
        return f"<UserAnalytics {self.user_id} - {self.period_type}>"


class AgentAnalytics(Base):
    """Agent performance and availability analytics"""
    __tablename__ = "agent_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String, nullable=False)  # hour, day, week, month

    # Performance metrics
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0.0)
    p50_response_time_ms = Column(Float, default=0.0)
    p95_response_time_ms = Column(Float, default=0.0)
    p99_response_time_ms = Column(Float, default=0.0)

    # Availability metrics
    uptime_seconds = Column(Integer, default=0)
    downtime_seconds = Column(Integer, default=0)
    availability_percent = Column(Float, default=100.0)

    # Contract metrics
    bids_placed = Column(Integer, default=0)
    contracts_won = Column(Integer, default=0)
    contracts_completed = Column(Integer, default=0)
    contracts_failed = Column(Integer, default=0)

    # Financial metrics
    revenue = Column(Float, default=0.0)
    avg_bid_price = Column(Float, default=0.0)

    # Quality metrics
    avg_validation_score = Column(Float, default=0.0)
    reputation_score = Column(Float, default=0.5)

    # Usage metrics
    unique_users = Column(Integer, default=0)
    unique_user_list = Column(JSON, default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for time-series queries
    __table_args__ = (
        Index('ix_agent_analytics_time_series', 'agent_id', 'period_start'),
        Index('ix_agent_analytics_period', 'period_type', 'period_start'),
    )

    def __repr__(self):
        return f"<AgentAnalytics {self.agent_id} - {self.period_type}>"


class PlatformMetrics(Base):
    """System-wide platform metrics"""
    __tablename__ = "platform_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String, nullable=False)  # hour, day, week, month

    # User metrics
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    churned_users = Column(Integer, default=0)

    # Agent metrics
    total_agents = Column(Integer, default=0)
    active_agents = Column(Integer, default=0)
    new_agents = Column(Integer, default=0)

    # Contract metrics
    total_contracts = Column(Integer, default=0)
    active_contracts = Column(Integer, default=0)
    completed_contracts = Column(Integer, default=0)
    failed_contracts = Column(Integer, default=0)

    # Financial metrics
    total_revenue = Column(Float, default=0.0)
    platform_fees = Column(Float, default=0.0)
    credits_purchased = Column(Float, default=0.0)
    credits_spent = Column(Float, default=0.0)

    # Performance metrics
    avg_response_time_ms = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    throughput_per_second = Column(Float, default=0.0)

    # System metrics
    api_calls = Column(BigInteger, default=0)
    orchestrations = Column(Integer, default=0)
    fraud_alerts = Column(Integer, default=0)
    security_events = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for time-series queries
    __table_args__ = (
        Index('ix_platform_metrics_time_series', 'period_type', 'period_start'),
    )

    def __repr__(self):
        return f"<PlatformMetrics {self.period_type} - {self.period_start}>"


class MetricEvent(Base):
    """Time-series event tracking for custom metrics"""
    __tablename__ = "metric_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Metric identification
    metric_name = Column(String, nullable=False, index=True)
    metric_type = Column(SQLEnum(MetricType), nullable=False)

    # Metric value
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)  # ms, bytes, count, percent

    # Dimensions (for filtering/grouping)
    tags = Column(JSON, default=dict)  # {"user_id": "...", "agent_id": "..."}

    # Context
    source = Column(String, nullable=True)  # api, orchestration, payment, etc.
    description = Column(Text, nullable=True)

    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Index for time-series queries
    __table_args__ = (
        Index('ix_metric_events_name_time', 'metric_name', 'timestamp'),
        Index('ix_metric_events_type_time', 'metric_type', 'timestamp'),
    )

    def __repr__(self):
        return f"<MetricEvent {self.metric_name} = {self.value}>"


class HealthCheck(Base):
    """Service health monitoring"""
    __tablename__ = "health_checks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Service identification
    service_name = Column(String, nullable=False, index=True)
    service_type = Column(String, nullable=False)  # api, database, cache, external
    endpoint = Column(String, nullable=True)

    # Health status
    status = Column(SQLEnum(HealthStatus), nullable=False, index=True)
    response_time_ms = Column(Float, nullable=True)

    # Details
    message = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)

    # Error tracking
    error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)

    # Metadata
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Index for monitoring queries
    __table_args__ = (
        Index('ix_health_checks_service_time', 'service_name', 'checked_at'),
        Index('ix_health_checks_status_time', 'status', 'checked_at'),
    )

    def __repr__(self):
        return f"<HealthCheck {self.service_name} - {self.status.value}>"


class AlertRule(Base):
    """Alert rule configuration"""
    __tablename__ = "alert_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Rule identification
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)

    # Condition
    metric_name = Column(String, nullable=False)
    condition_operator = Column(String, nullable=False)  # gt, lt, eq, gte, lte
    threshold = Column(Float, nullable=False)
    duration_seconds = Column(Integer, default=60)  # Must exceed threshold for this long

    # Actions
    notification_channels = Column(JSON, default=list)  # ["email", "slack", "webhook"]
    notification_config = Column(JSON, default=dict)

    # Status
    is_enabled = Column(Boolean, default=True, index=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)

    # Metadata
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AlertRule {self.name} - {self.severity.value}>"


class AlertIncident(Base):
    """Alert incident tracking"""
    __tablename__ = "alert_incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_rule_id = Column(String, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.OPEN, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)

    # Incident details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)

    # Context
    tags = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)

    # Resolution
    acknowledged_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Index for monitoring queries
    __table_args__ = (
        Index('ix_alert_incidents_status_time', 'status', 'triggered_at'),
        Index('ix_alert_incidents_severity_time', 'severity', 'triggered_at'),
    )

    def __repr__(self):
        return f"<AlertIncident {self.title} - {self.status.value}>"
