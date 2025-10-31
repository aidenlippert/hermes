"""
Analytics & Observability API

RESTful API endpoints for analytics, monitoring, metrics, and observability.

Sprint 5: Analytics & Observability
"""

from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.services.analytics_engine import AnalyticsEngine
from backend.services.monitoring_service import MonitoringService
from backend.services.metrics_service import MetricsService
from backend.database.models_analytics import AlertSeverity, MetricType

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Observability"])


class UserAnalyticsResponse(BaseModel):
    user_id: str
    period_type: str
    sessions: int
    page_views: int
    contracts_created: int
    credits_spent: float
    agents_used: int
    orchestrations_run: int


class AgentAnalyticsResponse(BaseModel):
    agent_id: str
    period_type: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    contracts_won: int
    revenue: float
    avg_validation_score: float
    reputation_score: float


class PlatformMetricsResponse(BaseModel):
    period_type: str
    total_users: int
    active_users: int
    new_users: int
    total_agents: int
    total_contracts: int
    total_revenue: float
    platform_fees: float


class MetricRequest(BaseModel):
    metric_name: str
    value: float
    metric_type: str = "gauge"
    unit: Optional[str] = None
    tags: Optional[dict] = None


class AlertRuleRequest(BaseModel):
    name: str
    metric_name: str
    condition_operator: str = Field(..., description="gt, lt, eq, gte, lte")
    threshold: float
    severity: str
    description: Optional[str] = None
    duration_seconds: int = 60
    notification_channels: Optional[List[str]] = None


