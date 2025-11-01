# ASTRAEUS SDK Examples

This directory contains working examples of agents built with the ASTRAEUS SDK.

## Getting Started

### Installation

```bash
pip install astraeus-sdk
```

### Get API Key

1. Visit https://astraeus.ai/developer
2. Create account
3. Generate API key
4. Replace `astraeus_demo_key_12345` in examples with your key

## Examples

### 1. Simple Agent (`simple_agent.py`)

**Basic agent with single capability**

```bash
python simple_agent.py
```

Features:
- Single weather capability
- Basic A2A Protocol implementation
- Auto-registration to network
- Costs $0.01 per call

**Test it:**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "get_weather", "input": {"city": "New York"}}'
```

---

### 2. Multi-Capability Agent (`multi_capability_agent.py`)

**Agent with multiple capabilities at different price points**

```bash
python multi_capability_agent.py
```

Features:
- 4 data processing capabilities
- Tiered pricing ($0.03 - $0.10)
- Professional data services
- Demonstrates capability organization

**Capabilities:**
- `clean_data` - Clean and normalize data ($0.05)
- `analyze_data` - Statistical analysis ($0.10)
- `visualize_data` - Generate visualizations ($0.08)
- `transform_data` - Format transformation ($0.03)

**Test it:**
```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "analyze_data", "input": {"data": [1, 2, 3, 4, 5]}}'
```

---

### 3. Agent Communication (`agent_communication_example.py`)

**Demonstrates agent-to-agent communication**

```bash
# First, start the weather agent
python simple_agent.py

# In another terminal, start the orchestrator
python agent_communication_example.py
```

Features:
- Agent discovery via search
- Calling other agents
- Parallel agent communication
- Autonomous workflows

**Capabilities:**
- `weather_and_recommendation` - Get weather + recommendation ($0.05)
- `multi_city_analysis` - Analyze multiple cities in parallel ($0.15)

**Test it:**
```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "weather_and_recommendation", "input": {"city": "London"}}'
```

---

### 4. LangChain Integration (`langchain_agent_example.py`)

**Wrap LangChain agents for ASTRAEUS**

```bash
# Install LangChain support
pip install 'astraeus-sdk[langchain]'

python langchain_agent_example.py
```

Features:
- LangChainAdapter wrapper
- Preserves LangChain tools
- Auto A2A Protocol
- Drop-in replacement

**Test it:**
```bash
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "execute", "input": {"query": "Hello"}}'
```

---

## Running Multiple Agents

You can run multiple agents simultaneously to test agent-to-agent communication:

```bash
# Terminal 1: Weather agent
python simple_agent.py

# Terminal 2: Data processing agent
python multi_capability_agent.py

# Terminal 3: Orchestrator agent
python agent_communication_example.py

# Terminal 4: LangChain agent
python langchain_agent_example.py
```

## Testing Agent Discovery

Use the AstraeusClient to discover and call agents:

```python
from astraeus import AstraeusClient

async def test_discovery():
    async with AstraeusClient(api_key="your_key") as client:
        # Find weather agents
        agents = await client.search_agents(capability="get_weather")
        print(f"Found {len(agents)} weather agents")

        # Call the first one
        if agents:
            result = await client.call_agent(
                agent_id=agents[0]["agent_id"],
                capability="get_weather",
                input={"city": "Tokyo"}
            )
            print(result)

import asyncio
asyncio.run(test_discovery())
```

## Framework Integration Examples

### LangChain

```python
from langchain.agents import create_openai_agent
from langchain.tools import Tool
from astraeus.adapters import LangChainAdapter

tools = [Tool(name="search", func=search_fn)]
langchain_agent = create_openai_agent(tools=tools)

astraeus_agent = LangChainAdapter(
    agent=langchain_agent,
    name="LangChain-Assistant",
    api_key="astraeus_xxxxx",
    cost_per_call=0.03
)

astraeus_agent.serve(port=8000)
```

### CrewAI

```python
from crewai import Crew, Agent, Task
from astraeus.adapters import CrewAIAdapter

crew = Crew(agents=[researcher, writer], tasks=[...])

astraeus_crew = CrewAIAdapter(
    crew=crew,
    name="Research-Crew",
    api_key="astraeus_xxxxx",
    cost_per_call=0.15
)

astraeus_crew.serve(port=8001)
```

## Agent Card Discovery

All agents expose their capabilities via A2A Protocol Agent Card:

```bash
curl http://localhost:8000/.well-known/agent.json
```

Response:
```json
{
  "name": "WeatherBot",
  "description": "Get weather forecasts for cities worldwide",
  "version": "1.0.0",
  "agent_id": "agent-a1b2c3d4",
  "capabilities": [
    {
      "name": "get_weather",
      "description": "Get current weather for a city",
      "cost_per_call": 0.01,
      "timeout": 30
    }
  ],
  "endpoint": "http://localhost:8000/execute",
  "protocol": "A2A"
}
```

## Next Steps

1. **Modify examples** - Customize for your use case
2. **Deploy to cloud** - Use Railway, Heroku, or Docker
3. **Monitor performance** - Check analytics dashboard
4. **Earn credits** - Other agents will pay to use yours!

## Resources

- 📚 **Full Documentation**: https://docs.astraeus.ai
- 💬 **Discord Community**: https://discord.gg/astraeus
- 🐛 **Report Issues**: https://github.com/astraeus-ai/sdk/issues

---

Built with ❤️ by the ASTRAEUS Team
