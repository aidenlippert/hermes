# 🔗 Integrating Mesh Protocol with Existing Hermes

This document explains how to **evolve the current Hermes system** into the full Mesh Protocol implementation.

---

## Current State Analysis

### What Hermes Has Today ✅

1. **Backend (FastAPI)**
   - SQLAlchemy ORM with Postgres
   - JWT authentication
   - WebSocket manager for real-time updates
   - A2A protocol client
   - Agent registry (in-memory)
   - Conductor (IntentParser → WorkflowPlanner → Executor)

2. **Frontend (Next.js 14)**
   - React with TypeScript
   - Zustand state management
   - Real-time WebSocket integration
   - Auth pages (login/register)
   - Chat interface

3. **Agent System**
   - Base A2A agent class
   - Flight agent (Amadeus API)
   - Hotel agent (basic)
   - Restaurant agent (Foursquare API)

4. **Infrastructure**
   - Railway deployment ready
   - Vercel deployment ready
   - Postgres database (8 tables)
   - Redis for caching

### What Mesh Protocol Adds 🚀

1. **Decentralized Architecture**
   - NATS JetStream event bus (replaces centralized conductor)
   - Peer-to-peer agent communication
   - Semantic capability discovery (vector embeddings)

2. **Economic Layer**
   - Bidding and auction system
   - Escrow and settlement
   - Reputation tracking

3. **Advanced Identity**
   - DID-based authentication (beyond JWT)
   - Cryptographic message signing (ed25519)
   - Verifiable credentials

4. **Protocol Standardization**
   - Protocol buffer definitions
   - Canonical message formats
   - Versioned API

---

## Migration Strategy

### Phase 1: Hybrid Mode (Weeks 1-4)

**Goal:** Mesh runs alongside existing conductor

```
┌─────────────────────────────────────────┐
│         Hermes Backend (FastAPI)        │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐    ┌───────────────┐ │
│  │  Legacy      │    │  Mesh         │ │
│  │  Conductor   │    │  Integration  │ │
│  │  (existing)  │    │  (new)        │ │
│  └──────────────┘    └───────────────┘ │
│         │                    │          │
│         ↓                    ↓          │
│    Sequential           Parallel        │
│    Execution           Collaboration    │
└─────────────────────────────────────────┘
```

**Implementation:**

```python
# backend/services/hybrid_conductor.py

from hermes.conductor.executor import Executor
from hermes.mesh.protocol import MeshNetwork

class HybridConductor:
    """Conductor that uses mesh for complex tasks, legacy for simple ones"""
    
    def __init__(self):
        self.legacy_executor = Executor()
        self.mesh = MeshNetwork(redis_url=os.getenv("REDIS_URL"))
        self.complexity_threshold = 0.7  # Tunable
    
    async def execute(self, task: str, user_id: str):
        """Route to appropriate execution engine"""
        
        # Analyze task complexity
        complexity = await self._analyze_complexity(task)
        
        if complexity < self.complexity_threshold:
            # Simple task → use legacy sequential executor
            logger.info(f"Using legacy executor (complexity: {complexity:.2f})")
            return await self.legacy_executor.execute(task)
        
        else:
            # Complex task → use mesh collaboration
            logger.info(f"Using mesh protocol (complexity: {complexity:.2f})")
            return await self.mesh.execute_collaborative_task(task)
    
    async def _analyze_complexity(self, task: str) -> float:
        """Estimate task complexity (0.0 to 1.0)"""
        
        # Heuristics:
        # - Multiple intents = higher complexity
        # - Multiple domains (flight + hotel + restaurant) = higher
        # - Constraints/preferences = higher
        # - Simple queries = lower
        
        task_lower = task.lower()
        
        # Count domain mentions
        domains = ["flight", "hotel", "restaurant", "event", "car", "activity"]
        domain_count = sum(1 for d in domains if d in task_lower)
        
        # Check for multi-step indicators
        multi_step_words = ["then", "also", "and", "plus", "after", "before"]
        has_multi_step = any(word in task_lower for word in multi_step_words)
        
        # Calculate complexity score
        base_complexity = min(domain_count / 3.0, 1.0)  # 3+ domains = max
        multi_step_bonus = 0.3 if has_multi_step else 0.0
        
        return min(base_complexity + multi_step_bonus, 1.0)
```

