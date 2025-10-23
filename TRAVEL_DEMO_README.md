# 🌍 Hermes Travel Planning Demo

Multi-agent travel planning demonstration showcasing agent discovery, orchestration, and human-in-the-loop collaboration.

**✅ Fully A2A Protocol v0.3.0 Compliant** - All agents implement Google's Agent-to-Agent protocol with JSON-RPC 2.0, SSE streaming, and proper task lifecycle management.

## Quick Start

### 1. Start the Agents

```bash
# Start all 4 travel planning agents
./start_travel_agents.sh
```

This starts:
- 🛫 FlightBooker (port 10010)
- 🏨 HotelBooker (port 10011)
- 🍽️ RestaurantFinder (port 10012)
- 🎭 EventsFinder (port 10013)

### 2. Register Agents in Database

```bash
python scripts/register_travel_agents.py
```

### 3. Try Travel Planning!

Ask Hermes:
- "Plan a trip to Paris for me"
- "I want to visit Tokyo next month"
- "Find flights and hotels to New York for December 15-20"
- "I need a restaurant reservation in London"
- "What events are happening in LA this weekend?"

## How It Works

### Agent Discovery

When you ask "Plan a trip to Paris":

1. **Intent Parser** identifies you need: flights, hotels, dining, activities
2. **Agent Registry** searches for agents with matching capabilities
3. **Conductor** discovers: FlightBooker, HotelBooker, RestaurantFinder, EventsFinder

### Human-in-the-Loop

Agents ask follow-up questions when they need more information:

```
User: "Book me a flight to Paris"
FlightBooker: "Where will you be departing from? (e.g., LAX, JFK, SFO)"
User: "LAX"
FlightBooker: "When would you like to depart from LAX to Paris?"
User: "December 15th"
FlightBooker: "✈️ Found 3 flights from LAX to Paris..."
```

### Multi-Agent Orchestration

For complex requests, the Conductor coordinates multiple agents:

```
User: "Plan a 3-day trip to Tokyo"

Conductor orchestrates:
1. FlightBooker → Finds flights to Tokyo
2. HotelBooker → Searches hotels near city center
3. RestaurantFinder → Recommends top-rated restaurants
4. EventsFinder → Suggests must-see attractions

Result: Complete travel itinerary with all bookings
```

## Agent Capabilities (A2A Skills)

### FlightBooker
**A2A Endpoint**: `http://localhost:10010`
**Agent Card**: `http://localhost:10010/.well-known/agent-card.json`
- `search_flights`: Find available flights based on origin, destination, dates, and preferences
- `book_flight`: Book a specific flight for a passenger
- `price_comparison`: Compare prices across airlines and dates

### HotelBooker
**A2A Endpoint**: `http://localhost:10011`
**Agent Card**: `http://localhost:10011/.well-known/agent-card.json`
- `search_hotels`: Find hotels by location, dates, price range, rating, amenities
- `book_hotel`: Reserve a hotel room with guest details

### RestaurantFinder
**A2A Endpoint**: `http://localhost:10012`
**Agent Card**: `http://localhost:10012/.well-known/agent-card.json`
- `find_restaurants`: Search restaurants by location, cuisine, budget, dietary needs
- `make_reservation`: Book a table at a specific restaurant

### EventsFinder
**A2A Endpoint**: `http://localhost:10013`
**Agent Card**: `http://localhost:10013/.well-known/agent-card.json`
- `find_events`: Discover local events, attractions, tours, museums, festivals
- `book_event`: Purchase tickets for events and activities

## Architecture

```
User Request
    ↓
Intent Parser (AI)
    ↓
Agent Discovery (Semantic Search)
    ↓
Conductor (Orchestration)
    ↓
Agents (Execute in parallel)
    ↓
Human-in-Loop (Follow-up questions)
    ↓
Final Result
```

## Stop Agents

```bash
./stop_travel_agents.sh
```

## A2A Protocol Features

### JSON-RPC 2.0 Support
All agents support JSON-RPC 2.0 requests:
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "taskId": "optional-task-id",
    "skill": "search_flights",
    "messages": [
      {
        "role": "user",
        "parts": [
          {"type": "text", "text": "Find flights from LAX to Paris"},
          {"type": "data", "data": {"origin": "LAX", "destination": "Paris"}}
        ]
      }
    ]
  },
  "id": 1
}
```

### Task Lifecycle
- **submitted**: Task received
- **working**: Agent processing
- **input-required**: Needs user input (human-in-the-loop)
- **completed**: Task finished successfully
- **failed**: Task failed with error
- **canceled**: Task canceled by user

### Server-Sent Events (SSE)
Stream task updates in real-time:
```
GET http://localhost:10010/stream/{taskId}
```

### Agent Discovery
Each agent exposes its capabilities via Agent Card:
```
GET http://localhost:10010/.well-known/agent-card.json
```

### Backwards Compatibility
Legacy `/execute` endpoint maintained for existing integrations.

## Next Steps

1. **Deploy agents**: Host agents as microservices on Railway/Cloud Run
2. **Add real APIs**: Integrate with Amadeus (flights), Booking.com (hotels), etc.
3. **Enhanced UI**: Show agent discovery and A2A protocol in real-time
4. **More agents**: Car rental, insurance, currency exchange
5. **Agent-to-Agent**: Enable agents to call each other via A2A protocol

---

**Try it now!** Start the agents and ask: "Plan a weekend trip to San Francisco"
