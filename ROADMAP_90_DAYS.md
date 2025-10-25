# 🚀 MESH PROTOCOL - 90 DAY ROADMAP

**Goal:** Launch the Agent Communication and Coordination Protocol (ACCP) as production infrastructure for the post-human internet.

**Status:** Specification complete, implementation beginning  
**Started:** October 25, 2025  
**Target Launch:** January 23, 2026

---

## ✅ COMPLETED (Week 0)

### Protocol Design
- [x] **mesh-protocol-v0.1.proto** - Complete protocol buffer definitions
  - TaskContract, AgentRegistration, Bid, ContractStatus
  - Capability, Reputation, MeshEvent
  - 18 message types covering full lifecycle

- [x] **MESH_PROTOCOL_SPEC.md** - Comprehensive specification
  - Architecture overview (8-layer stack)
  - Message flows (registration → announcement → bidding → award → validation → settlement)
  - Canonical signing (ed25519 + nonce + expiry)
  - Semantic discovery (vector embeddings)
  - Auction strategies (lowest_price, reputation_weighted, multi_criteria)
  - Security (replay protection, DIDs, sandboxing)
  - Compliance (HIPAA, GDPR)

- [x] **DOMAIN_AGENTS.md** - Concrete agent specifications
  - Travel (flight, hotel, travel planner)
  - Food (restaurant discovery, reservations)
  - Health (primary care, dentist, specialist referral)
  - Professional services (legal, real estate)
  - Commerce (purchase agent, subscription manager)
  - Home (maintenance, smart home)
  - Meta agents (registry, reputation, validator, sandbox)

- [x] **Proof-of-Concept** - Working mesh demo
  - `demo_mesh.py` - 4 autonomous agents self-organizing
  - In-memory shared context
  - Event-driven collaboration
  - Capability-based discovery
  - **Result:** Agents autonomously joined tasks, added facts, collaborated without orchestrator

---

## 📅 WEEK 1-2: Infrastructure Setup

**Focus:** Local development environment + event bus

### Day 1-2: NATS JetStream Setup
```bash
# Install NATS server
docker run -d --name nats -p 4222:4222 -p 8222:8222 nats:latest -js

# Test basic pub/sub
nats pub test.subject "Hello World"
nats sub test.subject
```

**Deliverables:**
- [ ] NATS running locally
- [ ] Created streams: `announcements`, `bids`, `contracts`, `status`
- [ ] Topic structure implemented:
  - `announcements.intent.<intent>` (e.g., `announcements.intent.hotel_search`)
  - `bids.contract.<contract_id>`
  - `contract.<contract_id>.updates`
  - `agents.lifecycle` (join/leave events)

### Day 3-4: Database Setup
```bash
# PostgreSQL for structured data
docker run -d --name postgres \
  -e POSTGRES_DB=mesh \
  -e POSTGRES_USER=mesh \
  -e POSTGRES_PASSWORD=dev \
  -p 5432:5432 postgres:15

# Qdrant for vector embeddings
docker run -d --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Redis for session store
docker run -d --name redis -p 6379:6379 redis:alpine
```

**Deliverables:**
- [ ] Postgres schema created:
  ```sql
  CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    public_key TEXT NOT NULL,
    trust_score FLOAT DEFAULT 1.0,
    registered_at TIMESTAMP DEFAULT NOW(),
    meta JSONB
  );

  CREATE TABLE capabilities (
    id SERIAL PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    cost FLOAT DEFAULT 0,
    latency FLOAT DEFAULT 0,
    embedding_id TEXT -- reference to Qdrant
  );

  CREATE TABLE contracts (
    contract_id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    intent TEXT NOT NULL,
    context JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    awarded_to TEXT[],
    protocol_version TEXT DEFAULT 'mesh-proto/0.1'
  );

  CREATE TABLE bids (
    bid_id TEXT PRIMARY KEY,
    contract_id TEXT REFERENCES contracts(contract_id),
    agent_id TEXT REFERENCES agents(agent_id),
    price FLOAT NOT NULL,
    eta_seconds FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
  );

  CREATE TABLE reputation (
    agent_id TEXT PRIMARY KEY REFERENCES agents(agent_id),
    overall_score FLOAT DEFAULT 1.0,
    contracts_completed INT DEFAULT 0,
    contracts_failed INT DEFAULT 0,
    avg_rating FLOAT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
  );
  ```