**Update main.py:**

```python
# backend/main.py

from backend.services.hybrid_conductor import HybridConductor

# Replace existing conductor
# conductor = Conductor()  # OLD
conductor = HybridConductor()  # NEW

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async for data in websocket.receive_json():
        user_message = data["message"]
        
        # Route through hybrid conductor
        result = await conductor.execute(user_message, user_id="demo")
        
        # Stream back to user
        await websocket.send_json({
            "type": "result",
            "content": result
        })
```

**Testing:**

```bash
# Simple task (should use legacy)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find flights to NYC"}'
# → Uses Executor (sequential)

# Complex task (should use mesh)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a 3-day trip to SF: flights, hotel near MOMA, Italian restaurant, and tickets to a Giants game"}'
# → Uses MeshNetwork (parallel collaboration)
```

### Phase 2: Mesh Integration (Weeks 5-8)

**Goal:** Full mesh capabilities integrated

**Add NATS to docker-compose.yml:**

```yaml
# docker-compose.yml

services:
  nats:
    image: nats:latest
    command: ["-js"]
    ports:
      - "4222:4222"  # Client connections
      - "8222:8222"  # HTTP management
    volumes:
      - nats-data:/data
    environment:
      - NATS_JETSTREAM_MAX_MEM=1G

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant-data:/qdrant/storage

volumes:
  nats-data:
  qdrant-data:
```

**Create Mesh Services:**

```
backend/
  mesh/
    __init__.py
    discovery.py      # Agent registry with vector search
    contracts.py      # Contract lifecycle management
    marketplace.py    # Bidding and auction
    reputation.py     # Reputation scoring
    eventbus.py       # NATS integration
```

**Update Agent Registration:**

```python
# backend/api/v1_agents.py (NEW FILE)

from fastapi import APIRouter, HTTPException
from backend.mesh.discovery import DiscoveryService

router = APIRouter()
discovery = DiscoveryService()

@router.post("/register")
async def register_agent(agent: AgentRegistration):
    """
    Register agent to mesh network
    
    This endpoint accepts A2A-compliant agents AND mesh-native agents
    """
    
    # Verify signature
    valid = await verify_signature(agent.dict(), agent.owner_signature)
    if not valid:
        raise HTTPException(401, "Invalid signature")
    
    # Register in discovery service
    agent_id = await discovery.register(agent)
    
    # Generate embeddings for capabilities
    for capability in agent.capabilities:
        embedding = await generate_embedding(capability.description)
        await discovery.index_capability(agent_id, capability, embedding)
    
    return {"ok": True, "agent_id": agent_id}
```

**Connect to NATS:**

```python
# backend/mesh/eventbus.py

import nats
from nats.js import JetStreamContext

class MeshEventBus:
    """NATS JetStream integration for mesh protocol"""
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.js = None
    
    async def connect(self):
        """Connect to NATS"""
        self.nc = await nats.connect(self.nats_url)
        self.js: JetStreamContext = self.nc.jetstream()
        
        # Create streams if they don't exist
        await self._create_streams()
    
    async def _create_streams(self):
        """Create required JetStream streams"""
        
        # Announcements stream
        try:
            await self.js.add_stream(
                name="announcements",
                subjects=["announcements.>"]
            )
        except Exception as e:
            logger.info(f"Stream 'announcements' already exists: {e}")
        
        # Bids stream
        try:
            await self.js.add_stream(
                name="bids",
                subjects=["bids.>"]
            )
        except Exception as e:
            logger.info(f"Stream 'bids' already exists: {e}")
    
    async def announce_contract(self, contract: TaskContract):
        """Announce contract to mesh"""
        
        subject = f"announcements.intent.{contract.intent}"
        
        await self.js.publish(
            subject,
            contract.json().encode()
        )
        
        logger.info(f"📢 Announced contract {contract.contract_id} on {subject}")
    
    async def subscribe_to_announcements(self, callback):
        """Subscribe to contract announcements"""
        
        async def message_handler(msg):
            contract_data = msg.data.decode()
            contract = TaskContract.parse_raw(contract_data)
            await callback(contract)
        
        await self.nc.subscribe("announcements.>", cb=message_handler)
```

