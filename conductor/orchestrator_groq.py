"""
FREE Groq Orchestrator - Zero-cost AI orchestration using Groq's free API

Uses Groq's lightning-fast inference (faster than paid APIs!) with generous free tier.
Models: llama-3-70b, mixtral-8x7b, gemma-7b
"""

import os
import json
from typing import Dict, Any, List
from groq import Groq


class FreeGroqOrchestrator:
    """
    Free orchestrator using Groq API (zero cost, blazing fast!)

    Groq advantages:
    - FREE tier with generous limits
    - Faster than OpenAI/Gemini (seriously!)
    - Great models (Llama 3, Mixtral)
    - Works on serverless platforms
    """

    def __init__(self, api_key: str = None, model: str = "llama-3-70b-8192"):
        """
        Initialize Groq orchestrator

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Model to use (llama-3-70b-8192, mixtral-8x7b-32768, gemma-7b-it)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key required! Set GROQ_API_KEY or pass api_key parameter")

        self.client = Groq(api_key=self.api_key)
        self.model = model

        print(f"🚀 FREE GROQ ORCHESTRATOR - Using {model}")
        print(f"⚡ Blazing fast inference (faster than paid APIs!)")
        print(f"💰 Cost: $0.00 (FREE tier)")

    async def parse_intent(self, user_request: str) -> Dict[str, Any]:
        """
        Parse user intent using Groq LLM

        Args:
            user_request: Natural language request from user

        Returns:
            Parsed intent with category and required capabilities
        """
        prompt = f"""
Analyze this user request and extract the intent:

User Request: "{user_request}"

Return JSON with:
- category: One of [travel, data_analysis, translation, general, weather, booking]
- required_capabilities: List of capabilities needed (e.g., ["flight_search", "hotel_search"])
- complexity: simple/moderate/complex

Return ONLY valid JSON, no other text.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()

        # Extract JSON from response
        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            intent = json.loads(result_text)
            print(f"📋 Parsed intent: {intent['category']}, capabilities: {intent['required_capabilities']}")
            return intent
        except Exception as e:
            print(f"⚠️ Failed to parse intent JSON: {e}")
            # Fallback
            return {
                "category": "general",
                "required_capabilities": ["general"],
                "complexity": "simple"
            }

    async def create_plan(self, intent: Dict[str, Any], available_agents: List[Dict]) -> Dict[str, Any]:
        """
        Create execution plan using Groq LLM

        Args:
            intent: Parsed user intent
            available_agents: List of agents discovered from network

        Returns:
            Execution plan with ordered steps
        """
        agents_summary = "\n".join([
            f"- {agent['name']}: {', '.join([cap['name'] for cap in agent.get('capabilities', [])])}"
            for agent in available_agents[:5]  # Limit to top 5
        ])

        prompt = f"""
Create an execution plan for this intent:

Intent: {json.dumps(intent)}

Available Agents:
{agents_summary}

Return JSON with:
- steps: List of steps, each with:
  - agent_id: Which agent to use
  - capability: Which capability to call
  - input: What input to provide
  - depends_on: List of step indices this depends on (empty if none)

Return ONLY valid JSON, no other text.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            plan = json.loads(result_text)
            print(f"📝 Created plan with {len(plan.get('steps', []))} steps")
            return plan
        except Exception as e:
            print(f"⚠️ Failed to parse plan JSON: {e}")
            # Fallback - create simple sequential plan
            return {
                "steps": [
                    {
                        "agent_id": agent['agent_id'],
                        "capability": agent['capabilities'][0]['name'],
                        "input": {"request": intent},
                        "depends_on": []
                    }
                    for agent in available_agents[:3]
                ]
            }

    async def orchestrate(self, user_request: str, astraeus_client) -> Dict[str, Any]:
        """
        Complete orchestration workflow using FREE Groq API

        Args:
            user_request: Natural language request from user
            astraeus_client: AstraeusClient instance for network access

        Returns:
            Orchestration result with combined outputs
        """
        print(f"\n{'='*70}")
        print(f"🤖 FREE GROQ ORCHESTRATOR - Starting")
        print(f"{'='*70}\n")

        # Step 1: Parse intent
        print("1️⃣ Parsing intent with Groq AI...")
        intent = await self.parse_intent(user_request)

        # Step 2: Discover agents
        print("2️⃣ Discovering agents on network...")
        agents = []
        for capability in intent.get('required_capabilities', []):
            discovered = await astraeus_client.search_agents(
                capability=capability,
                sort_by="smart",
                limit=3
            )
            agents.extend(discovered)

        if not agents:
            print("⚠️ No agents found, using all available agents")
            agents = await astraeus_client.search_agents(limit=5)

        print(f"   Found {len(agents)} agent(s)")

        # Step 3: Create plan
        print("3️⃣ Creating execution plan with Groq AI...")
        plan = await self.create_plan(intent, agents)

        # Step 4: Execute plan
        print("4️⃣ Executing plan...")
        results = []
        total_cost = 0.0

        for i, step in enumerate(plan.get('steps', [])):
            print(f"   Step {i+1}: Calling {step.get('agent_id', 'unknown')}")

            try:
                # Find agent
                agent = next((a for a in agents if a['agent_id'] == step['agent_id']), None)
                if not agent:
                    print(f"   ⚠️ Agent {step['agent_id']} not found, skipping")
                    continue

                # Call agent
                result = await astraeus_client.call_agent(
                    agent_id=step['agent_id'],
                    capability=step['capability'],
                    input=step.get('input', {})
                )

                results.append(result)
                total_cost += result.get('cost', 0.0)
                print(f"   ✅ Success (cost: ${result.get('cost', 0.0)})")

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({"error": str(e), "step": i})

        print(f"\n{'='*70}")
        print(f"✅ Orchestration Complete!")
        print(f"💰 Total Agent Costs: ${total_cost:.2f}")
        print(f"🆓 Groq API Cost: $0.00 (FREE!)")
        print(f"⚡ Total Cost: ${total_cost:.2f}")
        print(f"{'='*70}\n")

        return {
            "success": True,
            "intent": intent,
            "plan": plan,
            "results": results,
            "total_cost": total_cost,
            "orchestration_cost": 0.00,
            "orchestrator": f"Groq ({self.model})"
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from astraeus import AstraeusClient

    async def test_groq_orchestrator():
        # Initialize orchestrator
        orchestrator = FreeGroqOrchestrator(
            api_key=os.getenv("GROQ_API_KEY"),  # Set via environment variable
            model="llama-3-70b-8192"
        )

        # Create client
        async with AstraeusClient(
            api_key="demo",
            network_url="http://localhost:8000"
        ) as client:
            # Test orchestration
            result = await orchestrator.orchestrate(
                "Get weather forecast for Tokyo",
                client
            )

            print("\n📊 Final Result:")
            print(json.dumps(result, indent=2))

    asyncio.run(test_groq_orchestrator())
