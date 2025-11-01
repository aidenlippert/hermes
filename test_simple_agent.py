"""
Simple Test Agent for ASTRAEUS Network

This agent can be deployed locally and discovered from another computer.
It demonstrates:
- Agent registration on ASTRAEUS network
- Basic capabilities (echo and calculate)
- A2A Protocol compliance
- Agent Card exposure
"""

import asyncio
from astraeus import Agent

# Create your test agent
agent = Agent(
    name="TestAgent",
    description="Simple test agent for ASTRAEUS network verification",
    api_key="astraeus_demo_test_key",
    owner="test@example.com"
)


@agent.capability("echo", cost=0.00, description="Echo back a message")
async def echo(message: str) -> dict:
    """Simple echo capability to test connectivity"""
    return {
        "echo": f"You said: {message}",
        "agent": agent.name,
        "status": "✅ Working!",
        "timestamp": asyncio.get_event_loop().time()
    }


@agent.capability("calculate", cost=0.01, description="Perform basic calculations")
async def calculate(expression: str) -> dict:
    """Simple calculator capability"""
    try:
        # Note: In production, use safer eval alternatives like ast.literal_eval
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": result,
            "status": "✅ Calculated!",
            "agent": agent.name
        }
    except Exception as e:
        return {
            "error": str(e),
            "expression": expression,
            "status": "❌ Error",
            "agent": agent.name
        }


@agent.capability("ping", cost=0.00, description="Health check endpoint")
async def ping() -> dict:
    """Simple health check"""
    return {
        "status": "✅ Alive",
        "agent": agent.name,
        "message": "ASTRAEUS network connection successful!"
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 ASTRAEUS Test Agent Starting...")
    print("="*70)
    print("\nThis agent will:")
    print("  1. Register on the ASTRAEUS network")
    print("  2. Expose an A2A-compliant Agent Card at /.well-known/agent.json")
    print("  3. Be discoverable by other agents on the network")
    print("  4. Accept calls to its capabilities (echo, calculate, ping)")
    print("\n" + "="*70)
    print("\n🔧 Starting agent server...")
    print("📍 Endpoint: http://0.0.0.0:8000")
    print("📋 Agent Card: http://0.0.0.0:8000/.well-known/agent.json")
    print("\n⏳ Registering with ASTRAEUS network...\n")

    # Start the agent and register with ASTRAEUS network
    agent.serve(host="0.0.0.0", port=8000, register=True)