**Update Existing Agents:**

```python
# backend/agents/flight_agent_mesh.py

from backend.mesh.eventbus import MeshEventBus
from backend.mesh.contracts import ContractManager

class FlightAgentMesh:
    """Flight agent that participates in mesh network"""
    
    def __init__(self):
        self.eventbus = MeshEventBus()
        self.contracts = ContractManager()
        self.agent_id = "did:web:hermes.network:agents:flight"
    
    async def start(self):
        """Start listening for contracts"""
        
        await self.eventbus.connect()
        
        # Subscribe to flight-related announcements
        await self.eventbus.subscribe_to_announcements(
            self._on_contract_announced
        )
        
        logger.info("✈️ Flight agent monitoring mesh...")
    
    async def _on_contract_announced(self, contract: TaskContract):
        """Handle contract announcement"""
        
        # Check if we can handle this
        if contract.intent in ["flight_search", "flight_book"]:
            
            # Submit bid
            bid = Bid(
                bid_id=str(uuid.uuid4()),
                contract_id=contract.contract_id,
                agent_id=self.agent_id,
                price=2.50,
                eta_seconds=5.0,
                confidence=0.92,
                notes="Using Amadeus API for real-time flight data"
            )
            
            await self.contracts.submit_bid(bid)
            
            logger.info(f"🙋 Submitted bid for {contract.contract_id}")
```

**Deliverables:**
- [ ] NATS running locally and in Railway
- [ ] All agents converted to mesh-native
- [ ] Semantic capability search working
- [ ] Contracts announced via NATS instead of direct calls

### Phase 3: Full Migration (Weeks 9-12)

**Goal:** Legacy conductor removed, 100% mesh-native

**Remove Legacy Code:**

```python
# backend/services/conductor.py → DEPRECATED
# backend/conductor/executor.py → DEPRECATED
# backend/conductor/planner.py → DEPRECATED (mesh uses distributed planning)
```

**New Architecture:**

```python
# backend/main.py

from backend.mesh.network import MeshNetwork

mesh = MeshNetwork()

@app.on_event("startup")
async def startup():
    # Initialize mesh
    await mesh.start()
    
    # Register internal agents
    await mesh.register_agent(FlightAgentMesh())
    await mesh.register_agent(HotelAgentMesh())
    await mesh.register_agent(RestaurantAgentMesh())
    
    logger.info("🌐 Mesh network initialized")

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async for data in websocket.receive_json():
        user_message = data["message"]
        
        # Execute via mesh (agents self-organize)
        result = await mesh.execute_collaborative_task(
            task=user_message,
            timeout=30.0
        )
        
        # Stream results
        await websocket.send_json({
            "type": "result",
            "content": result
        })
```

**Deliverables:**
- [ ] No legacy conductor code remaining
- [ ] All tasks executed via mesh
- [ ] Performance metrics: 3x faster for multi-agent tasks
- [ ] External agents can register and participate

---

## Database Migration

### Add Mesh-Specific Tables

