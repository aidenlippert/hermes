# 🚀 Getting Started with Hermes

Welcome! You're about to build the future of AI interaction.

## What You Have Right Now

A **working MVP** of the Hermes orchestration engine! Here's what's already built:

- ✅ Core conductor that understands user intent
- ✅ Agent registry system
- ✅ REST API with FastAPI
- ✅ Auto-generated API docs
- ✅ Test suite
- ✅ Project structure ready to scale

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Test It Works

```bash
python test_hermes.py
```

You should see all tests pass! ✅

### 3. Start the Server

```bash
python start.py
```

### 4. Try It Out

**Option A: Browser**
- Open http://localhost:8000/docs
- Click on `/orchestrate` → Try it out
- Enter: `{"query": "write me a Python function"}`
- Execute!

**Option B: Command Line**
```bash
curl -X POST http://localhost:8000/orchestrate \
     -H "Content-Type: application/json" \
     -d '{"query": "write me a Python function"}'
```

**Option C: Python**
```python
import requests

response = requests.post(
    "http://localhost:8000/orchestrate",
    json={"query": "help me debug my code"}
)
print(response.json())
```

## What Just Happened?

1. You sent a natural language request to Hermes
2. Hermes parsed your intent and figured out what you wanted
3. Hermes found which agents could help (CodeWizard in this case)
4. Hermes returned a plan for how it would coordinate those agents

**Right now:** It's simulating the responses (MVP)
**Next step:** Actually connect to real agents via A2A protocol!

## Project Structure

```
Hermes/
├── hermes/
│   ├── conductor/      # The brain - orchestration logic
│   │   └── core.py     # Main conductor class
│   ├── api/           # REST API layer
│   │   └── server.py  # FastAPI server
│   ├── registry/      # Agent discovery (coming soon)
│   ├── protocols/     # A2A/MCP integration (coming soon)
│   └── agents/        # Pre-built agent integrations (coming soon)
├── tests/             # Test suite
├── docs/              # Documentation
├── start.py          # Quick start script
└── test_hermes.py    # Test runner
```

## Next Steps

Choose your path:

### Path A: Connect Real Agents (Recommended)
See `docs/CONNECTING_AGENTS.md` (we'll create this next)

### Path B: Improve Intent Understanding
See `docs/INTENT_SYSTEM.md` (we'll create this next)

### Path C: Build the Frontend
See `docs/FRONTEND.md` (we'll create this next)

### Path D: Deploy to Production
See `docs/DEPLOYMENT.md` (we'll create this next)

## FAQ

**Q: Where are the actual AI agents?**
A: Right now we're simulating them. Next step is connecting to real A2A agents or building simple ones to test with.

**Q: How do I add my own agents?**
A: Call the `/agents/register` endpoint with your agent's details!

**Q: Can I use this without A2A?**
A: Yes! You can integrate agents using any protocol. A2A is just the standard we're building around.

**Q: Is this production ready?**
A: This is MVP/prototype code. For production, you'll want to add:
- Real agent connections
- Error handling
- Authentication
- Rate limiting
- Monitoring
- Database for persistence

## Getting Help

- 📖 Read the docs in `/docs`
- 💬 Ask questions (add your Discord/Slack link here)
- 🐛 Report issues on GitHub
- 📧 Email the team

---

**Ready to change the world? Let's go! 🚀**
