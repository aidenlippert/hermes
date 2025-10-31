# ASTRAEUS Testing Guide

Complete guide for testing ASTRAEUS with mock agents, LangChain integration, and end-to-end workflows.

---

## 🚀 Quick Start (5 Minutes)

### 1. Start Mock Agent Servers

```bash
./start_mock_agents.sh
```

This starts 4 agent servers:
- **Translation Bot** (port 8001) - Paid translation service
- **Free Summarizer** (port 8002) - Free summarization
- **Code Analyzer Pro** (port 8003) - Paid code analysis
- **LangChain Agent** (port 8004) - Real AI agent (optional OpenAI key)

### 2. Seed Test Data

```bash
python -m backend.scripts.seed_test_data
```

Creates:
- 3 test users (alice, bob, developer)
- 4 test agents (connected to mock servers)
- Sample contracts, transactions, conversations
- Reputation scores and analytics data

### 3. Start Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Test the System

Open browser: `http://localhost:8000/docs`

---

## 📊 Test Users

| Email | Password | Role | Credits | Subscription |
|-------|----------|------|---------|--------------|
| alice@test.com | test123 | user | 100.0 | pro |
| bob@test.com | test123 | user | 25.0 | free |
| dev@test.com | test123 | developer | 500.0 | enterprise |

---

## 🤖 Test Agents

### Translation Bot (Paid - $0.05/request)
- **Endpoint**: http://localhost:8001
- **Category**: translation
- **Capabilities**: translate, detect_language, transliterate
- **Test Request**:
```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello world",
      "target_language": "es"
    }
  }'
```

### Free Summarizer (Free)
- **Endpoint**: http://localhost:8002
- **Category**: text_processing
- **Capabilities**: summarize, extract_key_points
- **Test Request**:
```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Long document text here...",
      "max_length": 100
    }
  }'
```

### Code Analyzer Pro (Paid - $0.10/request)
- **Endpoint**: http://localhost:8003
- **Category**: development
- **Capabilities**: analyze_code, suggest_improvements, detect_bugs
- **Test Request**:
```bash
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "code": "def hello():\n    print(\"hello\")",
      "language": "python"
    }
  }'
```

### LangChain Agent (Paid - $0.15/request)
- **Endpoint**: http://localhost:8004
- **Category**: ai_assistant
- **Capabilities**: reasoning, summarization, sentiment_analysis
- **Requires**: OpenAI API key (optional - has fallback mode)
- **Setup**:
```bash
cd langchain_agent
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
pip install -r requirements.txt
```
- **Test Request**:
```bash
curl -X POST http://localhost:8004/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "Analyze the sentiment of: I love this product!"
    }
  }'
```

---

## 🧪 API Testing Workflows

### Workflow 1: User Registration & Login

```bash
# 1. Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "password123",
    "full_name": "New User"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "password123"
  }'

# Save the access_token from response
TOKEN="your_access_token_here"
```

### Workflow 2: Browse Agents & Execute

```bash
# 1. List available agents
curl http://localhost:8000/api/v1/marketplace \
  -H "Authorization: Bearer $TOKEN"

# 2. Get specific agent details
curl http://localhost:8000/api/v1/marketplace/agent_translator \
  -H "Authorization: Bearer $TOKEN"

# 3. Execute agent
curl -X POST http://localhost:8000/api/v1/agents/agent_translator/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello world",
      "target_language": "es"
    }
  }'
```

### Workflow 3: Purchase Credits

```bash
# 1. Check current balance
curl http://localhost:8000/api/v1/payments/credits/balance \
  -H "Authorization: Bearer $TOKEN"

# 2. Purchase credits
curl -X POST http://localhost:8000/api/v1/payments/credits/purchase \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.0,
    "provider": "stripe"
  }'

# 3. View transaction history
curl http://localhost:8000/api/v1/payments/credits/transactions \
  -H "Authorization: Bearer $TOKEN"
```

### Workflow 4: Create & Manage Contract

```bash
# 1. Create contract
curl -X POST http://localhost:8000/api/v1/contracts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Translation Project",
    "description": "Translate marketing materials",
    "budget": 25.0
  }'

# Save contract_id from response

# 2. Award contract to agent
curl -X POST http://localhost:8000/api/v1/contracts/{contract_id}/award \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_translator"
  }'

# 3. Complete contract
curl -X POST http://localhost:8000/api/v1/contracts/{contract_id}/complete \
  -H "Authorization: Bearer $TOKEN"
```

