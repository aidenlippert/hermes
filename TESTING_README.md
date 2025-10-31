# 🧪 ASTRAEUS Testing Environment - Quick Start

**Complete testing setup with mock agents, LangChain integration, and sample data.**

---

## ⚡ 60-Second Setup

```bash
# 1. Install dependencies for mock agents
pip install -r mock_agents/requirements.txt

# 2. Start all mock agents
./start_mock_agents.sh

# 3. Seed test data
python -m backend.scripts.seed_test_data

# 4. Start backend (in another terminal)
cd backend && uvicorn main:app --reload
```

**Done! 🎉** Open http://localhost:8000/docs to test.

---

## 📊 What You Get

### **Test Users** (3)
- `alice@test.com` - Pro user with $100 credits
- `bob@test.com` - Free user with $25 credits
- `dev@test.com` - Agent developer with $500 credits

Password for all: `test123`

### **Mock Agents** (4)
| Agent | Type | Price | Port |
|-------|------|-------|------|
| Translation Bot | Paid | $0.05 | 8001 |
| Free Summarizer | Free | $0.00 | 8002 |
| Code Analyzer Pro | Paid | $0.10 | 8003 |
| LangChain AI | Paid | $0.15 | 8004 |

### **Sample Data**
- 3 contracts (active, completed, draft)
- Credit transactions history
- Conversations and messages
- Reputation scores
- Analytics data

---

## 🚀 Quick Tests

### Test Agent Execution
```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@test.com","password":"test123"}' \
  | jq -r '.access_token')

# Execute Translation Bot
curl -X POST http://localhost:8000/api/v1/agents/agent_translator/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input":{"text":"Hello","target_language":"es"}}'
```

### Test Multi-Agent Orchestration
```bash
# Create orchestration plan
curl -X POST http://localhost:8000/api/v1/orchestration/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Translate to Spanish then summarize"}'
```

### Test Credit Purchase
```bash
# Purchase credits
curl -X POST http://localhost:8000/api/v1/payments/credits/purchase \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":50.0,"provider":"stripe"}'
```

---

## 🤖 LangChain Agent (Optional)

The LangChain agent works in **fallback mode** without OpenAI API key.

**To enable real AI**:
```bash
cd langchain_agent
cp .env.example .env
# Add your OPENAI_API_KEY to .env
pip install -r requirements.txt
```

Then restart: `./stop_mock_agents.sh && ./start_mock_agents.sh`

---

## 📚 Full Documentation

See **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** for:
- Complete API workflows
- Testing scenarios
- Troubleshooting guide
- Health checks
- Logs and debugging

---

## 🛑 Stop Agents

```bash
./stop_mock_agents.sh
```

---

## ✅ Health Check

All systems ready when:
```bash
# All should return "healthy"
curl http://localhost:8000/health       # Backend
curl http://localhost:8001/health       # Translation
curl http://localhost:8002/health       # Summarizer
curl http://localhost:8003/health       # Code Analyzer
curl http://localhost:8004/health       # LangChain
```

---

**Next: Build frontend pages! 🎨**
