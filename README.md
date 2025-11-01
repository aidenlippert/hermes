# Hermes - The Operating System for AI Agent Orchestration

**Making Google's A2A Protocol Actually Usable**

Hermes is a production-ready AI agent orchestration platform that sits on top of the A2A (Agent-to-Agent) protocol, providing intelligent routing, multi-agent coordination, real-time streaming, and a complete developer experience.

Just like Chrome made TCP/IP usable for browsing, **Hermes makes A2A usable for everyone**.

## 🌟 Features

### Core Platform
- ✅ **Full A2A Protocol** - Complete implementation with agent discovery, task execution
- ✅ **Multi-Agent Orchestration** - Coordinate multiple agents to solve complex tasks
- ✅ **Real-Time Streaming** - Live WebSocket updates during execution
- ✅ **Semantic Agent Search** - Vector embeddings (pgvector) for intelligent agent discovery
- ✅ **Multi-Turn Memory** - Conversation persistence across sessions
- ✅ **Production Backend** - FastAPI with async/await, error handling, logging

### AI-Powered Intelligence
- ✅ **Intent Parser** - Gemini understands natural language queries
- ✅ **Workflow Planner** - Auto-generates multi-agent execution plans
- ✅ **Smart Routing** - Finds the right agents for each task
- ✅ **Execution Engine** - Robust orchestration with retries and fallbacks

### Developer Experience
- ✅ **RESTful API** - Clean, documented endpoints
- ✅ **WebSocket Streaming** - Real-time progress updates
- ✅ **JWT Authentication** - Secure user management
- ✅ **Rate Limiting** - Tier-based usage controls
- ✅ **OpenAPI Docs** - Auto-generated API documentation

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install Python 3.10+
python3 --version

# Install Docker
docker --version
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL + Redis
docker-compose up -d

# Initialize database (creates tables, seeds data)
python3 scripts/init_database.py
```

### 4. Start Hermes

```bash
# Terminal 1: Start backend
python3 backend/main_v2.py

# Terminal 2: Start all agents
./start_all_agents.sh

# Or start agents individually:
python3 test_agent_code_generator.py   # port 10001
python3 test_agent_content_writer.py   # port 10002
python3 test_agent_data_analyzer.py    # port 10003
python3 test_agent_web_searcher.py     # port 10004
```

### 5. Test It!

```bash
# Automated multi-agent test
python3 test_multi_agent.py

# WebSocket streaming test
python3 test_websocket_client.py

# Or use the API directly
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

## 🎯 What Hermes Does

### Example: Simple Query

```
User: "Write a Python function to calculate fibonacci numbers"

Hermes:
  1. Parses intent → "code_generation"
  2. Searches agents → Finds CodeGenerator
  3. Creates plan → 1-step execution
  4. Executes → Calls CodeGenerator via A2A
  5. Streams events → Real-time progress via WebSocket
  6. Returns result → Working Python code
```

### Example: Complex Multi-Agent Task

```
User: "Research AI trends and write a blog post about them"

Hermes:
  1. Parses intent → "research + content_creation"
  2. Searches agents → Finds WebSearcher + ContentWriter
  3. Creates plan:
     - Step 1: WebSearcher researches AI trends
     - Step 2: ContentWriter creates blog post using research
  4. Executes sequentially, passing context between steps
  5. Streams real-time updates for each step
  6. Returns final blog post
```

## 📡 Real-Time WebSocket Streaming

Watch orchestration happen live:

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/tasks/${taskId}?token=${token}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Events you'll receive:
  // - intent_parsing_started
  // - agents_found (with agent list)
  // - plan_created (with execution steps)
  // - step_started (for each agent)
  // - agent_thinking
  // - step_completed (with results)
  // - task_completed
};
```

See `WEBSOCKET_STREAMING.md` for complete guide.

## 🤖 Available Agents

### CodeGenerator (Port 10001)
Generates code in any programming language
- **Capabilities**: code_write, code_debug, code_explain, code_review
- **Example**: "Write a Python function to sort a list"

### ContentWriter (Port 10002)
Creates blog posts, articles, marketing copy
- **Capabilities**: content_write, blog_write, article_write, social_media, marketing_copy
- **Example**: "Write a blog post about AI in healthcare"

### DataAnalyzer (Port 10003)
Analyzes CSV/JSON data, finds patterns, provides insights
- **Capabilities**: data_analysis, csv_analysis, json_analysis, statistical_analysis
- **Example**: "Analyze this sales data and find trends"

### WebSearcher (Port 10004)
Searches the web, aggregates news, provides current information
- **Capabilities**: web_search, research, news_aggregation, fact_checking
- **Example**: "What are the latest developments in quantum computing?"

## 📚 API Endpoints

### Authentication
```
POST /api/v1/auth/register - Create account
POST /api/v1/auth/login    - Get JWT token
GET  /api/v1/auth/me       - Current user info
```

### Orchestration
```
POST /api/v1/chat          - Main endpoint (with streaming!)
```

### Agent Marketplace
```
GET  /api/v1/marketplace              - List all agents
POST /api/v1/marketplace/search       - Semantic search for agents
```

### Conversations
```
GET /api/v1/conversations             - User's conversations
GET /api/v1/conversations/{id}        - Full conversation with messages
```

### WebSocket
```
WS /api/v1/ws/tasks/{task_id}  - Real-time task updates
WS /api/v1/ws/user             - User-wide updates
```

### Docs
```
http://localhost:8000/docs - Interactive API documentation
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HERMES PLATFORM                       │
│                                                          │
│  ┌──────────┐    WebSocket    ┌────────────────┐       │
│  │  Client  │ ←───────────────→ │   WebSocket   │       │
│  └────┬─────┘     Events       │    Manager    │       │
│       │                         └────────────────┘       │
│       │ REST API                                         │
│       ↓                                                  │
│  ┌──────────────────────────────────────────────┐       │
│  │           FastAPI Backend                     │       │
│  │  ┌────────┐  ┌────────┐  ┌──────────────┐  │       │
│  │  │  Auth  │  │  Chat  │  │  Marketplace │  │       │
│  │  └────────┘  └────────┘  └──────────────┘  │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                    │
│  ┌──────────────────┴─────────────────────────┐         │
│  │       ORCHESTRATION ENGINE                 │         │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────┐ │         │
│  │  │  Intent  │→ │  Planner │→ │ Executor│ │         │
│  │  │  Parser  │  │ (Gemini) │  │(Stream) │ │         │
│  │  └──────────┘  └──────────┘  └─────┬───┘ │         │
│  └─────────────────────────────────────┼─────┘         │
│                                         │               │
│  ┌──────────────────────────────────────┼─────┐         │
│  │         DATABASE LAYER               │     │         │
│  │  ┌──────────────┐  ┌──────────────┐ │     │         │
│  │  │ PostgreSQL + │  │    Redis     │ │     │         │
│  │  │   pgvector   │  │ (Cache/Sub)  │ │     │         │
│  │  └──────────────┘  └──────────────┘ │     │         │
│  └─────────────────────────────────────┘     │         │
│                                               │         │
└───────────────────────────────────────────────┼─────────┘
                                                │
                  ┌─────────────────────────────┼──────┐
                  │       A2A PROTOCOL          │      │
                  └─────────────┬───────────────┘      │
                                │                      │
      ┌─────────────────────────┼──────────────────────┤
      ↓                         ↓                      ↓
