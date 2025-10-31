"""
ASTRAEUS SDK Resources

API resource classes for agents, contracts, payments, etc.

Sprint 6: Multi-Language SDKs
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AstraeusClient


class BaseResource:
    """Base class for API resources"""

    def __init__(self, client: "AstraeusClient"):
        self.client = client


class AgentsResource(BaseResource):
    """Agent management and execution"""

    def list(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List available agents.

        Args:
            category: Filter by category
            search: Search query
            limit: Max results
            offset: Pagination offset

        Returns:
            {"agents": [...], "total": 100}
        """
        params = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        if search:
            params["search"] = search

        return self.client.get("/api/v1/marketplace", params=params)

    def get(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details"""
        return self.client.get(f"/api/v1/marketplace/{agent_id}")

    def execute(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        wait_for_result: bool = True
    ) -> Dict[str, Any]:
        """
        Execute agent with input data.

        Args:
            agent_id: Agent ID
            input_data: Input data for agent
            wait_for_result: Wait for completion (default: True)

        Returns:
            Execution result
        """
        data = {
            "agent_id": agent_id,
            "input_data": input_data,
            "wait_for_result": wait_for_result
        }
        return self.client.post("/api/v1/agents/execute", data=data)

    def create(
        self,
        name: str,
        description: str,
        endpoint: str,
        capabilities: List[str],
        category: Optional[str] = None,
        is_free: bool = False,
        cost_per_request: float = 0.0
    ) -> Dict[str, Any]:
        """
        Register new agent.

        Args:
            name: Agent name
            description: Agent description
            endpoint: Agent API endpoint
            capabilities: List of capabilities
            category: Optional category
            is_free: Whether agent is free
            cost_per_request: Cost per request (if not free)

        Returns:
            Created agent
        """
        data = {
            "name": name,
            "description": description,
            "endpoint": endpoint,
            "capabilities": capabilities,
            "category": category,
            "is_free": is_free,
            "cost_per_request": cost_per_request
        }
        return self.client.post("/api/v1/agents", data=data)


class ContractsResource(BaseResource):
    """Contract management"""

    def create(
        self,
        title: str,
        description: str,
        budget: float,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create new contract.

        Args:
            title: Contract title
            description: Contract description
            budget: Budget amount
            requirements: Optional requirements

        Returns:
            Created contract
        """
        data = {
            "title": title,
            "description": description,
            "budget": budget,
            "requirements": requirements or {}
        }
        return self.client.post("/api/v1/contracts", data=data)

    def get(self, contract_id: str) -> Dict[str, Any]:
        """Get contract details"""
        return self.client.get(f"/api/v1/contracts/{contract_id}")

    def list(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List contracts.

        Args:
            status: Filter by status
            limit: Max results
            offset: Pagination offset

        Returns:
            {"contracts": [...], "total": 100}
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        return self.client.get("/api/v1/contracts", params=params)

    def award(self, contract_id: str, agent_id: str) -> Dict[str, Any]:
        """Award contract to agent"""
        data = {"agent_id": agent_id}
        return self.client.post(f"/api/v1/contracts/{contract_id}/award", data=data)


class PaymentsResource(BaseResource):
    """Payment and credit management"""

    def purchase_credits(
        self,
        amount: float,
        provider: str = "stripe"
    ) -> Dict[str, Any]:
        """
        Purchase credits.

        Args:
            amount: Amount to purchase
            provider: Payment provider (stripe, paypal, crypto)

        Returns:
            Payment details with intent/order ID
        """
        data = {"amount": amount, "provider": provider}
        return self.client.post("/api/v1/payments/credits/purchase", data=data)

    def get_balance(self) -> Dict[str, Any]:
        """Get credit balance"""
        return self.client.get("/api/v1/payments/credits/balance")

    def get_transactions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get credit transactions.

        Returns:
            {"transactions": [...], "total": 100}
        """
        params = {"limit": limit, "offset": offset}
        return self.client.get("/api/v1/payments/credits/transactions", params=params)


class OrchestrationResource(BaseResource):
    """Multi-agent orchestration"""

    def create_plan(
        self,
        query: str,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create orchestration plan.

        Args:
            query: User query
            pattern: Optional pattern (sequential, parallel, hierarchical, etc.)

        Returns:
            Orchestration plan
        """
        data = {"query": query}
        if pattern:
            data["pattern"] = pattern

        return self.client.post("/api/v1/orchestration/plan", data=data)

    def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """Execute orchestration plan"""
        return self.client.post(f"/api/v1/orchestration/plan/{plan_id}/execute")

    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get orchestration plan details"""
        return self.client.get(f"/api/v1/orchestration/plan/{plan_id}")


class AnalyticsResource(BaseResource):
    """Analytics and monitoring"""

    def get_dashboard(self, days: int = 7) -> Dict[str, Any]:
        """
        Get analytics dashboard.

        Args:
            days: Number of days for trends

        Returns:
            Dashboard data with metrics and trends
        """
        params = {"days": days}
        return self.client.get("/api/v1/analytics/dashboard", params=params)

    def get_user_analytics(
        self,
        user_id: str,
        period_type: str = "day"
    ) -> Dict[str, Any]:
        """Get user analytics"""
        params = {"period_type": period_type}
        return self.client.get(f"/api/v1/analytics/user/{user_id}", params=params)

    def get_agent_analytics(
        self,
        agent_id: str,
        period_type: str = "day"
    ) -> Dict[str, Any]:
        """Get agent analytics"""
        params = {"period_type": period_type}
        return self.client.get(f"/api/v1/analytics/agent/{agent_id}", params=params)

    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: str = "gauge",
        unit: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record custom metric.

        Args:
            metric_name: Metric name
            value: Metric value
            metric_type: counter, gauge, histogram, timer
            unit: Optional unit
            tags: Optional tags

        Returns:
            Success confirmation
        """
        data = {
            "metric_name": metric_name,
            "value": value,
            "metric_type": metric_type,
            "unit": unit,
            "tags": tags or {}
        }
        return self.client.post("/api/v1/analytics/metrics/record", data=data)


class SecurityResource(BaseResource):
    """Security and compliance"""

    def get_reputation(self, agent_id: str) -> Dict[str, Any]:
        """Get agent reputation details"""
        return self.client.get(f"/api/v1/security/reputation/{agent_id}")

    def get_fraud_alerts(
        self,
        fraud_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get fraud detection alerts.

        Args:
            fraud_type: Optional fraud type filter
            severity: Optional severity filter

        Returns:
            List of fraud alerts
        """
        params = {}
        if fraud_type:
            params["fraud_type"] = fraud_type
        if severity:
            params["severity"] = severity

        return self.client.get("/api/v1/security/fraud-alerts", params=params)

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data (GDPR).

        Args:
            user_id: User ID

        Returns:
            Complete user data export
        """
        data = {"user_id": user_id}
        return self.client.post("/api/v1/security/gdpr/export", data=data)
