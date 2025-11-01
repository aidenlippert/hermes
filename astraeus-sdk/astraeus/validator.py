"""
Agent Card Validator - Ensures A2A Protocol Compliance

Validates that agents have proper Agent Cards before deployment.
Checks all required fields and provides helpful error messages.
"""

import httpx
from typing import Dict, Any, List, Optional, Tuple


class AgentCardValidator:
    """Validator for A2A Protocol Agent Cards"""

    REQUIRED_FIELDS = [
        "name",
        "description",
        "capabilities",
        "endpoint",
        "a2a_version"
    ]

    REQUIRED_CAPABILITY_FIELDS = [
        "name",
        "description",
        "cost_per_call"
    ]

    def validate_agent_card(self, agent_card: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate agent card structure

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in agent_card:
                errors.append(f"❌ Missing required field: '{field}'")
            elif not agent_card[field]:
                errors.append(f"❌ Field '{field}' cannot be empty")

        # Validate capabilities
        if "capabilities" in agent_card:
            capabilities = agent_card["capabilities"]

            if not isinstance(capabilities, list):
                errors.append("❌ 'capabilities' must be a list")
            elif len(capabilities) == 0:
                errors.append("❌ Agent must have at least one capability")
            else:
                # Validate each capability
                for i, cap in enumerate(capabilities):
                    if not isinstance(cap, dict):
                        errors.append(f"❌ Capability {i+1} must be an object")
                        continue

                    for field in self.REQUIRED_CAPABILITY_FIELDS:
                        if field not in cap:
                            errors.append(f"❌ Capability '{cap.get('name', i+1)}' missing field: '{field}'")

                    # Validate cost
                    if "cost_per_call" in cap:
                        try:
                            cost = float(cap["cost_per_call"])
                            if cost < 0:
                                errors.append(f"❌ Capability '{cap.get('name')}' has negative cost")
                        except (ValueError, TypeError):
                            errors.append(f"❌ Capability '{cap.get('name')}' has invalid cost (must be number)")

        # Validate endpoint URL
        if "endpoint" in agent_card:
            endpoint = agent_card["endpoint"]
            if not endpoint.startswith(("http://", "https://")):
                errors.append(f"❌ Invalid endpoint URL: '{endpoint}' (must start with http:// or https://)")

        # Validate A2A version
        if "a2a_version" in agent_card:
            version = agent_card["a2a_version"]
            if not isinstance(version, str):
                errors.append("❌ 'a2a_version' must be a string")

        return len(errors) == 0, errors

    async def validate_live_agent(self, endpoint: str) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Validate a live agent by fetching its Agent Card

        Args:
            endpoint: Agent endpoint URL (e.g., http://localhost:8000)

        Returns:
            (is_valid, list_of_errors, agent_card_or_none)
        """
        errors = []
        agent_card = None

        # Ensure endpoint format
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"http://{endpoint}"

        # Remove trailing slash
        endpoint = endpoint.rstrip("/")

        agent_card_url = f"{endpoint}/.well-known/agent.json"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(agent_card_url)

                if response.status_code != 200:
                    errors.append(
                        f"❌ Agent Card endpoint returned {response.status_code}\n"
                        f"   URL: {agent_card_url}\n"
                        f"   Make sure your agent exposes /.well-known/agent.json"
                    )
                    return False, errors, None

                try:
                    agent_card = response.json()
                except Exception as e:
                    errors.append(
                        f"❌ Agent Card is not valid JSON\n"
                        f"   Error: {e}"
                    )
                    return False, errors, None

        except httpx.ConnectError:
            errors.append(
                f"❌ Cannot connect to agent\n"
                f"   URL: {agent_card_url}\n"
                f"   Make sure your agent is running!"
            )
            return False, errors, None

        except httpx.TimeoutException:
            errors.append(
                f"❌ Connection timeout\n"
                f"   URL: {agent_card_url}\n"
                f"   Agent took too long to respond"
            )
            return False, errors, None

        except Exception as e:
            errors.append(f"❌ Unexpected error: {e}")
            return False, errors, None

        # Validate the agent card structure
        is_valid, validation_errors = self.validate_agent_card(agent_card)
        errors.extend(validation_errors)

        return is_valid, errors, agent_card


def print_validation_report(is_valid: bool, errors: List[str], agent_card: Optional[Dict] = None):
    """Pretty print validation report"""
    print("\n" + "="*70)

    if is_valid:
        print("✅ AGENT CARD VALIDATION PASSED!")
        print("="*70 + "\n")

        if agent_card:
            print(f"📦 Agent: {agent_card.get('name')}")
            print(f"📋 Description: {agent_card.get('description')}")
            print(f"🔧 Capabilities: {len(agent_card.get('capabilities', []))}")
            print(f"📍 Endpoint: {agent_card.get('endpoint')}")
            print(f"🏷️  A2A Version: {agent_card.get('a2a_version')}")

            print("\n🎯 Capabilities:")
            for cap in agent_card.get('capabilities', []):
                print(f"   - {cap.get('name')}: ${cap.get('cost_per_call')} per call")
                print(f"     {cap.get('description')}")

        print("\n✅ Your agent is A2A Protocol compliant!")
        print("✅ Ready to register on ASTRAEUS network!")

    else:
        print("❌ AGENT CARD VALIDATION FAILED!")
        print("="*70 + "\n")

        print(f"Found {len(errors)} error(s):\n")
        for error in errors:
            print(error)

        print("\n📚 Fix these issues before deploying!")
        print("📖 See: https://docs.astraeus.ai/agent-card")

    print("="*70 + "\n")


async def validate_agent_command(endpoint: str = "http://localhost:8000"):
    """CLI command to validate agent"""
    print("\n🔍 ASTRAEUS Agent Card Validator\n")
    print(f"Checking agent at: {endpoint}\n")

    validator = AgentCardValidator()
    is_valid, errors, agent_card = await validator.validate_live_agent(endpoint)

    print_validation_report(is_valid, errors, agent_card)

    return is_valid


if __name__ == "__main__":
    import asyncio
    import sys

    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    asyncio.run(validate_agent_command(endpoint))
