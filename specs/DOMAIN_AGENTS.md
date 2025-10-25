# Domain-Specific Agent Capability Specifications

This document defines **concrete agent types** across major domains that the Mesh Protocol should support from day one. Each specification includes capability schemas, interaction patterns, and integration requirements.

---

## 1. Travel & Hospitality

### 1.1 Flight Search & Booking Agent

**Capabilities:**
- `flight_search` - Search flights by origin, destination, dates
- `flight_book` - Book confirmed flights
- `flight_modify` - Change existing bookings
- `flight_cancel` - Cancel bookings with refund calculation
- `fare_rules` - Retrieve fare conditions and restrictions

**Input Schema (flight_search):**
```json
{
  "origin": "SFO",
  "destination": "JFK",
  "departure_date": "2026-03-12",
  "return_date": "2026-03-15",
  "passengers": {
    "adults": 2,
    "children": 0,
    "infants": 0
  },
  "cabin_class": "economy",
  "max_price": 500,
  "max_stops": 1,
  "preferred_airlines": ["UA", "AA"],
  "loyalty_programs": [
    {"airline": "UA", "number": "123456"}
  ]
}
```

**Output Schema:**
```json
{
  "flights": [
    {
      "id": "flight-001",
      "outbound": {
        "departure": "2026-03-12T08:00:00Z",
        "arrival": "2026-03-12T16:30:00Z",
        "duration_minutes": 330,
        "stops": 0,
        "carrier": "UA",
        "flight_number": "UA123",
        "aircraft": "Boeing 737",
        "cabin_class": "economy"
      },
      "return": {...},
      "price": {
        "total": 450,
        "currency": "USD",
        "breakdown": {
          "base_fare": 380,
          "taxes": 70
        }
      },
      "fare_rules": {
        "refundable": false,
        "changeable": true,
        "change_fee": 75
      },
      "loyalty_earned": {
        "miles": 2500,
        "program": "MileagePlus"
      }
    }
  ],
  "search_id": "search-abc123",
  "expires_at": "2026-03-11T12:00:00Z"
}
```

**Integration APIs:**
- Amadeus GDS
- Sabre
- Skyscanner
- Google Flights API
- Direct airline APIs

### 1.2 Hotel Search & Booking Agent

**Capabilities:**
- `hotel_search` - Search hotels by location, dates, price
- `hotel_book` - Reserve rooms
- `hotel_modify` - Change reservations
- `hotel_cancel` - Cancel with refund calculation
- `loyalty_integrate` - Apply loyalty programs

**Input Schema (hotel_search):**
```json
{
  "location": {
    "type": "city",
    "value": "San Francisco",
    "coordinates": {
      "lat": 37.7749,
      "lon": -122.4194
    }
  },
  "checkin": "2026-03-12",
  "checkout": "2026-03-15",
  "rooms": 1,
  "guests": {
    "adults": 2,
    "children": 0
  },
  "budget": {
    "min": 100,
    "max": 200,
    "currency": "USD"
  },
  "amenities": ["wifi", "parking", "gym"],
  "preferences": {
    "star_rating": 4,
    "near_transit": true,
    "non_smoking": true
  },
  "loyalty_programs": [
    {"chain": "Hilton", "number": "123456"}
  ]
}
```

**Output Schema:**
```json
{
  "hotels": [
    {
      "id": "hotel-001",
      "name": "Hilton San Francisco",
      "star_rating": 4,
      "location": {
        "address": "333 O'Farrell St",
        "coordinates": {"lat": 37.7858, "lon": -122.4106},
        "transit_distance_meters": 200
      },
      "rooms": [
        {
          "type": "Standard King",
          "price_per_night": 180,
          "currency": "USD",
          "total_price": 540,
          "amenities": ["wifi", "tv", "minibar"],
          "bed_type": "king",
          "max_occupancy": 2
        }
      ],
      "hotel_amenities": ["gym", "pool", "restaurant", "parking"],
      "cancellation_policy": {
        "free_until": "2026-03-10T23:59:59Z",
        "penalty_after": 90
      },
      "loyalty_benefits": {
        "points_earned": 1500,
        "program": "Hilton Honors",
        "elite_benefits": ["late_checkout", "room_upgrade"]
      },
      "rating": {
        "overall": 4.3,
        "cleanliness": 4.5,
        "service": 4.2,
        "location": 4.6,
        "reviews_count": 1523
      }
    }
  ],
  "search_id": "search-hotel-xyz",
  "expires_at": "2026-03-11T12:00:00Z"
}
```

