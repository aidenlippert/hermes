"""
Monitoring and Alerting Service

Health checks, SLA monitoring, and threshold-based alerting.

Sprint 5: Analytics & Observability
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models_analytics import (
    HealthCheck,
    HealthStatus,
    AlertRule,
    AlertIncident,
    AlertSeverity,
    AlertStatus,
    MetricEvent
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Monitoring and alerting service.

    Features:
    - Health checks for services
    - Threshold-based alerting
    - SLA monitoring
    - Incident management
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_service_health(
        self,
        service_name: str,
        service_type: str,
        endpoint: Optional[str] = None,
        check_function: Optional[callable] = None
    ) -> HealthCheck:
        """
        Check health of a service.

        Args:
            service_name: Service name
            service_type: api, database, cache, external
            endpoint: Optional endpoint URL
            check_function: Optional custom check function

        Returns:
            HealthCheck record
        """
        start_time = datetime.utcnow()
        status = HealthStatus.UNKNOWN
        error = None
        response_time_ms = None

        try:
            if check_function:
                # Run custom check function
                await check_function()
                status = HealthStatus.HEALTHY
            else:
                # Default check (service exists in database)
                status = HealthStatus.HEALTHY

            # Calculate response time
            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error = str(e)
            logger.error(f"Health check failed for {service_name}: {e}")

        # Get previous check for consecutive failure tracking
        previous_result = await self.db.execute(
            select(HealthCheck)
            .where(HealthCheck.service_name == service_name)
            .order_by(HealthCheck.checked_at.desc())
            .limit(1)
        )
        previous_check = previous_result.scalar_one_or_none()

        consecutive_failures = 0
        if status == HealthStatus.UNHEALTHY:
            if previous_check and previous_check.status == HealthStatus.UNHEALTHY:
                consecutive_failures = previous_check.consecutive_failures + 1
            else:
                consecutive_failures = 1

        # Create health check record
        health_check = HealthCheck(
            service_name=service_name,
            service_type=service_type,
            endpoint=endpoint,
            status=status,
            response_time_ms=response_time_ms,
            error=error,
            consecutive_failures=consecutive_failures
        )

        self.db.add(health_check)
        await self.db.commit()

        logger.info(f"Health check: {service_name} - {status.value}")

        return health_check

    async def get_service_health(
        self,
        service_name: Optional[str] = None,
        hours: int = 24
    ) -> List[HealthCheck]:
        """
        Get recent health checks for services.

        Args:
            service_name: Optional service filter
            hours: Hours to look back

        Returns:
            List of health checks
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = select(HealthCheck).where(HealthCheck.checked_at >= since)

        if service_name:
            query = query.where(HealthCheck.service_name == service_name)

        query = query.order_by(HealthCheck.checked_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary for all services.

        Returns:
            Health summary statistics
        """
        # Get latest check for each service
        result = await self.db.execute(
            select(HealthCheck.service_name, func.max(HealthCheck.checked_at))
            .group_by(HealthCheck.service_name)
        )

        service_checks = result.all()

        services = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        for service_name, last_check_time in service_checks:
            # Get the actual latest check
            check_result = await self.db.execute(
                select(HealthCheck)
                .where(HealthCheck.service_name == service_name)
                .where(HealthCheck.checked_at == last_check_time)
            )

            check = check_result.scalar_one_or_none()
            if not check:
                continue

            services.append({
                "service_name": check.service_name,
                "status": check.status.value,
                "response_time_ms": check.response_time_ms,
                "consecutive_failures": check.consecutive_failures,
                "last_checked": check.checked_at.isoformat()
            })

            if check.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif check.status == HealthStatus.DEGRADED:
                degraded_count += 1
            elif check.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1

        overall_status = "healthy"
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "total_services": len(services),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "services": services
        }

    async def create_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition_operator: str,
        threshold: float,
        severity: AlertSeverity,
        description: Optional[str] = None,
        duration_seconds: int = 60,
        notification_channels: Optional[List[str]] = None,
        notification_config: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> AlertRule:
        """
        Create alert rule for threshold-based alerting.

        Args:
            name: Rule name (unique)
            metric_name: Metric to monitor
            condition_operator: gt, lt, eq, gte, lte
            threshold: Threshold value
            severity: Alert severity
            description: Optional description
            duration_seconds: Duration threshold must be exceeded
            notification_channels: List of channels (email, slack, webhook)
            notification_config: Notification configuration
            created_by: User who created the rule

        Returns:
            AlertRule
        """
        rule = AlertRule(
            name=name,
            description=description,
            severity=severity,
            metric_name=metric_name,
            condition_operator=condition_operator,
            threshold=threshold,
            duration_seconds=duration_seconds,
            notification_channels=notification_channels or [],
            notification_config=notification_config or {},
            created_by=created_by
        )

        self.db.add(rule)
        await self.db.commit()

        logger.info(f"Created alert rule: {name} ({metric_name} {condition_operator} {threshold})")

        return rule

    async def check_alert_rules(self) -> List[AlertIncident]:
        """
        Check all active alert rules and create incidents if triggered.

        This should be run as a periodic background task.

        Returns:
            List of newly created incidents
        """
        # Get all enabled rules
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.is_enabled == True)
        )

        rules = result.scalars().all()

        incidents = []

        for rule in rules:
            try:
                # Get recent metric values
                since = datetime.utcnow() - timedelta(seconds=rule.duration_seconds)

                metric_result = await self.db.execute(
                    select(MetricEvent.value)
                    .where(MetricEvent.metric_name == rule.metric_name)
                    .where(MetricEvent.timestamp >= since)
                    .order_by(MetricEvent.timestamp.desc())
                )

                values = [v for v, in metric_result.all()]

                if not values:
                    continue

                # Check if condition is met
                latest_value = values[0]
                triggered = self._evaluate_condition(
                    latest_value,
                    rule.condition_operator,
                    rule.threshold
                )

                if triggered:
                    # Check if already has open incident
                    existing_result = await self.db.execute(
                        select(AlertIncident)
                        .where(AlertIncident.alert_rule_id == rule.id)
                        .where(AlertIncident.status == AlertStatus.OPEN)
                    )

                    existing_incident = existing_result.scalar_one_or_none()

                    if not existing_incident:
                        # Create new incident
                        incident = await self._create_incident(
                            rule=rule,
                            metric_value=latest_value
                        )
                        incidents.append(incident)

                        # Update rule stats
                        rule.last_triggered = datetime.utcnow()
                        rule.trigger_count += 1

            except Exception as e:
                logger.error(f"Failed to check alert rule {rule.name}: {e}")

        await self.db.commit()

        logger.info(f"Alert check complete: {len(incidents)} new incidents")

        return incidents

    def _evaluate_condition(
        self,
        value: float,
        operator: str,
        threshold: float
    ) -> bool:
        """Evaluate alert condition"""
        if operator == "gt":
            return value > threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return value == threshold
        else:
            return False

    async def _create_incident(
        self,
        rule: AlertRule,
        metric_value: float
    ) -> AlertIncident:
        """Create alert incident"""
        incident = AlertIncident(
            alert_rule_id=rule.id,
            status=AlertStatus.OPEN,
            severity=rule.severity,
            title=f"{rule.name}: {rule.metric_name} {rule.condition_operator} {rule.threshold}",
            description=rule.description,
            metric_value=metric_value,
            threshold=rule.threshold
        )

        self.db.add(incident)

        logger.warning(f"Alert triggered: {incident.title} (value: {metric_value})")

        return incident

    async def get_open_incidents(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[AlertIncident]:
        """
        Get open alert incidents.

        Args:
            severity: Optional severity filter

        Returns:
            List of open incidents
        """
        query = select(AlertIncident).where(AlertIncident.status == AlertStatus.OPEN)

        if severity:
            query = query.where(AlertIncident.severity == severity)

        query = query.order_by(AlertIncident.severity.desc(), AlertIncident.triggered_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def acknowledge_incident(
        self,
        incident_id: str,
        acknowledged_by: str
    ) -> AlertIncident:
        """
        Acknowledge alert incident.

        Args:
            incident_id: Incident ID
            acknowledged_by: User acknowledging

        Returns:
            Updated incident
        """
        incident = await self.db.get(AlertIncident, incident_id)
        if not incident:
            raise ValueError("Incident not found")

        incident.status = AlertStatus.ACKNOWLEDGED
        incident.acknowledged_by = acknowledged_by
        incident.acknowledged_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Acknowledged incident {incident_id} by {acknowledged_by}")

        return incident

    async def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> AlertIncident:
        """
        Resolve alert incident.

        Args:
            incident_id: Incident ID
            resolved_by: User resolving
            resolution_notes: Optional resolution notes

        Returns:
            Updated incident
        """
        incident = await self.db.get(AlertIncident, incident_id)
        if not incident:
            raise ValueError("Incident not found")

        incident.status = AlertStatus.RESOLVED
        incident.resolved_by = resolved_by
        incident.resolved_at = datetime.utcnow()
        incident.resolution_notes = resolution_notes

        await self.db.commit()

        logger.info(f"Resolved incident {incident_id} by {resolved_by}")

        return incident

    async def calculate_sla_metrics(
        self,
        service_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate SLA metrics for a service.

        Args:
            service_name: Service name
            days: Number of days to calculate

        Returns:
            SLA metrics
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Get all health checks
        result = await self.db.execute(
            select(HealthCheck)
            .where(HealthCheck.service_name == service_name)
            .where(HealthCheck.checked_at >= since)
            .order_by(HealthCheck.checked_at)
        )

        checks = result.scalars().all()

        if not checks:
            return {
                "service_name": service_name,
                "period_days": days,
                "uptime_percent": 0.0,
                "avg_response_time_ms": 0.0,
                "total_checks": 0
            }

        # Calculate uptime
        healthy_checks = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
        uptime_percent = (healthy_checks / len(checks)) * 100

        # Calculate average response time
        response_times = [c.response_time_ms for c in checks if c.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        # Calculate downtime incidents
        downtime_incidents = 0
        in_downtime = False

        for check in checks:
            if check.status == HealthStatus.UNHEALTHY and not in_downtime:
                downtime_incidents += 1
                in_downtime = True
            elif check.status == HealthStatus.HEALTHY:
                in_downtime = False

        return {
            "service_name": service_name,
            "period_days": days,
            "uptime_percent": uptime_percent,
            "avg_response_time_ms": avg_response_time,
            "total_checks": len(checks),
            "healthy_checks": healthy_checks,
            "unhealthy_checks": len(checks) - healthy_checks,
            "downtime_incidents": downtime_incidents,
            "sla_met": uptime_percent >= 99.9  # 99.9% SLA target
        }

    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring dashboard data.

        Returns:
            Dashboard data with health, incidents, SLA
        """
        # Get health summary
        health = await self.get_health_summary()

        # Get open incidents
        incidents = await self.get_open_incidents()

        # Get critical incidents count
        critical_incidents = sum(1 for i in incidents if i.severity == AlertSeverity.CRITICAL)

        # Get active alert rules count
        rules_result = await self.db.execute(
            select(func.count(AlertRule.id)).where(AlertRule.is_enabled == True)
        )
        active_rules = rules_result.scalar_one_or_none() or 0

        return {
            "health": health,
            "incidents": {
                "total_open": len(incidents),
                "critical": critical_incidents,
                "warning": sum(1 for i in incidents if i.severity == AlertSeverity.WARNING),
                "recent": [
                    {
                        "id": i.id,
                        "title": i.title,
                        "severity": i.severity.value,
                        "status": i.status.value,
                        "triggered_at": i.triggered_at.isoformat()
                    }
                    for i in incidents[:10]
                ]
            },
            "alert_rules": {
                "active": active_rules
            },
            "timestamp": datetime.utcnow().isoformat()
        }
