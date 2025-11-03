#!/usr/bin/env python3
"""
Test OpenTelemetry distributed tracing across Hermes orchestration.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.services.observability import setup_tracing
from hermes.conductor.intent_parser import IntentParser


async def test_intent_parser_tracing():
    """Test that Intent Parser generates traces correctly"""
    print("\n" + "="*60)
    print("🧪 Testing OpenTelemetry Tracing - Intent Parser")
    print("="*60)

    # Initialize tracing
    setup_tracing(
        service_name="test-hermes",
        service_version="test",
        console_export=True
    )

    # Initialize parser
    api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")
    parser = IntentParser(api_key)

    # Test queries
    test_queries = [
        "Write a Python function to calculate fibonacci numbers",
        "Book a flight to NYC tomorrow"
    ]

    for query in test_queries:
        print(f"\n📝 Testing: {query}")
        intent = await parser.parse(query)
        print(f"   ✅ Category: {intent.category.value}")
        print(f"   ✅ Complexity: {intent.complexity:.2f}")
        print(f"   ✅ Confidence: {intent.confidence:.2f}")

    print("\n✅ Tracing test complete! Check console output for trace spans.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_intent_parser_tracing())