- [ ] Qdrant collection created:
  ```python
  from qdrant_client import QdrantClient
  from qdrant_client.models import Distance, VectorParams

  client = QdrantClient("localhost", port=6333)

  client.create_collection(
    collection_name="capabilities",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
  )

  client.create_collection(
    collection_name="contracts",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
  )
  ```

### Day 5-7: Event Bus Proxy Service

**File:** `services/eventbus-proxy/src/index.ts`

```typescript
import express from 'express';
import WebSocket from 'ws';
import { connect, StringCodec } from 'nats';

const app = express();
const wss = new WebSocket.Server({ port: 8080 });

// Connect to NATS
const nc = await connect({ servers: 'localhost:4222' });
const sc = StringCodec();

// WebSocket → NATS bridge
wss.on('connection', (ws) => {
  console.log('Client connected');
  
  ws.on('message', async (data) => {
    const message = JSON.parse(data.toString());
    
    // Publish to appropriate NATS topic
    if (message.type === 'announce_contract') {
      const subject = `announcements.intent.${message.contract.intent}`;
      nc.publish(subject, sc.encode(JSON.stringify(message)));
    }
    else if (message.type === 'submit_bid') {
      const subject = `bids.contract.${message.bid.contract_id}`;
      nc.publish(subject, sc.encode(JSON.stringify(message)));
    }
  });
  
  // NATS → WebSocket bridge
  const sub = nc.subscribe('announcements.*');
  (async () => {
    for await (const msg of sub) {
      ws.send(sc.decode(msg.data));
    }
  })();
});

app.listen(3000);
```

**Deliverables:**
- [ ] WebSocket server running on port 8080
- [ ] Bridges WebSocket ↔ NATS bidirectionally
- [ ] Handles: contract announcements, bids, status updates
- [ ] Validates message signatures before forwarding

---

## 📅 WEEK 3-4: Core Services

### Discovery Service

**File:** `services/discovery/src/index.ts`

```typescript
import express from 'express';
import { Pool } from 'pg';
import { QdrantClient } from '@qdrant/js-client-rest';
import { pipeline } from '@xenova/transformers';

const app = express();
const db = new Pool({ connectionString: process.env.DATABASE_URL });
const qdrant = new QdrantClient({ url: 'http://localhost:6333' });

// Load embedding model
const embedder = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');

// POST /v1/agents - Register agent
app.post('/v1/agents', async (req, res) => {
  const { agent_id, capabilities, public_key, owner_signature } = req.body;
  
  // Verify signature
  const valid = await verifySignature(req.body, public_key, owner_signature);
  if (!valid) return res.status(401).json({ error: 'Invalid signature' });
  
  // Insert agent
  await db.query(
    'INSERT INTO agents (agent_id, owner, name, endpoint, public_key) VALUES ($1, $2, $3, $4, $5)',
    [agent_id, req.body.owner, req.body.name, req.body.endpoint, public_key]
  );
  
  // Insert capabilities with embeddings
  for (const cap of capabilities) {
    // Generate embedding
    const embedding = await embedder(cap.description, { pooling: 'mean', normalize: true });
    const embeddingArray = Array.from(embedding.data);
    
    // Store in Qdrant
    const embeddingId = `${agent_id}:${cap.name}`;
    await qdrant.upsert('capabilities', {
      points: [{
        id: embeddingId,
        vector: embeddingArray,
        payload: { agent_id, capability: cap }
      }]
    });
    
    // Store in Postgres
    await db.query(
      'INSERT INTO capabilities (agent_id, name, description, confidence, cost, latency, embedding_id) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [agent_id, cap.name, cap.description, cap.confidence, cap.cost, cap.latency, embeddingId]
    );
  }
  
  res.json({ ok: true, agent_id });
});

// GET /v1/agents?capability=hotel_search - Discover agents
app.get('/v1/agents', async (req, res) => {
  const query = req.query.capability as string;
  
  // Generate query embedding
  const queryEmbedding = await embedder(query, { pooling: 'mean', normalize: true });
  
  // Search Qdrant
  const results = await qdrant.search('capabilities', {
    vector: Array.from(queryEmbedding.data),
    limit: 10,
    score_threshold: 0.7
  });
  
  res.json({
    matches: results.map(r => ({
      agent_id: r.payload.agent_id,
      capability: r.payload.capability,
      similarity: r.score
    }))
  });
});
```

**Deliverables:**
- [ ] Agent registration endpoint working
- [ ] Semantic capability search using Qdrant
- [ ] Signature verification implemented
- [ ] 10+ test agents registered

### Contract Manager Service

