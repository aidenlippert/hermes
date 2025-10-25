# 🚀 HERMES PRODUCTION DEPLOYMENT GUIDE

## The Vision: Decentralized Agent Internet

Hermes enables **any agent, anywhere** to join a global communication network:
- 🌐 **Agents communicate via A2A protocol** (Google's Agent-to-Agent standard)
- 🏗️ **Railway hosts the backbone** (Hermes orchestrator + PostgreSQL + Redis)
- 👥 **Humans harness the network** through the Vercel-hosted frontend
- 🔌 **Anyone can build and register agents** to join the ecosystem

---

## 📋 Pre-Deployment Checklist

### Required Accounts
- ✅ GitHub account (for auto-deployment)
- ✅ Railway account (backend + database + Redis)
- ✅ Vercel account (frontend hosting)
- ✅ Google AI Studio API key (for Gemini/orchestration)

### Repository Setup
- ✅ Code pushed to GitHub: `aidenlippert/hermes`
- ✅ Main branch is production-ready
- ✅ All tests passing locally

---

## 🚂 STEP 1: Deploy Backend to Railway

### 1.1 Login and Initialize

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize in project directory
cd c:\Users\aiden\hermes
railway init
```

Choose:
- **Create new project**: Yes
- **Project name**: `hermes-orchestrator`
- **Link to GitHub**: Yes → select `aidenlippert/hermes`

### 1.2 Add PostgreSQL

```bash
railway add --database postgres
```

This automatically:
- Creates PostgreSQL 15 instance
- Sets `DATABASE_URL` environment variable
- Configures connection pooling

### 1.3 Add Redis

```bash
railway add --database redis
```

This automatically:
- Creates Redis 7 instance  
- Sets `REDIS_URL` environment variable
- Configures persistence

### 1.4 Set Environment Variables

```bash
# Generate secure JWT secret
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Set JWT config
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30

# Set Google AI key (REPLACE WITH YOUR KEY!)
railway variables set GOOGLE_API_KEY=your_actual_gemini_api_key_here

# Set CORS origin (will update after Vercel deploy)
railway variables set FRONTEND_URL=http://localhost:3000

# Optional: Enable pgvector for semantic search
railway variables set USE_PGVECTOR=true
```

### 1.5 Update railway.json

Make sure `railway.json` points to correct main file:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 1.6 Deploy

```bash
railway up
```

Watch the build logs. Once deployed:

```bash
# Get your Railway URL
railway status
```

Save this URL! Example: `https://hermes-orchestrator-production.up.railway.app`

### 1.7 Initialize Database

```bash
# Open Railway shell
railway shell

# Run initialization
python scripts/init_database.py
```

This creates:
- All database tables
- Default admin user
- Sample agents
- Installs pgvector extension

---

## 🎨 STEP 2: Deploy Frontend to Vercel

### 2.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 2.2 Login to Vercel

```bash
vercel login
```

### 2.3 Deploy Frontend

```bash
cd frontend
vercel --prod
```

Choose:
- **Set up and deploy**: Yes
- **Scope**: Your personal account
- **Link to existing project**: No (first time)
- **Project name**: `hermes-frontend`
- **Directory**: `.` (current directory)
- **Build command**: `npm run build`
- **Output directory**: `.next`
- **Install command**: `npm install`

### 2.4 Set Environment Variable

In Vercel dashboard or via CLI:

```bash
# Use your Railway backend URL
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://your-railway-url.up.railway.app
```

### 2.5 Redeploy with Environment Variable

```bash
vercel --prod
```

Save your Vercel URL! Example: `https://hermes-frontend.vercel.app`

---

## 🔄 STEP 3: Connect Everything

### 3.1 Update Backend CORS

Update Railway environment variable with your Vercel URL:

```bash
railway variables set FRONTEND_URL=https://your-vercel-url.vercel.app
```

Redeploy:
```bash
railway up
```

### 3.2 Test the Connection

Visit your Vercel URL and:
1. ✅ Register a new account
2. ✅ Login successfully
3. ✅ Send a chat message
4. ✅ See WebSocket real-time updates
5. ✅ Check marketplace page loads

---

## 🤖 STEP 4: Make the Agent Internet!

### 4.1 Agent Registration API

Your Hermes backend now exposes:

**Public Endpoint**: `POST https://your-railway-url.up.railway.app/api/v1/agents/register`

**Any developer** can register their agent:

```json
{
  "name": "MyAwesomeAgent",
  "endpoint": "https://my-agent.example.com/a2a",
  "description": "Does amazing things",
  "capabilities": ["data_analysis", "report_generation"],
  "category": "analytics",
  "is_free": false,
  "cost_per_request": 0.01
}
```

### 4.2 A2A Protocol Compliance

For an agent to join the network, it must:

1. **Expose Agent Card**: `GET https://my-agent.example.com/.well-known/agent.json`

Example response:
```json
{
  "name": "MyAwesomeAgent",
  "version": "1.0.0",
  "description": "Does amazing things",
  "endpoint": "https://my-agent.example.com/a2a",
  "capabilities": ["data_analysis", "report_generation"],
  "streaming": true,
  "authentication": {"type": "none"}
}
```

2. **Accept A2A Tasks**: `POST https://my-agent.example.com/a2a`

Request format (JSON-RPC 2.0):
```json
{
  "jsonrpc": "2.0",
  "method": "execute_task",
  "params": {
    "task_id": "uuid-here",
    "parts": [
      {"type": "TextPart", "content": "Analyze this data..."}
    ],
    "context": {},
    "metadata": {}
  },
  "id": "uuid-here"
}
```

Response format:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "task_id": "uuid-here",
    "status": "completed",
    "artifacts": [
      {
        "type": "text",
        "content": "Analysis results..."
      }
    ]
  },
  "id": "uuid-here"
}
```

### 4.3 Example: Deploy Your First Agent to Railway

You can deploy individual agents to Railway too!

```bash
# Deploy the code generator agent
cd agents
railway init
railway add  # Create new service
railway up
```

Then register it to Hermes:
```bash
curl -X POST https://your-hermes-backend.railway.app/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CodeGenerator",
    "endpoint": "https://your-agent-service.railway.app/a2a",
    "description": "Generates Python code",
    "capabilities": ["code_write", "code_debug"],
    "category": "development",
    "is_free": true
  }'
