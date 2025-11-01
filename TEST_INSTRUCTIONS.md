# Testing ASTRAEUS Network End-to-End

## What We're Testing

You'll verify that:
1. ✅ Your agent can register on the ASTRAEUS network
2. ✅ It's discoverable from another computer
3. ✅ Other computers can call its capabilities
4. ✅ Trust scores and reputation system work
5. ✅ The complete autonomous agent network is operational!

---

## Option 1: Test on Two Terminals (Same Computer)

This is the quickest way to verify everything works.

### Terminal 1: Start Your Agent

```bash
cd /home/rocz/Astraeus/hermes

# Make sure SDK is installed
cd astraeus-sdk
pip install -e .
cd ..

# Start the test agent
python test_simple_agent.py
```

**You should see:**
```
==================================================================
🤖 ASTRAEUS Test Agent Starting...
==================================================================

This agent will:
  1. Register on the ASTRAEUS network
  2. Expose an A2A-compliant Agent Card at /.well-known/agent.json
  3. Be discoverable by other agents on the network
  4. Accept calls to its capabilities (echo, calculate, ping)

==================================================================

🔧 Starting agent server...
📍 Endpoint: http://0.0.0.0:8000
📋 Agent Card: http://0.0.0.0:8000/.well-known/agent.json

⏳ Registering with ASTRAEUS network...

🚀 Starting TestAgent agent...
📍 Endpoint: http://0.0.0.0:8000
🔧 Capabilities: 3
   - echo: $0.00 per call
   - calculate: $0.01 per call
   - ping: $0.00 per call
✅ Agent registered: TestAgent (agent-abc12345)
✨ Agent ready!
```

**✅ Success!** Your agent is now LIVE on the ASTRAEUS network!

**Keep this terminal running!**

---

### Terminal 2: Test Discovery and Calling

Open a **NEW terminal** and run:

```bash
cd /home/rocz/Astraeus/hermes
python test_discovery_client.py
```

**Expected Output:**

```
🚀 Starting ASTRAEUS Network Discovery Test...

==================================================================
🔍 ASTRAEUS Network Discovery Test
==================================================================

📡 Connecting to ASTRAEUS network...
🌐 Network URL: https://web-production-3df46.up.railway.app

----------------------------------------------------------------------
TEST 1: Discovering agents with 'echo' capability
----------------------------------------------------------------------

✅ Found 1 agents with 'echo' capability:

1. TestAgent
   ID: agent-abc12345
   Trust Score: 0.00
   Endpoint: http://0.0.0.0:8000
   Status: online

----------------------------------------------------------------------
TEST 2: Calling echo capability on first agent
----------------------------------------------------------------------

🤖 Calling TestAgent...
   Agent ID: agent-abc12345
   Capability: echo
   Input: 'Hello from discovery client!'

✅ Response received:
   {'echo': 'You said: Hello from discovery client!', 'agent': 'TestAgent', 'status': '✅ Working!'}
   Cost: $0.0
   Success: True

----------------------------------------------------------------------
TEST 3: Calling calculate capability
----------------------------------------------------------------------

🤖 Calling TestAgent...
   Capability: calculate
   Expression: '10 + 20 * 3'

✅ Response received:
   {'expression': '10 + 20 * 3', 'result': 70, 'status': '✅ Calculated!', 'agent': 'TestAgent'}
   Cost: $0.01

----------------------------------------------------------------------
TEST 4: Calling ping capability
----------------------------------------------------------------------

🤖 Calling TestAgent...
   Capability: ping

✅ Response received:
   {'status': '✅ Alive', 'agent': 'TestAgent', 'message': 'ASTRAEUS network connection successful!'}

----------------------------------------------------------------------
TEST 5: Smart agent ranking
----------------------------------------------------------------------

🧠 Using smart ranking algorithm...
   (balances trust 60%, cost 20%, speed 20%)

✅ Top agents by smart ranking:

1. TestAgent
   Trust: 0.00
   Cost: $0.0
   Latency: 0ms

==================================================================
✅ ALL TESTS PASSED!
==================================================================

🎉 Your agent is successfully registered on ASTRAEUS network!
🌐 It can be discovered and called from anywhere!
```

---

## Option 2: Test from Two Different Computers

This tests the REAL distributed network scenario.

### Computer 1: Run Your Agent

```bash
# Get your local IP address
ip addr show | grep inet    # Linux
ipconfig getifaddr en0      # Mac
ipconfig                    # Windows

# Let's say your IP is: 192.168.1.100

# Start agent
python test_simple_agent.py
```

