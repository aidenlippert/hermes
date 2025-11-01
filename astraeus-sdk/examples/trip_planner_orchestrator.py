"""
TripPlanner Orchestrator - Autonomous Multi-Agent Workflow Example

This orchestrator demonstrates the full power of ASTRAEUS:
1. Human requests a trip plan
2. Orchestrator discovers BEST agents on network (by trust score)
3. Orchestrator calls multiple agents autonomously
4. Complete trip plan returned with credits automatically transferred
"""

import asyncio
from astraeus import Agent, AstraeusClient


orchestrator = Agent(
    name="TripPlannerOrchestrator",
    description="Plans complete trips autonomously by orchestrating multiple specialized agents",
    api_key="astraeus_demo_key_orchestrator",
    owner="orchestrator@example.com"
)


@orchestrator.capability(
    "plan_complete_trip",
    cost=2.00,
    description="Plan a complete trip including flights, hotel, activities, and weather"
)
async def plan_complete_trip(
    destination: str,
    dates: str,
    budget: float,
    preferences: dict = None
) -> dict:
    """
    Orchestrate multiple agents to plan a complete trip

    This demonstrates:
    - Autonomous agent discovery
    - Smart agent selection (by trust score)
    - Parallel agent calls for efficiency
    - Automatic credit transfers
    - Resilient error handling

    Args:
        destination: City/country to visit
        dates: Travel dates (e.g., "May 1-7, 2024")
        budget: Total budget in USD
        preferences: Optional preferences (hotel_rating, activities_type, etc.)

    Returns:
        Complete trip plan with all bookings and itinerary
    """
    print(f"\n{'='*60}")
    print(f"🌍 Planning Trip to {destination}")
    print(f"📅 Dates: {dates}")
    print(f"💰 Budget: ${budget}")
    print(f"{'='*60}\n")

    preferences = preferences or {}
    results = {
        "destination": destination,
        "dates": dates,
        "budget": budget,
        "agents_used": [],
        "total_cost": 0.0,
        "plan": {}
    }

    async with AstraeusClient(api_key="astraeus_demo_key_orchestrator") as client:

        print("🔍 Step 1: Discovering agents on ASTRAEUS network...\n")

        flight_agent = await client.find_best_agent(
            capability="search_flights",
            max_cost=1.0,
            min_trust_score=0.5
        )

        hotel_agent = await client.find_best_agent(
            capability="book_hotel",
            max_cost=1.0,
            min_trust_score=0.5
        )

        activity_agent = await client.find_best_agent(
            capability="recommend_activities",
            max_cost=0.5,
            min_trust_score=0.3
        )

        weather_agent = await client.find_best_agent(
            capability="get_weather",
            max_cost=0.1,
            min_trust_score=0.5
        )

        if flight_agent:
            print(f"✅ Found FlightAgent: {flight_agent['name']}")
            print(f"   Trust: {flight_agent.get('trust_score', 0):.2f} | Cost: ${flight_agent.get('base_cost_per_call', 0)}")
        else:
            print("❌ No flight agents available (using mock)")

        if hotel_agent:
            print(f"✅ Found HotelAgent: {hotel_agent['name']}")
            print(f"   Trust: {hotel_agent.get('trust_score', 0):.2f} | Cost: ${hotel_agent.get('base_cost_per_call', 0)}")
        else:
            print("❌ No hotel agents available (using mock)")

        if activity_agent:
            print(f"✅ Found ActivityAgent: {activity_agent['name']}")
            print(f"   Trust: {activity_agent.get('trust_score', 0):.2f} | Cost: ${activity_agent.get('base_cost_per_call', 0)}")
        else:
            print("❌ No activity agents available (using mock)")

        if weather_agent:
            print(f"✅ Found WeatherAgent: {weather_agent['name']}")
            print(f"   Trust: {weather_agent.get('trust_score', 0):.2f} | Cost: ${weather_agent.get('base_cost_per_call', 0)}")
        else:
            print("❌ No weather agents available (using mock)")

        print(f"\n{'='*60}")
        print("🤖 Step 2: Calling agents in parallel for efficiency...\n")

        tasks = []

        if flight_agent:
            tasks.append(call_flight_agent(client, flight_agent, destination, dates, budget * 0.5))
        else:
            tasks.append(mock_flight_search(destination, dates, budget * 0.5))

        if hotel_agent:
            tasks.append(call_hotel_agent(client, hotel_agent, destination, dates, budget * 0.35))
        else:
            tasks.append(mock_hotel_booking(destination, dates, budget * 0.35))

        if activity_agent:
            tasks.append(call_activity_agent(client, activity_agent, destination, dates, preferences))
        else:
            tasks.append(mock_activity_recommendations(destination))

        if weather_agent:
            tasks.append(call_weather_agent(client, weather_agent, destination))
        else:
            tasks.append(mock_weather_forecast(destination))

        flight_result, hotel_result, activity_result, weather_result = await asyncio.gather(*tasks)

        results["plan"]["flights"] = flight_result["data"]
        results["plan"]["hotel"] = hotel_result["data"]
        results["plan"]["activities"] = activity_result["data"]
        results["plan"]["weather"] = weather_result["data"]

        results["agents_used"] = [
            flight_result.get("agent_name", "MockFlightAgent"),
            hotel_result.get("agent_name", "MockHotelAgent"),
            activity_result.get("agent_name", "MockActivityAgent"),
            weather_result.get("agent_name", "MockWeatherAgent")
        ]

        results["total_cost"] = (
            flight_result.get("cost", 0) +
            hotel_result.get("cost", 0) +
            activity_result.get("cost", 0) +
            weather_result.get("cost", 0)
        )

    print(f"{'='*60}")
    print("✅ Trip Planning Complete!")
    print(f"💵 Total Agent Costs: ${results['total_cost']:.2f}")
    print(f"🤖 Agents Used: {len(results['agents_used'])}")
    print(f"{'='*60}\n")

    return results


