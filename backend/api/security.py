"""
Security & Compliance API

RESTful API endpoints for security, reputation, fraud detection, and compliance.

Sprint 4: Advanced Security & Trust
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.services.reputation_engine import ReputationEngine
from backend.services.fraud_detection import FraudDetector
from backend.services.compliance_service import ComplianceService
from backend.services.security_service import SecurityService
from backend.database.models_security import (
    FraudType,
    FraudSeverity,
    ComplianceFramework,
    DataAccessPurpose
)

router = APIRouter(prefix="/api/v1/security", tags=["Security & Compliance"])


class ReputationResponse(BaseModel):
    agent_id: str
    overall_reputation: float
    trust_grade: str
    quality_score: float
    reliability_score: float
    speed_score: float
    honesty_score: float
    collaboration_score: float
    total_contracts: int
    successful_contracts: int
    average_rating: float
    is_flagged: bool
    last_calculated: Optional[datetime]


class FraudAlertResponse(BaseModel):
    id: str
    fraud_type: str
    severity: str
    confidence: float
    description: str
    evidence: dict
    related_agents: List[str]
    related_contracts: List[str]
    is_reviewed: bool
    created_at: datetime


class ReviewAlertRequest(BaseModel):
    reviewed_by: str
    resolution: str
    action_taken: str = Field(..., description="ban, warn, monitor, dismiss")


class DataExportRequest(BaseModel):
    user_id: str
    purpose: str = "user_request"


class ComplianceStatusResponse(BaseModel):
    total_controls: int
    compliant: int
    non_compliant: int
    compliance_rate: float
    by_framework: dict


class SecurityEventResponse(BaseModel):
    id: str
    event_type: str
    severity: str
    description: str
    user_id: Optional[str]
    agent_id: Optional[str]
    success: Optional[bool]
    created_at: datetime


class TrustOverviewResponse(BaseModel):
    agent_id: str
    agent_name: str
    reputation: dict
    verifications: List[dict]
    anomalies: List[dict]
    recent_security_events: List[dict]
    summary: dict


@router.get("/reputation/{agent_id}", response_model=ReputationResponse)
async def get_agent_reputation(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent reputation details.

    Returns comprehensive reputation scores and statistics.
    """
    engine = ReputationEngine(db)

    try:
        reputation = await engine.calculate_reputation(agent_id)

        return ReputationResponse(
            agent_id=reputation.agent_id,
            overall_reputation=reputation.overall_reputation,
            trust_grade=reputation.trust_grade,
            quality_score=reputation.quality_score,
            reliability_score=reputation.reliability_score,
            speed_score=reputation.speed_score,
            honesty_score=reputation.honesty_score,
            collaboration_score=reputation.collaboration_score,
            total_contracts=reputation.total_contracts,
            successful_contracts=reputation.successful_contracts,
            average_rating=reputation.average_rating,
            is_flagged=reputation.is_flagged,
            last_calculated=reputation.last_calculated
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reputation/{agent_id}/trends")
async def get_reputation_trends(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reputation trends over time.

    Args:
        agent_id: Agent ID
        days: Number of days to look back (1-365)

    Returns:
        List of historical reputation metrics
    """
    engine = ReputationEngine(db)

    trends = await engine.get_reputation_trends(agent_id, days=days)

    return {
        "agent_id": agent_id,
        "period_days": days,
        "data_points": len(trends),
        "trends": trends
    }


@router.post("/reputation/recalculate-all")
async def recalculate_all_reputations(db: AsyncSession = Depends(get_db)):
    """
    Recalculate reputation for all active agents.

    This should be run as a periodic background task.
    """
    engine = ReputationEngine(db)

    count = await engine.recalculate_all_reputations()

    return {
        "success": True,
        "agents_updated": count
    }


@router.get("/fraud-alerts", response_model=List[FraudAlertResponse])
async def get_fraud_alerts(
    fraud_type: Optional[FraudType] = None,
    severity: Optional[FraudSeverity] = None,
    is_reviewed: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get fraud detection alerts.

    Args:
        fraud_type: Optional fraud type filter
        severity: Optional severity filter
        is_reviewed: Show only reviewed/unreviewed alerts

    Returns:
        List of fraud alerts
    """
    detector = FraudDetector(db)

    if is_reviewed:
        from backend.database.models_security import FraudAlert
        from sqlalchemy import select

        query = select(FraudAlert).where(FraudAlert.is_reviewed == True)

        if fraud_type:
            query = query.where(FraudAlert.fraud_type == fraud_type)

        if severity:
            query = query.where(FraudAlert.severity == severity)

        result = await db.execute(query.limit(100))
        alerts = result.scalars().all()

    else:
        alerts = await detector.get_unreviewed_alerts(severity=severity)

    return [
        FraudAlertResponse(
            id=alert.id,
            fraud_type=alert.fraud_type.value,
            severity=alert.severity.value,
            confidence=alert.confidence,
            description=alert.description,
            evidence=alert.evidence,
            related_agents=alert.related_agents,
            related_contracts=alert.related_contracts,
            is_reviewed=alert.is_reviewed,
            created_at=alert.created_at
        )
        for alert in alerts
    ]


@router.post("/fraud-alerts/{alert_id}/review")
async def review_fraud_alert(
    alert_id: str,
    request: ReviewAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Review and resolve fraud alert.

    Args:
        alert_id: Alert ID
        request: Review request with action taken

    Returns:
        Updated alert
    """
    detector = FraudDetector(db)

    try:
        alert = await detector.review_alert(
            alert_id=alert_id,
            reviewed_by=request.reviewed_by,
            resolution=request.resolution,
            action_taken=request.action_taken
        )

        return {
            "success": True,
            "alert_id": alert.id,
            "action_taken": alert.action_taken,
            "reviewed_at": alert.reviewed_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/fraud-detection/run-all")
async def run_all_fraud_detection(db: AsyncSession = Depends(get_db)):
    """
    Run all fraud detection algorithms.

    This should be run as a periodic background task.

    Returns:
        Detection results summary
    """
    detector = FraudDetector(db)

    results = await detector.run_all_detections()

    summary = {
        "total_alerts": sum(len(alerts) for alerts in results.values()),
        "by_type": {
            fraud_type: len(alerts)
            for fraud_type, alerts in results.items()
        }
    }

    return {
        "success": True,
        "summary": summary
    }


@router.get("/compliance/{user_id}", response_model=ComplianceStatusResponse)
async def get_user_compliance_status(
    user_id: str,
    framework: Optional[ComplianceFramework] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get compliance status for a user.

    Args:
        user_id: User ID
        framework: Optional framework filter

    Returns:
        Compliance status summary
    """
    compliance = ComplianceService(db)

    status = await compliance.get_compliance_status(
        framework=framework,
        user_id=user_id
    )

    return ComplianceStatusResponse(**status)


@router.post("/gdpr/export")
async def export_user_data(
    request: DataExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Export all user data (GDPR right to data portability).

    Args:
        request: Export request with user ID

    Returns:
        Complete user data export
    """
    compliance = ComplianceService(db)

    try:
        data = await compliance.export_user_data(request.user_id)

        return {
            "success": True,
            "export_date": datetime.utcnow().isoformat(),
            "data": data
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/gdpr/delete/{user_id}")
async def delete_user_data(
    user_id: str,
    requested_by: str = Query(..., description="Who requested deletion"),
    reason: str = Query(..., description="Reason for deletion"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user data (GDPR right to be forgotten).

    Args:
        user_id: User ID to delete
        requested_by: Who requested deletion
        reason: Reason for deletion

    Returns:
        Deletion summary
    """
    compliance = ComplianceService(db)

    try:
        summary = await compliance.delete_user_data(
            user_id=user_id,
            requested_by=requested_by,
            reason=reason
        )

        return {
            "success": True,
            "summary": summary
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/gdpr/access-history/{user_id}")
async def get_data_access_history(
    user_id: str,
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get data access history for a user (GDPR requirement).

    Args:
        user_id: User ID
        days: Number of days to look back

    Returns:
        List of data access logs
    """
    compliance = ComplianceService(db)

    logs = await compliance.get_user_data_access_history(user_id, days=days)

    return {
        "user_id": user_id,
        "period_days": days,
        "total_accesses": len(logs),
        "access_logs": [
            {
                "id": log.id,
                "accessed_by": log.accessed_by,
                "access_method": log.access_method,
                "purpose": log.purpose.value,
                "data_types": log.data_types,
                "action": log.action,
                "accessed_at": log.accessed_at.isoformat()
            }
            for log in logs
        ]
    }


@router.get("/compliance/reports/{framework}")
async def generate_compliance_report(
    framework: ComplianceFramework,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate compliance report for auditing.

    Args:
        framework: Compliance framework (GDPR, SOC2, etc.)
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        Comprehensive compliance report
    """
    compliance = ComplianceService(db)

    report = await compliance.generate_compliance_report(
        framework=framework,
        start_date=start_date,
        end_date=end_date
    )

    return report


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
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
    security = SecurityService(db)

    from backend.database.models_security import SecurityEventType

    event_type_enum = None
    if event_type:
        try:
            event_type_enum = SecurityEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    events = await security.get_security_events(
        event_type=event_type_enum,
        severity=severity,
        user_id=user_id,
        days=days,
        limit=limit
    )

    return [
        SecurityEventResponse(
            id=event.id,
            event_type=event.event_type.value,
            severity=event.severity,
            description=event.description,
            user_id=event.user_id,
            agent_id=event.agent_id,
            success=event.success,
            created_at=event.created_at
        )
        for event in events
    ]


@router.get("/summary")
async def get_security_summary(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Get security summary for dashboard.

    Args:
        days: Number of days to look back

    Returns:
        Security summary statistics
    """
    security = SecurityService(db)

    summary = await security.get_security_summary(days=days)

    return summary


@router.get("/trust-overview/{agent_id}", response_model=TrustOverviewResponse)
async def get_agent_trust_overview(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive trust overview for an agent.

    Includes reputation, verifications, anomalies, and security events.

    Args:
        agent_id: Agent ID

    Returns:
        Complete trust overview
    """
    security = SecurityService(db)

    try:
        overview = await security.get_agent_trust_overview(agent_id)

        return TrustOverviewResponse(**overview)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/anomalies")
async def get_unresolved_anomalies(
    agent_id: Optional[str] = None,
    min_severity: float = Query(0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get unresolved anomalies.

    Args:
        agent_id: Optional agent filter
        min_severity: Minimum severity threshold

    Returns:
        List of anomaly detections
    """
    security = SecurityService(db)

    anomalies = await security.get_unresolved_anomalies(
        agent_id=agent_id,
        min_severity=min_severity
    )

    return {
        "total_anomalies": len(anomalies),
        "anomalies": [
            {
                "id": a.id,
                "agent_id": a.agent_id,
                "anomaly_type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "baseline_value": a.baseline_value,
                "observed_value": a.observed_value,
                "deviation": a.deviation,
                "detected_at": a.detected_at.isoformat()
            }
            for a in anomalies
        ]
    }


@router.post("/anomalies/{anomaly_id}/investigate")
async def investigate_anomaly(
    anomaly_id: str,
    investigation_notes: str = Query(..., description="Investigation notes"),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark anomaly as investigated.

    Args:
        anomaly_id: Anomaly ID
        investigation_notes: Investigation notes

    Returns:
        Updated anomaly
    """
    security = SecurityService(db)

    try:
        anomaly = await security.investigate_anomaly(
            anomaly_id=anomaly_id,
            investigation_notes=investigation_notes
        )

        return {
            "success": True,
            "anomaly_id": anomaly.id,
            "is_investigated": anomaly.is_investigated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
