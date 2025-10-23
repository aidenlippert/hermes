# 🌍 Hermes Travel Planning Demo

Multi-agent travel planning demonstration showcasing agent discovery, orchestration, and human-in-the-loop collaboration.

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

## Agent Capabilities

### FlightBooker
- `flight_search`: Find available flights
- `flight_booking`: Book selected flights
- `price_comparison`: Compare prices across airlines

### HotelBooker
- `hotel_search`: Search accommodations
- `hotel_booking`: Reserve rooms
- Filter by: price, amenities, rating, location

### RestaurantFinder
- `restaurant_search`: Discover dining options
- `restaurant_reservation`: Make reservations
- Filter by: cuisine, budget, dietary restrictions

### EventsFinder
- `events_search`: Find local events & attractions
- `activities`: Suggest things to do
- Categories: concerts, museums, tours, festivals

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

## Next Steps

1. **Deploy agents**: Host agents as microservices
2. **Add real APIs**: Integrate with Amadeus (flights), Booking.com (hotels), etc.
3. **Enhanced UI**: Show agent discovery and orchestration in real-time
4. **More agents**: Car rental, insurance, currency exchange

---

**Try it now!** Start the agents and ask: "Plan a weekend trip to San Francisco"
