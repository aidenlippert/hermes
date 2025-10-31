"""
GDPR/SOC2 Compliance Service

Implements data privacy, GDPR rights, and compliance tracking.

Sprint 4: Advanced Security & Trust
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User, Agent
from backend.database.models_security import (
    ComplianceRecord,
    ComplianceFramework,
    DataAccessLog,
    DataAccessPurpose
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    GDPR/SOC2 compliance service.

    Features:
    - GDPR compliance (Right to access, deletion, export)
    - Data access logging and audit trails
    - Consent management
    - Compliance reporting
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_data_access(
        self,
        user_id: str,
        accessed_by: str,
        access_method: str,
        purpose: DataAccessPurpose,
        data_types: List[str],
        action: str,
        legal_basis: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None
    ) -> DataAccessLog:
        """
        Log data access for GDPR compliance.

        Args:
            user_id: User whose data was accessed
            accessed_by: User who accessed the data
            access_method: api, admin_panel, support, system
            purpose: Purpose of access
            data_types: Types of data accessed (profile, payments, contracts)
            action: read, update, delete, export
            legal_basis: GDPR legal basis (consent, contract, legitimate_interest)
            ip_address: IP address of accessor
            user_agent: User agent of accessor
            description: Optional description

        Returns:
            DataAccessLog record
        """
        log = DataAccessLog(
            user_id=user_id,
            accessed_by=accessed_by,
            access_method=access_method,
            purpose=purpose,
            data_types=data_types,
            action=action,
            legal_basis=legal_basis,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description
        )

        self.db.add(log)
        await self.db.commit()

        logger.info(f"Logged data access: {user_id} by {accessed_by} ({action})")

        return log

    async def get_user_data_access_history(
        self,
        user_id: str,
        days: int = 90
    ) -> List[DataAccessLog]:
        """
        Get data access history for a user (GDPR requirement).

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of data access logs
        """
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(DataAccessLog)
            .where(DataAccessLog.user_id == user_id)
            .where(DataAccessLog.accessed_at >= since)
            .order_by(DataAccessLog.accessed_at.desc())
        )

        return list(result.scalars().all())

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data (GDPR right to data portability).

        Args:
            user_id: User ID

        Returns:
            Complete user data in structured format
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        # Get user profile
        user_data = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "profile": user.profile_data or {}
        }

        # Get owned agents
        agent_result = await self.db.execute(
            select(Agent).where(Agent.owner_id == user_id)
        )
        agents = agent_result.scalars().all()

        user_data["agents"] = [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "category": agent.category,
                "capabilities": agent.capabilities,
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            }
            for agent in agents
        ]

        # Get contracts
        from backend.database.models import Contract
        contract_result = await self.db.execute(
            select(Contract).where(Contract.requester_id == user_id)
        )
        contracts = contract_result.scalars().all()

        user_data["contracts"] = [
            {
                "id": contract.id,
                "title": contract.title,
                "status": contract.status.value,
                "created_at": contract.created_at.isoformat() if contract.created_at else None,
                "budget": float(contract.budget) if contract.budget else None
            }
            for contract in contracts
        ]

        # Get payments
        from backend.database.models_payments import Payment
        payment_result = await self.db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        payments = payment_result.scalars().all()

        user_data["payments"] = [
            {
                "id": payment.id,
                "amount": float(payment.amount),
                "provider": payment.provider.value,
                "status": payment.status.value,
                "created_at": payment.created_at.isoformat() if payment.created_at else None
            }
            for payment in payments
        ]

        # Get data access logs
        access_logs = await self.get_user_data_access_history(user_id, days=365)

        user_data["data_access_history"] = [
            {
                "accessed_by": log.accessed_by,
                "access_method": log.access_method,
                "purpose": log.purpose.value,
                "action": log.action,
                "accessed_at": log.accessed_at.isoformat() if log.accessed_at else None
            }
            for log in access_logs
        ]

        # Log this export
        await self.log_data_access(
            user_id=user_id,
            accessed_by=user_id,
            access_method="api",
            purpose=DataAccessPurpose.USER_REQUEST,
            data_types=["profile", "agents", "contracts", "payments", "access_logs"],
            action="export",
            legal_basis="user_request",
            description="User requested data export (GDPR)"
        )

        logger.info(f"Exported data for user {user_id}")

        return user_data

    async def delete_user_data(
        self,
        user_id: str,
        requested_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Delete user data (GDPR right to be forgotten).

        Args:
            user_id: User ID to delete
            requested_by: Who requested deletion
            reason: Reason for deletion

        Returns:
            Deletion summary
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        # Count what will be deleted
        agent_count = await self.db.execute(
            select(func.count(Agent.id)).where(Agent.owner_id == user_id)
        )
        agent_count = agent_count.scalar_one()

        from backend.database.models import Contract
        contract_count = await self.db.execute(
            select(func.count(Contract.id)).where(Contract.requester_id == user_id)
        )
        contract_count = contract_count.scalar_one()

        # Log the deletion request
        await self.log_data_access(
            user_id=user_id,
            accessed_by=requested_by,
            access_method="api",
            purpose=DataAccessPurpose.USER_REQUEST,
            data_types=["all"],
            action="delete",
            legal_basis="user_request",
            description=f"User deletion requested: {reason}"
        )

        # Delete user (cascades to related data)
        await self.db.delete(user)
        await self.db.commit()

        logger.info(f"Deleted user {user_id}: {agent_count} agents, {contract_count} contracts")

        return {
            "user_id": user_id,
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": requested_by,
            "reason": reason,
            "summary": {
                "agents": agent_count,
                "contracts": contract_count
            }
        }

    async def create_compliance_record(
        self,
        framework: ComplianceFramework,
        control_id: str,
        control_name: str,
        user_id: Optional[str] = None,
        is_compliant: bool = True,
        description: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        verified_by: Optional[str] = None
    ) -> ComplianceRecord:
        """
        Create compliance record for audit trail.

        Args:
            framework: Compliance framework (GDPR, SOC2, etc.)
            control_id: Control identifier (e.g., "GDPR-7.3")
            control_name: Control name
            user_id: Optional user ID if user-specific
            is_compliant: Whether control is compliant
            description: Description of compliance
            evidence: Evidence data
            notes: Additional notes
            verified_by: Who verified compliance

        Returns:
            ComplianceRecord
        """
        record = ComplianceRecord(
            framework=framework,
            control_id=control_id,
            control_name=control_name,
            user_id=user_id,
            is_compliant=is_compliant,
            description=description,
            evidence=evidence or {},
            notes=notes,
            verified_by=verified_by,
            compliance_date=datetime.utcnow() if is_compliant else None
        )

        self.db.add(record)
        await self.db.commit()

        logger.info(f"Created compliance record: {framework.value} - {control_id}")

        return record

    async def get_compliance_status(
        self,
        framework: Optional[ComplianceFramework] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get compliance status summary.

        Args:
            framework: Optional framework filter
            user_id: Optional user filter

        Returns:
            Compliance status summary
        """
        query = select(ComplianceRecord)

        if framework:
            query = query.where(ComplianceRecord.framework == framework)

        if user_id:
            query = query.where(ComplianceRecord.user_id == user_id)

        result = await self.db.execute(query)
        records = result.scalars().all()

        total = len(records)
        compliant = sum(1 for r in records if r.is_compliant)
        non_compliant = total - compliant

        compliance_rate = (compliant / total * 100) if total > 0 else 0

        status = {
            "total_controls": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "compliance_rate": compliance_rate,
            "by_framework": {}
        }

        # Group by framework
        for record in records:
            fw = record.framework.value
            if fw not in status["by_framework"]:
                status["by_framework"][fw] = {
                    "total": 0,
                    "compliant": 0,
                    "controls": []
                }

            status["by_framework"][fw]["total"] += 1
            if record.is_compliant:
                status["by_framework"][fw]["compliant"] += 1

            status["by_framework"][fw]["controls"].append({
                "control_id": record.control_id,
                "control_name": record.control_name,
                "is_compliant": record.is_compliant,
                "verified_at": record.verified_at.isoformat() if record.verified_at else None
            })

        return status

    async def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for auditing.

        Args:
            framework: Compliance framework
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Comprehensive compliance report
        """
        query = select(ComplianceRecord).where(
            ComplianceRecord.framework == framework
        )

        if start_date:
            query = query.where(ComplianceRecord.created_at >= start_date)

        if end_date:
            query = query.where(ComplianceRecord.created_at <= end_date)

        result = await self.db.execute(query.order_by(ComplianceRecord.created_at.desc()))
        records = result.scalars().all()

        report = {
            "framework": framework.value,
            "report_date": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "summary": {
                "total_controls": len(records),
                "compliant": sum(1 for r in records if r.is_compliant),
                "non_compliant": sum(1 for r in records if not r.is_compliant),
                "compliance_rate": (sum(1 for r in records if r.is_compliant) / len(records) * 100) if records else 0
            },
            "controls": [
                {
                    "control_id": r.control_id,
                    "control_name": r.control_name,
                    "is_compliant": r.is_compliant,
                    "description": r.description,
                    "evidence": r.evidence,
                    "verified_by": r.verified_by,
                    "verified_at": r.verified_at.isoformat() if r.verified_at else None
                }
                for r in records
            ]
        }

        logger.info(f"Generated compliance report: {framework.value} ({len(records)} controls)")

        return report
