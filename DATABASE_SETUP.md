# 🗄️ DATABASE SETUP GUIDE

Complete guide to setting up Hermes with PostgreSQL + Redis + full persistence!

---

## ✅ WHAT WE BUILT

### **Complete Database Layer**:
1. **PostgreSQL with pgvector** - Semantic search for agents
2. **Redis** - Caching and real-time features
3. **8 Database Tables**:
   - `users` - User accounts & authentication
   - `api_keys` - API key management
   - `agents` - Agent registry with embeddings
   - `agent_ratings` - User ratings for agents
   - `conversations` - Multi-turn chat sessions
   - `messages` - Individual messages
   - `tasks` - Orchestration requests
   - `executions` - Step-by-step execution logs

### **Services Built**:
1. **AuthService** - JWT auth, password hashing, API keys
2. **AgentRegistry** - Semantic search, agent management
3. **ConversationService** - Multi-turn context management
4. **TaskService** - Task and execution tracking

---

## 🚀 QUICK START (5 Minutes)

### Step 1: Start Docker Services

```bash
# Start PostgreSQL + Redis
docker-compose up -d

# Verify they're running
docker ps
```

You should see:
- `hermes_postgres` on port 5432
- `hermes_redis` on port 6379

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database

```bash
python3 scripts/init_database.py
```

This will:
- Create all tables
- Install pgvector extension
- Create admin & test users
- Register default agents

### Step 4: Test It!

```bash
# Test database connection
cd backend/database
python3 connection.py
```

---

## 📊 DATABASE SCHEMA

### Users Table
```sql
users:
  - id (uuid)
  - email (unique)
  - username (unique)
  - hashed_password
  - role (user|admin|agent_creator)
  - subscription_tier (free|pro|enterprise)
  - total_requests, requests_this_month
  - created_at, updated_at, last_login
```

### Agents Table (with pgvector!)
```sql
agents:
  - id (uuid)
  - name (unique)
  - description
  - endpoint
  - capabilities (json array)
  - description_embedding (vector[1536])  ← Semantic search!
  - performance metrics (total_calls, success_rate, avg_duration, avg_rating)
  - status (active|inactive|pending_review|rejected)
  - created_at, updated_at
```

### Tasks Table
```sql
tasks:
  - id (uuid)
  - user_id
  - conversation_id
  - query
  - status (pending|in_progress|completed|failed)
  - parsed_intent (json)
  - execution_plan (json)
  - final_output
  - metrics (total_steps, completed_steps, duration, cost)
  - created_at, completed_at
```

### Conversations Table
```sql
conversations:
  - id (uuid)
  - user_id
  - title
  - total_messages
  - created_at, last_message_at

messages:
  - id (uuid)
  - conversation_id
  - role (user|assistant|system)
  - content
  - task_id (optional)
  - created_at
```

---

## 🔐 DEFAULT CREDENTIALS

**Created by init script:**

**Admin Account:**
- Email: `admin@hermes.ai`
- Password: `admin123`

**Test Account:**
- Email: `test@example.com`
- Password: `test123`
- API Key: (printed during init)

⚠️ **CHANGE THESE IN PRODUCTION!**

---

## 🧪 TESTING THE DATABASE

### Test 1: Connection
```bash
cd backend/database
python3 connection.py
```

Expected output:
```
✅ PostgreSQL connected and initialized
✅ Redis connected and working
```

### Test 2: Create a User
```python
from backend.services.auth import AuthService
from backend.database.connection import AsyncSessionLocal

async with AsyncSessionLocal() as db:
    user = await AuthService.register_user(
        db,
        email="newuser@example.com",
        password="password123"
    )
    print(f"User created: {user.email}")
```

### Test 3: Semantic Agent Search
```python
from backend.services.agent_registry import AgentRegistry
from backend.database.connection import AsyncSessionLocal

async with AsyncSessionLocal() as db:
    # Search for agents
    agents = await AgentRegistry.semantic_search(
        db,
        query="I need help writing code",
        limit=5
    )

    for agent in agents:
        print(f"Found: {agent.name} - {agent.description}")
```

---

## 🛠️ COMMON OPERATIONS

### View Database (Optional)

Open pgAdmin in browser:
```
http://localhost:5050
Email: admin@hermes.ai
Password: admin
```

Add server:
- Host: `postgres`
- Port: `5432`
- Database: `hermes`
- Username: `hermes`
- Password: `hermes_dev_password`

### Reset Database

```bash
# Stop containers
docker-compose down

# Remove volumes (DELETES ALL DATA!)
docker volume rm hermes_postgres_data hermes_redis_data

# Start fresh
docker-compose up -d
python3 scripts/init_database.py
```

### Backup Database

```bash
# Backup
docker exec hermes_postgres pg_dump -U hermes hermes > backup.sql

# Restore
docker exec -i hermes_postgres psql -U hermes hermes < backup.sql
```

---

## 🔧 ENVIRONMENT VARIABLES

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://hermes:hermes_dev_password@localhost:5432/hermes
REDIS_URL=redis://:hermes_dev_password@localhost:6379/0

# Auth
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# APIs
GOOGLE_API_KEY=your-gemini-api-key
```

---

## 📈 WHAT YOU CAN DO NOW

With the database layer, you now have:

✅ **User Management**
- Registration & login
- JWT authentication
- API key management
- Subscription tiers

✅ **Agent Discovery**
- Semantic search for agents
- Agent performance tracking
- User ratings
- Agent marketplace ready

✅ **Conversation Memory**
- Multi-turn conversations
- Context persistence
- Conversation history

✅ **Task Tracking**
- Full orchestration history
- Step-by-step execution logs
- Performance analytics
- Cost tracking

---

## 🚨 TROUBLESHOOTING

**Docker containers won't start:**
```bash
# Check Docker is running
docker --version

# Check ports aren't in use
lsof -i :5432
lsof -i :6379

# View logs
docker-compose logs postgres
docker-compose logs redis
```

**Can't connect to database:**
```bash
# Test PostgreSQL directly
docker exec -it hermes_postgres psql -U hermes -d hermes

# Inside psql, run:
\dt  # List tables
\q   # Quit
```

**pgvector not installed:**
```bash
# Connect to postgres
docker exec -it hermes_postgres psql -U hermes -d hermes

# Run:
CREATE EXTENSION IF NOT EXISTS vector;
\dx  # List extensions
```

**Redis connection fails:**
```bash
# Test Redis
docker exec -it hermes_redis redis-cli -a hermes_dev_password ping

# Should return: PONG
```

---

## 🎯 NEXT STEPS

Now that you have the database:

1. **Update Backend API** - Connect `/api/v1/chat` to database
2. **Add Auth Endpoints** - `/api/v1/auth/register`, `/login`, etc.
3. **Agent Marketplace** - `/api/v1/marketplace` with search
4. **WebSocket Streaming** - Real-time updates
5. **Frontend** - Build the UI!

---

## 📝 FILES CREATED

```
docker-compose.yml                        # PostgreSQL + Redis
backend/database/
  ├── connection.py                       # DB connection & Redis
  ├── models.py                           # SQLAlchemy models (8 tables)
  ├── init.sql                            # Init script
  └── migrations/                         # Alembic migrations
backend/services/
  ├── auth.py                             # Authentication service
  ├── agent_registry.py                   # Agent discovery & search
  ├── conversation.py                     # Conversation memory
  └── task_service.py                     # Task tracking
scripts/
  └── init_database.py                    # Database initialization
alembic.ini                               # Migration config
```

---

**Database layer: COMPLETE! ✅**

**You now have enterprise-grade persistence, auth, and agent discovery!** 🚀