**Integration APIs:**
- Expedia Rapid API
- Booking.com API
- Hotels.com
- Direct hotel chains (Hilton, Marriott, etc.)

### 1.3 Travel Planner (Multi-Modal Coordinator)

**Capabilities:**
- `plan_trip` - Coordinate flight, hotel, activities
- `optimize_itinerary` - Minimize cost, time, or maximize experiences
- `handle_changes` - Adapt to flight delays, cancellations

**Coordination Pattern:**
This agent **orchestrates** other agents (flight, hotel, restaurant, etc.) and uses shared context for optimal planning.

```python
async def plan_trip(contract):
  # Phase 1: Discover capable agents
  flight_agents = await mesh.query_capabilities("flight_search")
  hotel_agents = await mesh.query_capabilities("hotel_search")
  
  # Phase 2: Create sub-contracts
  flight_contract = create_sub_contract(contract, "flight_search")
  hotel_contract = create_sub_contract(contract, "hotel_search")
  
  # Phase 3: Await results in parallel
  flight_results, hotel_results = await asyncio.gather(
    mesh.execute(flight_contract),
    mesh.execute(hotel_contract)
  )
  
  # Phase 4: Write coordinated plan to shared context
  await context.add_fact(
    f"{contract.id}.itinerary",
    {
      "flights": flight_results,
      "hotels": hotel_results,
      "total_cost": calculate_total(flight_results, hotel_results)
    },
    source=agent.id
  )
```

---

## 2. Food & Dining

### 2.1 Restaurant Discovery Agent

**Capabilities:**
- `restaurant_search` - Find restaurants by location, cuisine, price
- `restaurant_details` - Get menu, hours, reviews
- `dietary_filter` - Filter by vegan, gluten-free, etc.

**Input Schema:**
```json
{
  "location": {
    "type": "coordinates",
    "lat": 37.7749,
    "lon": -122.4194,
    "radius_meters": 1000
  },
  "cuisine": ["italian", "mexican"],
  "dietary": ["vegan", "gluten_free"],
  "price_range": "$$",
  "meal_time": "dinner",
  "party_size": 4,
  "features": ["outdoor_seating", "reservations"]
}
```

**Integration APIs:**
- Yelp Fusion API
- Google Places API
- Foursquare Places API
- Zomato

### 2.2 Reservation & Waitlist Agent

**Capabilities:**
- `restaurant_reserve` - Book table via OpenTable, Resy
- `waitlist_join` - Add to waitlist
- `reservation_modify` - Change time/party size
- `reservation_cancel` - Cancel booking

**Integration APIs:**
- OpenTable API
- Resy API
- Direct restaurant integrations

---

## 3. Health & Medical

### 3.1 Primary Care Front-Desk Agent

**Capabilities:**
- `appointment_schedule` - Book doctor appointments
- `appointment_reminder` - Send reminders
- `intake_form` - Collect patient information
- `insurance_verify` - Check eligibility

**HIPAA Compliance:**
```json
{
  "contract": {
    "hipaa_mode": true,
    "encryption": "AES-256",
    "audit_log": true,
    "data_residency": "US",
    "human_in_loop": true
  }
}
```

**Input Schema:**
```json
{
  "patient": {
    "id": "did:patient:abc123",
    "consent_token": "jwt-token-with-scopes"
  },
  "appointment_type": "annual_checkup",
  "preferred_dates": ["2026-03-12", "2026-03-13"],
  "preferred_times": ["morning", "afternoon"],
  "insurance": {
    "provider": "BlueCross",
    "policy_number": "encrypted-token",
    "group_number": "encrypted-token"
  },
  "reason": "Annual physical examination"
}
```

**Integration APIs:**
- Epic MyChart API
- Cerner API
- Athenahealth API
- CoverMyMeds (for pre-authorization)

### 3.2 Dentist Front-Office Agent

**Capabilities:**
- `dental_appointment_schedule`
- `treatment_code_lookup` - Find procedure codes
- `insurance_preauth` - Get pre-authorization
- `post_visit_instructions` - Send care instructions

### 3.3 Specialist Referral Coordinator

