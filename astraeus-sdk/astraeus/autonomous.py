"""
Autonomous Agent Capabilities - Agents that autonomously discover and collaborate

This module enables TRUE autonomy:
- Agents analyze tasks and decide what capabilities they need
- Agents autonomously discover other agents with required capabilities
- Agents call other agents WITHOUT human intervention
- Agents coordinate multi-step tasks automatically
"""

import asyncio
from typing import Dict, Any, List, Optional
from astraeus.client import AstraeusClient


class AutonomousAgent:
    """
    Extension to make any agent fully autonomous

    Example:
        from astraeus import Agent
        from astraeus.autonomous import AutonomousAgent

        agent = Agent(name="MyAgent", ...)

        # Make it autonomous!
        autonomous = AutonomousAgent(agent, api_key="...")

        # Now it can autonomously complete complex tasks
        result = await autonomous.autonomous_execute(
            "Book a trip to Paris for next week"
        )
        # Agent will autonomously:
        # 1. Discover FlightAgent
        # 2. Discover HotelAgent
        # 3. Call them both
        # 4. Return complete trip plan
    """

    def __init__(self, agent, api_key: str, astraeus_url: str = None):
        self.agent = agent
        self.api_key = api_key
        self.astraeus_url = astraeus_url or "https://web-production-3df46.up.railway.app"
        self.client = None

    async def _get_client(self) -> AstraeusClient:
        """Get or create ASTRAEUS client"""
        if not self.client:
            self.client = AstraeusClient(
                api_key=self.api_key,
                astraeus_url=self.astraeus_url
            )
        return self.client

    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze what capabilities are needed to complete a task

        Returns:
            {
                "can_do_myself": bool,
                "my_capabilities": list,
                "needed_capabilities": list,
                "complexity": float
            }
        """
        # Simple keyword-based analysis (can be enhanced with LLM)
        keywords_to_capabilities = {
            "translate": "translate",
            "flight": "search_flights",
            "hotel": "book_hotel",
            "weather": "get_weather",
            "code": "generate_code",
            "analyze": "analyze_data",
            "email": "send_email",
            "scrape": "scrape_web"
        }

        task_lower = task_description.lower()

        needed = []
        for keyword, capability in keywords_to_capabilities.items():
            if keyword in task_lower:
                needed.append(capability)

        # Check if I have these capabilities
        my_caps = list(self.agent.capabilities.keys())
        can_do = all(cap in my_caps for cap in needed)

        if not needed:
            # Unknown task, assume generic processing
            needed = ["process"]

        return {
            "can_do_myself": can_do,
            "my_capabilities": my_caps,
            "needed_capabilities": needed,
            "complexity": 0.3 if len(needed) == 1 else 0.7
        }

    async def autonomous_execute(self, task_description: str) -> Dict[str, Any]:
        """
        Autonomously execute a task by discovering and calling other agents

        This is the CORE of autonomy:
        1. Analyze what's needed
        2. Check if I can do it myself
        3. If not, discover agents who can
        4. Call them autonomously
        5. Return results

        Args:
            task_description: Natural language task

        Returns:
            Execution results
        """
        print(f"\n{'='*70}")
        print(f"🤖 AUTONOMOUS EXECUTION: {self.agent.name}")
        print(f"{'='*70}\n")
        print(f"📝 Task: {task_description}\n")

        # Step 1: Analyze task
        print("1️⃣ Analyzing task requirements...")
        analysis = await self.analyze_task(task_description)

        print(f"   Can do myself: {analysis['can_do_myself']}")
        print(f"   My capabilities: {analysis['my_capabilities']}")
        print(f"   Needed capabilities: {analysis['needed_capabilities']}\n")

        # Step 2: If I can do it, execute directly
        if analysis['can_do_myself']:
            print("2️⃣ Executing with my own capabilities...\n")

            # Execute with first matching capability
            for cap_name in analysis['needed_capabilities']:
                if cap_name in self.agent.capabilities:
                    cap = self.agent.capabilities[cap_name]
                    result = await cap['function'](task_description)

                    return {
                        "success": True,
                        "executor": self.agent.name,
                        "autonomous": True,
                        "result": result
                    }

        # Step 3: Discover agents with needed capabilities
        print("2️⃣ Discovering agents on network...\n")

        client = await self._get_client()
        discovered_agents = {}

        for capability in analysis['needed_capabilities']:
            print(f"   Searching for '{capability}' capability...")

            agents = await client.search_agents(
                capability=capability,
                sort_by="smart",
                limit=3
            )

            if agents:
                discovered_agents[capability] = agents[0]  # Best agent
                print(f"      ✅ Found: {agents[0]['name']} (trust: {agents[0].get('trust_score', 0):.2f})")
            else:
                print(f"      ❌ No agents found with '{capability}'")

        if not discovered_agents:
            return {
                "success": False,
                "autonomous": True,
                "error": "No agents found with required capabilities"
            }

        # Step 4: Autonomously call discovered agents
        print(f"\n3️⃣ Autonomously calling {len(discovered_agents)} agents...\n")

        results = {}

        for capability, agent_info in discovered_agents.items():
            print(f"   Calling {agent_info['name']} → {capability}")

            try:
                result = await client.call_agent(
                    agent_id=agent_info['agent_id'],
                    capability=capability,
                    input={"request": task_description}
                )

                results[capability] = {
                    "agent": agent_info['name'],
                    "success": result.get('success', False),
                    "result": result.get('result'),
                    "cost": result.get('cost', 0)
                }

                print(f"      ✅ Success (cost: ${result.get('cost', 0)})")

            except Exception as e:
                results[capability] = {
                    "agent": agent_info['name'],
                    "success": False,
                    "error": str(e)
                }
                print(f"      ❌ Failed: {e}")

        # Step 5: Combine results
        print(f"\n{'='*70}")
        print(f"✅ AUTONOMOUS EXECUTION COMPLETE")
        print(f"{'='*70}\n")

        successful = sum(1 for r in results.values() if r.get('success'))
        total_cost = sum(r.get('cost', 0) for r in results.values())

        print(f"📊 Results: {successful}/{len(results)} successful")
        print(f"💰 Total Cost: ${total_cost:.4f}\n")

        return {
            "success": successful == len(results),
            "autonomous": True,
            "orchestrator": self.agent.name,
            "task": task_description,
            "agents_called": list(results.keys()),
            "results": results,
            "total_cost": total_cost
        }

    async def autonomous_background_task(self, task_queue: asyncio.Queue):
        """
        Run as background task that continuously processes tasks

        Usage:
            queue = asyncio.Queue()
            asyncio.create_task(autonomous.autonomous_background_task(queue))

            # Later, add tasks:
            await queue.put("Translate text to Spanish")
            await queue.put("Get weather for Tokyo")
        """
        print(f"🔄 {self.agent.name} - Autonomous background task started")

        while True:
            try:
                # Wait for task
                task = await queue.get()

                if task is None:  # Shutdown signal
                    break

                # Execute autonomously
                result = await self.autonomous_execute(task)

                # Could store result, send notification, etc.
                print(f"✅ Background task completed: {result['success']}")

            except Exception as e:
                print(f"❌ Background task error: {e}")

            finally:
                queue.task_done()

    async def close(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close()


# Example usage
async def demo_autonomous_agent():
    """Demo of autonomous agent discovering and calling other agents"""
    from astraeus import Agent

    # Create a base agent
    agent = Agent(
        name="OrchestratorBot",
        description="Autonomous orchestrator that discovers and calls other agents",
        api_key="demo_key",
        owner="demo@example.com"
    )

    # Add a simple capability
    @agent.capability("orchestrate", cost=0.00, description="Orchestrate complex tasks")
    async def orchestrate(task: str) -> dict:
        return {"task": task, "status": "orchestrated"}

    # Make it autonomous!
    autonomous = AutonomousAgent(agent, api_key="demo_key")

    # Autonomously execute a complex task
    result = await autonomous.autonomous_execute(
        "Translate 'Hello World' to Spanish and get the weather for Madrid"
    )

    print("\n📋 Final Result:")
    print(result)

    await autonomous.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          🤖 AUTONOMOUS AGENT DEMO                             ║
║                                                                ║
║   Agents that discover and collaborate automatically!         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(demo_autonomous_agent())
