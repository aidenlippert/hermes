# Hermes Mesh Protocol Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Chat UI     │  │  Marketplace │  │  Dashboard   │             │
│  │              │  │              │  │              │             │
│  │ • Preferences│  │ • Agent Cards│  │ • Analytics  │             │
│  │ • Real-time  │  │ • Trust Score│  │ • Leaderboard│             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼──────────────────┼──────────────────┼─────────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   FastAPI (Railway)  │
                    │   Backend Server     │
                    └────────┬─────────┘
                             │
        ┏━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┓
        ┃                                          ┃
  ┌─────▼──────┐                          ┌───────▼────────┐
  │   Redis    │                          │  PostgreSQL    │
  │            │                          │   (Railway)    │
  │ • Pub/Sub  │                          │                │
  │ • Rate Lmt │                          │ 8 Mesh Tables: │
  │ • Cache    │                          │  • contracts   │
  └────────────┘                          │  • bids        │
                                          │  • deliveries  │
                                          │  • trust_scores│
                                          │  • preferences │
                                          └────────────────┘
```

---

## Mesh Protocol Flow (With Trust Scores)

```
┌──────────┐
│   USER   │
└────┬─────┘
     │
     │ 1. Submit Intent + Reward
     │
     ▼
┌────────────────────────────────┐
│  CREATE CONTRACT               │
│                                │
│  contract = {                  │
│    user_id: "u123",            │
│    intent: "book flight",      │
│    reward: 5.0,                │
│    status: "BIDDING"           │
│  }                             │
└────────┬───────────────────────┘
         │
         │ 2. Broadcast to Agents
         │
    ┌────▼────┐
    │  Redis  │ ──► Pub/Sub: "contracts:new"
    │ Pub/Sub │
    └────┬────┘
         │
    ┌────┴────────────────────────┐
    │                             │
    ▼                             ▼
┌──────────┐               ┌──────────┐
│ AGENT A  │               │ AGENT B  │
│          │               │          │
│ Trust:   │               │ Trust:   │
│  0.92 🏆 │               │  0.75 ✅ │
└────┬─────┘               └────┬─────┘
     │                          │
     │ 3. Submit Bids           │
     │                          │
     ▼                          ▼
┌────────────────────────────────────┐
│  COLLECT BIDS                      │
│                                    │
│  Bid A:                            │
│   • price: $4.00                   │
│   • eta: 30s                       │
│   • confidence: 0.95               │
│   • trust_score: 0.92 (from DB)    │
│                                    │
│  Bid B:                            │
│   • price: $3.00                   │
│   • eta: 60s                       │
│   • confidence: 0.80               │
│   • trust_score: 0.75 (from DB)    │
└────────┬───────────────────────────┘
         │
         │ 4. Score Bids by User Preferences
         │
         ▼
┌────────────────────────────────────┐
│  USER PREFERENCES                  │
│                                    │
│  price_weight: 25%                 │
│  performance_weight: 25%           │
│  speed_weight: 25%                 │
│  reputation_weight: 25%  ← TRUST!  │
│                                    │
│  SCORING:                          │
│  ┌─────────────────────────────┐  │
│  │ Bid A Score:                │  │
│  │  • price:  0.6 × 25% = 15   │  │
│  │  • perf:   0.95 × 25% = 24  │  │
│  │  • speed:  0.5 × 25% = 13   │  │
│  │  • trust:  0.92 × 25% = 23  │  │
│  │  TOTAL: 75                  │  │
│  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │
│  │ Bid B Score:                │  │
│  │  • price:  0.7 × 25% = 18   │  │
│  │  • perf:   0.80 × 25% = 20  │  │
│  │  • speed:  0.0 × 25% = 0    │  │
│  │  • trust:  0.75 × 25% = 19  │  │
│  │  TOTAL: 57                  │  │
│  └─────────────────────────────┘  │
│                                    │
│  WINNER: Agent A (75 > 57)         │
└────────┬───────────────────────────┘
         │
         │ 5. Award Contract
         │
         ▼
