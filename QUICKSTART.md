

# 🚀 HERMES QUICKSTART - See It Work in 5 Minutes

**You're about to witness REAL multi-agent orchestration powered by A2A!**

## What You'll See

1. Natural language → Structured intent (via Gemini)
2. Intent → Multi-agent plan (via Gemini)
3. Plan → Actual execution (via A2A protocol)
4. Agents working together to accomplish complex tasks

## Prerequisites

✅ Python 3.10+ installed
✅ Google API key (you have: `AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg`)
✅ 5 minutes of time

## Step 1: Install Dependencies (1 minute)

```bash
# Install everything
pip install -r requirements.txt
```

## Step 2: Start the Test Agent (30 seconds)

Open a **NEW terminal** and run:

```bash
python test_agent_code_generator.py
```

You should see:
```
🤖 CODEGENERATOR AGENT STARTING
📍 A2A Endpoint: http://localhost:10001/a2a
📋 Agent Card: http://localhost:10001/.well-known/agent.json
```

**Keep this running!** This is your first A2A-compliant agent.

## Step 3: Run the Full Orchestration Test (2 minutes)

In your **original terminal**, run:

```bash
python test_full_orchestration.py
```

## What You'll See

```
🚀 HERMES FULL ORCHESTRATION TEST

📦 Initializing components...

TEST 1: Write me a Python function to calculate fibonacci numbers

1️⃣ PARSING INTENT...
   Category: code_generation
   Capabilities: ['code_write']
   Complexity: 0.30
   Confidence: 1.00

2️⃣ CREATING PLAN...
   Steps: 1
      1. CodeGenerator: Write a Python function to calculate fibonacci...

3️⃣ EXECUTING PLAN...
   ▶️ Step 1: CodeGenerator
      Task: Write a Python function to calculate fibonacci numbers
   ✅ Step 1 completed

4️⃣ RESULTS:
   Success: ✅
   Completed: 1/1
   Duration: 2.34s

   📄 Generated Code:
   ------------------------------------------------------------------
   def fibonacci(n):
       if n <= 0:
           return []
       elif n == 1:
           return [0]
       elif n == 2:
           return [0, 1]

       fib = [0, 1]
       for i in range(2, n):
           fib.append(fib[i-1] + fib[i-2])
       return fib
   ------------------------------------------------------------------

✅ ORCHESTRATION TEST COMPLETE!
🎉 THIS IS REAL MULTI-AGENT ORCHESTRATION!
```

## 🎊 CONGRATULATIONS!

**You just ran a complete A2A-powered agent orchestration!**

### What Happened Under the Hood:

1. **Natural Language Input**: "Write me a Python function..."
2. **Gemini Parsed Intent**: Detected code_generation, complexity 0.3
3. **Gemini Created Plan**: 1 step using CodeGenerator agent
4. **Hermes Discovered Agent**: Fetched `/.well-known/agent.json`
5. **Hermes Sent A2A Task**: JSON-RPC 2.0 request to agent
6. **Agent Used Gemini**: Generated actual code
7. **Agent Returned Artifact**: Code as A2A-compliant response
8. **Hermes Returned Result**: Clean output to user

## 🧪 Try More Examples

Edit `test_full_orchestration.py` to test different queries:

```python
test_queries = [
    "Write a function to sort an array",
    "Create a REST API endpoint for user login",
    "Generate a Python class for a todo item",
    # Add your own!
]
```

## 🔍 Explore the Code

### Core Components:

1. **A2A Client** (`hermes/protocols/a2a_client.py`)
   - Discovers agents via agent cards
   - Sends/receives A2A tasks
   - Handles streaming and status checks

2. **Intent Parser** (`hermes/conductor/intent_parser.py`)
   - Uses Gemini to understand user requests
   - Extracts capabilities and complexity

3. **Workflow Planner** (`hermes/conductor/planner.py`)
   - Uses Gemini to create execution plans
   - Coordinates multiple agents

4. **Executor** (`hermes/conductor/executor.py`)
   - Runs the plan
   - Handles retries and errors
   - Streams progress

5. **Test Agent** (`test_agent_code_generator.py`)
   - A2A-compliant agent
   - Exposes agent card
   - Generates code with Gemini

## 🎯 What's Next?

Now that you've seen it work, you can:

### Option A: Add More Agents (Recommended First)

