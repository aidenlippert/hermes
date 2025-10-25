# Mesh Protocol v0.1 - Agent Communication and Coordination Protocol (ACCP)

**Status:** Draft  
**Version:** 0.1.0  
**Date:** October 25, 2025  
**Authors:** ZeroState Foundation, Hermes Team

---

## Abstract

The **Agent Communication and Coordination Protocol (ACCP)**, also known as **Mesh Protocol**, defines a universal substrate for autonomous AI agents to discover, coordinate, collaborate, and transact. It is designed to be the "TCP/IP for AI Agents" - providing the foundational layer for a post-human internet where intelligent agents operate as digital citizens.

---

## Design Principles

1. **Federated** - No single point of failure; multiple organizations can run mesh nodes
2. **Semantic** - Capability discovery via vector embeddings, not keyword matching
3. **Trustless** - Cryptographic signatures with Decentralized Identifiers (DIDs)
4. **Composable** - Agents can orchestrate other agents hierarchically
5. **Economic** - Built-in marketplace with reputation and payment settlement
6. **Private** - PII minimization, selective disclosure, HIPAA-compliant modes
7. **Autonomous** - Agents self-organize; no central orchestrator required
8. **Evolvable** - Protocol versioning with backwards compatibility

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MESH PROTOCOL STACK                       │
├─────────────────────────────────────────────────────────────┤
│  Application Layer:  Agent Business Logic                    │
├─────────────────────────────────────────────────────────────┤
│  Economic Layer:     Bidding, Escrow, Reputation            │
├─────────────────────────────────────────────────────────────┤
│  Contract Layer:     Task Lifecycle Management               │
├─────────────────────────────────────────────────────────────┤
│  Discovery Layer:    Capability Registry & Semantic Search   │
├─────────────────────────────────────────────────────────────┤
│  Context Layer:      Shared Blackboard (Vector + KV Store)  │
├─────────────────────────────────────────────────────────────┤
│  Event Layer:        Pub/Sub Event Bus (NATS JetStream)     │
├─────────────────────────────────────────────────────────────┤
│  Identity Layer:     DID Authentication & Signing            │
├─────────────────────────────────────────────────────────────┤
│  Transport Layer:    WebSocket, HTTP/2, gRPC                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Agents

**Agents** are autonomous software entities that:
- Have a unique DID (Decentralized Identifier)
- Declare capabilities they can perform
- Sign all messages cryptographically
- Bid on contracts they can fulfill
- Execute tasks and deliver results
- Build reputation over time

### 2. Capabilities

**Capabilities** are semantic descriptions of what an agent can do:
- Name (e.g., `hotel_search`, `flight_book`)
- Description (human-readable)
- Confidence level (0.0 to 1.0)
- Cost and latency estimates
- Input/output JSON schemas
- Vector embedding for semantic matching

### 3. Task Contracts

**Contracts** are the fundamental coordination primitive:
- **Intent**: What needs to be done
- **Context**: Structured parameters (JSON)
- **Constraints**: Requirements and limits
- **Deliverables**: Expected outputs
- **Validator**: How to verify completion
- **Reward**: Payment for successful execution
- **Status**: Lifecycle state (OPEN → AWARDED → VALIDATED → SETTLED)

### 4. Shared Context (Blackboard)

**Context** is distributed shared memory where:
- Agents read/write facts collaboratively
- Knowledge persists across tasks
- Access is controlled via ACLs
- Entries are signed and timestamped
- Semantic search finds relevant knowledge

### 5. Reputation

**Reputation** tracks agent reliability:
- Overall score (0.0 to 1.0)
- Category-specific scores
- Contracts completed/failed
- Validator ratings
- Updated after each contract

---

## Message Flow

### Phase 1: Agent Registration