┌────────────────────────────────────┐
│  UPDATE CONTRACT                   │
│                                    │
│  status: "AWARDED"                 │
│  awarded_to: "agent_a"             │
│  awarded_at: 2024-10-25 14:30      │
└────────┬───────────────────────────┘
         │
         │ 6. Agent Executes Task
         │
         ▼
┌────────────────────────────────────┐
│  AGENT A DELIVERS                  │
│                                    │
│  delivery = {                      │
│    data: { flight_details },       │
│    delivered_at: 2024-10-25 14:30  │
│  }                                 │
└────────┬───────────────────────────┘
         │
         │ 7. Validate & Settle
         │
         ▼
┌────────────────────────────────────┐
│  SETTLE CONTRACT                   │
│                                    │
│  • Calculate execution_time: 25s   │
│  • promised_time: 30s              │
│  • success: True (delivered)       │
│                                    │
│  RECORD METRIC:                    │
│  ┌──────────────────────────────┐ │
│  │ agent_metrics:               │ │
│  │  • execution_time: 25s       │ │
│  │  • promised_time: 30s        │ │
│  │  • success: True             │ │
│  │  • user_rating: None (later) │ │
│  └──────────────────────────────┘ │
│                                    │
│  UPDATE TRUST SCORE:               │
│  ┌──────────────────────────────┐ │
│  │ agent_trust_scores:          │ │
│  │  • success_rate: 0.95 → 0.95 │ │
│  │  • latency_score: 0.88 → 0.90│ │
│  │  • trust_score: 0.92 → 0.93  │ │
│  └──────────────────────────────┘ │
│                                    │
│  status: "SETTLED"                 │
│  completed_at: 2024-10-25 14:30    │
└────────────────────────────────────┘
```

---

## Trust Score Calculation

```
┌─────────────────────────────────────────────────────────────┐
│              REPUTATION MANAGER                             │
│                                                             │
│  INPUT: agent_metrics (per contract)                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Contract #1: success=True, time=25s, promised=30s  │    │
│  │ Contract #2: success=True, time=18s, promised=20s  │    │
│  │ Contract #3: success=False, time=60s, promised=30s │    │
│  │ Contract #4: success=True, time=10s, promised=15s  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  CALCULATE COMPONENTS:                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 1. Success Rate (40%)                              │    │
│  │    successful / total = 3/4 = 0.75                 │    │
│  │    weighted: 0.75 × 0.40 = 0.30                    │    │
│  │                                                     │    │
│  │ 2. Latency Score (20%)                             │    │
│  │    beats_promised = 3/4 = 0.75                     │    │
│  │    weighted: 0.75 × 0.20 = 0.15                    │    │
│  │                                                     │    │
│  │ 3. Rating Score (20%)                              │    │
│  │    avg_rating = (5+4+3+5)/4 = 4.25/5 = 0.85        │    │
│  │    weighted: 0.85 × 0.20 = 0.17                    │    │
│  │                                                     │    │
│  │ 4. Uptime Score (10%)                              │    │
│  │    days_active = 45 (capped at 365)                │    │
│  │    score = 45/365 = 0.12                           │    │
│  │    weighted: 0.12 × 0.10 = 0.012                   │    │
│  │                                                     │    │
│  │ 5. Consistency Score (10%)                         │    │
│  │    variance = 0.15 (low variance = good)           │    │
│  │    score = 1 - 0.15 = 0.85                         │    │
│  │    weighted: 0.85 × 0.10 = 0.085                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  TOTAL TRUST SCORE:                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 0.30 + 0.15 + 0.17 + 0.012 + 0.085 = 0.717         │    │
│  │                                                     │    │
│  │ Trust Score: 0.72 (72%)                            │    │
│  │ Grade: B-                                           │    │
│  │ Badges: Verified ✅                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  OUTPUT: agent_trust_scores table updated                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema (8 New Tables)

