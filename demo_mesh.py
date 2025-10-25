"""
Agent Mesh Protocol - Demo WITHOUT Redis Dependency

This proves the concept works with in-memory state.
In production, use protocol.py with Redis for distributed state.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Capability:
    """A capability an agent can perform"""
    name: str
    description: str
    confidence: float  # 0.0 to 1.0
    cost: float = 0.0
    latency: float = 0.0


@dataclass
class AgentIdentity:
    """Identity of an agent in the mesh"""
    id: str
    name: str
    endpoint: str
    capabilities: List[Capability]
    status: str = "active"
    reputation: float = 1.0
    
    def can_handle(self, query: str, threshold: float = 0.5) -> Optional[Capability]:
        """Check if agent can handle a query"""
        query_lower = query.lower()
        
        for cap in self.capabilities:
            if any(word in query_lower for word in cap.name.lower().split()):
                if cap.confidence >= threshold:
                    return cap
        return None


@dataclass
class MeshMessage:
    """Message in the agent mesh"""
    id: str
    type: str
    from_agent: str
    to_agent: Optional[str]
    content: str
    context_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content,
            "context_refs": self.context_refs,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class InMemoryMeshContext:
    """
    In-memory shared context for demo
    
    In production, use MeshContext with Redis for distributed state
    """
    
    def __init__(self):
        self.context_id = str(uuid.uuid4())[:8]
        self.facts: Dict[str, Any] = {}
        self.threads: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.subscribers: List[Callable] = []
        
    async def connect(self):
        """Mock connect"""
        logger.info(f"🔗 Connected to in-memory mesh context: {self.context_id}")
    
    async def disconnect(self):
        """Mock disconnect"""
        logger.info("👋 Disconnected from mesh context")
    
    async def add_fact(self, key: str, value: Any, source: str):
        """Add a verified fact to shared knowledge"""
        fact_data = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "verified": False
        }
        
        self.facts[key] = fact_data
        
        await self.broadcast({
            "type": "fact_added",
            "key": key,
            "value": value,
            "source": source
        })
        
        logger.info(f"📝 Fact added: {key} = {value} (by {source})")
    
    async def get_fact(self, key: str) -> Optional[Dict]:
        """Get a fact from shared knowledge"""
        return self.facts.get(key)
    
    async def verify_fact(self, key: str, verifier: str):
        """Verify a fact"""
        if key in self.facts:
            self.facts[key]["verified"] = True
            self.facts[key]["verified_by"] = verifier
            logger.info(f"✅ Fact verified: {key} (by {verifier})")
    
    async def get_all_facts(self) -> Dict[str, Any]:
        """Get all shared facts"""
        return self.facts.copy()
    
    async def broadcast(self, event: Dict[str, Any]):
        """Broadcast event to all agents"""
        self.events.append(event)
        
        # Notify all subscribers
        for subscriber in self.subscribers:
            try:
                await subscriber(event)
            except Exception as e:
                logger.error(f"Error in subscriber: {e}")
    
    async def subscribe(self, callback: Callable):
        """Subscribe to mesh events"""
        self.subscribers.append(callback)
        logger.info("📡 Subscribed to mesh events")
    
    async def add_thread(self, thread_id: str, topic: str, participants: List[str]):
        """Create a conversation thread"""
        self.threads[thread_id] = {
            "id": thread_id,
            "topic": topic,
            "participants": participants,
            "messages": [],
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    
    async def add_message_to_thread(self, thread_id: str, message: MeshMessage):
        """Add message to a thread"""
        if thread_id in self.threads:
            self.threads[thread_id]["messages"].append(message.to_dict())


class MeshAgent:
    """
    Agent that participates in the mesh
    
    Key principle: AUTONOMY
    - Doesn't wait for instructions
    - Monitors context actively  
    - Contributes when it has value
    - Collaborates peer-to-peer
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        context: InMemoryMeshContext,
    ):
        self.identity = identity
        self.context = context
        self.active_collaborations: Set[str] = set()
        self.contribution_count = 0
        self.answers_provided = 0
        self.facts_added = 0
        
        logger.info(f"🤖 Agent {identity.name} joined mesh")
    
    async def monitor_and_contribute(self):
        """
        Core agent behavior: Monitor context and contribute when relevant
        
        THIS IS THE KEY INNOVATION - agents are autonomous!
        """
        logger.info(f"👀 {self.identity.name} monitoring mesh...")
        
        async def on_event(event: Dict[str, Any]):
            """Handle mesh events autonomously"""
            event_type = event.get("type")
            
            if event_type == "capability_query":
                await self._respond_to_capability_query(event)
            
            elif event_type == "task_announced":
                await self._consider_joining_task(event)
            
            elif event_type == "proposal":
                await self._evaluate_proposal(event)
            
            elif event_type == "fact_added":
                await self._process_new_fact(event)
            
            elif event_type == "question":
                await self._consider_answering(event)
        
        await self.context.subscribe(on_event)
    
    async def _respond_to_capability_query(self, event: Dict[str, Any]):
        """Respond if we can help"""
        query = event.get("query", "")
        
        capability = self.identity.can_handle(query)
        
        if capability:
            response = {
                "type": "capability_response",
                "agent_id": self.identity.id,
                "agent_name": self.identity.name,
                "capability": capability.name,
                "confidence": capability.confidence,
            }
            
            await self.context.broadcast(response)
            
            logger.info(
                f"🙋 {self.identity.name} offered help: "
                f"{capability.name} (confidence: {capability.confidence:.2f})"
            )
    
    async def _consider_joining_task(self, event: Dict[str, Any]):
        """Consider joining a task"""
        task = event.get("task", "")
        task_id = event.get("task_id")
        
        # Check if this task matches our capabilities
        if self.identity.can_handle(task):
            logger.info(f"💪 {self.identity.name} joining task: {task_id}")
            
            # Add initial contribution
            await self.context.add_fact(
                f"{task_id}_{self.identity.name}_status",
                "working",
                self.identity.id
            )
            
            self.facts_added += 1
    
    async def _evaluate_proposal(self, event: Dict[str, Any]):
        """Evaluate a proposal"""
        proposal = event.get("content", "")
        from_agent = event.get("from_agent", "")
        
        if from_agent == self.identity.id:
            return
        
        # Check relevance
        for cap in self.identity.capabilities:
            if cap.name.lower() in proposal.lower():
                await self._add_perspective(event, cap)
                break
    
    async def _process_new_fact(self, event: Dict[str, Any]):
        """Process new fact"""
        key = event.get("key")
        value = event.get("value")
        logger.info(f"📖 {self.identity.name} noted: {key} = {value}")
    
    async def _consider_answering(self, event: Dict[str, Any]):
        """Consider answering a question"""
        question = event.get("content", "")
        
        if self.identity.can_handle(question):
            answer = await self._generate_answer(question)
            
            await self.context.broadcast({
                "type": "answer",
                "from_agent": self.identity.id,
                "question_id": event.get("id"),
                "content": answer
            })
            
            self.answers_provided += 1
    
    async def _add_perspective(self, proposal_event: Dict, capability: Capability):
        """Add perspective to proposal"""
        perspective = (
            f"From {capability.name} perspective: "
            f"This aligns with best practices for {capability.description}"
        )
        
        await self.context.broadcast({
            "type": "perspective",
            "from_agent": self.identity.id,
            "from_agent_name": self.identity.name,
            "on_proposal": proposal_event.get("id"),
            "content": perspective,
            "capability": capability.name
        })
        
        self.contribution_count += 1
        
        logger.info(f"💬 {self.identity.name} added perspective")
    
    async def _generate_answer(self, question: str) -> str:
        """Generate answer"""
        return f"Based on {self.identity.capabilities[0].name}: [detailed answer would go here]"
    
    async def propose(self, proposal: str, thread_id: Optional[str] = None):
        """Propose something to mesh"""
        message = MeshMessage(
            id=str(uuid.uuid4()),
            type="proposal",
            from_agent=self.identity.id,
            to_agent=None,
            content=proposal
        )
        
        await self.context.broadcast(message.to_dict())
        
        if thread_id:
            await self.context.add_message_to_thread(thread_id, message)
        
        logger.info(f"💡 {self.identity.name} proposed: {proposal[:80]}...")


