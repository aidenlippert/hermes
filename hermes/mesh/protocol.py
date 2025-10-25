"""
Agent Mesh Protocol - TRUE Decentralized Agent Collaboration

This is the REAL future:
- No central orchestrator
- Agents communicate peer-to-peer
- Shared context for coordination
- Emergent behavior
- Parallel by default

Key Insight: Agents are PEERS, not workers
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class Capability:
    """A capability an agent can perform"""
    name: str
    description: str
    confidence: float  # 0.0 to 1.0
    cost: float = 0.0  # Estimated cost
    latency: float = 0.0  # Estimated seconds


@dataclass
class AgentIdentity:
    """Identity of an agent in the mesh"""
    id: str
    name: str
    endpoint: str
    capabilities: List[Capability]
    status: str = "active"  # "active", "busy", "offline"
    reputation: float = 1.0  # Trust score
    
    def can_handle(self, query: str, threshold: float = 0.5) -> Optional[Capability]:
        """Check if agent can handle a query"""
        # In production: use embeddings for semantic matching
        # For now: simple keyword matching
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
    type: str  # "broadcast", "proposal", "response", "fact", "question"
    from_agent: str
    to_agent: Optional[str]  # None = broadcast
    content: str
    context_refs: List[str] = field(default_factory=list)  # References to shared context
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


class MeshContext:
    """
    Shared context for agent collaboration
    
    This is the "hive mind" - a living knowledge graph
    that all agents read and write to.
    
    Uses Redis for:
    - Real-time pub/sub
    - Distributed state
    - Fast reads/writes
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.context_id = str(uuid.uuid4())
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        logger.info(f"🔗 Connected to mesh context: {self.context_id}")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("👋 Disconnected from mesh context")
    
    async def add_fact(self, key: str, value: Any, source: str):
        """Add a verified fact to shared knowledge"""
        fact_data = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "verified": False
        }
        
        await self.redis_client.hset(
            f"context:{self.context_id}:facts",
            key,
            json.dumps(fact_data)
        )
        
        # Broadcast fact addition
        await self.broadcast({
            "type": "fact_added",
            "key": key,
            "value": value,
            "source": source
        })
        
        logger.info(f"📝 Fact added: {key} = {value} (by {source})")
    
    async def get_fact(self, key: str) -> Optional[Dict]:
        """Get a fact from shared knowledge"""
        fact_json = await self.redis_client.hget(
            f"context:{self.context_id}:facts",
            key
        )
        
        if fact_json:
            return json.loads(fact_json)
        return None
    
    async def verify_fact(self, key: str, verifier: str):
        """Verify a fact (consensus mechanism)"""
        fact = await self.get_fact(key)
        if fact:
            fact["verified"] = True
            fact["verified_by"] = verifier
            
            await self.redis_client.hset(
                f"context:{self.context_id}:facts",
                key,
                json.dumps(fact)
            )
            
            logger.info(f"✅ Fact verified: {key} (by {verifier})")
    
    async def get_all_facts(self) -> Dict[str, Any]:
        """Get all shared facts"""
        facts_dict = await self.redis_client.hgetall(f"context:{self.context_id}:facts")
        return {k: json.loads(v) for k, v in facts_dict.items()}
    
    async def broadcast(self, event: Dict[str, Any]):
        """Broadcast event to all agents in mesh"""
        await self.redis_client.publish(
            f"mesh:{self.context_id}:events",
            json.dumps(event)
        )
    
    async def subscribe(self, callback: Callable):
        """Subscribe to mesh events"""
        await self.pubsub.subscribe(f"mesh:{self.context_id}:events")
        
        logger.info("📡 Subscribed to mesh events")
        
        # Listen for events
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                await callback(event)
    
    async def add_thread(self, thread_id: str, topic: str, participants: List[str]):
        """Create a conversation thread"""
        thread_data = {
            "id": thread_id,
            "topic": topic,
            "participants": participants,
            "messages": [],
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        await self.redis_client.hset(
            f"context:{self.context_id}:threads",
            thread_id,
            json.dumps(thread_data)
        )
    
    async def add_message_to_thread(self, thread_id: str, message: MeshMessage):
        """Add message to a thread"""
        thread_json = await self.redis_client.hget(
            f"context:{self.context_id}:threads",
            thread_id
        )
        
        if thread_json:
            thread = json.loads(thread_json)
            thread["messages"].append(message.to_dict())
            
            await self.redis_client.hset(
                f"context:{self.context_id}:threads",
                thread_id,
                json.dumps(thread)
            )


class MeshAgent:
    """
    Agent that participates in the mesh
    
    Key differences from traditional agents:
    - Doesn't wait for instructions
    - Monitors context actively
    - Contributes when it has value to add
    - Collaborates peer-to-peer
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        context: MeshContext,
        llm_endpoint: Optional[str] = None
    ):
        self.identity = identity
        self.context = context
        self.llm_endpoint = llm_endpoint
        self.active_collaborations: Set[str] = set()
        self.contribution_count = 0
        
        logger.info(f"🤖 Agent {identity.name} joined mesh")
    
    async def monitor_and_contribute(self):
        """
        Core agent behavior: Monitor context and contribute when relevant
        
        This is the "autonomous" part - agent decides when to act
        """
        logger.info(f"👀 {self.identity.name} monitoring mesh...")
        
        async def on_event(event: Dict[str, Any]):
            """Handle mesh events"""
            event_type = event.get("type")
            
            if event_type == "capability_query":
                # Someone asking "who can help with X?"
                await self._respond_to_capability_query(event)
            
            elif event_type == "proposal":
                # Someone proposed something
                await self._evaluate_proposal(event)
            
            elif event_type == "fact_added":
                # New fact added - check if relevant
                await self._process_new_fact(event)
            
            elif event_type == "question":
                # Someone asked a question
                await self._consider_answering(event)
        
        # Subscribe to mesh events
        await self.context.subscribe(on_event)
    
    async def _respond_to_capability_query(self, event: Dict[str, Any]):
        """Respond if we can help with the query"""
        query = event.get("query", "")
        
        # Check if we can handle this
        capability = self.identity.can_handle(query)
        
        if capability:
            # We can help! Respond with confidence
            response = {
                "type": "capability_response",
                "agent_id": self.identity.id,
                "agent_name": self.identity.name,
                "capability": capability.name,
                "confidence": capability.confidence,
                "cost": capability.cost,
                "latency": capability.latency
            }
            
            await self.context.broadcast(response)
            
            logger.info(
                f"🙋 {self.identity.name} offered help: "
                f"{capability.name} (confidence: {capability.confidence:.2f})"
            )
    
    async def _evaluate_proposal(self, event: Dict[str, Any]):
        """Evaluate if a proposal is good"""
        # In production: use LLM to evaluate
        # For now: simple heuristics
        
        proposal = event.get("content", "")
        from_agent = event.get("from_agent", "")
        
        # Don't evaluate our own proposals
        if from_agent == self.identity.id:
            return
        
        # Check if this relates to our capabilities
        for cap in self.identity.capabilities:
            if cap.name.lower() in proposal.lower():
                # Relevant to us - contribute
                await self._add_perspective(event, cap)
    
    async def _process_new_fact(self, event: Dict[str, Any]):
        """Process a new fact added to shared context"""
        key = event.get("key")
        value = event.get("value")
        
        # In production: verify facts using our knowledge
        # For now: just acknowledge
        logger.info(f"📖 {self.identity.name} noted fact: {key} = {value}")
    
    async def _consider_answering(self, event: Dict[str, Any]):
        """Consider answering a question"""
        question = event.get("content", "")
        
        # Check if question relates to our capabilities
        if self.identity.can_handle(question):
            # We can answer! Generate response
            answer = await self._generate_answer(question)
            
            # Share answer
            await self.context.broadcast({
                "type": "answer",
                "from_agent": self.identity.id,
                "question_id": event.get("id"),
                "content": answer
            })
    
    async def _add_perspective(self, proposal_event: Dict, capability: Capability):
        """Add our perspective to a proposal"""
        
        perspective = f"From {capability.name} perspective: "
        
        # In production: use LLM to generate perspective
        # For now: template
        perspective += "This looks promising, but we should also consider..."
        
        await self.context.broadcast({
            "type": "perspective",
            "from_agent": self.identity.id,
            "on_proposal": proposal_event.get("id"),
            "content": perspective,
            "capability": capability.name
        })
        
        self.contribution_count += 1
    
    async def _generate_answer(self, question: str) -> str:
        """Generate answer to a question"""
        # In production: call LLM
        # For now: simple template
        return f"Based on my {self.identity.capabilities[0].name} expertise: ..."
    
    async def propose(self, proposal: str, thread_id: Optional[str] = None):
        """Propose something to the mesh"""
        message = MeshMessage(
            id=str(uuid.uuid4()),
            type="proposal",
            from_agent=self.identity.id,
            to_agent=None,  # Broadcast
            content=proposal
        )
        
        await self.context.broadcast(message.to_dict())
        
        if thread_id:
            await self.context.add_message_to_thread(thread_id, message)
        
        logger.info(f"💡 {self.identity.name} proposed: {proposal[:100]}...")
    
    async def collaborate_with(self, other_agent_id: str, topic: str):
        """Start direct collaboration with another agent"""
        collab_id = f"{self.identity.id}_{other_agent_id}_{uuid.uuid4().hex[:8]}"
        
        self.active_collaborations.add(collab_id)
        
        # Create thread for this collaboration
        await self.context.add_thread(
            thread_id=collab_id,
            topic=topic,
            participants=[self.identity.id, other_agent_id]
        )
        
        logger.info(
            f"🤝 {self.identity.name} started collaboration: {collab_id}"
        )
        
        return collab_id


class MeshNetwork:
    """
    The mesh network itself - manages agent discovery and coordination
    
    This is NOT an orchestrator - it's just infrastructure
    Agents self-organize; the network just provides communication
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.context = MeshContext(redis_url)
        self.agents: Dict[str, MeshAgent] = {}
        self.running = False
    
    async def start(self):
        """Start the mesh network"""
        await self.context.connect()
        self.running = True
        logger.info("🌐 Mesh network started")
    
    async def stop(self):
        """Stop the mesh network"""
        self.running = False
        await self.context.disconnect()
        logger.info("🛑 Mesh network stopped")
    
    async def register_agent(self, agent: MeshAgent):
        """Register an agent to the mesh"""
        self.agents[agent.identity.id] = agent
        
        # Announce to network
        await self.context.broadcast({
            "type": "agent_joined",
            "agent_id": agent.identity.id,
            "agent_name": agent.identity.name,
            "capabilities": [cap.name for cap in agent.identity.capabilities]
        })
        
        logger.info(f"✅ Registered {agent.identity.name} to mesh")
    
    async def query_capabilities(self, query: str, timeout: float = 2.0) -> List[Dict]:
        """Query mesh for agents with specific capabilities"""
        
        responses = []
        
        # Broadcast capability query
        await self.context.broadcast({
            "type": "capability_query",
            "query": query,
            "query_id": str(uuid.uuid4())
        })
        
        # Collect responses (in production: listen to pubsub)
        # For now: direct check
        for agent in self.agents.values():
            cap = agent.identity.can_handle(query)
            if cap:
                responses.append({
                    "agent_id": agent.identity.id,
                    "agent_name": agent.identity.name,
                    "capability": cap.name,
                    "confidence": cap.confidence
                })
        
        # Sort by confidence
        responses.sort(key=lambda x: x["confidence"], reverse=True)
        
        return responses
    
    async def execute_collaborative_task(
        self,
        task: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Execute a task using mesh collaboration
        
        Key: NO orchestration - agents self-organize!
        """
        logger.info(f"🎯 Collaborative task: {task}")
        
        # 1. Query for capable agents
        capable_agents = await self.query_capabilities(task)
        logger.info(f"   Found {len(capable_agents)} capable agents")
        
        # 2. Let them know about the task
        task_id = str(uuid.uuid4())
        await self.context.broadcast({
            "type": "task_announced",
            "task_id": task_id,
            "task": task,
            "capable_agents": capable_agents
        })
        
        # 3. Create shared thread for this task
        await self.context.add_thread(
            thread_id=task_id,
            topic=task,
            participants=[a["agent_id"] for a in capable_agents]
        )
        
        # 4. Wait for emergence (agents will self-organize)
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check if task is complete
            # In production: agents signal completion
            # For now: wait for timeout
            await asyncio.sleep(1)
        
        # 5. Gather results from shared context
        facts = await self.context.get_all_facts()
        
        return {
            "task_id": task_id,
            "task": task,
            "participating_agents": capable_agents,
            "shared_facts": facts,
            "duration": (datetime.now() - start_time).total_seconds()
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        print("\n" + "="*70)
        print("🌐 AGENT MESH PROTOCOL DEMO")
        print("="*70)
        
        # Create mesh network
        mesh = MeshNetwork()
        await mesh.start()
        
        # Create agents with different capabilities
        agents_config = [
            {
                "name": "ResearchAgent",
                "capabilities": [
                    Capability("research", "Find information online", 0.9),
                    Capability("fact_check", "Verify facts", 0.85)
                ]
            },
            {
                "name": "CodeAgent",
                "capabilities": [
                    Capability("code_generation", "Generate code", 0.92),
                    Capability("code_review", "Review code quality", 0.88)
                ]
            },
            {
                "name": "WriterAgent",
                "capabilities": [
                    Capability("writing", "Write clear documentation", 0.90),
                    Capability("summarization", "Summarize content", 0.87)
                ]
            }
        ]
        
        # Create and register agents
        agents = []
        for config in agents_config:
            identity = AgentIdentity(
                id=str(uuid.uuid4()),
                name=config["name"],
                endpoint=f"http://localhost:8000/{config['name'].lower()}",
                capabilities=config["capabilities"]
            )
            
            agent = MeshAgent(identity, mesh.context)
            await mesh.register_agent(agent)
            agents.append(agent)
        
        print(f"\n✅ {len(agents)} agents joined the mesh")
        
        # Start agents monitoring
        print("\n👀 Agents now monitoring mesh autonomously...")
        
        # Execute collaborative task
        print("\n" + "="*70)
        print("🎯 COLLABORATIVE TASK")
        print("="*70)
        
        result = await mesh.execute_collaborative_task(
            "Build a simple REST API for a todo app with documentation",
            timeout=5.0
        )
        
        print(f"\n✅ Task completed!")
        print(f"   Participating agents: {len(result['participating_agents'])}")
        for agent_info in result['participating_agents']:
            print(f"      - {agent_info['agent_name']}: {agent_info['capability']} ({agent_info['confidence']:.2f})")
        
        # Cleanup
        await mesh.stop()
        
        print("\n" + "="*70)
        print("🎉 Demo complete!")
        print("="*70)
    
    asyncio.run(demo())