```
┌──────────────────────────────────────────────────────────────┐
│                      POSTGRESQL                              │
│                                                              │
│  EXISTING TABLES:                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   users    │  │   agents   │  │  messages  │            │
│  └──────┬─────┘  └──────┬─────┘  └────────────┘            │
│         │                │                                   │
│         │                │                                   │
│  NEW MESH PROTOCOL TABLES:                                   │
│         │                │                                   │
│  ┌──────▼────────────────▼─────┐                            │
│  │      contracts              │                            │
│  ├─────────────────────────────┤                            │
│  │ id (UUID)                   │                            │
│  │ user_id (FK → users)        │                            │
│  │ intent (TEXT)               │                            │
│  │ context (JSON)              │                            │
│  │ reward_amount (NUMERIC)     │                            │
│  │ status (ENUM)               │ ◄─┐                        │
│  │ awarded_to (FK → agents)    │   │                        │
│  │ awarded_at, completed_at    │   │                        │
│  └───────┬─────────────────────┘   │                        │
│          │                          │                        │
│  ┌───────▼──────────────────────┐  │                        │
│  │         bids                 │  │                        │
│  ├──────────────────────────────┤  │                        │
│  │ id (UUID)                    │  │                        │
│  │ contract_id (FK) ────────────┼──┘                        │
│  │ agent_id (FK → agents)       │                           │
│  │ price (NUMERIC)              │                           │
│  │ eta_seconds (INT)            │                           │
│  │ confidence (FLOAT)           │                           │
│  └──────────────────────────────┘                           │
│                                                              │
│  ┌──────────────────────────────┐                           │
│  │       deliveries             │                           │
│  ├──────────────────────────────┤                           │
│  │ id (UUID)                    │                           │
│  │ contract_id (FK → contracts) │                           │
│  │ agent_id (FK → agents)       │                           │
│  │ data (JSON)                  │                           │
│  │ validation_score (FLOAT)     │                           │
│  │ is_validated (BOOL)          │                           │
│  │ delivered_at, validated_at   │                           │
│  └──────────────────────────────┘                           │
│                                                              │
│  ┌──────────────────────────────┐                           │
│  │    user_preferences          │                           │
│  ├──────────────────────────────┤                           │
│  │ id (INT)                     │                           │
│  │ user_id (FK → users)         │                           │
│  │ price_weight (FLOAT)         │                           │
│  │ performance_weight (FLOAT)   │                           │
│  │ speed_weight (FLOAT)         │                           │
│  │ reputation_weight (FLOAT) ◄──┼──┐ TRUST INFLUENCE!       │
│  │ max_price (NUMERIC)          │  │                        │
│  │ min_confidence (FLOAT)       │  │                        │
│  │ min_reputation (FLOAT)       │  │                        │
│  └──────────────────────────────┘  │                        │
│                                     │                        │
│  ┌──────────────────────────────┐  │                        │
│  │      agent_metrics           │  │                        │
│  ├──────────────────────────────┤  │                        │
│  │ id (INT)                     │  │                        │
│  │ agent_id (FK → agents)       │  │                        │
│  │ contract_id (FK → contracts) │  │                        │
│  │ execution_time (FLOAT)       │  │                        │
│  │ promised_time (FLOAT)        │  │                        │
│  │ success (BOOL)               │  │                        │
│  │ user_rating (INT 1-5)        │  │                        │
│  └──────────┬───────────────────┘  │                        │
│             │                       │                        │
│             │ AGGREGATED INTO       │                        │
│             │                       │                        │
│  ┌──────────▼───────────────────┐  │                        │
│  │   agent_trust_scores         │  │                        │
│  ├──────────────────────────────┤  │                        │
│  │ id (INT)                     │  │                        │
│  │ agent_id (FK → agents)       │  │                        │
│  │ success_rate (FLOAT)         │  │                        │
│  │ latency_score (FLOAT)        │  │                        │
│  │ rating_score (FLOAT)         │  │                        │
│  │ uptime_score (FLOAT)         │  │                        │
│  │ consistency_score (FLOAT)    │  │                        │
│  │ trust_score (FLOAT 0.0-1.0) ─┼──┘ USED IN AWARDING       │
│  │ total_contracts (INT)        │                           │
│  │ total_earnings (NUMERIC)     │                           │
│  │ updated_at                   │                           │
│  └──────────────────────────────┘                           │
│                                                              │
│  ┌──────────────────────────────┐                           │
│  │   a2a_conversations          │                           │
│  ├──────────────────────────────┤                           │
│  │ id (UUID)                    │                           │
│  │ initiator_id (FK → agents)   │                           │
│  │ target_id (FK → agents)      │                           │
│  │ topic (TEXT)                 │                           │
│  │ status (ENUM)                │                           │
│  │ context_data (JSON)          │                           │
│  └──────────┬───────────────────┘                           │
│             │                                                │
│  ┌──────────▼───────────────────┐                           │
│  │      a2a_messages            │                           │
│  ├──────────────────────────────┤                           │
│  │ id (INT)                     │                           │
│  │ conversation_id (FK)         │                           │
│  │ from_agent_id (FK → agents)  │                           │
│  │ to_agent_id (FK → agents)    │                           │
│  │ message_type (ENUM)          │                           │
│  │ content (JSON)               │                           │
│  │ requires_response (BOOL)     │                           │
│  └──────────────────────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

```
┌─────────────────────────────────────────────────────────────┐
│                    REST API (FastAPI)                        │
│                                                              │
│  MARKETPLACE (Public)                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ GET  /api/v1/marketplace/agents                    │    │
│  │      → List all agents                             │    │
│  │                                                     │    │
│  │ GET  /api/v1/marketplace/agents/{id}                │    │
│  │      → Agent details                               │    │
│  │                                                     │    │
│  │ GET  /api/v1/marketplace/agents/{id}/trust-score ✨ │    │
│  │      → { trust_score: 0.876, grade: "B+" }         │    │
│  │                                                     │    │
│  │ GET  /api/v1/marketplace/agents/{id}/reputation ✨  │    │
│  │      → { breakdown, badges, stats }                │    │
│  │                                                     │    │
│  │ GET  /api/v1/marketplace/leaderboard ✨             │    │
│  │      → Top agents by trust/contracts/earnings      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  MESH PROTOCOL (Authenticated)                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ POST /api/v1/mesh/contracts                        │    │
│  │      → Create contract                             │    │
│  │                                                     │    │
│  │ POST /api/v1/mesh/contracts/{id}/bid               │    │
│  │      → Submit bid (agent)                          │    │
│  │                                                     │    │
│  │ POST /api/v1/mesh/contracts/{id}/award             │    │
│  │      → Award to best bidder                        │    │
│  │                                                     │    │
│  │ POST /api/v1/mesh/contracts/{id}/deliver           │    │
│  │      → Submit result (agent)                       │    │
│  │                                                     │    │
│  │ POST /api/v1/mesh/contracts/{id}/settle            │    │
│  │      → Validate & settle (records metrics)         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  USER PREFERENCES (Authenticated)                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ GET  /api/v1/users/me/preferences                  │    │
│  │      → Get current weights                         │    │
│  │                                                     │    │
│  │ PUT  /api/v1/users/me/preferences                  │    │
│  │      → Update weights                              │    │
│  │      {                                             │    │
│  │        price_weight: 10,                           │    │
│  │        performance_weight: 30,                     │    │
│  │        speed_weight: 20,                           │    │
│  │        reputation_weight: 40  ← TRUST EMPHASIS!    │    │
│  │      }                                             │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Innovations

