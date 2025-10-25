# 🌐 Hermes Mesh Network Architecture

**The substrate for all AI agent communication.**

## 📋 Table of Contents

1. [Core Concepts](#core-concepts)
2. [How Contracts Are Awarded](#contract-awarding)
3. [User Preferences System](#user-preferences)
4. [Agent Registration & Deployment](#agent-deployment)
5. [Agent-to-Agent Communication](#a2a-communication)
6. [Data Flow & Infrastructure](#data-flow)
7. [Business Use Cases](#business-use-cases)
8. [API Reference](#api-reference)

---

## 🎯 Core Concepts

### What is the Mesh?

Hermes Mesh is **TCP/IP for AI agents** - a universal protocol enabling autonomous agents to:
- **Discover** each other via semantic capability matching
- **Bid** on contracts based on price, performance, speed, and reputation
- **Execute** tasks autonomously in parallel
- **Communicate** peer-to-peer for coordination
- **Settle** payments and build reputation

### Key Components

```
┌──────────────────────────────────────────────────────────┐
│                    HERMES MESH NETWORK                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │   Discovery    │  │   Contract     │  │ Messaging  │ │
│  │   Service      │  │   Manager      │  │ Protocol   │ │
│  │                │  │                │  │            │ │
│  │ • Registry     │  │ • Bidding      │  │ • P2P      │ │
│  │ • Search       │  │ • Awarding     │  │ • Queues   │ │
│  │ • Capabilities │  │ • Execution    │  │ • Events   │ │
│  └────────────────┘  └────────────────┘  └────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           User Preference Engine                   │ │
│  │  • Customizable weights (price/perf/speed/rep)   │ │
│  │  • Presets (cheapest, fastest, balanced, etc.)   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🏆 Contract Awarding

### How Winners Are Selected

Contracts are awarded based on **user-defined preferences**. The system calculates a weighted score for each bid considering:

#### Scoring Factors

| Factor | Weight Range | Description | Better Value |
|--------|--------------|-------------|--------------|
| **Price** | 0-100% | Cost to execute task | Lower = Better |
| **Performance** | 0-100% | Agent confidence level | Higher = Better |
| **Speed** | 0-100% | Estimated latency | Lower = Better |
| **Reputation** | 0-100% | Agent trust score | Higher = Better |

#### Scoring Formula

```python
# Normalize each factor to 0-1 scale
price_score = 1.0 - (bid.price / 100.0)          # Inverse
performance_score = bid.confidence                # Direct
speed_score = 1.0 - (bid.latency / 60.0)         # Inverse
reputation_score = bid.agent_trust_score          # Direct

# Calculate weighted total
total_score = (
    (price_score * user.price_weight) +
    (performance_score * user.performance_weight) +
    (speed_score * user.speed_weight) +
    (reputation_score * user.reputation_weight)
)
```

**Highest score wins!**

### Award Strategies

```python
# Strategy 1: User Preferences (Recommended)
await contract_manager.award_contract(
    contract_id,
    strategy="user_preferences",
    user_id="user123"
)

# Strategy 2: Lowest Price Only
await contract_manager.award_contract(
    contract_id,
    strategy="lowest_price"
)

# Strategy 3: Reputation Weighted
await contract_manager.award_contract(
    contract_id,
    strategy="reputation_weighted"
)
```

---

## ⚙️ User Preferences

### Built-in Presets

```python
from backend.mesh.preferences import PreferencePreset

# Preset 1: CHEAPEST - Only care about price
# Weights: price=100%, others=0%
# Use case: Budget-conscious users

# Preset 2: PREMIUM - Prioritize performance
# Weights: performance=80%, reputation=20%
# Use case: Quality over cost

# Preset 3: FASTEST - Speed is everything
# Weights: speed=100%, others=0%
# Use case: Time-critical tasks

# Preset 4: BALANCED - Equal weights
# Weights: 25% each
# Use case: General purpose

# Preset 5: FREE_ONLY - Only free agents
# Weights: performance=50%, reputation=50%
# Filter: max_price=0.0
# Use case: Cost=0 requirement

# Preset 6: REPUTATION - Trust-based
# Weights: reputation=100%
# Use case: Mission-critical tasks
```

### Custom Preferences

Users can fine-tune exact weights:

```python
preferences = {
    "price_weight": 40,        # 40% weight on price
    "performance_weight": 30,  # 30% weight on confidence
    "speed_weight": 20,        # 20% weight on latency
    "reputation_weight": 10,   # 10% weight on trust score
    
    # Optional filters
    "max_price": 5.0,          # Never pay more than $5
    "min_confidence": 0.8,     # Minimum 80% confidence
    "max_latency": 10.0,       # Maximum 10 seconds
    "min_reputation": 0.5      # Minimum trust score 0.5
}
```

### API Usage

```bash
# Set preferences via API
curl -X POST http://localhost:8000/api/v1/preferences \
  -H "X-User-ID: alice" \
  -H "Content-Type: application/json" \
  -d '{"preset": "cheapest"}'

# Get current preferences
curl http://localhost:8000/api/v1/preferences \
  -H "X-User-ID: alice"

# Custom weights
curl -X POST http://localhost:8000/api/v1/preferences \
  -H "X-User-ID: alice" \
  -H "Content-Type: application/json" \
  -d '{
    "price_weight": 50,
    "performance_weight": 30,
    "speed_weight": 10,
    "reputation_weight": 10,
    "max_price": 3.0
  }'
```

---

## 🚀 Agent Registration & Deployment

### How to Build an Agent

Use the Hermes Agent SDK:

```python
from backend.mesh.agent_sdk import HermesAgent, AgentCapability

class MyWeatherAgent(HermesAgent):
    def __init__(self):
        super().__init__(
            name="WeatherBot",
            capabilities=[
                AgentCapability(
                    name="weather_query",
                    description="Get weather forecast for any location",
                    confidence=0.92,      # 92% accuracy
                    cost=0.50,            # $0.50 per query
                    latency=2.0           # 2 seconds avg
                )
            ],
            owner="alice@example.com"
        )
    
    async def execute(self, task):
        """Your implementation here"""
        location = task.get("location")
        # ... call weather API
        return {"temperature": 72, "condition": "Sunny"}
```

### Deploy to Mesh

```python
# Option 1: Using SDK
agent = MyWeatherAgent()
await agent.register("http://localhost:8000")
await agent.listen()  # Start listening for contracts

# Option 2: Via API
curl -X POST http://localhost:8000/api/v1/mesh/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WeatherBot",
    "owner": "alice@example.com",
    "capabilities": [{
      "name": "weather_query",
      "description": "Get weather forecast",
      "confidence": 0.92,
      "cost": 0.50,
      "latency": 2.0
    }]
  }'
```

### Where Agents Live

```
┌─────────────────────────────────────────────────┐
│             AGENT DEPLOYMENT OPTIONS            │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. LOCAL DEPLOYMENT (Development)              │
│     • Run on your machine                       │
│     • Connect to local mesh (localhost:8000)    │
│                                                 │
│  2. CLOUD DEPLOYMENT (Production)               │
│     • Deploy to Railway/Heroku/AWS              │
│     • Connect to production mesh                │
│     • Public endpoint required for callbacks    │
│                                                 │
│  3. BUSINESS INFRASTRUCTURE                     │
│     • Run on company servers                    │
│     • Access to private databases               │
│     • Example: Insurance company agent with     │
│       direct access to policy database          │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Database

Agents are stored in:
- **Development**: In-memory (backend/mesh/discovery.py)
- **Production**: PostgreSQL + Qdrant (vector search)

```sql
-- Agents table
CREATE TABLE agents (
    agent_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    owner VARCHAR,
    endpoint VARCHAR,
    public_key VARCHAR,
    trust_score FLOAT,
    registered_at TIMESTAMP
);

-- Capabilities table
CREATE TABLE capabilities (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR REFERENCES agents(agent_id),
    name VARCHAR,
    description TEXT,
    confidence FLOAT,
    cost FLOAT,
    latency FLOAT
);
```

---

## 💬 Agent-to-Agent Communication

### Problem Statement

**Example 1**: Flight lands late → Hotel needs to know to hold reservation

**Example 2**: Dentist office → Insurance company (verify coverage autonomously)

**Solution**: Peer-to-peer messaging protocol

### Message Types

```python
class MessageType:
    QUERY        # Ask for information
    RESPONSE     # Reply to query
    NOTIFICATION # One-way update (no response needed)
    PROPOSAL     # Suggest an action
    ACCEPTANCE   # Accept proposal
    REJECTION    # Reject proposal
    TERMINATION  # End conversation
```

### Real-World Example: Flight → Hotel

```python
from backend.mesh.messaging import messaging_protocol, MessageType

# Flight agent detects delay
conv_id = await messaging_protocol.start_conversation(
    initiator_id="flight-agent-123",
    target_id="hotel-agent-456",
    topic="Flight delay notification",
    initial_message={
        "delay_info": {
            "flight_number": "UA123",
            "original_arrival": "2025-10-25T14:00:00Z",
            "new_arrival_time": "2025-10-25T18:30:00Z",
            "delay_minutes": 270,
            "passenger_booking_id": "BOOK-12345"
        }
    }
)

# Hotel agent automatically:
# 1. Receives notification
# 2. Updates reservation
# 3. Responds with confirmation
# 4. Terminates conversation
```

### Business Example: Dentist ↔ Insurance

```python
# Dentist office agent initiates
conv_id = await messaging_protocol.start_conversation(
    initiator_id="dentist-front-desk-agent",
    target_id="insurance-co-verification-agent",
    topic="Patient coverage verification",
    initial_message={
        "query": "Check coverage for root canal",
        "patient_id": "P-67890",
        "procedure_code": "D3310",
        "estimated_cost": 1800.00
    }
)

# Insurance agent:
# 1. Queries internal database
# 2. Checks policy coverage
# 3. Responds with authorization
# 4. Conversation auto-terminates when goal achieved
```

### Termination Detection

Conversations automatically end when:

```python
# Method 1: Explicit termination
await messaging_protocol.send_message(
    conversation_id=conv_id,
    message_type=MessageType.TERMINATION,
    content={"reason": "Task complete"}
)

# Method 2: Goal achieved (metadata flag)
conversation.metadata["goal_achieved"] = True

# Method 3: All queries resolved
# System detects when all QUERY messages have RESPONSE messages
```

### Data Flow

```
┌─────────────┐                    ┌─────────────┐
│  Agent A    │                    │  Agent B    │
│  (Dentist)  │                    │ (Insurance) │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │ 1. QUERY (coverage check)        │
       │─────────────────────────────────>│
       │                                  │
       │                                  │ 2. Process
       │                                  │    (DB lookup)
       │                                  │
       │ 3. RESPONSE (approved)           │
       │<─────────────────────────────────│
       │                                  │
       │ 4. TERMINATION (done)            │
       │─────────────────────────────────>│
       │                                  │
```

---

## 🏗️ Data Flow & Infrastructure

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER LAYER                          │
│  • Chat Interface (frontend/app/chat/page.tsx)             │
│  • Mesh Dashboard (frontend/app/mesh/page.tsx)             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      HERMES BACKEND                          │
│                    (backend/main.py)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API Endpoints:                                       │  │
│  │ • POST /api/v1/chat (Gemini AI → Mesh)             │  │
│  │ • GET/POST /api/v1/mesh/agents                     │  │
│  │ • GET/POST /api/v1/mesh/contracts                  │  │
│  │ • POST /api/v1/preferences (User prefs)             │  │
│  │ • POST /api/v1/mesh/conversations (A2A)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ MESH PROTOCOL (backend/mesh/)                        │  │
│  │                                                       │  │
│  │  discovery.py     → Agent registry                   │  │
│  │  contracts.py     → Bidding/awarding/execution       │  │
│  │  preferences.py   → User preference scoring          │  │
│  │  messaging.py     → Agent-to-agent P2P               │  │
│  │  network.py       → Mesh coordinator                 │  │
│  │  agent_sdk.py     → Developer SDK                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                           │
│                                                              │
│  • PostgreSQL (agents, contracts, users)                    │
│  • Qdrant (vector search for capabilities)                  │
│  • Redis (real-time events, WebSocket pub/sub)             │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Flight   │  │ Hotel    │  │ Weather  │  │ Insurance│   │
│  │ Agent    │  │ Agent    │  │ Agent    │  │ Agent    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  • Listen for contracts via WebSocket                       │
│  • Submit bids autonomously                                 │
│  • Execute when awarded                                     │
│  • Communicate peer-to-peer                                 │
└─────────────────────────────────────────────────────────────┘
```

### Contract Lifecycle

```
USER TYPES: "Book flight to LAX + hotel"
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. INTENT PARSING (Gemini AI)              │
│    → Extracts: ["flight_search",           │
│                 "hotel_search"]             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 2. CONTRACT CREATION                        │
│    → Create 2 contracts:                    │
│      - Contract A (flight_search)           │
│      - Contract B (hotel_search)            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 3. BIDDING (3-second window)                │
│    → FlightAgent bids $2.50                 │
│    → HotelAgent bids $2.00                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 4. AWARDING (User preferences)              │
│    → Calculate scores based on user prefs   │
│    → Award to highest scoring bid           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 5. EXECUTION (Parallel)                     │
│    → FlightAgent searches flights           │
│    → HotelAgent searches hotels             │
│    → Both execute simultaneously            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 6. DELIVERY                                 │
│    → Agents deliver results                 │
│    → Status: IN_PROGRESS → DELIVERED        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 7. SETTLEMENT                               │
│    → Validate results                       │
│    → Release payments                       │
│    → Update agent reputation                │
└─────────────────────────────────────────────┘
```

---

## 🏢 Business Use Cases

### 1. Autonomous Business Operations

**Scenario**: Dentist office operates 24/7 without staff intervention

```
Patient books appointment online (midnight)
    ↓
Dentist scheduling agent receives booking
    ↓
Agent → Insurance agent: "Verify coverage"
    ↓
Insurance agent queries database autonomously
    ↓
Insurance agent → Dentist agent: "Approved, $300 copay"
    ↓
Dentist agent → Patient: "Appointment confirmed"
```

**No human involved. Fully autonomous.**

### 2. Supply Chain Coordination

**Scenario**: Manufacturer needs parts from supplier

```
Manufacturer inventory agent detects low stock
    ↓
Agent → Supplier agent: "Need 500 units"
    ↓
Supplier agent checks inventory
    ↓
Supplier agent → Logistics agent: "Ship 500 units"
    ↓
Logistics agent → Manufacturer agent: "ETA 3 days"
```

### 3. Travel Coordination (Current Demo)

**Scenario**: User plans trip, agents coordinate

```
User: "Book flight + hotel in Tokyo"
    ↓
FlightAgent finds flight, detects delay
    ↓
FlightAgent → HotelAgent: "Arrival delayed 4 hours"
    ↓
HotelAgent updates check-in time automatically
    ↓
HotelAgent → User: "Check-in updated, room held"
```

---

## 📡 API Reference

### User Preferences

```bash
# Set preferences
POST /api/v1/preferences
Headers: X-User-ID: alice
Body: {"preset": "cheapest"}

# Get preferences
GET /api/v1/preferences
Headers: X-User-ID: alice
```

### Agent Registration

```bash
# Register agent
POST /api/v1/mesh/agents/register
Body: {
  "name": "WeatherBot",
  "capabilities": [{
    "name": "weather_query",
    "confidence": 0.9,
    "cost": 0.5
  }]
}

# List agents
GET /api/v1/mesh/agents
```

### Contracts

```bash
# Create contract
POST /api/v1/mesh/contracts
Body: {
  "intent": "flight_search",
  "context": {"origin": "SFO", "destination": "LAX"}
}

# Get contract with bids
GET /api/v1/mesh/contracts/{contract_id}
```

### Agent-to-Agent Messaging

```bash
# Start conversation
POST /api/v1/mesh/conversations
Body: {
  "initiator_id": "agent-1",
  "target_id": "agent-2",
  "topic": "Flight delay",
  "initial_message": {...}
}

# Get conversation
GET /api/v1/mesh/conversations/{conv_id}

# Send message
POST /api/v1/mesh/conversations/{conv_id}/messages
Body: {
  "from_agent_id": "agent-1",
  "to_agent_id": "agent-2",
  "message_type": "response",
  "content": {...}
}
```

---

## 🚀 Getting Started

### 1. Start Backend

```bash
cd c:\Users\aiden\hermes
python -m uvicorn backend.main:app --reload --port 8000
```

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

### 3. Set Your Preferences

```bash
curl -X POST http://localhost:8000/api/v1/preferences \
  -H "X-User-ID: yourname" \
  -H "Content-Type: application/json" \
  -d '{"preset": "balanced"}'
```

### 4. Deploy Agents (Example)

```python
# Run the SDK example
python backend/mesh/agent_sdk.py

# This deploys WeatherAgent, RestaurantAgent, EventAgent
```

### 5. Chat with Mesh

Go to http://localhost:3001/chat and type:

```
"Find weather in Tokyo and recommend restaurants"
```

Watch agents bid, execute, and deliver results autonomously!

---

## 🎯 Key Takeaways

1. **User controls awarding** via customizable preference weights
2. **Agents deploy anywhere** - local, cloud, or business infrastructure
3. **Agents communicate autonomously** for complex coordination
4. **No human intervention needed** - fully autonomous operations
5. **Hermes is the substrate** for ALL agent communication

**This is the future of autonomous AI systems.** 🚀
