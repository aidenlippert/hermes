"""
Simple Weather Agent Example

This example shows how to create a basic agent with a single capability.
"""

from astraeus import Agent


agent = Agent(
    name="WeatherBot",
    description="Get weather forecasts for cities worldwide",
    api_key="astraeus_demo_key_12345",
    owner="demo@example.com"
)


@agent.capability(
    "get_weather",
    cost=0.01,
    description="Get current weather for a city"
)
async def get_weather(city: str) -> dict:
    """
    Get weather forecast for a city

    Args:
        city: City name (e.g., "New York", "London")

    Returns:
        Weather data including temperature and condition
    """
    weather_data = {
        "New York": {"temperature": 72, "condition": "sunny", "humidity": 65},
        "London": {"temperature": 55, "condition": "cloudy", "humidity": 80},
        "Tokyo": {"temperature": 68, "condition": "rainy", "humidity": 75},
    }

    city_weather = weather_data.get(city, {
        "temperature": 70,
        "condition": "unknown",
        "humidity": 60
    })

    return {
        "city": city,
        "temperature": city_weather["temperature"],
        "condition": city_weather["condition"],
        "humidity": city_weather["humidity"],
        "unit": "fahrenheit"
    }


if __name__ == "__main__":
    agent.serve(host="0.0.0.0", port=8000, register=True)