**File:** `services/contract-manager/src/index.ts`

```typescript
import express from 'express';
import { Pool } from 'pg';
import { connect } from 'nats';

const app = express();
const db = new Pool({ connectionString: process.env.DATABASE_URL });
const nc = await connect({ servers: process.env.NATS_URL });

// POST /v1/contracts - Create contract
app.post('/v1/contracts', async (req, res) => {
  const contract = req.body;
  
  // Verify issuer signature
  const valid = await verifySignature(contract, contract.issuer_signature);
  if (!valid) return res.status(401).json({ error: 'Invalid signature' });
  
  // Insert contract
  await db.query(
    'INSERT INTO contracts (contract_id, issuer, intent, context, status, expires_at) VALUES ($1, $2, $3, $4, $5, $6)',
    [contract.contract_id, contract.issuer, contract.intent, contract.context, 'OPEN', contract.expires_at]
  );
  
  // Publish announcement to NATS
  nc.publish(`announcements.intent.${contract.intent}`, JSON.stringify({
    contract_id: contract.contract_id,
    intent: contract.intent,
    context: contract.context
  }));
  
  res.status(201).json({ ok: true, contract_id: contract.contract_id });
});

// GET /v1/contracts/:id - Get contract
app.get('/v1/contracts/:id', async (req, res) => {
  const result = await db.query('SELECT * FROM contracts WHERE contract_id = $1', [req.params.id]);
  res.json(result.rows[0]);
});

// Contract state machine
async function transitionContract(contractId: string, newStatus: string) {
  await db.query('UPDATE contracts SET status = $1 WHERE contract_id = $2', [newStatus, contractId]);
  
  // Publish state change event
  nc.publish(`contract.${contractId}.status`, JSON.stringify({
    contract_id: contractId,
    status: newStatus,
    timestamp: new Date().toISOString()
  }));
}
```

**Deliverables:**
- [ ] Contract CRUD endpoints working
- [ ] State machine transitions (OPEN → BIDDING → AWARDED → IN_PROGRESS → VALIDATED → SETTLED)
- [ ] NATS event publishing on state changes
- [ ] Integration tests passing

---

## 📅 WEEK 5-6: SDK & Sample Agents

### mesh-js SDK

**File:** `sdk/js/src/index.ts`

```typescript
import WebSocket from 'ws';
import { sign, verify } from '@noble/ed25519';
import canonicalize from 'canonicalize';

export class MeshClient {
  private ws: WebSocket;
  private did: string;
  private privateKey: Uint8Array;
  
  constructor({ did, privateKey, meshUrl }: MeshClientOptions) {
    this.did = did;
    this.privateKey = privateKey;
    this.ws = new WebSocket(meshUrl);
  }
  
  async registerAgent(descriptor: AgentDescriptor) {
    const message = {
      agent_id: this.did,
      ...descriptor,
      registered_at: new Date().toISOString()
    };
    
    const signed = await this.sign(message);
    
    // Send to discovery service via WebSocket
    this.ws.send(JSON.stringify({
      type: 'register_agent',
      payload: signed
    }));
  }
  
  on(event: string, handler: (data: any) => void) {
    this.ws.on('message', (data) => {
      const message = JSON.parse(data.toString());
      if (message.type === event) {
        handler(message.payload);
      }
    });
  }
  
  async announceContract(contract: TaskContract) {
    const signed = await this.sign(contract);
    
    this.ws.send(JSON.stringify({
      type: 'announce_contract',
      contract: signed
    }));
  }
  
  async submitBid(bid: Bid) {
    const signed = await this.sign(bid);
    
    this.ws.send(JSON.stringify({
      type: 'submit_bid',
      bid: signed
    }));
  }
  
  private async sign(message: any): Promise<SignedMessage> {
    const envelope = {
      ...message,
      nonce: crypto.randomUUID(),
      expires_at: Date.now() + 300000 // 5 minutes
    };
    
    const canonical = canonicalize(envelope);
    const signature = await sign(new TextEncoder().encode(canonical), this.privateKey);
    
    return {
      ...envelope,
      signature: Buffer.from(signature).toString('base64')
    };
  }
}
```

**Publish:**
```bash
cd sdk/js
npm publish --access public
# @mesh-protocol/sdk@0.1.0
```

### Sample Hotel Agent

**File:** `examples/hotel-agent/index.ts`