class MeshNetwork:
    """
    The mesh network - provides infrastructure only
    
    NOT an orchestrator - agents self-organize!
    """
    
    def __init__(self):
        self.context = InMemoryMeshContext()
        self.agents: Dict[str, MeshAgent] = {}
        self.running = False
    
    async def start(self):
        """Start network"""
        await self.context.connect()
        self.running = True
        logger.info("🌐 Mesh network started")
    
    async def stop(self):
        """Stop network"""
        self.running = False
        await self.context.disconnect()
        logger.info("🛑 Mesh network stopped")
    
    async def register_agent(self, agent: MeshAgent):
        """Register agent"""
        self.agents[agent.identity.id] = agent
        
        await self.context.broadcast({
            "type": "agent_joined",
            "agent_id": agent.identity.id,
            "agent_name": agent.identity.name,
            "capabilities": [cap.name for cap in agent.identity.capabilities]
        })
        
        logger.info(f"✅ Registered {agent.identity.name}")
        
        # Start monitoring
        asyncio.create_task(agent.monitor_and_contribute())
    
    async def query_capabilities(self, query: str) -> List[Dict]:
        """Query for capable agents"""
        responses = []
        
        await self.context.broadcast({
            "type": "capability_query",
            "query": query,
        })
        
        # Give agents time to respond
        await asyncio.sleep(0.1)
        
        # Collect responses
        for agent in self.agents.values():
            cap = agent.identity.can_handle(query)
            if cap:
                responses.append({
                    "agent_id": agent.identity.id,
                    "agent_name": agent.identity.name,
                    "capability": cap.name,
                    "confidence": cap.confidence
                })
        
        responses.sort(key=lambda x: x["confidence"], reverse=True)
        return responses
    
    async def execute_collaborative_task(
        self,
        task: str,
        timeout: float = 3.0
    ) -> Dict[str, Any]:
        """
        Execute task with mesh collaboration
        
        KEY: Agents self-organize - we just facilitate!
        """
        logger.info(f"\n🎯 TASK: {task}")
        
        # 1. Find capable agents
        capable_agents = await self.query_capabilities(task)
        logger.info(f"   ✓ Found {len(capable_agents)} capable agents")
        
        # 2. Announce task
        task_id = str(uuid.uuid4())[:8]
        await self.context.broadcast({
            "type": "task_announced",
            "task_id": task_id,
            "task": task,
        })
        
        # 3. Create thread
        await self.context.add_thread(
            thread_id=task_id,
            topic=task,
            participants=[a["agent_id"] for a in capable_agents]
        )
        
        # 4. Let agents self-organize
        logger.info(f"   ⏳ Agents collaborating...")
        await asyncio.sleep(timeout)
        
        # 5. Gather results
        facts = await self.context.get_all_facts()
        
        return {
            "task_id": task_id,
            "task": task,
            "participating_agents": capable_agents,
            "shared_facts": facts,
            "event_count": len(self.context.events)
        }


