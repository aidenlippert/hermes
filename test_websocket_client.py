"""
WebSocket Test Client

Demonstrates real-time streaming from Hermes orchestration.

Shows live updates during:
- Intent parsing
- Agent discovery
- Planning
- Step execution
- Task completion
"""

import asyncio
import websockets
import json
import httpx
from datetime import datetime

# Test config
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# Test credentials
TEST_EMAIL = "test@hermes.ai"
TEST_PASSWORD = "test123"


class WebSocketClient:
    """Interactive WebSocket client for testing"""

    def __init__(self):
        self.token = None
        self.task_id = None

    async def register_or_login(self):
        """Get auth token"""
        print("\n🔐 Authenticating...")

        async with httpx.AsyncClient() as client:
            # Try login first
            try:
                response = await client.post(
                    f"{API_URL}/api/v1/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
                )

                if response.status_code == 200:
                    data = response.json()
                    self.token = data["access_token"]
                    print(f"✅ Logged in as {TEST_EMAIL}")
                    return

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
                data = response.json()
                self.token = data["access_token"]
                print(f"✅ Registered as {TEST_EMAIL}")
            else:
                raise Exception(f"Authentication failed: {response.text}")

    async def send_chat_request(self, query: str):
        """Send chat request and get task ID"""
        print(f"\n💬 Sending query: {query}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/chat",
                json={"query": query},
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code != 200:
                raise Exception(f"Chat request failed: {response.text}")

            data = response.json()
            self.task_id = data["task_id"]
            print(f"✅ Task created: {self.task_id}")

            return data

    async def listen_to_websocket(self, task_id: str):
        """Connect to WebSocket and listen for events"""
        ws_url = f"{WS_URL}/api/v1/ws/tasks/{task_id}?token={self.token}"

        print(f"\n🔌 Connecting to WebSocket...")
        print(f"   URL: {ws_url}")

        try:
            async with websockets.connect(ws_url) as websocket:
                print("✅ Connected! Listening for events...\n")
                print("="*70)

                # Listen for events
                while True:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=30.0
                        )

                        # Parse event
                        event = json.loads(message)

                        # Display event
                        self.display_event(event)

                        # Check if task is complete
                        if event.get("type") in ["task_completed", "task_failed"]:
                            print("\n" + "="*70)
                            print("🏁 Task finished!")
                            break

                    except asyncio.TimeoutError:
                        # Send keepalive ping
                        await websocket.send("ping")

        except Exception as e:
            print(f"❌ WebSocket error: {e}")

    def display_event(self, event: dict):
        """Pretty print events"""
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        timestamp = event.get("timestamp", "")

        # Color-coded by event type
        icons = {
            "connected": "✅",
            "task_created": "📝",
            "intent_parsing_started": "🧠",
            "intent_parsed": "✅",
            "agent_search_started": "🔍",
            "agents_found": "✅",
            "planning_started": "📋",
            "plan_created": "✅",
            "execution_started": "⚡",
            "step_started": "▶️",
            "agent_thinking": "💭",
            "step_completed": "✅",
            "step_failed": "❌",
            "task_completed": "🎉",
            "task_failed": "❌",
            "error": "🚨"
        }

        icon = icons.get(event_type, "📡")

        print(f"{icon} [{event_type}] {message}")

        # Show additional data for important events
        if event_type == "plan_created":
            steps = event.get("data", {}).get("steps", [])
            if steps:
                print(f"   📋 Plan has {len(steps)} steps:")
                for step in steps[:3]:  # Show first 3
                    print(f"      {step.get('step_number')}. {step.get('agent_name')} - {step.get('task_description', '')[:50]}...")

        elif event_type == "step_started":
            data = event.get("data", {})
            print(f"   📊 Progress: {data.get('progress', 0)*100:.0f}%")

        elif event_type == "task_completed":
            data = event.get("data", {})
            print(f"   ⏱️ Duration: {data.get('duration', 0):.1f}s")

    async def test_full_workflow(self, query: str):
        """Test complete workflow with WebSocket"""

        # Authenticate
        await self.register_or_login()

        # Start WebSocket listener in background
        async def run_websocket():
            # Wait a bit for chat request to create task
            await asyncio.sleep(1)
            await self.listen_to_websocket(self.task_id)

        # Start chat request in background
        async def run_chat():
            return await self.send_chat_request(query)

        # Run both concurrently
        websocket_task = asyncio.create_task(run_websocket())
        chat_result = await run_chat()

        # Wait for WebSocket to finish
        await websocket_task

        print("\n📊 Final Result:")
        print(f"   Status: {chat_result.get('status')}")
        print(f"   Message: {chat_result.get('message')}")
        if chat_result.get('result'):
            print(f"   Result: {chat_result['result'][:200]}...")


async def main():
    """Run WebSocket test"""

    print("\n" + "="*70)
    print("🧪 HERMES WEBSOCKET TEST CLIENT")
    print("="*70)

    client = WebSocketClient()

    # Test queries
    queries = [
        "Write a Python function to calculate fibonacci numbers",
        # "Help me analyze my data and create a visualization",
        # "Search the web for latest AI news and summarize it"
    ]

    for query in queries:
        try:
            print(f"\n\n{'='*70}")
            print(f"TEST: {query}")
            print("="*70)

            await client.test_full_workflow(query)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("✅ Tests complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