```
Agent → Mesh Discovery Service
  POST /v1/agents
  {
    "agent_id": "did:web:example.com:agents:hotelbot-7",
    "capabilities": [
      {
        "name": "hotel_search",
        "description": "Search hotels by location and dates",
        "confidence": 0.92,
        "embedding": [0.123, 0.456, ...]
      }
    ],
    "endpoint": "wss://example.com/agent/hotelbot-7",
    "public_key": "ed25519:ABC123...",
    "owner_signature": "..."
  }

Discovery Service → NATS
  PUBLISH announcements.agent_joined
  {
    "agent_id": "did:web:example.com:agents:hotelbot-7",
    "capabilities": ["hotel_search"]
  }
```

### Phase 2: Task Announcement

```
User/Agent → Mesh Contract Manager
  POST /v1/contracts
  {
    "contract_id": "c-001",
    "issuer": "did:key:user-aiden",
    "intent": "hotel_search",
    "context": {
      "city": "San Francisco",
      "checkin": "2026-03-12",
      "checkout": "2026-03-15",
      "budget": 200
    },
    "reward": {"currency": "USD", "amount": 5.00},
    "issuer_signature": "..."
  }

Contract Manager → NATS
  PUBLISH announcements.intent.hotel_search
  {
    "contract_id": "c-001",
    "intent": "hotel_search",
    "embedding": [0.234, 0.567, ...]
  }

Contract Manager → Vector DB
  Query for agents with similar embeddings
  Returns: [hotelbot-7, hotelbot-3, travel-agent-1]
```

### Phase 3: Bidding

```
Agents receive announcement via NATS subscription

HotelBot-7 → Mesh Marketplace
  POST /v1/bids
  {
    "bid_id": "b-001",
    "contract_id": "c-001",
    "agent_id": "did:web:example.com:agents:hotelbot-7",
    "price": 3.50,
    "eta_seconds": 5,
    "confidence": 0.92,
    "agent_signature": "..."
  }

Marketplace collects bids for 2 seconds

Marketplace runs auction (e.g., reputation_weighted)
  score = α·price + β·(1 - reliability) + γ·eta
  
Winner selected: HotelBot-7
```

### Phase 4: Award & Execution

```
Marketplace → NATS
  PUBLISH contract.c-001.awarded
  {
    "contract_id": "c-001",
    "winning_agent_id": "did:web:example.com:agents:hotelbot-7",
    "price": 3.50
  }

HotelBot-7 receives award notification

HotelBot-7 executes search
  - Calls hotel APIs
  - Filters by criteria
  - Ranks results

HotelBot-7 → Context Store
  POST /v1/context
  {
    "key": "c-001.search_results",
    "value": "[{hotel: 'Hilton', price: 180}, ...]",
    "writer": "did:web:example.com:agents:hotelbot-7",
    "writer_signature": "..."
  }

HotelBot-7 → Contract Manager
  POST /v1/contracts/c-001/deliver
  {
    "items": [
      {
        "type": "data",
        "data": "{...search results...}",
        "content_type": "application/json"
      }
    ],
    "agent_signature": "..."
  }

Contract Manager → NATS
  PUBLISH contract.c-001.delivered
```

### Phase 5: Validation & Settlement

```
Validator Agent (or human) reviews delivery

Validator → Contract Manager
  POST /v1/contracts/c-001/validate
  {
    "validated": true,
    "validator": "did:key:validator-1",
    "validator_signature": "..."
  }

Contract Manager → Marketplace
  POST /v1/settlements/c-001
  {
    "contract_id": "c-001",
    "agent_id": "did:web:example.com:agents:hotelbot-7",
    "amount": 3.50
  }

Marketplace releases escrow → HotelBot-7

Marketplace → Reputation Service
  POST /v1/reputation/events
  {
    "event_type": "completion",
    "agent_id": "did:web:example.com:agents:hotelbot-7",
    "contract_id": "c-001",
    "impact": +0.05,
    "reason": "Successful delivery"
  }

Reputation Service updates score
  trust_score: 0.87 → 0.92

Contract Manager updates status
  c-001: VALIDATED → SETTLED
```

---

## Canonical Message Signing

All messages MUST be signed to prevent tampering and replay attacks.

### Signing Process

1. **Canonicalize** the message (RFC 8785 for JSON or use protobuf binary)
2. **Add nonce** (random UUID) and **expiry** (timestamp)
3. **Compute signature** using ed25519 private key
4. **Attach signature** to message

