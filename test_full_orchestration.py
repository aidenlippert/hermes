"""
FULL END-TO-END ORCHESTRATION TEST

This demonstrates the COMPLETE Hermes flow:
1. User says something in natural language
2. Intent Parser figures out what they want (Gemini)
3. Workflow Planner creates a multi-agent plan (Gemini)
4. Executor runs the plan via A2A protocol
5. Results returned to user

This is THE test that proves Hermes works!

Prerequisites:
1. Run test_agent_code_generator.py on port 10001
2. Set GOOGLE_API_KEY environment variable
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from hermes.conductor.intent_parser import IntentParser
from hermes.conductor.planner import WorkflowPlanner
from hermes.conductor.executor import Executor
from hermes.protocols.a2a_client import A2AClient


async def main():
    print("\n" + "="*70)
    print("🚀 HERMES FULL ORCHESTRATION TEST")
    print("="*70)

    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")

    if not api_key or api_key == "your_key_here":
        print("❌ Set GOOGLE_API_KEY environment variable")
        return

    # Initialize components
    print("\n📦 Initializing components...")
    intent_parser = IntentParser(api_key)
    planner = WorkflowPlanner(api_key)
    a2a_client = A2AClient()
    executor = Executor(a2a_client)

    # Progress callback
    def on_progress(event):
        event_type = event.get("type", "unknown")
        if event_type == "step_started":
            print(f"   ▶️ Step {event['step']}: {event['agent']}")
            print(f"      Task: {event['task'][:80]}...")
        elif event_type == "step_completed":
            print(f"   ✅ Step {event['step']} completed")
        elif event_type == "step_failed":
            print(f"   ❌ Step {event['step']} failed: {event['error']}")

    executor.on_progress(on_progress)

    # Available agents (in a real system, this comes from the registry)
    available_agents = [
        {
            "name": "CodeGenerator",
            "endpoint": "http://localhost:10001/a2a",
            "capabilities": ["code_write", "code_debug", "code_explain"],
            "description": "Generates code in any programming language"
        }
    ]

    # Test queries
    test_queries = [
        "Write me a Python function to calculate fibonacci numbers",
        "Create a JavaScript function that sorts an array",
        "Debug this code and fix the error"
    ]

    for i, query in enumerate(test_queries, 1):
        print("\n" + "="*70)
        print(f"TEST {i}: {query}")
        print("="*70)

        # STEP 1: Parse Intent
        print("\n1️⃣ PARSING INTENT...")
        intent = await intent_parser.parse(query)

        print(f"   Category: {intent.category.value}")
        print(f"   Capabilities: {intent.required_capabilities}")
        print(f"   Complexity: {intent.complexity:.2f}")
        print(f"   Confidence: {intent.confidence:.2f}")

        # STEP 2: Create Plan
        print("\n2️⃣ CREATING PLAN...")
        plan = await planner.create_plan(
            user_query=query,
            parsed_intent=intent.to_dict(),
            available_agents=available_agents
        )

        print(f"   Steps: {len(plan.steps)}")
        for step in plan.steps:
            print(f"      {step.step_number}. {step.agent_name}: {step.task_description[:60]}...")

        # STEP 3: Execute Plan
        print("\n3️⃣ EXECUTING PLAN...")

        result = await executor.execute(plan)

        # STEP 4: Show Results
        print(f"\n4️⃣ RESULTS:")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Completed: {result.completed_steps}/{len(plan.steps)}")
        print(f"   Duration: {result.total_duration:.2f}s")

        if result.final_output:
            print(f"\n   📄 Generated Code:")
            print("   " + "-"*66)
            for line in result.final_output.split("\n")[:20]:  # First 20 lines
                print(f"   {line}")
            if len(result.final_output.split("\n")) > 20:
                print("   ...")
            print("   " + "-"*66)

        if not result.success:
            print(f"\n   ❌ Error: {result.error}")
            for step in plan.steps:
                if step.error:
                    print(f"      Step {step.step_number}: {step.error}")

        # Only run first test unless --all flag
        if "--all" not in sys.argv:
            print("\n💡 Run with --all to test all queries")
            break

    # Cleanup
    await a2a_client.close()

    print("\n" + "="*70)
    print("✅ ORCHESTRATION TEST COMPLETE!")
    print("="*70)
    print("\nWhat just happened:")
    print("  1. You gave Hermes a natural language request")
    print("  2. Gemini parsed what you wanted")
    print("  3. Gemini created an execution plan")
    print("  4. Hermes called the CodeGenerator agent via A2A")
    print("  5. Agent returned generated code")
    print("  6. Hermes returned it to you")
    print("\n🎉 THIS IS REAL MULTI-AGENT ORCHESTRATION!")
    print("\nNext steps:")
    print("  - Add more agents (writers, analyzers, etc.)")
    print("  - Add database for agent registry")
    print("  - Add web UI for user interaction")
    print("  - Deploy to production!")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
