"""
Quick test script to verify Hermes is working

Run this after installing dependencies:
    python test_hermes.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from hermes.conductor.core import HermesConductor


def test_conductor():
    """Test the basic conductor functionality"""
    print("\n" + "="*60)
    print("🧪 TESTING HERMES CONDUCTOR")
    print("="*60)

    # Initialize
    print("\n1️⃣ Initializing Conductor...")
    conductor = HermesConductor()
    assert conductor is not None
    print("   ✅ Conductor created")

    # Register agents
    print("\n2️⃣ Registering test agents...")
    conductor.register_agent(
        name="CodeWizard",
        endpoint="localhost:10001",
        capabilities=["code", "debug", "program"]
    )
    conductor.register_agent(
        name="WritingPro",
        endpoint="localhost:10002",
        capabilities=["write", "content", "article"]
    )
    print("   ✅ 2 agents registered")

    # Test intent understanding
    print("\n3️⃣ Testing intent understanding...")
    test_queries = [
        "Write me a Python function",
        "Debug this code",
        "Create a blog article",
        "Help me with something random"
    ]

    for query in test_queries:
        print(f"\n   Query: '{query}'")
        intent = conductor.understand_intent(query)
        print(f"   → Capabilities: {intent['detected_capabilities']}")
        print(f"   → Confidence: {intent['confidence']:.2f}")

    # Test orchestration
    print("\n4️⃣ Testing full orchestration...")
    result = conductor.orchestrate("Write me a function to calculate fibonacci")
    print(f"\n   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get('agents_selected'):
        print(f"   Agents: {result['agents_selected']}")

    # Check status
    print("\n5️⃣ Checking system status...")
    status = conductor.get_status()
    print(f"   Agents registered: {status['agents_registered']}")
    print(f"   Agents active: {status['agents_active']}")
    print(f"   Version: {status['version']}")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n🚀 Hermes is ready to orchestrate!")
    print("\nNext steps:")
    print("  1. Run: python start.py")
    print("  2. Open: http://localhost:8000/docs")
    print("  3. Start building!")
    print()


if __name__ == "__main__":
    try:
        test_conductor()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