```sql
-- Run this migration

-- Contracts table (mesh-native)
CREATE TABLE mesh_contracts (
  contract_id TEXT PRIMARY KEY,
  issuer TEXT NOT NULL,
  intent TEXT NOT NULL,
  context JSONB NOT NULL,
  constraints TEXT[],
  deliverables JSONB,
  validator JSONB,
  reward JSONB,
  status TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  awarded_to TEXT[],
  protocol_version TEXT DEFAULT 'mesh-proto/0.1',
  nonce TEXT,
  issuer_signature TEXT
);

-- Bids table
CREATE TABLE mesh_bids (
  bid_id TEXT PRIMARY KEY,
  contract_id TEXT REFERENCES mesh_contracts(contract_id),
  agent_id TEXT NOT NULL,
  price DECIMAL NOT NULL,
  currency TEXT DEFAULT 'USD',
  eta_seconds DECIMAL NOT NULL,
  confidence DECIMAL NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  stake DECIMAL,
  agent_signature TEXT
);

-- Reputation events
CREATE TABLE reputation_events (
  id SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  contract_id TEXT,
  impact DECIMAL NOT NULL,
  reason TEXT,
  reporter TEXT,
  occurred_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_contracts_status ON mesh_contracts(status);
CREATE INDEX idx_contracts_intent ON mesh_contracts(intent);
CREATE INDEX idx_bids_contract ON mesh_bids(contract_id);
CREATE INDEX idx_reputation_agent ON reputation_events(agent_id);
```

### Migrate Existing Data

```python
# scripts/migrate_to_mesh.py

async def migrate():
    """Migrate existing agent registry to mesh format"""
    
    # Get all agents from old in-memory registry
    old_agents = agent_registry.get_all()
    
    for old_agent in old_agents:
        # Convert to mesh format
        mesh_agent = AgentRegistration(
            agent_id=f"did:web:hermes.network:agents:{old_agent['id']}",
            owner="did:web:hermes.network",  # System-owned
            name=old_agent["name"],
            capabilities=[
                Capability(
                    name=cap["name"],
                    description=cap["description"],
                    confidence=0.85,
                    cost=cap.get("cost", 1.0),
                    latency=cap.get("latency", 3.0)
                )
                for cap in old_agent.get("capabilities", [])
            ],
            endpoint=old_agent["endpoint"],
            public_key=generate_key_pair()[1],  # Generate new keys
        )
        
        # Register in mesh
        await discovery.register(mesh_agent)
    
    logger.info(f"Migrated {len(old_agents)} agents to mesh")
```

---

## Frontend Updates

### Add Mesh Event Visualization

```typescript
// frontend/components/MeshEventTimeline.tsx

export function MeshEventTimeline() {
  const [events, setEvents] = useState<MeshEvent[]>([]);
  
  useEffect(() => {
    // Connect to mesh WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/mesh');
    
    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data);
      
      setEvents(prev => [...prev, {
        ...event,
        timestamp: new Date()
      }]);
    };
    
    return () => ws.close();
  }, []);
  
  return (
    <div className="mesh-timeline">
      <h3>Mesh Network Activity</h3>
      
      {events.map((event, i) => (
        <div key={i} className={`event event-${event.type}`}>
          <div className="timestamp">
            {event.timestamp.toLocaleTimeString()}
          </div>
          
          <div className="type">
            {event.type === 'contract_announced' && '📢 Contract Announced'}
            {event.type === 'bid_submitted' && '🙋 Bid Submitted'}
            {event.type === 'contract_awarded' && '🏆 Contract Awarded'}
            {event.type === 'agent_joined' && '🤖 Agent Joined'}
          </div>
          
          <div className="details">
            <pre>{JSON.stringify(event.payload, null, 2)}</pre>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Add to Chat Page

```typescript
// frontend/app/chat/page.tsx

export default function ChatPage() {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2">
        <ChatInterface />
      </div>
      
      <div className="col-span-1">
        <MeshEventTimeline />
      </div>
    </div>
  );
}
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_mesh_discovery.py

