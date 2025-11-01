"""
Simple Weather Agent - ASTRAEUS SDK Example

Demonstrates:
1. A2A Protocol compliance (Agent Card)
2. Auto-registration with central network
3. Discoverable capabilities
4. Ready for autonomous agent calls
"""

from astraeus import Agent
import random

agent = Agent(
    name="WeatherAgent",
    description="Provides weather forecasts for any location worldwide",
    api_key="test_weather_api_key_12345",
    owner="test@astraeus.network"
)


@agent.capability("get_weather", cost=0.01, description="Get current weather for a location")
async def get_weather(location: str) -> dict:
    """Get weather for a location (mock data for testing)"""
    weather_conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "windy"]
    temperatures = list(range(15, 35))
    
    return {
        "location": location,
        "temperature": random.choice(temperatures),
        "condition": random.choice(weather_conditions),
        "humidity": random.randint(30, 90),
        "wind_speed": random.randint(5, 25),
        "forecast": "Clear skies expected",
        "agent": "WeatherAgent"
    }


@agent.capability("get_forecast", cost=0.02, description="Get 7-day weather forecast")
async def get_forecast(location: str, days: int = 7) -> dict:
    """Get multi-day forecast"""
    forecasts = []
    for i in range(min(days, 7)):
        forecasts.append({
            "day": i + 1,
            "high": random.randint(20, 35),
            "low": random.randint(10, 20),
            "condition": random.choice(["sunny", "cloudy", "rainy"]),
            "precipitation_chance": random.randint(0, 100)
        })
    
    return {
        "location": location,
        "days": days,
        "forecasts": forecasts,
        "agent": "WeatherAgent"
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print(f"🌤️  Starting {agent.name}")
    print("="*70)
    print(f"\n📋 Description: {agent.description}")
    print(f"📧 Owner: {agent.owner}")
    print(f"🎯 Capabilities: {len(agent.capabilities)}")
    for cap_name, cap_data in agent.capabilities.items():
        print(f"   - {cap_name}: ${cap_data['cost']} per call")
        print(f"     {cap_data['description']}")
    print("\n" + "="*70 + "\n")
    
    # Start agent server with auto-registration
    agent.serve(
        host="0.0.0.0",
        port=8005,
        register=True  # Auto-register with ASTRAEUS network!
    )
