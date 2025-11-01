"""
FREE Orchestrator for ASTRAEUS - Uses Local Ollama (No API Costs!)

This orchestrator uses open-source LLMs running locally via Ollama.
ZERO API costs, fully autonomous, runs on any machine.

Installation:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: ollama pull mistral
    3. Run this orchestrator!

Supported Models:
    - mistral (recommended, fast)
    - llama2
    - codellama
    - mixtral
    - phi
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx


class FreeOrchestrator:
    """Free orchestrator using local Ollama LLM (no API costs)"""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "mistral"):
        self.ollama_url = ollama_url
        self.model = model

    async def _generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate response from local Ollama"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            raise Exception(f"Ollama error: {e}. Make sure Ollama is running: ollama serve")

    async def parse_intent(self, user_request: str) -> Dict[str, Any]:
        """Parse user request into structured intent"""
        system_prompt = """You are an AI task analyzer. Extract the intent from user requests.

Return JSON with:
- category: (code_generation, data_analysis, translation, web_scraping, etc.)
- capabilities: list of required capabilities
- complexity: 0.0-1.0
- description: what the user wants"""

        prompt = f"""Analyze this request and return JSON:

User Request: "{user_request}"

Return ONLY valid JSON, no markdown, no explanation."""

        response = await self._generate(prompt, system_prompt)

        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                intent = json.loads(json_str)
            else:
                # Fallback: simple intent
                intent = {
                    "category": "general",
                    "capabilities": ["process"],
                    "complexity": 0.5,
                    "description": user_request
                }
        except:
            # Fallback parsing
            intent = {
                "category": "general",
                "capabilities": ["process"],
                "complexity": 0.5,
                "description": user_request
            }

        return intent

    async def create_plan(self, intent: Dict[str, Any], available_agents: List[Dict]) -> Dict[str, Any]:
        """Create execution plan using available agents"""
        system_prompt = """You are an AI task planner. Create execution plans using available agents.

Return JSON with:
- steps: list of {agent_name, capability, input_description}
- parallel: list of step indices that can run in parallel
- reasoning: why this plan works"""

        agents_info = "\n".join([
            f"- {a['name']}: {', '.join([c['name'] for c in a.get('capabilities', [])])}"
            for a in available_agents
        ])

        prompt = f"""Create an execution plan:

User wants: {intent['description']}
Required capabilities: {intent['capabilities']}

Available agents:
{agents_info}

Return ONLY valid JSON plan, no markdown."""

        response = await self._generate(prompt, system_prompt)

        # Extract JSON
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                plan = json.loads(json_str)
            else:
                # Fallback: simple plan
                plan = {
                    "steps": [{
                        "agent_name": available_agents[0]['name'] if available_agents else "unknown",
                        "capability": intent['capabilities'][0] if intent['capabilities'] else "process",
                        "input_description": intent['description']
                    }],
                    "parallel": [],
                    "reasoning": "Simple sequential execution"
                }
        except:
            # Fallback plan
            plan = {
                "steps": [{
                    "agent_name": available_agents[0]['name'] if available_agents else "unknown",
                    "capability": intent['capabilities'][0] if intent['capabilities'] else "process",
                    "input_description": intent['description']
                }],
                "parallel": [],
                "reasoning": "Auto-generated fallback plan"
            }

        return plan

    async def orchestrate(self, user_request: str, astraeus_client) -> Dict[str, Any]:
        """
        Complete autonomous orchestration using free local LLM

        Args:
            user_request: Natural language request
            astraeus_client: AstraeusClient for agent discovery

        Returns:
            Execution results
        """
        print(f"\n{'='*70}")
        print(f"🤖 FREE ORCHESTRATOR - Using {self.model} (Local, Zero Cost)")
        print(f"{'='*70}\n")

        # Step 1: Parse intent
        print("1️⃣ Parsing intent with local LLM...")
        intent = await self.parse_intent(user_request)
        print(f"   Category: {intent['category']}")
        print(f"   Capabilities: {intent['capabilities']}")
        print(f"   Complexity: {intent['complexity']:.2f}\n")

        # Step 2: Discover agents
        print("2️⃣ Discovering agents on network...")
        all_agents = []
        for capability in intent['capabilities']:
            agents = await astraeus_client.search_agents(
                capability=capability,
                sort_by="smart",
                limit=3
            )
            all_agents.extend(agents)

        # Deduplicate
        seen = set()
        unique_agents = []
        for agent in all_agents:
            if agent['agent_id'] not in seen:
                seen.add(agent['agent_id'])
                unique_agents.append(agent)

        print(f"   Found {len(unique_agents)} agents\n")

        if not unique_agents:
            return {
                "success": False,
                "error": "No agents found with required capabilities",
                "intent": intent
            }

        # Step 3: Create plan
        print("3️⃣ Creating execution plan with local LLM...")
        plan = await self.create_plan(intent, unique_agents)
        print(f"   Steps: {len(plan['steps'])}")
        print(f"   Parallel: {plan.get('parallel', [])}")
        print(f"   Reasoning: {plan['reasoning']}\n")

        # Step 4: Execute plan
        print("4️⃣ Executing plan...\n")
        results = []

        for i, step in enumerate(plan['steps']):
            print(f"   Step {i+1}: {step['agent_name']} → {step['capability']}")

            # Find agent
            agent = next(
                (a for a in unique_agents if a['name'] == step['agent_name']),
                unique_agents[0] if unique_agents else None
            )

            if not agent:
                results.append({
                    "step": i+1,
                    "success": False,
                    "error": "Agent not found"
                })
                continue

            try:
                # Call agent
                result = await astraeus_client.call_agent(
                    agent_id=agent['agent_id'],
                    capability=step['capability'],
                    input={"request": step['input_description']}
                )

                results.append({
                    "step": i+1,
                    "agent": step['agent_name'],
                    "success": result.get('success', False),
                    "result": result.get('result'),
                    "cost": result.get('cost', 0)
                })

                print(f"      ✅ Success (cost: ${result.get('cost', 0)})")

            except Exception as e:
                results.append({
                    "step": i+1,
                    "agent": step['agent_name'],
                    "success": False,
                    "error": str(e)
                })
                print(f"      ❌ Failed: {e}")

        # Summary
        print(f"\n{'='*70}")
        print(f"✅ Orchestration Complete!")
        print(f"{'='*70}\n")

        successful = sum(1 for r in results if r.get('success'))
        total_cost = sum(r.get('cost', 0) for r in results)

        print(f"📊 Results: {successful}/{len(results)} successful")
        print(f"💰 Total Cost: ${total_cost:.4f}")
        print(f"🆓 Orchestration Cost: $0.00 (Free Local LLM!)")
        print()

        return {
            "success": successful == len(results),
            "intent": intent,
            "plan": plan,
            "results": results,
            "total_cost": total_cost,
            "orchestrator": f"Free ({self.model})"
        }


async def test_free_orchestrator():
    """Test the free orchestrator"""
    from astraeus import AstraeusClient

    orchestrator = FreeOrchestrator(model="mistral")

    async with AstraeusClient(api_key="demo") as client:
        result = await orchestrator.orchestrate(
            "Translate 'Hello World' to Spanish",
            client
        )

        print("\n📋 Full Results:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          🆓 FREE ASTRAEUS ORCHESTRATOR                        ║
║                                                                ║
║   Powered by Local Ollama - Zero API Costs!                   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

Prerequisites:
1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh
2. Start Ollama: ollama serve
3. Pull a model: ollama pull mistral

Then run this script!
    """)

    asyncio.run(test_free_orchestrator())
