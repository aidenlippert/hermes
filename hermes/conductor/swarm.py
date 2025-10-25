"""
Swarm Mode - Autonomous Multi-Agent Collaboration

This enables REAL multi-agent collaboration:
- Agents can talk to each other directly (not just through Hermes)
- Conversational loops (agents debate, refine, collaborate)
- Shared memory (hive mind)
- Self-organization (agents decide who does what)
- Dynamic re-planning (adapt on the fly)

Think: A team of experts in a room collaborating on a problem,
not a boss assigning tasks one-by-one.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from hermes.protocols.a2a_client import A2AClient
from hermes.conductor.planner import ExecutionPlan

logger = logging.getLogger(__name__)


class SwarmPhase(Enum):
    """Phase of swarm execution"""
    INITIALIZATION = "initialization"
    DISCOVERY = "discovery"  # Agents discover each other
    COLLABORATION = "collaboration"  # Agents work together
    CONSENSUS = "consensus"  # Agents reach agreement
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """Message between agents in the swarm"""
    from_agent: str
    to_agent: Optional[str]  # None = broadcast to all
    message_type: str  # "question", "answer", "proposal", "critique", "consensus"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class SharedMemory:
    """
    Hive Mind - Shared knowledge across all agents
    
    All agents can read and write to this shared context.
    Think: A shared whiteboard everyone can see and annotate.
    """
    task_description: str
    conversation_history: List[AgentMessage] = field(default_factory=list)
    shared_facts: Dict[str, Any] = field(default_factory=dict)
    partial_results: Dict[str, Any] = field(default_factory=dict)
    consensus_items: List[str] = field(default_factory=list)
    active_agents: Set[str] = field(default_factory=set)
    
    def add_message(self, message: AgentMessage):
        """Add message to conversation history"""
        self.conversation_history.append(message)
        logger.info(f"💬 {message.from_agent} → {message.to_agent or 'ALL'}: {message.content[:100]}...")
    
    def add_fact(self, key: str, value: Any, source: str):
        """Add verified fact to shared knowledge"""
        self.shared_facts[key] = {
            "value": value,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"📝 Fact added: {key} = {value} (by {source})")
    
    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get all context relevant to an agent"""
        return {
            "task": self.task_description,
            "conversation": [msg.to_dict() for msg in self.conversation_history[-10:]],  # Last 10 messages
            "shared_facts": self.shared_facts,
            "partial_results": self.partial_results,
            "consensus": self.consensus_items,
            "active_agents": list(self.active_agents)
        }


@dataclass
class SwarmAgent:
    """Agent participating in the swarm"""
    name: str
    endpoint: str
    capabilities: List[str]
    role: str  # "lead", "contributor", "critic", "synthesizer"
    status: str = "idle"  # "idle", "working", "waiting", "done"
    contribution: Optional[str] = None


