"""
Metrics Collection Service

Custom metrics tracking, event recording, and performance profiling.

Sprint 5: Analytics & Observability
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from statistics import mean, median

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models_analytics import MetricEvent, MetricType

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Metrics collection and aggregation service.

    Features:
    - Custom metric tracking (counters, gauges, histograms, timers)
    - Time-series metric storage
    - Metric aggregation and rollups
    - Performance profiling
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        unit: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        description: Optional[str] = None
    ) -> MetricEvent:
        """
        Record a metric event.

        Args:
            metric_name: Metric name (e.g., "api.response_time")
            value: Metric value
            metric_type: counter, gauge, histogram, timer
            unit: Optional unit (ms, bytes, count, percent)
            tags: Optional tags for filtering/grouping
            source: Optional source (api, orchestration, payment)
            description: Optional description

        Returns:
            MetricEvent record
        """
        event = MetricEvent(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {},
            source=source,
            description=description
        )

        self.db.add(event)
        await self.db.commit()

        logger.debug(f"Recorded metric: {metric_name} = {value} {unit or ''}")

        return event

    async def record_counter(
        self,
        name: str,
        increment: float = 1.0,
        tags: Optional[Dict[str, Any]] = None
    ) -> MetricEvent:
        """
        Record counter metric (incremental count).

        Args:
            name: Counter name
            increment: Increment value
            tags: Optional tags

        Returns:
            MetricEvent
        """
        return await self.record_metric(
            metric_name=name,
            value=increment,
            metric_type=MetricType.COUNTER,
            unit="count",
            tags=tags
        )

    async def record_gauge(
        self,
        name: str,
        value: float,
        unit: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> MetricEvent:
        """
        Record gauge metric (point-in-time value).

        Args:
            name: Gauge name
            value: Current value
            unit: Optional unit
            tags: Optional tags

        Returns:
            MetricEvent
        """
        return await self.record_metric(
            metric_name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            unit=unit,
            tags=tags
        )

    async def record_timer(
        self,
        name: str,
        duration_ms: float,
        tags: Optional[Dict[str, Any]] = None
    ) -> MetricEvent:
        """
        Record timer metric (duration measurement).

        Args:
            name: Timer name
            duration_ms: Duration in milliseconds
            tags: Optional tags

        Returns:
            MetricEvent
        """
        return await self.record_metric(
            metric_name=name,
            value=duration_ms,
            metric_type=MetricType.TIMER,
            unit="ms",
            tags=tags
        )

    async def record_histogram(
        self,
        name: str,
        value: float,
        unit: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> MetricEvent:
        """
        Record histogram metric (distribution).

        Args:
            name: Histogram name
            value: Sample value
            unit: Optional unit
            tags: Optional tags

        Returns:
            MetricEvent
        """
        return await self.record_metric(
            metric_name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            unit=unit,
            tags=tags
        )

    async def get_metric_values(
        self,
        metric_name: str,
        hours: int = 24,
        tags: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """
        Get recent metric values.

        Args:
            metric_name: Metric name
            hours: Hours to look back
            tags: Optional tag filters

        Returns:
            List of metric values
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = select(MetricEvent.value).where(
            MetricEvent.metric_name == metric_name,
            MetricEvent.timestamp >= since
        )

        # Filter by tags if provided
        if tags:
            for key, value in tags.items():
                query = query.where(
                    func.json_extract(MetricEvent.tags, f'$.{key}') == value
                )

        query = query.order_by(MetricEvent.timestamp)

        result = await self.db.execute(query)
        return [v for v, in result.all()]

    async def aggregate_metric(
        self,
        metric_name: str,
        aggregation: str = "avg",
        hours: int = 24,
        tags: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Aggregate metric values.

        Args:
            metric_name: Metric name
            aggregation: avg, sum, min, max, count, p50, p95, p99
            hours: Hours to look back
            tags: Optional tag filters

        Returns:
            Aggregated value
        """
        values = await self.get_metric_values(metric_name, hours, tags)

        if not values:
            return 0.0

        if aggregation == "avg":
            return mean(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "count":
            return len(values)
        elif aggregation == "p50":
            return median(values)
        elif aggregation == "p95":
            values_sorted = sorted(values)
            idx = int(len(values_sorted) * 0.95)
            return values_sorted[idx]
        elif aggregation == "p99":
            values_sorted = sorted(values)
            idx = int(len(values_sorted) * 0.99)
            return values_sorted[idx]
        else:
            return 0.0

    async def get_metric_statistics(
        self,
        metric_name: str,
        hours: int = 24,
        tags: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive metric statistics.

        Args:
            metric_name: Metric name
            hours: Hours to look back
            tags: Optional tag filters

        Returns:
            Statistics dictionary
        """
        values = await self.get_metric_values(metric_name, hours, tags)

        if not values:
            return {
                "metric_name": metric_name,
                "count": 0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "sum": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }

        values_sorted = sorted(values)

        return {
            "metric_name": metric_name,
            "count": len(values),
            "avg": mean(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
            "p50": median(values),
            "p95": values_sorted[int(len(values_sorted) * 0.95)] if len(values_sorted) > 0 else 0.0,
            "p99": values_sorted[int(len(values_sorted) * 0.99)] if len(values_sorted) > 0 else 0.0
        }

    async def get_metric_time_series(
        self,
        metric_name: str,
        hours: int = 24,
        bucket_minutes: int = 60,
        aggregation: str = "avg",
        tags: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metric time series with bucketing.

        Args:
            metric_name: Metric name
            hours: Hours to look back
            bucket_minutes: Bucket size in minutes
            aggregation: avg, sum, min, max, count
            tags: Optional tag filters

        Returns:
            List of time-bucketed data points
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = select(MetricEvent).where(
            MetricEvent.metric_name == metric_name,
            MetricEvent.timestamp >= since
        )

        # Filter by tags if provided
        if tags:
            for key, value in tags.items():
                query = query.where(
                    func.json_extract(MetricEvent.tags, f'$.{key}') == value
                )

        query = query.order_by(MetricEvent.timestamp)

        result = await self.db.execute(query)
        events = result.scalars().all()

        if not events:
            return []

        # Bucket events
        buckets = {}
        bucket_size = timedelta(minutes=bucket_minutes)

        for event in events:
            # Round timestamp down to bucket
            bucket_start = event.timestamp.replace(second=0, microsecond=0)
            bucket_start = bucket_start - timedelta(
                minutes=bucket_start.minute % bucket_minutes
            )

            if bucket_start not in buckets:
                buckets[bucket_start] = []

            buckets[bucket_start].append(event.value)

        # Aggregate buckets
        time_series = []

        for bucket_time in sorted(buckets.keys()):
            values = buckets[bucket_time]

            if aggregation == "avg":
                agg_value = mean(values)
            elif aggregation == "sum":
                agg_value = sum(values)
            elif aggregation == "min":
                agg_value = min(values)
            elif aggregation == "max":
                agg_value = max(values)
            elif aggregation == "count":
                agg_value = len(values)
            else:
                agg_value = mean(values)

            time_series.append({
                "timestamp": bucket_time.isoformat(),
                "value": agg_value,
                "count": len(values)
            })

        return time_series

    async def track_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None
    ):
        """
        Track API call metrics.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user ID
        """
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        }

        if user_id:
            tags["user_id"] = user_id

        # Record response time
        await self.record_timer(
            name="api.response_time",
            duration_ms=response_time_ms,
            tags=tags
        )

        # Record call count
        await self.record_counter(
            name="api.calls",
            tags=tags
        )

        # Record errors
        if status_code >= 400:
            await self.record_counter(
                name="api.errors",
                tags=tags
            )

    async def track_contract_execution(
        self,
        contract_id: str,
        agent_id: str,
        execution_time_ms: float,
        success: bool
    ):
        """
        Track contract execution metrics.

        Args:
            contract_id: Contract ID
            agent_id: Agent ID
            execution_time_ms: Execution time
            success: Whether execution succeeded
        """
        tags = {
            "agent_id": agent_id,
            "success": success
        }

        # Record execution time
        await self.record_timer(
            name="contract.execution_time",
            duration_ms=execution_time_ms,
            tags=tags
        )

        # Record execution count
        await self.record_counter(
            name="contract.executions",
            tags=tags
        )

    async def track_orchestration(
        self,
        orchestration_id: str,
        pattern: str,
        agent_count: int,
        total_time_ms: float,
        success: bool
    ):
        """
        Track orchestration metrics.

        Args:
            orchestration_id: Orchestration ID
            pattern: Orchestration pattern
            agent_count: Number of agents involved
            total_time_ms: Total execution time
            success: Whether orchestration succeeded
        """
        tags = {
            "pattern": pattern,
            "success": success
        }

        # Record orchestration time
        await self.record_timer(
            name="orchestration.total_time",
            duration_ms=total_time_ms,
            tags=tags
        )

        # Record agent count
        await self.record_gauge(
            name="orchestration.agent_count",
            value=agent_count,
            unit="count",
            tags=tags
        )

        # Record orchestration count
        await self.record_counter(
            name="orchestration.executions",
            tags=tags
        )

    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary across all metrics.

        Returns:
            Performance summary statistics
        """
        # API metrics
        api_response_time = await self.get_metric_statistics("api.response_time", hours=1)
        api_calls_result = await self.aggregate_metric("api.calls", "count", hours=1)
        api_errors_result = await self.aggregate_metric("api.errors", "count", hours=1)

        # Contract metrics
        contract_time = await self.get_metric_statistics("contract.execution_time", hours=1)
        contract_count = await self.aggregate_metric("contract.executions", "count", hours=1)

        # Orchestration metrics
        orch_time = await self.get_metric_statistics("orchestration.total_time", hours=1)
        orch_count = await self.aggregate_metric("orchestration.executions", "count", hours=1)

        # Calculate error rate
        error_rate = (api_errors_result / api_calls_result * 100) if api_calls_result > 0 else 0.0

        return {
            "api": {
                "response_time": api_response_time,
                "total_calls": api_calls_result,
                "total_errors": api_errors_result,
                "error_rate_percent": error_rate
            },
            "contracts": {
                "execution_time": contract_time,
                "total_executions": contract_count
            },
            "orchestration": {
                "execution_time": orch_time,
                "total_executions": orch_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def cleanup_old_metrics(self, days: int = 90):
        """
        Delete old metric events to manage storage.

        Args:
            days: Delete metrics older than this many days

        Returns:
            Number of deleted records
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(func.count(MetricEvent.id))
            .where(MetricEvent.timestamp < cutoff)
        )

        count = result.scalar_one_or_none() or 0

        if count > 0:
            # Delete old metrics
            await self.db.execute(
                MetricEvent.__table__.delete().where(MetricEvent.timestamp < cutoff)
            )

            await self.db.commit()

            logger.info(f"Deleted {count} old metric events (older than {days} days)")

        return count
