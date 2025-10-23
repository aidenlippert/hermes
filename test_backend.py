"""
Test the REAL Hermes Backend

This script tests the actual backend API with real requests.

Prerequisites:
1. Backend running on localhost:8000
2. Test agent running on localhost:10001
"""

import requests
import json
import time


def test_health():
    """Test health endpoint"""
    print("\n1️⃣ Testing health endpoint...")
    response = requests.get("http://localhost:8000/api/v1/health")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Backend is healthy!")
        print(f"   Agents available: {data['agents_available']}")
        return True
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
        return False


def test_list_agents():
    """Test agent listing"""
    print("\n2️⃣ Testing agent listing...")
    response = requests.get("http://localhost:8000/api/v1/agents")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {data['total']} agents:")
        for agent in data['agents']:
            print(f"      - {agent['name']}: {agent['description']}")
        return True
    else:
        print(f"   ❌ List agents failed: {response.status_code}")
        return False


def test_orchestration():
    """Test the main orchestration endpoint"""
    print("\n3️⃣ Testing orchestration...")

    request_data = {
        "query": "Write me a Python function to calculate the factorial of a number"
    }

    print(f"   Query: {request_data['query']}")
    print("   Sending request...")

    start_time = time.time()

    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )

    duration = time.time() - start_time

    if response.status_code == 200:
        data = response.json()

        print(f"   ✅ Request completed in {duration:.2f}s")
        print(f"   Task ID: {data['task_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")

        if data.get('result'):
            print(f"\n   📄 Generated Code:")
            print("   " + "-"*60)
            for line in data['result'].split("\n")[:15]:
                print(f"   {line}")
            print("   " + "-"*60)

        if data.get('steps'):
            print(f"\n   📊 Execution Steps:")
            for step in data['steps']:
                status_icon = "✅" if step['status'] == "completed" else "❌"
                print(f"      {status_icon} Step {step['step_number']}: {step['agent_name']}")

        return True
    else:
        print(f"   ❌ Orchestration failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Response: {response.text}")
        return False


def main():
    print("\n" + "="*70)
    print("🧪 TESTING HERMES BACKEND")
    print("="*70)

    print("\n⚠️ Make sure:")
    print("   1. Backend is running: python backend/main.py")
    print("   2. Test agent is running: python test_agent_code_generator.py")
    print()

    input("Press Enter to start tests...")

    # Run tests
    results = []

    results.append(("Health Check", test_health()))
    time.sleep(0.5)

    results.append(("List Agents", test_list_agents()))
    time.sleep(0.5)

    results.append(("Orchestration", test_orchestration()))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS")
    print("="*70)

    for test_name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"   {icon} {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n   Passed: {total_passed}/{total_tests}")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✨ Your Hermes backend is working perfectly!")
        print("\nNext steps:")
        print("   - Add more agents")
        print("   - Build the frontend")
        print("   - Add database")
        print("   - Deploy to production")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        print("\nCommon issues:")
        print("   - Backend not running on port 8000")
        print("   - Test agent not running on port 10001")
        print("   - Dependencies not installed")
        print("   - Google API key not set")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted")
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error!")
        print("\nMake sure both are running:")
        print("   Terminal 1: python test_agent_code_generator.py")
        print("   Terminal 2: python backend/main.py")
        print("   Terminal 3: python test_backend.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