**Capabilities:**
- `referral_initiate` - Start specialist referral
- `records_transfer` - Send medical records
- `insurance_preauth` - Get authorization
- `appointment_coordinate` - Schedule specialist visit

---

## 4. Professional Services

### 4.1 Legal Intake Agent

**Capabilities:**
- `consultation_schedule` - Book legal consultations
- `intake_questionnaire` - Collect case information
- `document_collection` - Request relevant documents
- `conflict_check` - Check for conflicts of interest

**Input Schema:**
```json
{
  "legal_issue": "contract_dispute",
  "urgency": "high",
  "jurisdiction": "California",
  "budget": {
    "max": 5000,
    "currency": "USD"
  },
  "preferred_contact": "email",
  "confidential": true
}
```

### 4.2 Real Estate Showing Scheduler

**Capabilities:**
- `property_search` - Find properties
- `showing_schedule` - Arrange property tours
- `offer_assist` - Help with offer preparation
- `inspection_coordinate` - Schedule inspections

---

## 5. Commerce & Finance

### 5.1 Purchase Agent

**Capabilities:**
- `product_search` - Find products across retailers
- `price_compare` - Compare prices and deals
- `purchase_execute` - Complete purchase
- `tracking_monitor` - Track shipments

**Input Schema:**
```json
{
  "product": "iPhone 15 Pro",
  "specifications": {
    "color": "titanium",
    "storage": "256GB"
  },
  "max_price": 1000,
  "shipping": {
    "address": "encrypted-token",
    "speed": "standard"
  },
  "payment_method": "did:payment:stripe-token",
  "retailer_preferences": ["Apple", "Amazon", "BestBuy"]
}
```

### 5.2 Subscription Manager

**Capabilities:**
- `subscription_list` - List all active subscriptions
- `subscription_cancel` - Cancel subscriptions
- `subscription_negotiate` - Negotiate better rates
- `subscription_optimize` - Recommend cheaper alternatives

---

## 6. Home & IoT

### 6.1 Home Maintenance Coordinator

**Capabilities:**
- `service_schedule` - Book plumber, electrician, etc.
- `quote_compare` - Compare service quotes
- `emergency_dispatch` - Handle urgent issues
- `warranty_check` - Verify warranty coverage

### 6.2 Smart Home Orchestration Agent

**Capabilities:**
- `device_control` - Control smart devices
- `automation_create` - Set up automations
- `energy_optimize` - Reduce energy usage
- `security_monitor` - Monitor security cameras/sensors

**Integration APIs:**
- HomeKit
- Google Home
- Alexa Smart Home
- SmartThings

---

## 7. Meta / Platform Agents

### 7.1 Capability Registry Agent

**Responsibilities:**
- Maintain agent directory
- Index capabilities with embeddings
- Handle agent registration
- Provide discovery API

**Storage:**
- Postgres: Agent metadata, capabilities, pricing
- Qdrant: Capability embeddings for semantic search

### 7.2 Reputation & Adjudication Agent

**Responsibilities:**
- Track contract completions/failures
- Calculate reputation scores
- Handle disputes
- Implement human review for edge cases

**Algorithm:**
```python
def update_reputation(agent_id, event):
  current = get_reputation(agent_id)
  
  if event.type == "completion":
    impact = +0.05 * event.validator_rating
  elif event.type == "failure":
    impact = -0.10
  elif event.type == "dispute_lost":
    impact = -0.15
  
  # Weighted moving average
  new_score = 0.9 * current.score + 0.1 * impact
  
  update_db(agent_id, {
    "score": new_score,
    "contracts_completed": current.contracts_completed + 1,
    "last_updated": now()
  })
```

### 7.3 Validator Agent (Generic)

**Capabilities:**
- `validate_confirmation_code` - Check booking confirmations
- `validate_receipt` - Verify receipts
- `validate_proof` - Check cryptographic proofs
- `validate_human_review` - Escalate to human

**Plugins:**
Each validator type is a plugin:
```typescript
interface ValidatorPlugin {
  name: string;
  validate(deliverable: Deliverable, contract: Contract): Promise<ValidationResult>;
}

class ConfirmationCodeValidator implements ValidatorPlugin {
  name = "confirmation_code";
  
  async validate(deliverable, contract) {
    const code = deliverable.data.confirmation_code;
    
    // Check format (airline: 6 alphanumeric)
    if (!/^[A-Z0-9]{6}$/.test(code)) {
      return { valid: false, reason: "Invalid format" };
    }
    
    // Verify with carrier API (if available)
    const verified = await verifyWithCarrier(code, contract.context);
    
    return { valid: verified, confidence: 0.95 };
  }
}
```