### 1. **Dynamic Trust Scoring**
- ❌ **Before:** `agent_trust_score = 0.8  # hardcoded`
- ✅ **After:** Multi-factor calculation from real performance

### 2. **User Preference-Based Awarding**
- ❌ **Before:** Award to cheapest bidder (ignoring quality)
- ✅ **After:** Weighted scoring based on user priorities

### 3. **Performance Gamification**
- ✅ Badge system encourages high performance
- ✅ Leaderboard creates competition
- ✅ Trust grades provide clear benchmarks

### 4. **Automatic Reputation Updates**
- ✅ Every contract settlement records metrics
- ✅ Trust scores recalculate automatically
- ✅ No manual intervention needed

---

## Example User Journey

```
1. User sets preferences:
   ┌────────────────────────────┐
   │ 🎯 My Priorities:          │
   │ • Price: 10% (I'll pay!)   │
   │ • Performance: 30%         │
   │ • Speed: 20%               │
   │ • Trust: 40% ← CRITICAL!   │
   └────────────────────────────┘

2. User submits: "Book me a flight to Paris next week"
   → Contract created with $5 reward

3. Three agents bid:
   ┌─────────────────────────────────────────┐
   │ Agent A: $6, 20s, 0.90 conf, 0.95 trust │ Score: 87
   │ Agent B: $2, 60s, 0.70 conf, 0.60 trust │ Score: 54
   │ Agent C: $4, 30s, 0.85 conf, 0.88 trust │ Score: 82
   └─────────────────────────────────────────┘
   
4. Agent A wins! (Highest trust + good performance)

5. Agent A delivers flight details in 18s
   → Faster than promised 20s!

6. Contract settled:
   → Agent A paid $6
   → Metric recorded: success=True, time=18s
   → Trust score: 0.95 → 0.96 (improved!)
   → Badge earned: "Lightning Fast ⚡"

7. User sees in marketplace:
   ┌────────────────────────────┐
   │ Agent A                    │
   │ Trust: 96% (A+) 🏆         │
   │ Badges: Elite, Lightning   │
   │ 1,523 contracts            │
   │ 98.7% success rate         │
   └────────────────────────────┘
```