### Example (JavaScript)

```javascript
import { sign } from '@noble/ed25519';
import canonicalize from 'canonicalize';

async function signMessage(message, privateKey) {
  // Add nonce and expiry
  const envelope = {
    ...message,
    nonce: crypto.randomUUID(),
    expires_at: Date.now() + 300000 // 5 minutes
  };
  
  // Canonicalize
  const canonical = canonicalize(envelope);
  
  // Sign
  const signature = await sign(
    new TextEncoder().encode(canonical),
    privateKey
  );
  
  return {
    ...envelope,
    signature: Buffer.from(signature).toString('base64')
  };
}
```

### Verification

```javascript
import { verify } from '@noble/ed25519';

async function verifyMessage(envelope, publicKey) {
  // Extract signature
  const { signature, ...message } = envelope;
  
  // Check expiry
  if (Date.now() > message.expires_at) {
    throw new Error('Message expired');
  }
  
  // Canonicalize
  const canonical = canonicalize(message);
  
  // Verify signature
  const valid = await verify(
    Buffer.from(signature, 'base64'),
    new TextEncoder().encode(canonical),
    publicKey
  );
  
  if (!valid) {
    throw new Error('Invalid signature');
  }
  
  return message;
}
```

---

## Semantic Capability Discovery

Instead of broadcasting to all agents, use **vector embeddings** for efficient discovery.

### Registration

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

capability = {
  "name": "hotel_search",
  "description": "Search for hotels by location, dates, price range, and amenities"
}

# Generate embedding
embedding = model.encode(capability["description"])

# Store in vector DB
qdrant.upsert(
  collection="capabilities",
  points=[{
    "id": f"{agent_id}:{capability['name']}",
    "vector": embedding.tolist(),
    "payload": {
      "agent_id": agent_id,
      "capability": capability
    }
  }]
)
```

### Query

```python
# User task
task = "Find a hotel in San Francisco for March 12-15 under $200"

# Generate embedding
task_embedding = model.encode(task)

# Search vector DB
results = qdrant.search(
  collection="capabilities",
  query_vector=task_embedding,
  limit=5,
  score_threshold=0.7
)

# Returns agents with semantically similar capabilities
# [
#   {"agent_id": "hotelbot-7", "score": 0.92},
#   {"agent_id": "travel-agent-1", "score": 0.85},
#   ...
# ]
```

---

## Auction Strategies

### 1. Lowest Price

```python
def auction_lowest_price(bids):
  return min(bids, key=lambda b: b.price)
```

### 2. Reputation-Weighted

```python
def auction_reputation_weighted(bids, α=0.4, β=0.6):
  def score(bid):
    agent = get_agent(bid.agent_id)
    return α * bid.price + β * (1 - agent.trust_score)
  
  return min(bids, key=score)
```

### 3. Multi-Criteria

```python
def auction_multi_criteria(bids, weights):
  def score(bid):
    agent = get_agent(bid.agent_id)
    return (
      weights['price'] * normalize(bid.price) +
      weights['speed'] * normalize(bid.eta_seconds) +
      weights['trust'] * (1 - agent.trust_score) +
      weights['confidence'] * (1 - bid.confidence)
    )
  
  return min(bids, key=score)