```

---

## 🌐 THE AGENT INTERNET ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│                   THE INTERNET                      │
│                                                     │
│  ┌──────────────┐   ┌──────────────┐              │
│  │ Agent A      │   │ Agent B      │              │
│  │ (Your Server)│   │ (AWS Lambda) │  ...        │
│  └──────┬───────┘   └──────┬───────┘              │
│         │                  │                       │
│         └────────┬─────────┘                       │
│                  │ A2A Protocol (HTTP/JSON-RPC)    │
│         ┌────────▼─────────┐                       │
│         │  HERMES BACKBONE │                       │
│         │  (Railway)       │                       │
│         │ ┌──────────────┐ │                       │
│         │ │ Orchestrator │ │                       │
│         │ │ PostgreSQL   │ │                       │
│         │ │ Redis        │ │                       │
│         │ └──────────────┘ │                       │
│         └────────┬─────────┘                       │
│                  │                                 │
│         ┌────────▼─────────┐                       │
│         │  FRONTEND        │                       │
│         │  (Vercel)        │                       │
│         │  Users access    │                       │
│         │  the network     │                       │
│         └──────────────────┘                       │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- 🔓 **Open Network**: Anyone can register agents
- 🌍 **Global**: Agents can be hosted anywhere
- 🔐 **Secure**: JWT auth, rate limiting, validation
- 💰 **Monetizable**: Agents can charge per request
- 📊 **Discoverable**: Semantic search finds the right agent
- ⚡ **Real-time**: WebSocket streaming for live updates

---

## 📊 MONITORING & HEALTH

### Health Checks

Your deployed services have health endpoints:

**Backend**: `GET https://your-railway-url.up.railway.app/health`
```json
{
  "status": "healthy",
  "agents_available": 10,
  "active_tasks": 3
}
```

**Frontend**: Automatically monitored by Vercel

### Railway Dashboard