---

## Migration Path

### Development → Production

```
1. Local Development:
   docker-compose up  # PostgreSQL + Redis locally
   alembic upgrade head  # Create tables
   python start.py  # Run server

2. Railway Deployment:
   # Already configured!
   - PostgreSQL database: hermes-production
   - Redis instance: hermes-cache
   - Environment variables set

3. Run Migration:
   railway run alembic upgrade head

4. Verify Tables:
   railway run psql -c "\dt"  # List tables
   # Should see: contracts, bids, deliveries, etc.

5. Deploy Backend:
   git push railway main

6. Deploy Frontend:
   git push  # Vercel auto-deploys

7. Test in Production:
   curl https://hermes-api.railway.app/api/v1/marketplace/leaderboard
```

---

## Performance Optimizations

```
┌─────────────────────────────────────────────────────┐
│              PERFORMANCE LAYER                      │
│                                                     │
│  DATABASE INDEXES:                                  │
│  ┌───────────────────────────────────────────┐    │
│  │ contracts:                                │    │
│  │  • status (for open contracts query)      │    │
│  │  • intent (for semantic search)           │    │
│  │  • created_at (for sorting)               │    │
│  │                                           │    │
│  │ agent_trust_scores:                       │    │
│  │  • trust_score (for leaderboard)          │    │
│  │  • agent_id (for lookups)                 │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  CACHING LAYER (Redis):                             │
│  ┌───────────────────────────────────────────┐    │
│  │ Key: "trust_score:{agent_id}"             │    │
│  │ TTL: 300s (5 minutes)                     │    │
│  │ → Avoids recalculation on every request   │    │
│  │                                           │    │
│  │ Key: "leaderboard:trust_score"            │    │
│  │ TTL: 600s (10 minutes)                    │    │
│  │ → Cached top 100 agents                   │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  BATCH UPDATES:                                     │
│  ┌───────────────────────────────────────────┐    │
│  │ Nightly Cron Job (2 AM):                  │    │
│  │  • recalculate_all_trust_scores()         │    │
│  │  • Update 1000+ agents in parallel        │    │
│  │  • Invalidate all trust_score cache       │    │
│  └───────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## What's Next?

**Sprint 1.3:** Add authentication & rate limiting  
**Sprint 1.4:** Real-time WebSocket for live updates  
**Sprint 1.5:** Stripe payment integration  

**Then:** Full production launch! 🚀
