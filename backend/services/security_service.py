"""
Security Service

Security event logging, monitoring, and verification management.

Sprint 4: Advanced Security & Trust
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent
from backend.database.models_security import (
    SecurityEvent,
    SecurityEventType,
    VerificationRecord,
    AnomalyDetection,
    ReputationScore
)

logger = logging.getLogger(__name__)


class SecurityService:
    """
    Security service for event logging and monitoring.

    Features:
    - Security event logging
    - Anomaly detection
    - Verification management
    - Security dashboard
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        error_message: Optional[str] = None
    ) -> SecurityEvent:
        """
        Log security event for audit trail.

        Args:
            event_type: Type of security event
            severity: info, warning, error, critical
            description: Event description
            user_id: Optional user ID
            agent_id: Optional agent ID
            ip_address: Optional IP address
            user_agent: Optional user agent
            metadata: Optional metadata
            success: Whether event was successful
            error_message: Optional error message

        Returns:
            SecurityEvent record
        """
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            user_id=user_id,
            agent_id=agent_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            success=success,
            error_message=error_message
        )

        self.db.add(event)
        await self.db.commit()

        logger.info(f"Security event: {event_type.value} - {severity} - {description}")

        return event

    async def get_security_events(
        self,
        event_type: Optional[SecurityEventType] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 7,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """
        Get security events for monitoring.

        Args:
            event_type: Optional event type filter
            severity: Optional severity filter
            user_id: Optional user filter
            days: Number of days to look back
            limit: Max results

        Returns:
            List of security events
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = select(SecurityEvent).where(SecurityEvent.created_at >= since)

        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)

        if severity:
            query = query.where(SecurityEvent.severity == severity)

        if user_id:
            query = query.where(SecurityEvent.user_id == user_id)

        query = query.order_by(SecurityEvent.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get security summary for dashboard.

        Args:
            days: Number of days to look back

        Returns:
            Security summary statistics
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Total events
        total_result = await self.db.execute(
            select(func.count(SecurityEvent.id))
            .where(SecurityEvent.created_at >= since)
        )
        total_events = total_result.scalar_one()

        # By severity
        severity_result = await self.db.execute(
            select(SecurityEvent.severity, func.count(SecurityEvent.id))
            .where(SecurityEvent.created_at >= since)
            .group_by(SecurityEvent.severity)
        )
        severity_counts = dict(severity_result.all())

        # By event type
        type_result = await self.db.execute(
            select(SecurityEvent.event_type, func.count(SecurityEvent.id))
            .where(SecurityEvent.created_at >= since)
            .group_by(SecurityEvent.event_type)
        )
        type_counts = {et.value: count for et, count in type_result.all()}

        # Failed events
        failed_result = await self.db.execute(
            select(func.count(SecurityEvent.id))
            .where(SecurityEvent.created_at >= since)
            .where(SecurityEvent.success == False)
        )
        failed_events = failed_result.scalar_one()

        # Get anomalies
        anomaly_result = await self.db.execute(
            select(func.count(AnomalyDetection.id))
            .where(AnomalyDetection.detected_at >= since)
            .where(AnomalyDetection.is_investigated == False)
        )
        unresolved_anomalies = anomaly_result.scalar_one()

        return {
            "period_days": days,
            "total_events": total_events,
            "by_severity": severity_counts,
            "by_type": type_counts,
            "failed_events": failed_events,
            "unresolved_anomalies": unresolved_anomalies,
            "critical_alerts": severity_counts.get("critical", 0)
        }

    async def create_verification(
        self,
        agent_id: str,
        verification_type: str,
        status: str,
        verified_by: Optional[str] = None,
        verification_method: Optional[str] = None,
        verification_data: Optional[Dict[str, Any]] = None,
        is_verified: bool = False,
        verification_score: Optional[float] = None,
        notes: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> VerificationRecord:
        """
        Create agent verification record.

        Args:
            agent_id: Agent ID
            verification_type: identity, endpoint, capability, security
            status: pending, approved, rejected, expired
            verified_by: Who verified
            verification_method: manual, automated, third_party
            verification_data: Verification data
            is_verified: Whether verified
            verification_score: Score (0.0-1.0)
            notes: Notes
            expires_at: Expiration date

        Returns:
            VerificationRecord
        """
        record = VerificationRecord(
            agent_id=agent_id,
            verification_type=verification_type,
            status=status,
            verified_by=verified_by,
            verification_method=verification_method,
            verification_data=verification_data or {},
            is_verified=is_verified,
            verification_score=verification_score,
            notes=notes,
            verified_at=datetime.utcnow() if is_verified else None,
            expires_at=expires_at
        )

        self.db.add(record)
        await self.db.commit()

        logger.info(f"Created verification: {verification_type} for agent {agent_id}")

        return record

    async def get_agent_verifications(self, agent_id: str) -> List[VerificationRecord]:
        """
        Get all verifications for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of verification records
        """
        result = await self.db.execute(
            select(VerificationRecord)
            .where(VerificationRecord.agent_id == agent_id)
            .order_by(VerificationRecord.created_at.desc())
        )

        return list(result.scalars().all())

    async def detect_anomaly(
        self,
        agent_id: str,
        anomaly_type: str,
        severity: float,
        description: str,
        baseline_value: Optional[float] = None,
        observed_value: Optional[float] = None,
        deviation: Optional[float] = None,
        model_version: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> AnomalyDetection:
        """
        Detect and log anomaly for agent behavior.

        Args:
            agent_id: Agent ID
            anomaly_type: response_time, quality, pricing, availability
            severity: Severity (0.0-1.0)
            description: Description
            baseline_value: Baseline value
            observed_value: Observed value
            deviation: Standard deviations
            model_version: ML model version
            confidence: Confidence (0.0-1.0)

        Returns:
            AnomalyDetection record
        """
        anomaly = AnomalyDetection(
            agent_id=agent_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            baseline_value=baseline_value,
            observed_value=observed_value,
            deviation=deviation,
            model_version=model_version,
            confidence=confidence
        )

        self.db.add(anomaly)
        await self.db.commit()

        # Log security event if high severity
        if severity >= 0.7:
            await self.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity="warning" if severity < 0.9 else "critical",
                description=f"Anomaly detected: {anomaly_type} - {description}",
                agent_id=agent_id,
                metadata={
                    "anomaly_id": anomaly.id,
                    "severity": severity,
                    "deviation": deviation
                }
            )

        logger.info(f"Anomaly detected: {anomaly_type} for agent {agent_id} (severity: {severity:.2f})")

        return anomaly

    async def get_unresolved_anomalies(
        self,
        agent_id: Optional[str] = None,
        min_severity: float = 0.5
    ) -> List[AnomalyDetection]:
        """
        Get unresolved anomalies.

        Args:
            agent_id: Optional agent filter
            min_severity: Minimum severity threshold

        Returns:
            List of anomaly detections
        """
        query = select(AnomalyDetection).where(
            AnomalyDetection.is_investigated == False,
            AnomalyDetection.severity >= min_severity
        )

        if agent_id:
            query = query.where(AnomalyDetection.agent_id == agent_id)

        query = query.order_by(AnomalyDetection.severity.desc(), AnomalyDetection.detected_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def investigate_anomaly(
        self,
        anomaly_id: str,
        investigation_notes: str
    ) -> AnomalyDetection:
        """
        Mark anomaly as investigated.

        Args:
            anomaly_id: Anomaly ID
            investigation_notes: Investigation notes

        Returns:
            Updated anomaly record
        """
        anomaly = await self.db.get(AnomalyDetection, anomaly_id)
        if not anomaly:
            raise ValueError("Anomaly not found")

        anomaly.is_investigated = True
        anomaly.investigation_notes = investigation_notes

        await self.db.commit()

        logger.info(f"Investigated anomaly {anomaly_id}")

        return anomaly

    async def get_agent_trust_overview(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive trust overview for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Trust overview with reputation, verifications, anomalies
        """
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            raise ValueError("Agent not found")

        # Get reputation
        reputation = await self.db.get(ReputationScore, agent_id)

        # Get verifications
        verifications = await self.get_agent_verifications(agent_id)

        # Get recent anomalies
        anomalies = await self.get_unresolved_anomalies(agent_id=agent_id)

        # Get security events
        security_events = await self.get_security_events(
            agent_id=agent_id,
            days=30,
            limit=20
        )

        overview = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "reputation": {
                "overall": reputation.overall_reputation if reputation else 0.5,
                "trust_grade": reputation.trust_grade if reputation else "C",
                "quality": reputation.quality_score if reputation else 0.5,
                "reliability": reputation.reliability_score if reputation else 0.5,
                "is_flagged": reputation.is_flagged if reputation else False
            },
            "verifications": [
                {
                    "type": v.verification_type,
                    "status": v.status,
                    "is_verified": v.is_verified,
                    "verified_at": v.verified_at.isoformat() if v.verified_at else None
                }
                for v in verifications
            ],
            "anomalies": [
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "description": a.description,
                    "detected_at": a.detected_at.isoformat() if a.detected_at else None
                }
                for a in anomalies[:5]
            ],
            "recent_security_events": [
                {
                    "event_type": e.event_type.value,
                    "severity": e.severity,
                    "description": e.description,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in security_events[:5]
            ],
            "summary": {
                "total_verifications": len(verifications),
                "verified_count": sum(1 for v in verifications if v.is_verified),
                "unresolved_anomalies": len(anomalies),
                "recent_events": len(security_events)
            }
        }

        return overview