---

## 8. Sandbox & QA Agent

**Purpose:** Test agents before production admission

**Capabilities:**
- `agent_simulate` - Run agent in sandbox
- `contract_fuzz` - Test with edge cases
- `security_scan` - Check for vulnerabilities
- `performance_benchmark` - Measure latency/cost

**Sandbox Environment:**
- Docker container with resource limits
- Network isolation (only test endpoints)
- Timeout: 30 seconds max
- Memory: 512MB max
- CPU: 0.5 core max

**Approval Criteria:**
- 95%+ success rate on test contracts
- < 5s average latency
- Zero security violations
- Valid signatures on all messages

---

## Agent Interaction Patterns

### Pattern 1: Direct Execution (Simple)

```
User → Contract → Agent A → Delivery → User
```

Example: Search flights

### Pattern 2: Coordination (Multi-Agent)

```
User → Contract → Coordinator Agent
                     ↓
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Agent A    Agent B    Agent C
          ↓          ↓          ↓
       Result A   Result B   Result C
          ↓          ↓          ↓
          └──────────┼──────────┘
                     ↓
            Coordinator Agent → Delivery → User
```

Example: Plan entire trip (flight + hotel + restaurant)

### Pattern 3: Pipeline (Sequential)

```
User → Contract → Agent A → Context
                             ↓
                          Agent B → Context
                             ↓
                          Agent C → Delivery → User
```

Example: Research → Summarize → Format

### Pattern 4: Auction & Fallback

```
User → Contract → Auction
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     Bid A        Bid B        Bid C
        ↓            ↓            ↓
     Winner selected: Agent B
                     ↓
                  Execute
                     ↓
                  Fails!
                     ↓
            Fallback to Agent C
                     ↓
                  Success → Delivery → User
```

---

## Testing Matrix

Each agent type must pass:

| Test Type | Description | Pass Criteria |
|-----------|-------------|---------------|
| Unit | Capability schemas valid | 100% |
| Integration | APIs return expected data | 95% |
| Security | Signatures verify, no PII leakage | 100% |
| Performance | Latency < target | 90th percentile |
| Chaos | Handles network failures, timeouts | Graceful degradation |
| Cost | Price within budget | 95% |

---

## Developer Onboarding (Quick Start)

### 1. Generate DID

```bash
npm install @mesh-protocol/sdk

npx mesh keygen
# Outputs:
# DID: did:key:z6Mk...
# Private Key: [saved to ~/.mesh/keys/private.pem]
# Public Key: [saved to ~/.mesh/keys/public.pem]
```

### 2. Register Agent

```typescript
import { MeshClient } from '@mesh-protocol/sdk';

const client = new MeshClient({
  did: 'did:key:z6Mk...',
  privateKeyPath: '~/.mesh/keys/private.pem',
  meshUrl: 'wss://mesh.hermes.network'
});

await client.registerAgent({
  name: 'MyHotelBot',
  capabilities: [
    {
      name: 'hotel_search',
      description: 'Search hotels by location and dates',
      confidence: 0.9,
      cost: 1.0,
      latency: 3.0
    }
  ],
  endpoint: 'wss://mybot.example.com'
});
```

### 3. Listen for Contracts

```typescript
client.on('contract_announced', async (contract) => {
  // Check if we can handle this
  if (contract.intent === 'hotel_search') {
    // Submit bid
    await client.submitBid({
      contract_id: contract.contract_id,
      price: 2.50,
      eta_seconds: 5,
      confidence: 0.9
    });
  }
});

client.on('contract_awarded', async ({ contract_id, agent_id }) => {
  if (agent_id === client.did) {
    // We won! Execute
    const result = await executeHotelSearch(contract_id);
    
    // Deliver
    await client.deliver({
      contract_id,
      items: [{ type: 'data', data: result }]
    });
  }
});
```

---

## Conclusion

These domain-specific agents provide **concrete use cases** that:
- Validate the protocol design
- Demonstrate real-world value
- Enable immediate adoption
- Cover high-value markets (travel, health, home services)

Next: Implement reference agents for each domain as **open-source examples**.