async def test_semantic_capability_search():
    discovery = DiscoveryService()
    
    # Register agent with capability
    await discovery.register(AgentRegistration(
        agent_id="test-agent",
        capabilities=[
            Capability(
                name="hotel_search",
                description="Find hotels by location, dates, and price range"
            )
        ]
    ))
    
    # Search with similar query
    results = await discovery.search_capabilities(
        "I need a place to stay in San Francisco"
    )
    
    assert len(results) > 0
    assert results[0].agent_id == "test-agent"
    assert results[0].similarity > 0.7
```

### Integration Tests

```python
# tests/test_mesh_e2e.py

async def test_full_contract_lifecycle():
    mesh = MeshNetwork()
    await mesh.start()
    
    # Register test agent
    agent = TestFlightAgent()
    await mesh.register_agent(agent)
    
    # Announce contract
    contract = TaskContract(
        contract_id="test-001",
        intent="flight_search",
        context={"origin": "SFO", "destination": "JFK"}
    )
    
    result = await mesh.execute_collaborative_task(contract)
    
    assert result["status"] == "SETTLED"
    assert len(result["deliverables"]) > 0
```

---

## Deployment Updates

### Railway Configuration

```yaml
# railway.json

{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  },
  "services": [
    {
      "name": "backend",
      "plan": "pro"
    },
    {
      "name": "nats",
      "image": "nats:latest",
      "command": ["-js", "-m", "8222"],
      "plan": "starter"
    },
    {
      "name": "qdrant",
      "image": "qdrant/qdrant",
      "plan": "starter"
    }
  ]
}
```

### Environment Variables

```bash
# .env.production (Railway)

# Existing
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
GOOGLE_API_KEY=...

# New for Mesh
NATS_URL=nats://nats.railway.internal:4222
QDRANT_URL=http://qdrant.railway.internal:6333
MESH_MODE=enabled
MESH_PROTOCOL_VERSION=0.1.0

# Feature flags
USE_HYBRID_CONDUCTOR=true  # Phase 1
USE_FULL_MESH=false        # Phase 3
```

---

## Rollout Plan

### Week 1-2: Preparation
- [ ] Deploy NATS + Qdrant to Railway staging environment
- [ ] Test mesh services locally
- [ ] Create migration scripts

### Week 3-4: Hybrid Mode
- [ ] Deploy HybridConductor to production
- [ ] Monitor complexity routing
- [ ] Collect metrics (% mesh vs legacy)

### Week 5-6: Gradual Migration
- [ ] Lower complexity threshold (more tasks use mesh)
- [ ] Monitor performance and reliability
- [ ] Fix bugs

### Week 7-8: Full Mesh
- [ ] Set USE_FULL_MESH=true
- [ ] Remove legacy conductor
- [ ] Monitor for 1 week

### Week 9-12: Optimization
- [ ] Tune auction strategies
- [ ] Optimize vector search
- [ ] Add more domain agents

---

## Success Criteria

✅ **Phase 1 Complete When:**
- Hybrid conductor routes tasks correctly
- At least 50% of complex tasks use mesh
- No regressions in simple task performance

✅ **Phase 2 Complete When:**
- All agents are mesh-native
- External agents can register successfully
- Semantic search works better than keyword matching

✅ **Phase 3 Complete When:**
- Legacy conductor code removed
- 100% of tasks use mesh
- 3x performance improvement for multi-agent tasks
- 10+ external agents registered

---

## Questions & Answers

**Q: Will this break existing functionality?**
A: No! Hybrid mode ensures backwards compatibility. Legacy conductor remains until mesh is proven.

**Q: How long will migration take?**
A: 8-12 weeks for full migration. Hybrid mode can run indefinitely if needed.

**Q: What if mesh fails?**
A: Fallback to legacy conductor is built-in. We can toggle with USE_FULL_MESH flag.

**Q: Do we need to rewrite all agents?**
A: No. Agents just need to implement mesh interface (listen to NATS, submit bids). Core logic stays same.

**Q: What about costs?**
A: NATS + Qdrant add ~$50/month to Railway bill. Offset by performance gains (3x faster = less compute time).

---

**Ready to start? Next step: Install NATS locally and test basic pub/sub!** 🚀
