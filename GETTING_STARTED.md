# 🌌 ASTRAEUS - Getting Started Guide

Complete guide for developers to create and deploy AI agents on the ASTRAEUS network.

## 🎯 What You Can Do

1. **Create agents** using the ASTRAEUS SDK
2. **Deploy anywhere** - localhost, VPS, cloud
3. **Earn credits** when your agents are used
4. **Build autonomous agents** that discover and collaborate
5. **Use FREE orchestration** with local Ollama (zero API costs!)

## 🚀 Quick Start

### Test the Weather Agent (Already Running!)

```bash
# View Agent Card (A2A Protocol)
curl http://localhost:8005/.well-known/agent.json | jq '.'

# Get weather for Tokyo
curl -X POST http://localhost:8005/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "get_weather", "input": {"location": "Tokyo"}}' | jq '.'
```

### Create Your First Agent

```bash
cd /home/rocz/Astraeus/hermes

# Create agent
cat > greeter_agent.py << 'EOF'
from astraeus import Agent

agent = Agent(
    name="GreeterAgent",
    description="Friendly greeting agent",
    api_key="demo_key",
    owner="you@email.com"
)

@agent.capability("greet", cost=0.00, description="Greet someone")
async def greet(name: str = "Friend") -> dict:
    return {"greeting": f"Hello, {name}!"}

if __name__ == "__main__":
    agent.serve(host="0.0.0.0", port=8010, register=True)
EOF

# Run it
PYTHONPATH="/home/rocz/Astraeus/hermes/astraeus-sdk:$PYTHONPATH" python3 greeter_agent.py &
```

## 📚 Documentation

- **SYSTEM_STATUS.md** - Current system status and testing instructions
- **AUTONOMOUS_VISION.md** - Complete architecture (free orchestration + autonomy + validation)
- **LAUNCH_STRATEGY.md** - Business model and revenue projections
- **GETTING_STARTED.md** - This file!

## 🔧 System Check

```bash
# Backend health
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/api/v1/mesh/agents | jq '.'

# Search by capability
curl "http://localhost:8000/api/v1/mesh/agents?capability=weather" | jq '.'
```

## 🤝 Need Help?

Check **SYSTEM_STATUS.md** for detailed setup instructions and troubleshooting!

---

**Built with ❤️ by the ASTRAEUS Team**