┌────────────┐          ┌────────────┐        ┌────────────┐
│CodeGen     │          │ContentWrite│        │DataAnalyze │
│(10001)     │          │(10002)     │        │(10003)     │
└────────────┘          └────────────┘        └────────────┘
      ↓
┌────────────┐
│WebSearch   │
│(10004)     │
└────────────┘
```

## 💾 Database Schema

### Key Tables
- **users** - Authentication, subscription tiers, usage tracking
- **agents** - Agent registry with vector embeddings for semantic search
- **tasks** - Task tracking with intent, plan, execution status
- **conversations** - Multi-turn conversation persistence
- **messages** - Full chat history with role and timestamps
- **executions** - Performance metrics and execution history
- **agent_ratings** - User feedback and agent performance
- **api_keys** - API key management

See `backend/database/models.py` for complete schema.

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL="postgresql+asyncpg://hermes:hermes@localhost:5432/hermes"

# Redis
REDIS_URL="redis://localhost:6379"

# JWT
SECRET_KEY="your-secret-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google AI
GOOGLE_API_KEY="your-gemini-api-key"
```

### Docker Services

```yaml
# PostgreSQL 15 + pgvector (port 5432)
# Redis 7 (port 6379)
# pgAdmin (port 5050, optional)
```

## 📖 Documentation

- **STATUS.md** - Current development status and roadmap
- **WEBSOCKET_STREAMING.md** - WebSocket integration guide
- **backend/database/models.py** - Database schema
- **http://localhost:8000/docs** - Interactive API docs

## 🧪 Testing

### Automated Tests

```bash
# Multi-agent coordination
python3 test_multi_agent.py

# WebSocket streaming
python3 test_websocket_client.py

# Individual agents
python3 test_agent_code_generator.py
python3 test_agent_content_writer.py
python3 test_agent_data_analyzer.py
python3 test_agent_web_searcher.py
```

### Manual Testing

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# 2. Login (get token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# 3. Send query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "Write a Python function to reverse a string"}'
```

## 🎨 What Makes Hermes Special

### 1. Semantic Agent Discovery
Not keyword matching - uses vector embeddings to understand meaning:
```
Query: "help me write code"
→ Finds: CodeGenerator, not just agents with "code" in name
```

### 2. Hub-and-Spoke Architecture
Agents never talk directly - all communication flows through Hermes:
- Central state management
- Full audit trail
- Error recovery
- Performance tracking

### 3. Multi-Turn Memory
Context persists across sessions:
```
User: "Write a function"
Hermes: *generates code*
User: "Add error handling"
Hermes: *understands context, updates code*
```

### 4. Real-Time Streaming
See orchestration happen live via WebSocket

### 5. Production-Ready
JWT auth, rate limiting, error handling, migrations, Docker

## 📋 Roadmap

### Next Steps
- [ ] Build more agents (Image generation, Email, etc.)
- [ ] Create frontend (Next.js with live streaming)
- [ ] Agent builder UI (no-code agent creation)
- [ ] Deploy to production (Google Cloud Run + Vercel)

See `STATUS.md` for complete roadmap.

## 🤝 Contributing

This is a product in active development. Core features are complete and working.

## 📄 License

MIT License - see LICENSE file

## 🎯 Vision

**Hermes makes A2A Protocol usable for everyone.**

Just like:
- Chrome/Safari made TCP/IP usable for browsing
- Stripe made payment APIs usable for developers
- Twilio made telecom APIs usable for apps

We don't replace A2A - we make it *actually work* for consumers and businesses.

---

**Version**: 2.0.0
**Status**: 🟢 Production-ready core, expanding agent ecosystem
**Made with**: Python, FastAPI, PostgreSQL, Redis, Gemini AI, A2A Protocol
# Force Railway redeploy - Fri Oct 31 22:39:06 PDT 2025