Create more A2A-compliant agents:
- Content writer agent
- Data analyzer agent
- Email sender agent
- Web search agent

See `docs/BUILD_MORE_AGENTS.md` (coming soon)

### Option B: Build the API

Connect this to a REST API so you can call it from anywhere:

```bash
python start.py
```

Then call:
```bash
curl -X POST http://localhost:8000/orchestrate \
     -H "Content-Type: application/json" \
     -d '{"query": "Write me a function"}'
```

### Option C: Add Database

Set up PostgreSQL with pgvector for:
- Agent registry (discover agents dynamically)
- User management
- Task history

### Option D: Build Frontend

Create a beautiful chat interface with:
- Next.js + TypeScript
- Real-time streaming
- Agent marketplace

### Option E: Deploy to Production

Deploy to Google Cloud Run:
- Serverless scaling
- Production-ready
- Global distribution

## 🐛 Troubleshooting

**Agent won't start:**
```bash
# Check if port 10001 is already in use
lsof -ti:10001
# Kill the process if needed
kill -9 $(lsof -ti:10001)
```

**Gemini API errors:**
```bash
# Verify your API key
echo $GOOGLE_API_KEY
# Or set it explicitly
export GOOGLE_API_KEY="your_key_here"
```

**Import errors:**
```bash
# Make sure you're in the Hermes directory
cd /home/rocz/VegaWorks/Hermes
# Reinstall dependencies
pip install -r requirements.txt
```

**Connection errors:**
- Make sure the agent is running in a separate terminal
- Check that nothing is blocking localhost:10001
- Try restarting both the agent and the test

## 🪟 Windows Quickstart (SQLite Dev Mode)

Use this path to run the full backend without external services.

1) Start the backend and keep this terminal open

```powershell
$env:DATABASE_URL = 'sqlite+aiosqlite:///c:/Users/aiden/hermes/hermes_dev.db'
python -m uvicorn backend.main_v2:app --host 127.0.0.1 --port 8000 --log-level info
```

You should see Database initialized, a Redis warning (ok), and "Hermes Platform Ready!".

2) In a second terminal, run a quick smoke test

```powershell
python -c "import requests,uuid,time; BASE='http://127.0.0.1:8000'; print('health:', requests.get(BASE + '/api/v1/health', timeout=5).status_code); email='orgdemo_%d_%s@example.com' % (int(time.time()), uuid.uuid4().hex[:6]); r=requests.post(BASE + '/api/v1/auth/register', json={'email':email,'password':'demo123'}); tok=r.json()['access_token']; hdr={'Authorization': 'Bearer ' + tok}; on='TestOrg-%d-%s' % (int(time.time()), uuid.uuid4().hex[:6]); org=requests.post(BASE + '/api/v1/orgs', headers=hdr, json={'name':on}).json(); oid=org['id']; print('assign:', requests.post(BASE + f'/api/v1/orgs/{oid}/assign_demo_agents', headers=hdr).status_code); print('agents:', requests.get(BASE + '/api/v1/agents', headers=hdr).status_code)"
```

3) Optional federation smoke

```powershell
python scripts/federation_inbox_smoke.py
```

Tips:
- If your prompt shows `>>>`, you are in the Python REPL. Type `exit()` to return to PowerShell.
- Keep the server running in Terminal 1; run tests and curls in Terminal 2.

## 📚 Understanding A2A

The A2A protocol has three key parts:

1. **Agent Card** (`/.well-known/agent.json`)
   - Describes what an agent can do
   - Like a business card for agents

2. **JSON-RPC 2.0 Tasks**
   - Standardized request/response format
   - Every agent speaks the same language

3. **Artifacts**
   - The actual results (code, text, data)
   - Returned in a structured format

## 🤝 Contributing

Want to help build the future of AI orchestration?

1. Build more test agents
2. Improve the orchestration logic
3. Add features (streaming, retries, etc.)
4. Write documentation
5. Share your use cases

## 🎉 You Did It!

**You're now running a working multi-agent orchestration system!**

This is not a demo. This is not a simulation. This is **REAL agent-to-agent communication via the A2A protocol**, powered by Gemini, orchestrated by Hermes.

**Welcome to the future of AI! 🚀**

---

**Questions?** Open an issue or ask in Discord (link coming soon)

**Want to contribute?** Check out `CONTRIBUTING.md` (coming soon)

**Ready to deploy?** See `DEPLOYMENT.md` (coming soon)
