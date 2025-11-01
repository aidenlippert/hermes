"""
Agent-to-Agent Communication Example

This example shows how agents can discover and communicate with other agents
on the ASTRAEUS network, enabling autonomous workflows.
"""

import asyncio
from astraeus import Agent, AstraeusClient


agent = Agent(
    name="WorkflowOrchestrator",
    description="Orchestrates workflows by calling other agents",
    api_key="astraeus_demo_key_12345",
    owner="demo@example.com"
)


@agent.capability(
    "weather_and_recommendation",
    cost=0.05,
    description="Get weather and provide activity recommendation"
)
async def weather_and_recommendation(city: str) -> dict:
    """
    Get weather for a city and provide activity recommendation

    This capability demonstrates agent-to-agent communication by:
    1. Searching for weather agents on the network
    2. Calling a weather agent to get current weather
    3. Using the weather data to make a recommendation

    Args:
        city: City name

    Returns:
        Weather data and activity recommendation
    """
    async with AstraeusClient(api_key="astraeus_demo_key_12345") as client:
        weather_agents = await client.search_agents(
            capability="get_weather",
            min_trust_score=0.5,
            limit=3
        )

        if not weather_agents:
            return {
                "error": "No weather agents available on the network",
                "recommendation": "Try again later"
            }

        weather_agent = weather_agents[0]
        agent_id = weather_agent.get("agent_id")

        weather_result = await client.call_agent(
            agent_id=agent_id,
            capability="get_weather",
            input={"city": city}
        )

        if not weather_result.get("success"):
            return {
                "error": "Failed to get weather data",
                "recommendation": "Unable to provide recommendation"
            }

        weather = weather_result["result"]
        temp = weather.get("temperature", 70)
        condition = weather.get("condition", "unknown")

        if temp > 80:
            recommendation = "It's hot! Perfect day for swimming or staying indoors with AC."
        elif temp > 65:
            recommendation = "Beautiful weather! Great for a walk or outdoor activities."
        elif temp > 50:
            recommendation = "Cool weather. Good for hiking or a light jacket walk."
        else:
            recommendation = "It's cold! Perfect for hot chocolate indoors."

        if condition == "rainy":
            recommendation += " Don't forget your umbrella!"
        elif condition == "sunny":
            recommendation += " Wear sunscreen!"

        return {
            "city": city,
            "weather": weather,
            "recommendation": recommendation,
            "agent_used": weather_agent.get("name"),
            "cost": weather_result.get("cost", 0)
        }


@agent.capability(
    "multi_city_analysis",
    cost=0.15,
    description="Analyze weather across multiple cities"
)
async def multi_city_analysis(cities: list) -> dict:
    """
    Get weather for multiple cities in parallel

    Demonstrates parallel agent-to-agent communication

    Args:
        cities: List of city names

    Returns:
        Weather data for all cities with comparison
    """
    async with AstraeusClient(api_key="astraeus_demo_key_12345") as client:
        weather_agents = await client.search_agents(capability="get_weather")

        if not weather_agents:
            return {"error": "No weather agents available"}

        weather_agent = weather_agents[0]
        agent_id = weather_agent.get("agent_id")

        tasks = []
        for city in cities:
            task = client.call_agent(
                agent_id=agent_id,
                capability="get_weather",
                input={"city": city}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        city_weather = {}
        total_cost = 0

        for i, result in enumerate(results):
            if result.get("success"):
                city_weather[cities[i]] = result["result"]
                total_cost += result.get("cost", 0)

        if not city_weather:
            return {"error": "Failed to get weather for any city"}

        temps = [w.get("temperature", 0) for w in city_weather.values()]
        avg_temp = sum(temps) / len(temps) if temps else 0

        return {
            "cities": city_weather,
            "summary": {
                "total_cities": len(city_weather),
                "average_temperature": round(avg_temp, 1),
                "warmest": max(temps) if temps else 0,
                "coldest": min(temps) if temps else 0
            },
            "total_cost": total_cost
        }


if __name__ == "__main__":
    print("\n🤝 Agent-to-Agent Communication Example")
    print("=" * 50)
    print("This agent demonstrates:")
    print("  • Discovering other agents on the network")
    print("  • Calling agent capabilities")
    print("  • Parallel agent communication")
    print("  • Autonomous workflows")
    print("=" * 50)
    print("\nNote: Requires a weather agent running on the network")
    print("  → Run examples/simple_agent.py first")
    print()

    agent.serve(host="0.0.0.0", port=8002, register=True)