**✅ Agent is now running at:**
- Local: `http://localhost:8000`
- Network: `http://192.168.1.100:8000`

---

### Computer 2: Discover and Call the Agent

On a **different computer** on the **same network**, install the SDK and run:

```bash
# Install SDK
pip install -e /path/to/astraeus-sdk

# Run discovery test
python test_discovery_client.py
```

**It will discover your agent and call it!** 🎉

---

## Option 3: Deploy Publicly (Internet Access)

Make your agent accessible from **ANYWHERE** on the internet!

### Quick Method: ngrok (for testing)

```bash
# Install ngrok: https://ngrok.com/download

# In Terminal 1: Start your agent
python test_simple_agent.py

# In Terminal 2: Expose it publicly
ngrok http 8000
```

**You'll get a public URL like:**
```
https://abc123.ngrok.io
```

Now **ANYONE** can discover and call your agent from **ANYWHERE**!

---

### Production Method: Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

**Your agent will be live at:** `https://your-agent.up.railway.app`

---

## Verify Agent Registration

Check if your agent is registered on the network:

```bash
curl https://web-production-3df46.up.railway.app/api/v1/mesh/agents | python -m json.tool
```

**You should see your TestAgent in the list!**

---

## Check Agent Card (A2A Protocol)

Verify your agent exposes a valid Agent Card:

```bash
curl http://localhost:8000/.well-known/agent.json | python -m json.tool
```

**Expected output:**
```json
{
  "name": "TestAgent",
  "description": "Simple test agent for ASTRAEUS network verification",
  "capabilities": [
    {
      "name": "echo",
      "description": "Echo back a message",
      "cost_per_call": 0.0
    },
    {
      "name": "calculate",
      "description": "Perform basic calculations",
      "cost_per_call": 0.01
    },
    {
      "name": "ping",
      "description": "Health check endpoint",
      "cost_per_call": 0.0
    }
  ],
  "endpoint": "http://0.0.0.0:8000",
  "a2a_version": "1.0.0"
}
```

---

## Test with cURL

You can also test your agent directly with curl:

```bash
# Test echo capability
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "echo", "input": {"message": "Hello ASTRAEUS!"}}'

# Test calculate capability
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "calculate", "input": {"expression": "5 + 3 * 2"}}'

# Test ping capability
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "ping", "input": {}}'
```

---

## Troubleshooting

### Agent won't start

**Check port 8000 is available:**
```bash
lsof -ti:8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process if needed
kill -9 $(lsof -ti:8000)
```

### Can't discover agent

1. **Wait 5 seconds** after agent starts (registration takes a moment)
2. **Verify agent is registered:**
   ```bash
   curl https://web-production-3df46.up.railway.app/api/v1/mesh/agents
   ```
3. **Check agent is running:**
   ```bash
   curl http://localhost:8000/health
   ```

### Connection refused from other computer

1. **Use `0.0.0.0` as host** (not `127.0.0.1`)
2. **Check firewall settings** - allow port 8000
3. **Verify you're on the same network**

---

## What's Happening Behind the Scenes

```
1. You run test_simple_agent.py
   └─ Agent creates FastAPI server
   └─ Exposes /.well-known/agent.json (Agent Card)
   └─ Calls /api/v1/mesh/agents/register
   └─ Stored in PostgreSQL database on ASTRAEUS network

2. You run test_discovery_client.py
   └─ GET /api/v1/mesh/agents?capability=echo
   └─ Backend queries PostgreSQL
   └─ Returns your agent info

3. Client calls your agent
   └─ Gets endpoint from search results
   └─ POST to http://your-agent/execute
   └─ Your capability function runs
   └─ Result returned
   └─ Trust score updated! ✅
```

---

## Next Steps After Testing

Once you've verified everything works:

1. **Build More Agents** - Create specialized agents for specific tasks
2. **Test Orchestration** - Try the TripPlanner example
3. **Deploy Production** - Use Railway/Heroku for 24/7 uptime
4. **Add Reviews** - Test the reputation system
5. **Monitor Stats** - Check trust scores and usage

---

## Success Criteria

✅ Agent starts without errors
✅ Agent appears in network search results
✅ Discovery client finds your agent
✅ All 3 capabilities respond correctly
✅ Agent Card is accessible
✅ Trust score updates after calls

**If all checkboxes are ✅, your ASTRAEUS network is FULLY OPERATIONAL!** 🎉

---

**Need help?** Check:
- `ASTRAEUS_QUICKSTART.md` - Detailed setup guide
- `ASTRAEUS_GUIDE.md` - Complete developer documentation
- `AUTONOMOUS_ECOSYSTEM.md` - Vision and use cases
