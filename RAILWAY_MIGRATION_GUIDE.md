# Running Database Migration on Railway

## Prerequisites

- ✅ Railway account with PostgreSQL database
- ✅ Railway CLI installed (`npm i -g @railway/cli`)
- ✅ Logged in to Railway (`railway login`)

---

## Step-by-Step Guide

### 1. Link to Railway Project

```bash
# Navigate to hermes directory
cd c:\Users\aiden\hermes

# Link to your Railway project
railway link
# Select: hermes-production (or your project name)
```

### 2. Verify Database Connection

```bash
# Check environment variables
railway variables

# Should see:
# DATABASE_URL=postgresql://user:pass@host:port/db
```

### 3. Test Connection

```bash
# Connect to PostgreSQL shell
railway run psql $DATABASE_URL

# Once connected, list existing tables:
\dt

# You should see existing tables:
# - users
# - agents
# - messages
# - conversations
# - tasks
# - executions
# - agent_ratings
# - api_keys

# Exit psql:
\q
```

### 4. Run Alembic Migration

```bash
# Run migration on Railway database
railway run alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 1234 -> 5678, add_mesh_protocol_tables
✅ Migration complete!
```

### 5. Verify New Tables

```bash
# Check that new tables were created
railway run psql $DATABASE_URL -c "\dt"
```

**You should now see 8 additional tables:**
- ✅ `contracts`
- ✅ `bids`
- ✅ `deliveries`
- ✅ `user_preferences`
- ✅ `agent_metrics`
- ✅ `agent_trust_scores`
- ✅ `a2a_conversations`
- ✅ `a2a_messages`

### 6. Verify Table Structure

```bash
# Check contracts table
railway run psql $DATABASE_URL -c "\d contracts"

# Should show:
# - id (uuid, primary key)
# - user_id (varchar, foreign key → users)
# - intent (text)
# - context (jsonb)
# - reward_amount (numeric)
# - status (contractstatus enum)
# - awarded_to (varchar, foreign key → agents)
# - timestamps
```

---

## Troubleshooting

### Problem: "Cannot connect to database"

**Solution:**
```bash
# Check if DATABASE_URL is set
railway variables | grep DATABASE_URL

# If missing, add it:
railway variables set DATABASE_URL=<your-connection-string>
```

### Problem: "Migration already applied"

**Solution:**
```bash
# Check current migration version
railway run alembic current

# If already at latest:
# ✅ Migration already applied, nothing to do!

# If behind:
railway run alembic upgrade head
```

### Problem: "Permission denied"

**Solution:**
```bash
# Your Railway database user might not have CREATE permission
# Contact Railway support or create new database with admin user
```

---

## Manual Migration (If Alembic Fails)

If Alembic doesn't work, you can run the SQL directly:

### 1. Extract SQL from Migration File

Open: `backend/database/migrations/versions/2025_10_25_1500_add_mesh_protocol_tables.py`

Look for the `upgrade()` function - it contains all CREATE TABLE statements.

### 2. Run SQL Directly

```bash
# Connect to psql
railway run psql $DATABASE_URL

# Copy-paste CREATE TYPE statements:
CREATE TYPE contractstatus AS ENUM (
    'OPEN', 'BIDDING', 'AWARDED', 'IN_PROGRESS',
    'DELIVERED', 'VALIDATED', 'SETTLED', 'CANCELLED', 'FAILED'
);

CREATE TYPE messagetype AS ENUM (
    'REQUEST', 'RESPONSE', 'BROADCAST', 'DIRECT', 'SYSTEM'
);

CREATE TYPE conversationstatus AS ENUM (
    'ACTIVE', 'COMPLETED', 'FAILED', 'TIMEOUT'
);

# Then copy-paste CREATE TABLE statements...
# (See migration file for full SQL)
```

---

## Rollback (If Something Goes Wrong)

```bash
# Downgrade to previous migration
railway run alembic downgrade -1

# This will:
# - Drop all 8 new tables
# - Drop enum types
# - Return to previous state
```

---

## Post-Migration Verification

### 1. Check Row Counts

```bash
railway run psql $DATABASE_URL -c "
  SELECT 
    'contracts' AS table_name, COUNT(*) FROM contracts
  UNION ALL
  SELECT 'bids', COUNT(*) FROM bids
  UNION ALL
  SELECT 'deliveries', COUNT(*) FROM deliveries
  UNION ALL
  SELECT 'agent_trust_scores', COUNT(*) FROM agent_trust_scores;
"
```

**Expected:** All counts should be 0 (empty tables)

### 2. Test Insert

```bash
railway run psql $DATABASE_URL

# Insert test user preference
INSERT INTO user_preferences (user_id, price_weight, performance_weight, speed_weight, reputation_weight)
VALUES ('test_user_123', 25.0, 25.0, 25.0, 25.0);

# Verify
SELECT * FROM user_preferences;

# Clean up
DELETE FROM user_preferences WHERE user_id = 'test_user_123';
```

### 3. Check Foreign Keys

```bash
railway run psql $DATABASE_URL -c "\d contracts"

# Verify foreign key constraints:
# - user_id references users(id)
# - awarded_to references agents(id)
```

---

## Environment Variables to Set

After migration, update Railway environment variables:

```bash
# Backend service
railway variables set ENABLE_TRUST_SCORES=true
railway variables set ENABLE_USER_PREFERENCES=true
railway variables set TRUST_SCORE_CACHE_TTL=300

# Redis (for caching trust scores)
railway variables set REDIS_URL=<your-redis-url>
```

---

## Next Steps After Migration

1. **Deploy Backend Changes**
   ```bash
   git add .
   git commit -m "Add trust scoring system"
   git push railway main
   ```

2. **Restart Services**
   ```bash
   railway restart
   ```

3. **Test API Endpoints**
   ```bash
   # Test trust score endpoint
   curl https://your-api.railway.app/api/v1/marketplace/agents/test-agent/trust-score
   
   # Should return:
   # {
   #   "agent_id": "test-agent",
   #   "trust_score": 0.800,  # Default for new agents
   #   "grade": "B+"
   # }
   ```

4. **Monitor Logs**
   ```bash
   railway logs
   
   # Look for:
   # ✅ "Trust score calculated for agent_123: 0.876"
   # ✅ "Metric recorded for contract_456"
   ```

---

## Success Criteria

✅ All 8 tables created  
✅ Foreign keys working  
✅ Enum types defined  
✅ Indexes created  
✅ No errors in logs  
✅ API endpoints responding  
✅ Trust scores calculating correctly  

---

## Contact

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Check Alembic history: `railway run alembic history`
3. Review migration file for SQL syntax errors
4. Verify DATABASE_URL is correct

---

## Quick Reference

```bash
# List all Alembic commands
railway run alembic --help

# Show current migration version
railway run alembic current

# Show migration history
railway run alembic history

# Upgrade to latest
railway run alembic upgrade head

# Downgrade one step
railway run alembic downgrade -1

# Check database connection
railway run psql $DATABASE_URL -c "SELECT 1;"

# List all tables
railway run psql $DATABASE_URL -c "\dt"

# Show table structure
railway run psql $DATABASE_URL -c "\d <table_name>"
```

---

**Ready to run the migration!** 🚀

Execute: `railway run alembic upgrade head`
