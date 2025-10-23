"""
Multi-Agent Coordination Test

Tests Hermes orchestrating multiple agents to complete complex tasks.

Demonstrates:
- Intent parsing
- Multi-agent planning
- Parallel execution
- WebSocket streaming
- Complex workflows

Requires all agents running:
- CodeGenerator (10001)
- ContentWriter (10002)
- DataAnalyzer (10003)
- WebSearcher (10004)
"""

import asyncio
import httpx
import json

API_URL = "http://localhost:8000"

# Test credentials
TEST_EMAIL = "test@hermes.ai"
TEST_PASSWORD = "test123"


async def get_auth_token():
    """Get JWT token"""
    print("🔐 Authenticating...")

    async with httpx.AsyncClient() as client:
        # Try login first
        try:
            response = await client.post(
                f"{API_URL}/api/v1/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )

            if response.status_code == 200:
                token = response.json()["access_token"]
                print(f"✅ Logged in as {TEST_EMAIL}")
                return token
        except:
            pass

        # Register if login fails
        response = await client.post(
            f"{API_URL}/api/v1/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            }
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Registered as {TEST_EMAIL}")
            return token

        raise Exception(f"Authentication failed: {response.text}")


async def test_query(token: str, query: str, expected_agents: list = None):
    """Test a query and show results"""
    print("\n" + "="*80)
    print(f"📝 QUERY: {query}")
    print("="*80)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_URL}/api/v1/chat",
            json={"query": query},
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return

        result = response.json()

        print(f"\n📊 RESULT:")
        print(f"   Task ID: {result['task_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")

        if result.get('steps'):
            print(f"\n📋 EXECUTION PLAN ({len(result['steps'])} steps):")
            for step in result['steps']:
                status_icon = "✅" if step['status'] == 'completed' else "❌" if step['status'] == 'failed' else "⏳"
                print(f"   {status_icon} Step {step['step_number']}: {step['agent_name']}")
                print(f"      Task: {step['task_description'][:80]}...")
                if step.get('result'):
                    print(f"      Result: {step['result'][:100]}...")

            # Check if expected agents were used
            if expected_agents:
                used_agents = [step['agent_name'] for step in result['steps']]
                print(f"\n🤖 AGENTS USED: {', '.join(used_agents)}")

                for expected_agent in expected_agents:
                    if expected_agent in used_agents:
                        print(f"   ✅ {expected_agent} - Used as expected")
                    else:
                        print(f"   ⚠️ {expected_agent} - NOT used (expected)")

        if result.get('result'):
            print(f"\n💬 FINAL OUTPUT:")
            print(f"   {result['result'][:300]}...")
            if len(result['result']) > 300:
                print(f"   ... ({len(result['result'])} characters total)")

        print("\n" + "="*80)

        return result


async def main():
    """Run multi-agent tests"""

    print("\n" + "="*80)
    print("🧪 HERMES MULTI-AGENT COORDINATION TEST")
    print("="*80)
    print("\n⚠️ Prerequisites:")
    print("   1. Backend running: python backend/main_v2.py")
    print("   2. All agents running:")
    print("      - python test_agent_code_generator.py  (port 10001)")
    print("      - python test_agent_content_writer.py   (port 10002)")
    print("      - python test_agent_data_analyzer.py    (port 10003)")
    print("      - python test_agent_web_searcher.py     (port 10004)")
    print()

    input("Press Enter to start tests...")

    # Get auth token
    token = await get_auth_token()

    # Test Cases
    tests = [
        {
            "query": "Write a Python function to calculate fibonacci numbers",
            "expected_agents": ["CodeGenerator"],
            "description": "Single agent - Code generation"
        },
        {
            "query": "Write a blog post about the benefits of AI in healthcare",
            "expected_agents": ["ContentWriter"],
            "description": "Single agent - Content writing"
        },
        {
            "query": "Find the latest news about electric vehicles and summarize it",
            "expected_agents": ["WebSearcher"],
            "description": "Single agent - Web search"
        },
        {
            "query": "Research current AI trends, then write a blog post about them",
            "expected_agents": ["WebSearcher", "ContentWriter"],
            "description": "Multi-agent - Research + Writing"
        },
        {
            "query": "Search for Python best practices, then write code examples demonstrating them",
            "expected_agents": ["WebSearcher", "CodeGenerator"],
            "description": "Multi-agent - Research + Code"
        }
    ]

    print("\n" + "="*80)
    print(f"🎯 RUNNING {len(tests)} TEST CASES")
    print("="*80)

    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST {i}/{len(tests)}: {test['description']}")
        print("="*80)

        try:
            result = await test_query(
                token,
                test['query'],
                test['expected_agents']
            )
            results.append({
                "test": test['description'],
                "success": result['status'] == 'completed',
                "result": result
            })

            # Wait between tests
            if i < len(tests):
                print("\n⏳ Waiting 3 seconds before next test...")
                await asyncio.sleep(3)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test": test['description'],
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")
    print()

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {status} - {result['test']}")

    print("\n" + "="*80)

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️ {total - passed} tests failed")

    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
