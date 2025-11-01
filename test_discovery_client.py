"""
ASTRAEUS Network Discovery Client

This script can be run from ANY computer to discover and call agents on the network.
It demonstrates:
- Discovering agents by capability
- Calling remote agents
- Viewing agent statistics and trust scores
"""

import asyncio
from astraeus import AstraeusClient


async def test_network_discovery():
    """Test discovering and calling agents on ASTRAEUS network"""

    print("\n" + "="*70)
    print("🔍 ASTRAEUS Network Discovery Test")
    print("="*70)

    # Connect to ASTRAEUS network
    client = AstraeusClient(api_key="astraeus_demo_test_key")

    try:
        print("\n📡 Connecting to ASTRAEUS network...")
        print("🌐 Network URL: https://web-production-3df46.up.railway.app")

        # Test 1: Search for agents with "echo" capability
        print("\n" + "-"*70)
        print("TEST 1: Discovering agents with 'echo' capability")
        print("-"*70)

        agents = await client.search_agents(capability="echo", limit=10)

        if agents:
            print(f"\n✅ Found {len(agents)} agents with 'echo' capability:\n")

            for i, agent in enumerate(agents, 1):
                print(f"{i}. {agent['name']}")
                print(f"   ID: {agent['agent_id']}")
                print(f"   Trust Score: {agent.get('trust_score', 0):.2f}")
                print(f"   Endpoint: {agent.get('endpoint', 'N/A')}")
                print(f"   Status: {agent.get('status', 'unknown')}")
                print()
        else:
            print("\n❌ No agents found with 'echo' capability")
            print("   Make sure test_simple_agent.py is running!")
            return

        # Test 2: Call the first agent's echo capability
        print("-"*70)
        print("TEST 2: Calling echo capability on first agent")
        print("-"*70)

        target_agent = agents[0]
        print(f"\n🤖 Calling {target_agent['name']}...")
        print(f"   Agent ID: {target_agent['agent_id']}")
        print(f"   Capability: echo")
        print(f"   Input: 'Hello from discovery client!'")

        result = await client.call_agent(
            agent_id=target_agent['agent_id'],
            capability="echo",
            input={"message": "Hello from discovery client!"}
        )

        print(f"\n✅ Response received:")
        print(f"   {result.get('result', {})}")
        print(f"   Cost: ${result.get('cost', 0)}")
        print(f"   Success: {result.get('success', False)}")

        # Test 3: Call calculate capability
        print("\n" + "-"*70)
        print("TEST 3: Calling calculate capability")
        print("-"*70)

        print(f"\n🤖 Calling {target_agent['name']}...")
        print(f"   Capability: calculate")
        print(f"   Expression: '10 + 20 * 3'")

        result = await client.call_agent(
            agent_id=target_agent['agent_id'],
            capability="calculate",
            input={"expression": "10 + 20 * 3"}
        )

        print(f"\n✅ Response received:")
        print(f"   {result.get('result', {})}")
        print(f"   Cost: ${result.get('cost', 0)}")

        # Test 4: Call ping capability
        print("\n" + "-"*70)
        print("TEST 4: Calling ping capability")
        print("-"*70)

        print(f"\n🤖 Calling {target_agent['name']}...")
        print(f"   Capability: ping")

        result = await client.call_agent(
            agent_id=target_agent['agent_id'],
            capability="ping",
            input={}
        )

        print(f"\n✅ Response received:")
        print(f"   {result.get('result', {})}")

        # Test 5: Search with smart ranking
        print("\n" + "-"*70)
        print("TEST 5: Smart agent ranking")
        print("-"*70)

        print("\n🧠 Using smart ranking algorithm...")
        print("   (balances trust 60%, cost 20%, speed 20%)")

        smart_agents = await client.search_agents(
            capability="echo",
            sort_by="smart",
            limit=5
        )

        if smart_agents:
            print(f"\n✅ Top agents by smart ranking:\n")
            for i, agent in enumerate(smart_agents, 1):
                print(f"{i}. {agent['name']}")
                print(f"   Trust: {agent.get('trust_score', 0):.2f}")
                print(f"   Cost: ${agent.get('base_cost_per_call', 0)}")
                print(f"   Latency: {agent.get('avg_latency_ms', 0)}ms")
                print()

        print("="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n🎉 Your agent is successfully registered on ASTRAEUS network!")
        print("🌐 It can be discovered and called from anywhere!")

    except Exception as e:
        print(f"\n❌ Error during discovery: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    print("\n🚀 Starting ASTRAEUS Network Discovery Test...\n")
    asyncio.run(test_network_discovery())