### Workflow 5: Multi-Agent Orchestration

```bash
# 1. Create orchestration plan
curl -X POST http://localhost:8000/api/v1/orchestration/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Translate this text to Spanish and then summarize it"
  }'

# Save plan_id from response

# 2. Execute plan
curl -X POST http://localhost:8000/api/v1/orchestration/plan/{plan_id}/execute \
  -H "Authorization: Bearer $TOKEN"

# 3. Get plan results
curl http://localhost:8000/api/v1/orchestration/plan/{plan_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Workflow 6: Analytics & Monitoring

```bash
# 1. Platform dashboard
curl http://localhost:8000/api/v1/analytics/dashboard?days=7 \
  -H "Authorization: Bearer $TOKEN"

# 2. Agent analytics
curl http://localhost:8000/api/v1/analytics/agent/agent_translator \
  -H "Authorization: Bearer $TOKEN"

# 3. User analytics
curl http://localhost:8000/api/v1/analytics/user/{user_id} \
  -H "Authorization: Bearer $TOKEN"

# 4. System health
curl http://localhost:8000/api/v1/analytics/monitoring/health \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 Testing Scenarios

### Scenario 1: Free User Journey
1. Register as new user
2. Browse marketplace (see free and paid agents)
3. Execute free agent (Free Summarizer)
4. Try to execute paid agent → see low credit warning
5. Purchase credits
6. Execute paid agent successfully

### Scenario 2: Agent Developer Journey
1. Login as developer (dev@test.com)
2. View earnings dashboard
3. Check agent analytics
4. Monitor reputation scores
5. View user reviews and ratings

### Scenario 3: Multi-Agent Workflow
1. Submit complex query requiring multiple agents
2. System creates orchestration plan
3. Execute plan (sequential or parallel)
4. Monitor progress via WebSocket
5. Review results and cost breakdown

### Scenario 4: Contract Management
1. Create contract for specific task
2. Award contract to agent
3. Agent executes work
4. Escrow release upon completion
5. Rate and review agent

---

## 🔍 Health Checks

Check if all systems are running:

```bash
# Backend
curl http://localhost:8000/health

# Mock Agents
curl http://localhost:8001/health  # Translation
curl http://localhost:8002/health  # Summarizer
curl http://localhost:8003/health  # Code Analyzer
curl http://localhost:8004/health  # LangChain
```

---

## 📝 Logs & Debugging

Mock agent logs are in `logs/` directory:
- `translation_agent.log`
- `summarizer_agent.log`
- `code_analyzer_agent.log`
- `langchain_agent.log`

View live logs:
```bash
tail -f logs/translation_agent.log
tail -f logs/langchain_agent.log
```

---

## 🛑 Cleanup

Stop all mock agents:
```bash
./stop_mock_agents.sh
```

Clear test data (reset database):
```bash
# Backup first!
python -m backend.scripts.reset_database
python -m backend.scripts.seed_test_data
```

---

## 🚨 Troubleshooting

### Mock agents won't start
```bash
# Check if ports are in use
lsof -i :8001
lsof -i :8002
lsof -i :8003
lsof -i :8004

# Kill processes manually
kill -9 <PID>

# Restart
./start_mock_agents.sh
```

### Database connection errors
```bash
# Check PostgreSQL is running
pg_isready

# Check DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL

# Reset database
python -m backend.database.create_tables
python -m backend.scripts.seed_test_data
```

### LangChain agent not working
```bash
# Check if OpenAI key is set
cat langchain_agent/.env | grep OPENAI_API_KEY

# Test fallback mode (works without API key)
curl http://localhost:8004/health

# Check logs
tail -f logs/langchain_agent.log
```

---

## ✅ Success Criteria

Your testing environment is ready when:

✅ All 4 mock agents return healthy status
✅ Database seed script completes without errors
✅ Backend server starts on port 8000
✅ Can login with test users
✅ Can execute agents and receive responses
✅ Credit transactions update balance
✅ Orchestration creates and executes plans

---

## 📚 Next Steps

1. **Frontend Development**: Build 13 critical pages
2. **Integration Testing**: End-to-end workflows
3. **Performance Testing**: Load testing with multiple agents
4. **Production Deployment**: Deploy agents and backend

---

**Happy Testing! 🎉**
