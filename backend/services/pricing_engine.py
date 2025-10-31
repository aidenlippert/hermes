"""
Pricing Engine

Dynamic pricing based on demand, reputation, and market conditions.

Sprint 3: Economic System & Payments
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent
from backend.database.models_payments import PricingRule

logger = logging.getLogger(__name__)


class PricingEngine:
    """Dynamic pricing engine"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_price(
        self,
        agent_id: str,
        base_price: Decimal,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate dynamic price for agent service.

        Args:
            agent_id: Agent ID
            base_price: Base price
            context: Pricing context (demand, time, etc.)

        Returns:
            {
                "base_price": Decimal,
                "adjusted_price": Decimal,
                "multiplier": float,
                "adjustments": List[Dict]
            }
        """
        context = context or {}
        agent = await self.db.get(Agent, agent_id)

        adjustments = []
        total_multiplier = 1.0

        # Get active pricing rules
        result = await self.db.execute(
            select(PricingRule).where(
                PricingRule.is_active == True
            ).order_by(PricingRule.priority.desc())
        )
        rules = result.scalars().all()

        # Apply rules
        for rule in rules:
            if await self._rule_applies(rule, agent, context):
                total_multiplier *= rule.multiplier
                adjustments.append({
                    "rule": rule.name,
                    "type": rule.rule_type,
                    "multiplier": rule.multiplier,
                    "description": rule.description
                })

        adjusted_price = base_price * Decimal(str(total_multiplier))

        return {
            "base_price": base_price,
            "adjusted_price": adjusted_price,
            "multiplier": total_multiplier,
            "adjustments": adjustments
        }

    async def _rule_applies(
        self,
        rule: PricingRule,
        agent: Agent,
        context: Dict[str, Any]
    ) -> bool:
        """Check if pricing rule applies"""
        # Check agent applicability
        applies_to = rule.applies_to_agents or []
        if applies_to and "all" not in applies_to:
            if agent.id not in applies_to:
                return False

        # Check capability applicability
        applies_to_caps = rule.applies_to_capabilities or []
        if applies_to_caps:
            agent_caps = set(agent.capabilities or [])
            rule_caps = set(applies_to_caps)
            if not agent_caps & rule_caps:
                return False

        # Check conditions
        conditions = rule.conditions or {}

        # Demand-based pricing
        if "demand_threshold" in conditions:
            demand = context.get("demand", 0.0)
            if demand < conditions["demand_threshold"]:
                return False

        # Time-based pricing
        if "time_of_day" in conditions:
            current_hour = datetime.utcnow().hour
            time_condition = conditions["time_of_day"]

            if time_condition == "peak":
                if current_hour not in range(9, 18):  # 9 AM - 6 PM
                    return False
            elif time_condition == "off_peak":
                if current_hour in range(9, 18):
                    return False

        # Reputation-based pricing
        if "min_reputation" in conditions:
            if agent.trust_score < conditions["min_reputation"]:
                return False

        return True

    async def create_surge_pricing_rule(
        self,
        demand_threshold: float = 0.8,
        multiplier: float = 1.5
    ) -> PricingRule:
        """Create surge pricing rule for high demand"""
        rule = PricingRule(
            name=f"surge_pricing_{demand_threshold}",
            description=f"Surge pricing when demand exceeds {demand_threshold}",
            rule_type="surge",
            conditions={"demand_threshold": demand_threshold},
            multiplier=multiplier,
            applies_to_agents=["all"],
            is_active=True,
            priority=10
        )

        self.db.add(rule)
        await self.db.commit()

        return rule

    async def create_reputation_discount(
        self,
        min_reputation: float = 0.9,
        discount_percent: float = 10.0
    ) -> PricingRule:
        """Create discount for high-reputation agents"""
        multiplier = 1.0 - (discount_percent / 100.0)

        rule = PricingRule(
            name=f"reputation_discount_{int(min_reputation*100)}",
            description=f"Discount for agents with reputation >= {min_reputation}",
            rule_type="reputation_based",
            conditions={"min_reputation": min_reputation},
            multiplier=multiplier,
            applies_to_agents=["all"],
            is_active=True,
            priority=5
        )

        self.db.add(rule)
        await self.db.commit()

        return rule