async def call_flight_agent(client, agent, destination, dates, budget):
    """Call real flight search agent"""
    try:
        result = await client.call_agent(
            agent_id=agent['agent_id'],
            capability="search_flights",
            input={"destination": destination, "dates": dates, "max_price": budget}
        )
        print(f"✈️  FlightAgent: Found {len(result.get('result', {}).get('options', []))} flight options")
        return {
            "agent_name": agent['name'],
            "cost": result.get('cost', 0),
            "data": result.get('result', {})
        }
    except Exception as e:
        print(f"⚠️  FlightAgent failed: {e}, using mock")
        return await mock_flight_search(destination, dates, budget)


async def call_hotel_agent(client, agent, destination, dates, budget):
    """Call real hotel booking agent"""
    try:
        result = await client.call_agent(
            agent_id=agent['agent_id'],
            capability="book_hotel",
            input={"city": destination, "dates": dates, "budget": budget}
        )
        print(f"🏨 HotelAgent: Found {result.get('result', {}).get('hotel_name', 'hotel')}")
        return {
            "agent_name": agent['name'],
            "cost": result.get('cost', 0),
            "data": result.get('result', {})
        }
    except Exception as e:
        print(f"⚠️  HotelAgent failed: {e}, using mock")
        return await mock_hotel_booking(destination, dates, budget)


async def call_activity_agent(client, agent, destination, dates, preferences):
    """Call real activity recommendation agent"""
    try:
        result = await client.call_agent(
            agent_id=agent['agent_id'],
            capability="recommend_activities",
            input={"city": destination, "dates": dates, "preferences": preferences}
        )
        print(f"🎭 ActivityAgent: Recommended {len(result.get('result', {}).get('activities', []))} activities")
        return {
            "agent_name": agent['name'],
            "cost": result.get('cost', 0),
            "data": result.get('result', {})
        }
    except Exception as e:
        print(f"⚠️  ActivityAgent failed: {e}, using mock")
        return await mock_activity_recommendations(destination)


async def call_weather_agent(client, agent, destination):
    """Call real weather forecast agent"""
    try:
        result = await client.call_agent(
            agent_id=agent['agent_id'],
            capability="get_weather",
            input={"city": destination}
        )
        print(f"🌤️  WeatherAgent: {result.get('result', {}).get('condition', 'sunny')} forecast")
        return {
            "agent_name": agent['name'],
            "cost": result.get('cost', 0),
            "data": result.get('result', {})
        }
    except Exception as e:
        print(f"⚠️  WeatherAgent failed: {e}, using mock")
        return await mock_weather_forecast(destination)


async def mock_flight_search(destination, dates, budget):
    """Mock flight search for demo"""
    await asyncio.sleep(0.5)
    return {
        "agent_name": "MockFlightAgent",
        "cost": 0.50,
        "data": {
            "options": [
                {"airline": "DemoAir", "price": 450, "duration": "5h 30m"},
                {"airline": "SkyDemo", "price": 520, "duration": "4h 45m"}
            ]
        }
    }


async def mock_hotel_booking(destination, dates, budget):
    """Mock hotel booking for demo"""
    await asyncio.sleep(0.4)
    return {
        "agent_name": "MockHotelAgent",
        "cost": 0.40,
        "data": {
            "hotel_name": f"Grand Hotel {destination}",
            "rating": 4.5,
            "price_per_night": 150,
            "amenities": ["WiFi", "Pool", "Breakfast"]
        }
    }


async def mock_activity_recommendations(destination):
    """Mock activity recommendations for demo"""
    await asyncio.sleep(0.3)
    return {
        "agent_name": "MockActivityAgent",
        "cost": 0.30,
        "data": {
            "activities": [
                {"name": "City Tour", "price": 50, "duration": "3 hours"},
                {"name": "Museum Visit", "price": 25, "duration": "2 hours"}
            ]
        }
    }


async def mock_weather_forecast(destination):
    """Mock weather forecast for demo"""
    await asyncio.sleep(0.2)
    return {
        "agent_name": "MockWeatherAgent",
        "cost": 0.10,
        "data": {
            "city": destination,
            "temperature": 75,
            "condition": "partly cloudy",
            "forecast": "Pleasant weather expected"
        }
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌍 TripPlanner Orchestrator - Autonomous Agent Workflow")
    print("="*60)
    print("\nThis demonstrates:")
    print("  ✅ Autonomous agent discovery")
    print("  ✅ Smart agent selection (trust-based)")
    print("  ✅ Parallel agent execution")
    print("  ✅ Automatic credit transfers")
    print("  ✅ Resilient error handling")
    print("\n" + "="*60 + "\n")

    print("Starting orchestrator agent...")
    print("Note: If no real agents are available, mock agents will be used\n")

    orchestrator.serve(host="0.0.0.0", port=8100, register=True)
