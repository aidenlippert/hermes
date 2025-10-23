# WebSocket Real-Time Streaming

Hermes now supports **real-time WebSocket streaming** for live task progress updates!

## Features

🔴 **Live Progress**: See every step of orchestration in real-time
- Intent parsing
- Agent discovery
- Planning
- Step execution
- Task completion

📊 **Rich Events**: Comprehensive event types for every stage
- `task_created` - Task initiated
- `intent_parsing_started` - Understanding user request
- `intent_parsed` - Intent detected
- `agent_search_started` - Finding suitable agents
- `agents_found` - Agents discovered
- `planning_started` - Creating execution plan
- `plan_created` - Plan ready
- `execution_started` - Starting execution
- `step_started` - Step beginning
- `agent_thinking` - Agent processing
- `step_completed` - Step finished
- `step_failed` - Step failed
- `task_completed` - Task completed
- `task_failed` - Task failed

🔐 **Secure**: JWT authentication required for all connections

## WebSocket Endpoints

### Per-Task Updates
```
ws://localhost:8000/api/v1/ws/tasks/{task_id}?token=YOUR_JWT_TOKEN
```

Subscribe to updates for a specific task. Get real-time events as orchestration progresses.

### User-Wide Updates
```
ws://localhost:8000/api/v1/ws/user?token=YOUR_JWT_TOKEN
```

Subscribe to all tasks for a user. Great for dashboards.

## Quick Start

### 1. Start the Backend

Make sure Docker services are running:
```bash
docker-compose up -d
```

Initialize database:
```bash
python3 scripts/init_database.py
```

Start Hermes:
```bash
python3 backend/main_v2.py
```

Start test agent:
```bash
python3 test_agent_code_generator.py
```

### 2. Run the Test Client

The automated test client handles everything:

```bash
pip install websockets httpx

python3 test_websocket_client.py
```

This will:
1. ✅ Register/login a test user
2. ✅ Connect to WebSocket
3. ✅ Send a chat request
4. ✅ Stream all events in real-time
5. ✅ Show final results

### 3. Manual Testing

#### Step 1: Get Auth Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@hermes.ai",
    "password": "test123",
    "full_name": "Test User"
  }'
```

Save the `access_token` from the response.

#### Step 2: Start a Task

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "Write a Python function to calculate fibonacci numbers"
  }'
```

Save the `task_id` from the response.

#### Step 3: Connect to WebSocket

Use the simple WebSocket client:

```bash
python3 test_websocket_simple.py TASK_ID YOUR_TOKEN
```

Or use a WebSocket client like `wscat`:

```bash
npm install -g wscat

wscat -c "ws://localhost:8000/api/v1/ws/tasks/TASK_ID?token=YOUR_TOKEN"
```

## Event Format

All events follow this structure:

```json
{
  "type": "step_started",
  "task_id": "abc123...",
  "message": "▶️ Step 1/3: CodeGenerator",
  "data": {
    "step_number": 1,
    "agent_name": "CodeGenerator",
    "task_description": "Generate Python code...",
    "total_steps": 3,
    "progress": 0.33
  },
  "timestamp": "2025-01-23T10:30:45.123Z"
}
```

## Example Event Sequence

Here's what you'll see during a typical task:

```
✅ [connected] Connected to task abc123...
📝 [task_created] Task created: Write a Python function...
🧠 [intent_parsing_started] Understanding your request...
✅ [intent_parsed] Detected: code_generation
🔍 [agent_search_started] Finding agents with: code_write, python...
✅ [agents_found] Found 3 agents: CodeGenerator, PythonExpert, ScriptWriter
📋 [planning_started] Creating execution plan...
✅ [plan_created] Plan ready: 2 steps
⚡ [execution_started] Starting execution: 2 steps
▶️ [step_started] Step 1/2: CodeGenerator
💭 [agent_thinking] CodeGenerator is working...
✅ [step_completed] Step 1/2 completed
▶️ [step_started] Step 2/2: PythonExpert
💭 [agent_thinking] PythonExpert is working...
✅ [step_completed] Step 2/2 completed
🎉 [task_completed] Task completed in 5.2s
```

## Integration Examples

### JavaScript/TypeScript

```typescript
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/tasks/${taskId}?token=${token}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'step_started':
      console.log(`Step ${data.data.step_number}: ${data.data.agent_name}`);
      break;
    case 'task_completed':
      console.log('Task finished!', data.data);
      break;
  }
};
```

### Python

```python
import asyncio
import websockets
import json

async def listen_to_task(task_id: str, token: str):
    uri = f"ws://localhost:8000/api/v1/ws/tasks/{task_id}?token={token}"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            event = json.loads(message)
            print(f"{event['type']}: {event['message']}")

            if event['type'] in ['task_completed', 'task_failed']:
                break

asyncio.run(listen_to_task(task_id, token))
```

### React Hook

```typescript
function useTaskStream(taskId: string, token: string) {
  const [events, setEvents] = useState([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/api/v1/ws/tasks/${taskId}?token=${token}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev, data]);

      if (['task_completed', 'task_failed'].includes(data.type)) {
        setIsComplete(true);
      }
    };

    return () => ws.close();
  }, [taskId, token]);

  return { events, isComplete };
}
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ WebSocket
       ↓
┌──────────────────┐
│ WebSocket Manager│ ← Routes events to subscribers
└──────┬───────────┘
       │
       ↓
┌───────────────────┐
│ Streaming Executor│ ← Emits events during execution
└──────┬────────────┘
       │
       ↓
┌──────────────┐
│ A2A Protocol │ ← Calls agents
└──────────────┘
```

## Next Steps

- ✅ WebSocket streaming implemented
- 🔜 Build more agents to demonstrate multi-agent coordination
- 🔜 Create frontend dashboard with live progress
- 🔜 Add WebSocket reconnection and error handling
- 🔜 Implement agent streaming for long-running tasks

## Troubleshooting

**WebSocket connection fails**
- Check that the backend is running on port 8000
- Verify JWT token is valid (not expired)
- Ensure task_id exists

**No events received**
- Check that task was created successfully
- Verify agents are running (test_agent_code_generator.py)
- Check backend logs for errors

**Connection drops**
- Implement automatic reconnection in client
- Use ping/pong keepalive (client sends "ping", server responds "pong")

## API Reference

### WebSocket Stats
```
GET /api/v1/ws/stats
```

Returns current WebSocket connection statistics:
```json
{
  "websocket_stats": {
    "total_connections": 5,
    "active_tasks": 3,
    "active_users": 2,
    "tasks": {
      "abc123...": 2,
      "def456...": 1
    }
  }
}
```