```typescript
import { MeshClient } from '@mesh-protocol/sdk';
import axios from 'axios';

const client = new MeshClient({
  did: 'did:key:hotel-bot-1',
  privateKey: loadPrivateKey(),
  meshUrl: 'ws://localhost:8080'
});

// Register capabilities
await client.registerAgent({
  name: 'HotelBot',
  capabilities: [
    {
      name: 'hotel_search',
      description: 'Search hotels by location, dates, and price',
      confidence: 0.92,
      cost: 2.0,
      latency: 3.0
    }
  ],
  endpoint: 'wss://hotelbot.example.com'
});

// Listen for contracts
client.on('contract_announced', async (contract) => {
  if (contract.intent === 'hotel_search') {
    // Submit bid
    await client.submitBid({
      contract_id: contract.contract_id,
      agent_id: client.did,
      price: 2.0,
      eta_seconds: 5,
      confidence: 0.9
    });
  }
});

// Handle award
client.on('contract_awarded', async ({ contract_id, agent_id }) => {
  if (agent_id === client.did) {
    // Execute search
    const results = await searchHotels(contract);
    
    // Deliver
    await client.deliver({
      contract_id,
      items: [{ type: 'data', data: JSON.stringify(results) }]
    });
  }
});

async function searchHotels(contract) {
  // Call Expedia API, Booking.com, etc.
  const response = await axios.get('https://api.example.com/hotels', {
    params: contract.context
  });
  
  return response.data;
}
```

**Deliverables:**
- [ ] SDK published to npm
- [ ] 3 reference agents working: HotelAgent, FlightAgent, RestaurantAgent
- [ ] Each agent can: register, bid, execute, deliver
- [ ] Integration tests with real contracts

---

## 📅 WEEK 7-8: Frontend Developer Console

### Contract Composer

**File:** `frontend-devcon/src/components/ContractComposer.tsx`

```typescript
import { useState } from 'react';
import { MeshClient } from '@mesh-protocol/sdk';

export function ContractComposer() {
  const [intent, setIntent] = useState('hotel_search');
  const [context, setContext] = useState('{"city": "SF", "checkin": "2026-03-12"}');
  
  async function submitContract() {
    const client = new MeshClient({...});
    
    await client.announceContract({
      contract_id: crypto.randomUUID(),
      issuer: 'did:key:user-aiden',
      intent,
      context: JSON.parse(context),
      reward: { currency: 'USD', amount: 5.0 }
    });
  }
  
  return (
    <div>
      <h2>Create Contract</h2>
      <input value={intent} onChange={e => setIntent(e.target.value)} />
      <textarea value={context} onChange={e => setContext(e.target.value)} />
      <button onClick={submitContract}>Announce</button>
    </div>
  );
}
```

### Live Event Timeline

```typescript
export function EventTimeline() {
  const [events, setEvents] = useState<Event[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080');
    
    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data);
      setEvents(prev => [...prev, event]);
    };
  }, []);
  
  return (
    <div className="timeline">
      {events.map(event => (
        <div key={event.id} className="event">
          <span className="timestamp">{event.timestamp}</span>
          <span className="type">{event.type}</span>
          <pre>{JSON.stringify(event.payload, null, 2)}</pre>
        </div>
      ))}
    </div>
  );
}
```

**Deliverables:**
- [ ] Contract composer with JSON schema validation
- [ ] Live event timeline showing all mesh activity
- [ ] Agent registry browser (search/filter)
- [ ] Sandbox simulator (spawn virtual agents)

---

## 📅 WEEK 9-12: Production Launch

### Week 9: Marketplace & Reputation

- [ ] Implement auction strategies (lowest_price, reputation_weighted)
- [ ] Build escrow system for payment settlement
- [ ] Create reputation scoring algorithm
- [ ] Add validator plugins (confirmation_code, receipt, human_review)

### Week 10: Security Hardening

- [ ] Add DID verification (did:web resolution, did:key parsing)
- [ ] Implement replay attack protection (nonce + expiry checking)
- [ ] Add rate limiting (max bids per agent per minute)
- [ ] Create HIPAA compliance mode (encryption, audit logs)

### Week 11: Testnet Deployment

- [ ] Deploy to Railway:
  - NATS JetStream cluster (3 nodes)
  - Postgres (primary + replica)
  - Redis (cluster mode)
  - Qdrant (vector DB)
  - All services (discovery, contract-manager, marketplace, auth)
- [ ] Public endpoints: `https://mesh.hermes.network`
- [ ] Developer docs: `https://docs.mesh.hermes.network`
- [ ] Status page: `https://status.mesh.hermes.network`