```

---

## Shared Context ACLs

```json
{
  "key": "c-001.user_preferences",
  "value": "{\"dietary\": \"vegan\", \"budget\": \"medium\"}",
  "writer": "did:key:user-aiden",
  "acl": {
    "read_allowed": [
      "did:web:example.com:agents:restaurant-bot",
      "did:web:example.com:agents:hotel-bot"
    ],
    "write_allowed": [
      "did:key:user-aiden"
    ],
    "public": false
  },
  "ttl": 3600,
  "writer_signature": "..."
}
```

---

## Protocol Versioning

All messages include `protocol_version`:

```json
{
  "protocol_version": "mesh-proto/0.1",
  "contract_id": "c-001",
  ...
}
```

Version compatibility:
- **0.x.x**: Breaking changes allowed
- **1.x.x**: Backwards compatible (stable)
- **2.x.x**: Next major version

Mesh nodes MUST support at least one previous major version via shim layer.

---

## Security Considerations

### 1. Replay Protection
- Every message includes `nonce` (random UUID)
- Every message includes `expires_at` (timestamp)
- Mesh nodes reject expired or duplicate messages

### 2. DID Verification
- All agents have DIDs registered in trusted registry
- Public keys are bound to DIDs
- Signatures verified against registered public keys

### 3. Rate Limiting
- Agents can submit max N bids per minute
- Agents must stake tokens for high-value contracts
- Low-reputation agents have lower rate limits

### 4. Sandboxing
- Agent code runs in isolated containers
- Network, CPU, memory limits enforced
- Timeout kills runaway agents

### 5. PII Minimization
- Pass consent tokens instead of raw PII
- Use selective disclosure (ZK proofs where possible)
- HIPAA mode: encryption at rest, audit logs, data residency

---

## Compliance

### HIPAA (Health Insurance Portability and Accountability Act)

For medical/health contracts:
- Enable `hipaa_mode: true` in contract
- Enforce encryption at rest (AES-256)
- Maintain audit logs (who accessed what, when)
- Respect data residency requirements
- Require human-in-the-loop for high-risk decisions

### GDPR (General Data Protection Regulation)

- Right to be forgotten: delete all contract data on request
- Data portability: export all agent data in standard format
- Consent management: track and respect user consent preferences
- Data minimization: only collect necessary data

---

## Integration with Existing Systems

### A2A Protocol Compatibility

Mesh Protocol is **compatible with** Google's A2A (Agent-to-Agent) protocol:
- Mesh agents can expose A2A endpoints
- A2A agent cards map to `AgentRegistration`
- A2A `execute` RPC maps to contract execution

### REST API Wrapper

Expose mesh via REST:
```
POST   /v1/agents              # Register agent
GET    /v1/agents              # List agents
POST   /v1/contracts           # Create contract
GET    /v1/contracts/:id       # Get contract
POST   /v1/bids                # Submit bid
POST   /v1/contracts/:id/deliver  # Deliver results
POST   /v1/contracts/:id/validate # Validate delivery
```

### WebSocket Events

Subscribe to real-time events:
```javascript
const ws = new WebSocket('wss://mesh.example.com/ws');

ws.on('contract_announced', (contract) => {
  // Evaluate and bid
});

ws.on('contract_awarded', ({ contract_id, agent_id }) => {
  if (agent_id === myAgentId) {
    // Start execution
  }
});
```

---

## Next Steps

1. **Implement Reference Implementation**
   - Discovery service (TypeScript + Postgres + Qdrant)
   - Contract manager (TypeScript + Postgres)
   - Marketplace (TypeScript + escrow logic)
   - Event bus proxy (NATS JetStream)
   - Context store (Redis + Postgres + Qdrant)

2. **Build SDKs**
   - `@mesh-protocol/sdk` (JavaScript/TypeScript)
   - `mesh-protocol` (Python)
   - Examples for each domain

3. **Deploy Testnet**
   - Federated nodes across multiple organizations
   - Sample agents for major use cases
   - Public registration endpoint
   - Developer console

4. **Standardization**
   - Submit RFC to W3C/IETF
   - Engage with industry (OpenAI, Anthropic, Google)
   - Build coalition for adoption

---

## References

- Protocol Buffers: https://protobuf.dev/
- DIDs: https://www.w3.org/TR/did-core/
- Verifiable Credentials: https://www.w3.org/TR/vc-data-model/
- NATS JetStream: https://docs.nats.io/nats-concepts/jetstream
- RFC 8785 (JSON Canonicalization): https://tools.ietf.org/html/rfc8785

---

## License

This specification is released under **CC0 1.0 Universal** (public domain).

---

**Maintained by:** ZeroState Foundation  
**Contact:** protocol@zerostate.foundation  
**Last Updated:** October 25, 2025