@router.get("/dashboard")
async def get_analytics_dashboard(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive analytics dashboard data.

    Args:
        days: Number of days for trends

    Returns:
        Dashboard data with platform metrics and trends
    """
    engine = AnalyticsEngine(db)
    metrics_service = MetricsService(db)
    monitoring_service = MonitoringService(db)

    # Get latest platform metrics
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=1)

    platform_metrics = await engine.track_platform_metrics(
        period_start=period_start,
        period_end=period_end,
        period_type="day"
    )

    # Get platform trends
    trends = await engine.get_platform_trends(days=days)

    # Get performance summary
    performance = await metrics_service.get_performance_summary()

    # Get monitoring summary
    monitoring = await monitoring_service.get_monitoring_dashboard()

    return {
        "current_metrics": {
            "users": {
                "total": platform_metrics.total_users,
                "active": platform_metrics.active_users,
                "new": platform_metrics.new_users
            },
            "agents": {
                "total": platform_metrics.total_agents,
                "active": platform_metrics.active_agents,
                "new": platform_metrics.new_agents
            },
            "contracts": {
                "total": platform_metrics.total_contracts,
                "active": platform_metrics.active_contracts,
                "completed": platform_metrics.completed_contracts
            },
            "financial": {
                "revenue": platform_metrics.total_revenue,
                "platform_fees": platform_metrics.platform_fees,
                "credits_purchased": platform_metrics.credits_purchased
            }
        },
        "trends": trends,
        "performance": performance,
        "monitoring": monitoring,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/user/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: str,
    period_type: str = Query("day", description="hour, day, week, month"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user analytics for current period.

    Args:
        user_id: User ID
        period_type: Period type (hour, day, week, month)

    Returns:
        User analytics
    """
    engine = AnalyticsEngine(db)

    # Calculate period
    if period_type == "hour":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(hours=1)
    elif period_type == "day":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=1)
    elif period_type == "week":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(weeks=1)
    elif period_type == "month":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid period_type")

    try:
        analytics = await engine.track_user_analytics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type
        )

        return UserAnalyticsResponse(
            user_id=analytics.user_id,
            period_type=analytics.period_type,
            sessions=analytics.sessions,
            page_views=analytics.page_views,
            contracts_created=analytics.contracts_created,
            credits_spent=analytics.credits_spent,
            agents_used=analytics.agents_used,
            orchestrations_run=analytics.orchestrations_run
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/user/{user_id}/trends")
async def get_user_trends(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user activity trends over time.

    Args:
        user_id: User ID
        days: Number of days to look back

    Returns:
        List of daily analytics data points
    """
    engine = AnalyticsEngine(db)

    trends = await engine.get_user_trends(user_id, days=days)

    return {
        "user_id": user_id,
        "period_days": days,
        "data_points": len(trends),
        "trends": trends
    }


@router.get("/agent/{agent_id}", response_model=AgentAnalyticsResponse)
async def get_agent_analytics(
    agent_id: str,
    period_type: str = Query("day", description="hour, day, week, month"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent analytics for current period.

    Args:
        agent_id: Agent ID
        period_type: Period type (hour, day, week, month)

    Returns:
        Agent analytics
    """
    engine = AnalyticsEngine(db)

    # Calculate period
    if period_type == "hour":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(hours=1)
    elif period_type == "day":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=1)
    elif period_type == "week":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(weeks=1)
    elif period_type == "month":
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid period_type")

    try:
        analytics = await engine.track_agent_analytics(
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type
        )

        return AgentAnalyticsResponse(
            agent_id=analytics.agent_id,
            period_type=analytics.period_type,
            total_calls=analytics.total_calls,
            successful_calls=analytics.successful_calls,
            failed_calls=analytics.failed_calls,
            contracts_won=analytics.contracts_won,
            revenue=analytics.revenue,
            avg_validation_score=analytics.avg_validation_score,
            reputation_score=analytics.reputation_score
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/agent/{agent_id}/trends")
async def get_agent_trends(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent performance trends over time.

    Args:
        agent_id: Agent ID
        days: Number of days to look back

    Returns:
        List of daily analytics data points
    """
    engine = AnalyticsEngine(db)

    trends = await engine.get_agent_trends(agent_id, days=days)

    return {
        "agent_id": agent_id,
        "period_days": days,
        "data_points": len(trends),
        "trends": trends
    }


@router.get("/platform/trends")
async def get_platform_trends(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get platform-wide trends over time.

    Args:
        days: Number of days to look back

    Returns:
        List of daily platform metrics
    """
    engine = AnalyticsEngine(db)

    trends = await engine.get_platform_trends(days=days)

    return {
        "period_days": days,
        "data_points": len(trends),
        "trends": trends
    }


@router.post("/metrics/record")
async def record_metric(
    request: MetricRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a custom metric.

    Args:
        request: Metric request with name, value, type, and tags

    Returns:
        Success confirmation
    """
    metrics = MetricsService(db)

    try:
        metric_type = MetricType(request.metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric_type: {request.metric_type}")

    event = await metrics.record_metric(
        metric_name=request.metric_name,
        value=request.value,
        metric_type=metric_type,
        unit=request.unit,
        tags=request.tags
    )

    return {
        "success": True,
        "metric_id": event.id,
        "timestamp": event.timestamp.isoformat()
    }


@router.get("/metrics/{metric_name}/statistics")
async def get_metric_statistics(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get metric statistics.

    Args:
        metric_name: Metric name
        hours: Hours to look back

    Returns:
        Comprehensive statistics
    """
    metrics = MetricsService(db)

    stats = await metrics.get_metric_statistics(metric_name, hours=hours)

    return stats


@router.get("/metrics/{metric_name}/time-series")
async def get_metric_time_series(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168),
    bucket_minutes: int = Query(60, ge=1, le=1440),
    aggregation: str = Query("avg", description="avg, sum, min, max, count"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get metric time series with bucketing.

    Args:
        metric_name: Metric name
        hours: Hours to look back
        bucket_minutes: Bucket size in minutes
        aggregation: Aggregation function

    Returns:
        Time-bucketed data points
    """
    metrics = MetricsService(db)

    time_series = await metrics.get_metric_time_series(
        metric_name=metric_name,
        hours=hours,
        bucket_minutes=bucket_minutes,
        aggregation=aggregation
    )

    return {
        "metric_name": metric_name,
        "aggregation": aggregation,
        "bucket_minutes": bucket_minutes,
        "data_points": len(time_series),
        "time_series": time_series
    }


@router.get("/performance")
async def get_performance_summary(db: AsyncSession = Depends(get_db)):
    """
    Get performance summary across all metrics.

    Returns:
        Performance statistics for API, contracts, orchestration
    """
    metrics = MetricsService(db)

    summary = await metrics.get_performance_summary()

    return summary


@router.get("/monitoring/health")
async def get_health_summary(db: AsyncSession = Depends(get_db)):
    """
    Get overall health summary for all services.

    Returns:
        Health status for all monitored services
    """
    monitoring = MonitoringService(db)

    summary = await monitoring.get_health_summary()

    return summary


@router.get("/monitoring/health/{service_name}")
async def get_service_health(
    service_name: str,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get health checks for a specific service.

    Args:
        service_name: Service name
        hours: Hours to look back

    Returns:
        List of health checks
    """
    monitoring = MonitoringService(db)

    checks = await monitoring.get_service_health(service_name, hours=hours)

    return {
        "service_name": service_name,
        "period_hours": hours,
        "total_checks": len(checks),
        "checks": [
            {
                "status": check.status.value,
                "response_time_ms": check.response_time_ms,
                "error": check.error,
                "checked_at": check.checked_at.isoformat()
            }
            for check in checks
        ]
    }


@router.get("/monitoring/sla/{service_name}")
async def get_sla_metrics(
    service_name: str,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Get SLA metrics for a service.

    Args:
        service_name: Service name
        days: Number of days to calculate

    Returns:
        SLA metrics including uptime percentage
    """
    monitoring = MonitoringService(db)

    metrics = await monitoring.calculate_sla_metrics(service_name, days=days)

    return metrics


@router.post("/alerts/rules")
async def create_alert_rule(
    request: AlertRuleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create alert rule.

    Args:
        request: Alert rule configuration

    Returns:
        Created alert rule
    """
    monitoring = MonitoringService(db)

    try:
        severity = AlertSeverity(request.severity)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")

    rule = await monitoring.create_alert_rule(
        name=request.name,
        metric_name=request.metric_name,
        condition_operator=request.condition_operator,
        threshold=request.threshold,
        severity=severity,
        description=request.description,
        duration_seconds=request.duration_seconds,
        notification_channels=request.notification_channels
    )

    return {
        "success": True,
        "rule_id": rule.id,
        "name": rule.name
    }


@router.get("/alerts/incidents")
async def get_open_incidents(
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get open alert incidents.

    Args:
        severity: Optional severity filter

    Returns:
        List of open incidents
    """
    monitoring = MonitoringService(db)

    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    incidents = await monitoring.get_open_incidents(severity=severity_enum)

    return {
        "total_incidents": len(incidents),
        "incidents": [
            {
                "id": incident.id,
                "title": incident.title,
                "severity": incident.severity.value,
                "status": incident.status.value,
                "metric_value": incident.metric_value,
                "threshold": incident.threshold,
                "triggered_at": incident.triggered_at.isoformat()
            }
            for incident in incidents
        ]
    }


@router.post("/alerts/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(
    incident_id: str,
    acknowledged_by: str = Query(..., description="User acknowledging"),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge alert incident.

    Args:
        incident_id: Incident ID
        acknowledged_by: User acknowledging

    Returns:
        Updated incident
    """
    monitoring = MonitoringService(db)

    try:
        incident = await monitoring.acknowledge_incident(incident_id, acknowledged_by)

        return {
            "success": True,
            "incident_id": incident.id,
            "acknowledged_at": incident.acknowledged_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    resolved_by: str = Query(..., description="User resolving"),
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve alert incident.

    Args:
        incident_id: Incident ID
        resolved_by: User resolving
        resolution_notes: Optional resolution notes

    Returns:
        Updated incident
    """
    monitoring = MonitoringService(db)

    try:
        incident = await monitoring.resolve_incident(incident_id, resolved_by, resolution_notes)

        return {
            "success": True,
            "incident_id": incident.id,
            "resolved_at": incident.resolved_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batch-track")
async def batch_track_analytics(
    period_type: str = Query("day", description="hour, day, week, month"),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch track analytics for all users, agents, and platform.

    This should be run as a periodic background task.

    Args:
        period_type: Period type to track

    Returns:
        Summary of tracking results
    """
    engine = AnalyticsEngine(db)

    # Calculate period based on type
    period_end = datetime.utcnow()

    if period_type == "hour":
        period_start = period_end - timedelta(hours=1)
    elif period_type == "day":
        period_start = period_end - timedelta(days=1)
    elif period_type == "week":
        period_start = period_end - timedelta(weeks=1)
    elif period_type == "month":
        period_start = period_end - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid period_type")

    summary = await engine.batch_track_analytics(
        period_start=period_start,
        period_end=period_end,
        period_type=period_type
    )

    return {
        "success": True,
        "summary": summary
    }
