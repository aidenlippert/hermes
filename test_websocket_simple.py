"""
Simple WebSocket Test

Just connect and listen to a task's progress.
Run this AFTER starting a task via the API.
"""

import asyncio
import websockets
import json
import sys

# Config
WS_URL = "ws://localhost:8000/api/v1/ws/tasks"
TASK_ID = None  # Will be provided as argument
TOKEN = None     # Will be provided as argument


async def listen_to_task(task_id: str, token: str):
    """Connect to WebSocket and print all events"""

    ws_url = f"{WS_URL}/{task_id}?token={token}"

    print(f"\n🔌 Connecting to WebSocket...")
    print(f"   Task ID: {task_id}")
    print(f"   URL: {ws_url}\n")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected! Listening for events...\n")
            print("="*70)

            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=60.0
                    )

                    # Parse and display
                    event = json.loads(message)

                    event_type = event.get("type", "unknown")
                    message = event.get("message", "")

                    print(f"📡 [{event_type}] {message}")

                    # Show full event data
                    if event.get("data"):
                        print(f"   Data: {json.dumps(event['data'], indent=2)}")

                    # Exit on completion
                    if event_type in ["task_completed", "task_failed"]:
                        print("\n" + "="*70)
                        print("🏁 Task finished!")
                        break

                except asyncio.TimeoutError:
                    # Send keepalive
                    await websocket.send("ping")
                    print("💓 Keepalive...")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("\nUsage: python test_websocket_simple.py <task_id> <token>")
        print("\nExample:")
        print("  python test_websocket_simple.py abc123 eyJhbGciOiJIUzI1...")
        print("\n")
        sys.exit(1)

    TASK_ID = sys.argv[1]
    TOKEN = sys.argv[2]

    asyncio.run(listen_to_task(TASK_ID, TOKEN))