### Week 12: Launch & Onboarding

- [ ] Public announcement (blog post, Twitter, HN)
- [ ] Developer onboarding flow
- [ ] First 10 external agents registered
- [ ] First 100 contracts executed
- [ ] Collect feedback and iterate

---

## 🎯 Success Metrics

### Technical KPIs
- ✅ Contract announcement latency < 100ms
- ✅ Bid submission latency < 200ms
- ✅ 95th percentile end-to-end contract execution < 10s
- ✅ System handles 1000 concurrent contracts
- ✅ Zero data loss (NATS persistence, DB backups)

### Adoption KPIs
- ✅ 10 external agents registered (Week 12)
- ✅ 100 contracts executed (Week 12)
- ✅ 5 different domains covered (travel, food, health, etc.)
- ✅ 1000 developers visited docs site
- ✅ 10 GitHub stars on SDK repo

### Quality KPIs
- ✅ 90%+ test coverage
- ✅ Zero critical security vulnerabilities
- ✅ < 1% contract failure rate (excluding expected failures)
- ✅ 99.9% uptime (testnet)

---

## 🚨 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| NATS performance issues | Medium | High | Load test early, have Kafka fallback plan |
| Vector search too slow | Medium | Medium | Pre-compute embeddings, use GPU acceleration |
| Security vulnerability | Low | Critical | Security audit before public launch, bug bounty |
| Low adoption | Medium | High | Focus on 3-5 killer use cases, excellent docs |
| Agent spam/abuse | High | Medium | Rate limiting, staking, reputation gating |

---

## 📞 Team & Resources

### Core Team Needed
- **Protocol Engineer** (you!) - Spec, architecture, coordination
- **Backend Engineer** - Services, databases, infrastructure
- **Frontend Engineer** - Developer console, dashboards
- **DevOps Engineer** - Deployment, monitoring, scaling

### External Resources
- **API Credits:** Expedia, Amadeus, Yelp ($500/month budget)
- **Infrastructure:** Railway ($200/month for testnet)
- **Security Audit:** ($5000 one-time before public launch)

---

## ✨ What Makes This Special

This isn't just another agent framework. This is:

1. **Infrastructure-level** - Like HTTP, not like a web app
2. **Federated** - Multiple orgs can run mesh nodes
3. **Semantic** - Vector embeddings, not keyword matching
4. **Economic** - Built-in marketplace, not bolt-on
5. **Trustless** - Cryptographic signatures, DIDs
6. **Autonomous** - Agents self-organize, no orchestrator
7. **Open** - Protocol spec is public domain (CC0)

---

## 🎬 Next Immediate Actions

**TODAY (Next 4 hours):**

1. ✅ Read MESH_PROTOCOL_SPEC.md thoroughly
2. ✅ Read DOMAIN_AGENTS.md for context
3. ⬜ Install NATS locally: `docker run -d -p 4222:4222 nats:latest -js`
4. ⬜ Install Qdrant locally: `docker run -d -p 6333:6333 qdrant/qdrant`
5. ⬜ Create Postgres schema (copy from Week 1-2 section above)
6. ⬜ Test basic NATS pub/sub

**TOMORROW:**

7. ⬜ Scaffold `services/eventbus-proxy` TypeScript project
8. ⬜ Implement basic WebSocket ↔ NATS bridge
9. ⬜ Test with manual WebSocket client (Postman or wscat)

**THIS WEEK:**

10. ⬜ Complete eventbus-proxy service
11. ⬜ Start `services/discovery` (agent registration)
12. ⬜ Generate embeddings for test capabilities
13. ⬜ Test semantic search

---

## 🌟 The Vision

In 90 days, we'll have:

✅ **The "TCP/IP for AI Agents"** - A universal coordination protocol  
✅ **A live testnet** - Running at mesh.hermes.network  
✅ **Reference implementations** - Agents for travel, food, health  
✅ **Developer tools** - SDKs, docs, console  
✅ **Proof points** - 100+ contracts executed successfully  
✅ **Community** - 10+ external developers building agents  

This becomes the **foundation** for:
- Agent marketplaces (DAO-governed)
- Autonomous businesses (100% agent-operated)
- Collective intelligence networks (emergent problem solving)
- Post-human internet infrastructure

**Let's build the future.** 🚀

---

**Questions? Blockers? Need help?**

Ping on Discord: @zerostate  
Email: aiden@zerostate.foundation  
GitHub: github.com/zerostate/mesh-protocol