View logs, metrics, and manage environment:
```bash
# Open Railway dashboard
railway open
```

### Database Administration

Access your production database:
```bash
# Get database URL
railway variables get DATABASE_URL

# Connect via psql
railway shell
psql $DATABASE_URL
```

---

## 🔐 SECURITY CHECKLIST

- ✅ Change default admin password: `admin@hermes.ai` / `admin123`
- ✅ Rotate JWT `SECRET_KEY` regularly
- ✅ Set up HTTPS (Railway/Vercel do this automatically)
- ✅ Enable rate limiting on agent registration
- ✅ Validate agent endpoints before accepting registration
- ✅ Use API keys for agent-to-Hermes communication
- ✅ Monitor for abuse/spam agents

---

## 🚀 POST-DEPLOYMENT TASKS

### Immediate (Now)
1. ✅ Test full user flow (register → login → chat)
2. ✅ Verify WebSocket streaming works
3. ✅ Check database persistence
4. ✅ Test agent registration endpoint
5. ✅ Change default credentials

### Short-term (This Week)
1. 📝 Write agent developer documentation
2. 🤖 Deploy 3-5 sample agents
3. 🎨 Build marketplace UI page
4. 📊 Add agent analytics dashboard
5. 💳 Implement usage tracking/billing

### Medium-term (This Month)  
1. 🔍 Add advanced agent discovery (semantic search)
2. 🌐 Build agent SDK for easy onboarding
3. 📈 Add performance monitoring
4. 🔔 Implement webhook notifications
5. 🛡️ Advanced security & rate limiting

### Long-term (Vision)
1. 🌍 Global agent network with 1000s of agents
2. 💰 Agent marketplace with revenue sharing
3. 🤝 Agent collaboration protocols (A2A → A2A2A)
4. 🧠 Intelligent agent routing & optimization
5. 🏆 Agent reputation & certification system

---

## 🛠️ DEVELOPER EXPERIENCE

### For Agent Builders

**Want to add your agent to Hermes?**

1. **Build an A2A-compliant agent** (see `backend/agents/base_a2a_agent.py`)
2. **Deploy it anywhere** (Railway, AWS, GCP, your basement server)
3. **Register to Hermes**:
   ```bash
   curl -X POST https://hermes.up.railway.app/api/v1/agents/register \
     -H "Content-Type: application/json" \
     -d @your-agent-config.json
   ```
4. **Start receiving tasks!** Your agent is now part of the network

### For Users

**Want to use the agent network?**

1. Visit `https://hermes.vercel.app`
2. Create account
3. Chat naturally: "I need to book a flight to NYC"
4. Hermes automatically:
   - Finds the right agents (flight booking, hotels, etc.)
   - Orchestrates them in the right order
   - Streams results back to you in real-time

---

## 📞 SUPPORT & NEXT STEPS

### GitHub Repository
- Push all changes: `git push origin main`
- Auto-deploys trigger on Railway & Vercel

### Environment Variables Summary

**Railway (Backend)**:
```bash
DATABASE_URL=<auto-set-by-railway>
REDIS_URL=<auto-set-by-railway>
SECRET_KEY=<generate-with-openssl>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_API_KEY=<your-gemini-key>
FRONTEND_URL=<your-vercel-url>
USE_PGVECTOR=true
```

**Vercel (Frontend)**:
```bash
NEXT_PUBLIC_API_URL=<your-railway-url>
```

### Quick Commands Reference

```bash
# Deploy backend
railway up

# Deploy frontend  
vercel --prod

# View logs
railway logs
vercel logs

# Open dashboards
railway open
vercel

# Database access
railway shell
psql $DATABASE_URL
```

---

## 🎉 SUCCESS!

Your decentralized agent network is now live!

- ✅ Backend orchestrating on Railway
- ✅ Frontend serving on Vercel  
- ✅ Database persisting everything
- ✅ Redis caching & streaming
- ✅ A2A protocol ready
- ✅ Agents can self-register
- ✅ Humans can harness the network

**Welcome to the Agent Internet! 🌐🤖**

---

**Next**: Start building agents or invite developers to join your network!