async def demo():
    """
    PROOF OF CONCEPT: Decentralized Agent Collaboration
    """
    print("\n" + "="*80)
    print("🌐 AGENT MESH PROTOCOL - PROOF OF CONCEPT")
    print("="*80)
    print("\nThis demonstrates:")
    print("  ✓ Decentralized mesh network (no orchestrator)")
    print("  ✓ Autonomous agent behavior (monitor & contribute)")
    print("  ✓ Peer-to-peer collaboration")
    print("  ✓ Shared context for coordination")
    print("  ✓ Emergent task completion")
    print("\n" + "="*80 + "\n")
    
    # Create mesh
    mesh = MeshNetwork()
    await mesh.start()
    
    # Create diverse agents
    agents_config = [
        {
            "name": "ResearchAgent",
            "capabilities": [
                Capability("research", "Find and analyze information", 0.92),
                Capability("fact_check", "Verify claims and data", 0.88)
            ]
        },
        {
            "name": "CodeAgent",
            "capabilities": [
                Capability("code", "Write and review code", 0.95),
                Capability("architecture", "Design system architecture", 0.90)
            ]
        },
        {
            "name": "WriterAgent",
            "capabilities": [
                Capability("writing", "Write clear documentation", 0.93),
                Capability("summarization", "Condense complex information", 0.89)
            ]
        },
        {
            "name": "DataAgent",
            "capabilities": [
                Capability("analysis", "Analyze data patterns", 0.91),
                Capability("visualization", "Create data visualizations", 0.87)
            ]
        }
    ]
    
    # Register agents
    agents = []
    for config in agents_config:
        identity = AgentIdentity(
            id=str(uuid.uuid4())[:8],
            name=config["name"],
            endpoint=f"ws://localhost:8000/{config['name'].lower()}",
            capabilities=config["capabilities"]
        )
        
        agent = MeshAgent(identity, mesh.context)
        await mesh.register_agent(agent)
        agents.append(agent)
    
    print(f"✓ {len(agents)} autonomous agents joined mesh\n")
    
    # Small delay for monitoring to start
    await asyncio.sleep(0.2)
    
    # Execute collaborative tasks
    tasks = [
        "Build a REST API with documentation",
        "Research and analyze user feedback trends",
        "Write comprehensive project documentation"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'─'*80}")
        print(f"TASK #{i}")
        print(f"{'─'*80}")
        
        result = await mesh.execute_collaborative_task(task, timeout=1.5)
        
        print(f"\n✅ Completed!")
        print(f"   Participating agents:")
        for agent_info in result['participating_agents']:
            print(
                f"      • {agent_info['agent_name']}: "
                f"{agent_info['capability']} ({agent_info['confidence']:.0%})"
            )
        print(f"   Events generated: {result['event_count']}")
        print(f"   Shared facts: {len(result['shared_facts'])}")
    
    # Show agent statistics
    print(f"\n{'='*80}")
    print("AGENT STATISTICS (Showing Autonomous Behavior)")
    print(f"{'='*80}\n")
    
    for agent in agents:
        print(f"🤖 {agent.identity.name}:")
        print(f"   • Contributions: {agent.contribution_count}")
        print(f"   • Answers provided: {agent.answers_provided}")
        print(f"   • Facts added: {agent.facts_added}")
        print(f"   • Active collaborations: {len(agent.active_collaborations)}")
        print()
    
    # Cleanup
    await mesh.stop()
    
    print("="*80)
    print("🎉 PROOF OF CONCEPT COMPLETE")
    print("="*80)
    print("\nKey Takeaway:")
    print("  Agents operated AUTONOMOUSLY - no orchestrator commanded them!")
    print("  They monitored context, decided when to contribute, and self-organized.")
    print("  This is the FUTURE of multi-agent collaboration.")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