class SwarmOrchestrator:
    """
    Swarm Mode Orchestrator
    
    Unlike the standard Executor which runs sequential plans,
    this enables true multi-agent collaboration where agents:
    1. Discover each other
    2. Communicate directly
    3. Self-organize
    4. Reach consensus
    5. Adapt dynamically
    """
    
    def __init__(
        self,
        a2a_client: Optional[A2AClient] = None,
        max_rounds: int = 5,
        consensus_threshold: float = 0.8
    ):
        """
        Initialize swarm orchestrator
        
        Args:
            a2a_client: A2A client for agent communication
            max_rounds: Max collaboration rounds
            consensus_threshold: When to consider consensus reached (0-1)
        """
        self.a2a_client = a2a_client or A2AClient()
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        
        logger.info("🐝 Swarm Mode initialized")
    
    async def execute_swarm(
        self,
        task: str,
        agents: List[Dict[str, Any]],
        mode: str = "collaborative"  # "collaborative", "debate", "consensus"
    ) -> Dict[str, Any]:
        """
        Execute task using swarm collaboration
        
        Args:
            task: The task to accomplish
            agents: Available agents
            mode: Collaboration mode
            
        Returns:
            Swarm execution result
        """
        logger.info(f"🐝 Starting swarm execution: {task[:100]}...")
        logger.info(f"   Agents in swarm: {len(agents)}")
        logger.info(f"   Mode: {mode}")
        
        # Initialize shared memory (hive mind)
        memory = SharedMemory(task_description=task)
        
        # Initialize swarm agents with roles
        swarm_agents = self._assign_roles(agents, task)
        for agent in swarm_agents:
            memory.active_agents.add(agent.name)
        
        phase = SwarmPhase.INITIALIZATION
        round_num = 0
        
        try:
            # Phase 1: Discovery - Agents introduce themselves
            phase = SwarmPhase.DISCOVERY
            await self._discovery_phase(swarm_agents, memory)
            
            # Phase 2: Collaboration - Agents work together
            phase = SwarmPhase.COLLABORATION
            while round_num < self.max_rounds:
                round_num += 1
                logger.info(f"\n🔄 Collaboration Round {round_num}/{self.max_rounds}")
                
                # Each agent contributes
                await self._collaboration_round(swarm_agents, memory, mode)
                
                # Check if consensus reached
                if await self._check_consensus(swarm_agents, memory):
                    logger.info("✅ Consensus reached!")
                    break
            
            # Phase 3: Consensus - Finalize the solution
            phase = SwarmPhase.CONSENSUS
            final_result = await self._consensus_phase(swarm_agents, memory)
            
            phase = SwarmPhase.COMPLETED
            
            return {
                "success": True,
                "result": final_result,
                "rounds": round_num,
                "conversation": [msg.to_dict() for msg in memory.conversation_history],
                "shared_facts": memory.shared_facts,
                "consensus_items": memory.consensus_items,
                "participating_agents": [a.name for a in swarm_agents]
            }
            
        except Exception as e:
            logger.error(f"❌ Swarm execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": phase.value,
                "rounds": round_num,
                "conversation": [msg.to_dict() for msg in memory.conversation_history]
            }
    
    def _assign_roles(
        self,
        agents: List[Dict[str, Any]],
        task: str
    ) -> List[SwarmAgent]:
        """
        Assign roles to agents based on capabilities
        
        Roles:
        - lead: Coordinates the collaboration
        - contributor: Provides expertise
        - critic: Challenges assumptions
        - synthesizer: Combines insights
        """
        swarm_agents = []
        
        for i, agent in enumerate(agents):
            # First agent is lead
            if i == 0:
                role = "lead"
            # Last agent synthesizes
            elif i == len(agents) - 1:
                role = "synthesizer"
            # Some agents critique
            elif i % 3 == 0:
                role = "critic"
            # Most contribute
            else:
                role = "contributor"
            
            swarm_agents.append(SwarmAgent(
                name=agent["name"],
                endpoint=agent["endpoint"],
                capabilities=agent.get("capabilities", []),
                role=role
            ))
            
            logger.info(f"   👤 {agent['name']}: {role}")
        
        return swarm_agents
    
    async def _discovery_phase(
        self,
        agents: List[SwarmAgent],
        memory: SharedMemory
    ):
        """Phase 1: Agents discover each other and share capabilities"""
        logger.info("\n🔍 Discovery Phase: Agents introducing themselves")
        
        for agent in agents:
            introduction = f"I am {agent.name}, I can {', '.join(agent.capabilities[:3])}. My role is {agent.role}."
            
            message = AgentMessage(
                from_agent=agent.name,
                to_agent=None,  # Broadcast
                message_type="introduction",
                content=introduction,
                metadata={"capabilities": agent.capabilities, "role": agent.role}
            )
            
            memory.add_message(message)
    
    async def _collaboration_round(
        self,
        agents: List[SwarmAgent],
        memory: SharedMemory,
        mode: str
    ):
        """One round of collaboration"""
        
        # Each agent gets a turn based on their role
        for agent in agents:
            agent.status = "working"
            
            # Build context for this agent
            context = memory.get_context_for_agent(agent.name)
            
            # Determine what this agent should do based on role
            instruction = self._get_role_instruction(agent, context, mode)
            
            # Agent processes and responds
            response = await self._agent_think(agent, instruction, context)
            
            # Add to shared memory
            message = AgentMessage(
                from_agent=agent.name,
                to_agent=None,
                message_type=self._get_message_type(agent.role),
                content=response,
                metadata={"role": agent.role, "round": len(memory.conversation_history)}
            )
            
            memory.add_message(message)
            agent.contribution = response
            agent.status = "done"
            
            # Small delay to simulate thinking
            await asyncio.sleep(0.5)
    
    def _get_role_instruction(
        self,
        agent: SwarmAgent,
        context: Dict[str, Any],
        mode: str
    ) -> str:
        """Get instruction for agent based on role"""
        
        task = context["task"]
        conversation = context.get("conversation", [])
        
        if agent.role == "lead":
            return f"""You are the lead agent coordinating this task: {task}

Review what other agents have said:
{json.dumps(conversation, indent=2)}

What should the team focus on next? Provide direction."""

        elif agent.role == "contributor":
            return f"""You are contributing your expertise to: {task}

Current conversation:
{json.dumps(conversation, indent=2)}

What insights can you add? What solutions do you propose?"""

        elif agent.role == "critic":
            return f"""You are the critic evaluating proposals for: {task}

Proposals so far:
{json.dumps(conversation, indent=2)}

What are the weaknesses? What could go wrong? How can we improve?"""

        elif agent.role == "synthesizer":
            return f"""You are synthesizing all inputs for: {task}

All contributions:
{json.dumps(conversation, indent=2)}

Combine these into a coherent solution. What's the best path forward?"""
        
        return task
    
    async def _agent_think(
        self,
        agent: SwarmAgent,
        instruction: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Agent processes instruction and returns response
        
        In real implementation, this would call the agent via A2A.
        For now, we'll simulate intelligent responses.
        """
        logger.info(f"   🤔 {agent.name} ({agent.role}) is thinking...")
        
        # TODO: In production, call actual agent via A2A
        # response = await self.a2a_client.send_task(agent.endpoint, instruction)
        
        # Simulated intelligent response based on role
        if agent.role == "lead":
            return f"Based on our capabilities, I suggest we divide this into 3 phases: research, implementation, and validation."
        elif agent.role == "contributor":
            return f"I can handle the {agent.capabilities[0] if agent.capabilities else 'analysis'} portion. Here's my approach: ..."
        elif agent.role == "critic":
            return f"I see a potential issue with timing. We should also consider edge cases in ..."
        elif agent.role == "synthesizer":
            return f"Combining everyone's input: We'll use {agent.name}'s approach for X, address the critic's concerns with Y, and deliver Z."
        
        return f"Contribution from {agent.name}"
    
    def _get_message_type(self, role: str) -> str:
        """Get message type based on role"""
        role_to_type = {
            "lead": "coordination",
            "contributor": "proposal",
            "critic": "critique",
            "synthesizer": "synthesis"
        }
        return role_to_type.get(role, "comment")
    
    async def _check_consensus(
        self,
        agents: List[SwarmAgent],
        memory: SharedMemory
    ) -> bool:
        """Check if agents have reached consensus"""
        
        # In real implementation, use AI to detect consensus
        # For now, check if all agents have contributed
        contributed = sum(1 for a in agents if a.contribution)
        consensus_score = contributed / len(agents)
        
        logger.info(f"   📊 Consensus score: {consensus_score:.2f}")
        
        return consensus_score >= self.consensus_threshold
    
    async def _consensus_phase(
        self,
        agents: List[SwarmAgent],
        memory: SharedMemory
    ) -> str:
        """Finalize the swarm result through consensus"""
        logger.info("\n🤝 Consensus Phase: Finalizing solution")
        
        # Get synthesizer's final output
        synthesizer = next((a for a in agents if a.role == "synthesizer"), agents[-1])
        
        final_context = memory.get_context_for_agent(synthesizer.name)
        
        final_instruction = f"""Based on all the collaboration, provide the FINAL solution to: {memory.task_description}

All contributions:
{json.dumps([msg.to_dict() for msg in memory.conversation_history], indent=2)}

Provide a clear, actionable final answer."""
        
        final_result = await self._agent_think(synthesizer, final_instruction, final_context)
        
        memory.consensus_items.append(final_result)
        
        return final_result


# Integration with existing conductor
class HybridExecutor:
    """
    Hybrid Executor - Combines sequential and swarm modes
    
    - Simple tasks: Use standard sequential execution
    - Complex tasks: Use swarm collaboration
    - You choose: Specify mode explicitly
    """
    
    def __init__(self, a2a_client: Optional[A2AClient] = None):
        from hermes.conductor.executor import Executor
        
        self.sequential_executor = Executor(a2a_client)
        self.swarm_orchestrator = SwarmOrchestrator(a2a_client)
        
        logger.info("🎯 Hybrid Executor initialized (Sequential + Swarm)")
    
    async def execute(
        self,
        plan: ExecutionPlan,
        mode: str = "auto",  # "auto", "sequential", "swarm", "hybrid"
        available_agents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute plan using best mode
        
        Args:
            plan: Execution plan
            mode: Execution mode
            available_agents: Agents available for swarm
            
        Returns:
            Execution result
        """
        
        # Auto-detect best mode
        if mode == "auto":
            # Use swarm if task is complex or has multiple agents
            if len(plan.steps) > 3 or plan.metadata.get("complexity", 0) > 0.7:
                mode = "swarm"
            else:
                mode = "sequential"
        
        logger.info(f"🎯 Executing in {mode.upper()} mode")
        
        if mode == "sequential":
            # Standard sequential execution
            result = await self.sequential_executor.execute(plan)
            return {
                "mode": "sequential",
                "success": result.success,
                "result": result.final_output,
                "steps_completed": result.completed_steps
            }
        
        elif mode == "swarm":
            # Swarm collaboration
            if not available_agents:
                # Extract agents from plan
                available_agents = [
                    {
                        "name": step.agent_name,
                        "endpoint": step.agent_endpoint,
                        "capabilities": []
                    }
                    for step in plan.steps
                ]
            
            return await self.swarm_orchestrator.execute_swarm(
                task=plan.original_query,
                agents=available_agents,
                mode="collaborative"
            )
        
        elif mode == "hybrid":
            # Use swarm for planning, then sequential execution
            # First, let agents collaborate on HOW to solve it
            swarm_result = await self.swarm_orchestrator.execute_swarm(
                task=f"Plan how to accomplish: {plan.original_query}",
                agents=available_agents or [],
                mode="consensus"
            )
            
            # Then execute the plan sequentially
            exec_result = await self.sequential_executor.execute(plan)
            
            return {
                "mode": "hybrid",
                "planning": swarm_result,
                "execution": {
                    "success": exec_result.success,
                    "result": exec_result.final_output
                }
            }
        
        else:
            raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    async def demo_swarm():
        """Demo swarm collaboration"""
        
        print("\n" + "="*70)
        print("🐝 SWARM MODE DEMO - Autonomous Multi-Agent Collaboration")
        print("="*70)
        
        # Mock agents
        agents = [
            {
                "name": "ResearchAgent",
                "endpoint": "http://localhost:10001/a2a",
                "capabilities": ["research", "fact_finding", "analysis"]
            },
            {
                "name": "CodeAgent",
                "endpoint": "http://localhost:10002/a2a",
                "capabilities": ["code_generation", "debugging", "testing"]
            },
            {
                "name": "WriterAgent",
                "endpoint": "http://localhost:10003/a2a",
                "capabilities": ["documentation", "explanation", "summarization"]
            },
            {
                "name": "ReviewAgent",
                "endpoint": "http://localhost:10004/a2a",
                "capabilities": ["review", "quality_check", "optimization"]
            }
        ]
        
        task = "Build a REST API for managing a todo list"
        
        print(f"\n📋 Task: {task}")
        print(f"\n🤖 Swarm Members:")
        for agent in agents:
            print(f"   - {agent['name']}: {', '.join(agent['capabilities'][:2])}")
        
        # Create swarm
        swarm = SwarmOrchestrator()
        
        print(f"\n🐝 Starting swarm collaboration...")
        print("=" * 70)
        
        result = await swarm.execute_swarm(task, agents, mode="collaborative")
        
        print("\n" + "=" * 70)
        print("🏁 SWARM RESULT")
        print("=" * 70)
        
        print(f"\n✅ Success: {result['success']}")
        print(f"🔄 Collaboration Rounds: {result['rounds']}")
        print(f"👥 Agents Participated: {', '.join(result['participating_agents'])}")
        
        print(f"\n💬 Conversation ({len(result['conversation'])} messages):")
        for msg in result['conversation']:
            print(f"\n   {msg['from']} ({msg['type']}):")
            print(f"   {msg['content'][:150]}...")
        
        print(f"\n🎯 Final Result:")
        print(f"   {result['result']}")
        
        print("\n" + "=" * 70)
        print("✨ This is the power of swarm intelligence!")
        print("=" * 70)
    
    asyncio.run(demo_swarm())
