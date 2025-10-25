# 🚀 Automatic Railway Deployment with Database Migration

## What Just Changed?

Your Railway deployment now **automatically runs database migrations** every time you push to GitHub! 

---

## How It Works

### Before (Manual Migration)
```bash
git push
# Then manually run:
railway run alembic upgrade head
```

### After (Automatic Migration) ✨
```bash
git push
# Migration runs automatically! 
```

---

## Files Modified

### 1. `railway.json` (Updated)
```json
{
  "build": {
    "buildCommand": "pip install -r requirements.txt && chmod +x railway_migrate.sh"
  },
  "deploy": {
    "startCommand": "bash railway_migrate.sh && uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

**What it does:**
- Before starting the server, runs `railway_migrate.sh`
- Migration script runs `alembic upgrade head`
- Only starts server if migration succeeds

### 2. `railway_migrate.sh` (New)
```bash
#!/bin/bash
echo "🚀 Starting Railway post-deployment tasks..."
alembic upgrade head  # ← Runs migration automatically
python scripts/init_database.py  # ← Seeds initial data
echo "🎉 Post-deployment tasks complete!"
```

---

## Deployment Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. You push code to GitHub                             │
│     git push origin main                                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  2. Railway detects new commit                          │
│     "New deployment triggered from GitHub"              │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  3. Railway builds your app                             │
│     pip install -r requirements.txt                     │
│     chmod +x railway_migrate.sh                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  4. Railway runs migration script                       │
│     bash railway_migrate.sh                             │
│                                                          │
│     ⏳ Waiting for database connection...               │
│     📦 Running database migrations...                   │
│     alembic upgrade head                                │
│                                                          │
│     INFO  [alembic] Running upgrade -> add_mesh_tables  │
│     ✅ Migrations completed successfully!               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  5. Railway starts your server                          │
│     uvicorn backend.main:app --host 0.0.0.0 --port $PORT│
│                                                          │
│     ✅ Server running on port 8000                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  6. Your API is live with new database tables!          │
│     https://hermes-production.railway.app               │
└─────────────────────────────────────────────────────────┘
```

---

## To Deploy Sprint 1.2 (Trust & Reputation)

### Step 1: Commit All Changes

```bash
git add .
git commit -m "Add trust scoring and reputation system (Sprint 1.2)

- Added ReputationManager service with multi-factor trust algorithm
- Added DBContractManager for database-backed contracts
- Added 3 reputation API endpoints (trust-score, reputation, leaderboard)
- Added automatic migration script for Railway
- Database migration: 8 new mesh protocol tables
"
```

### Step 2: Push to GitHub

```bash
git push origin main
```

### Step 3: Watch Railway Deploy

Go to: https://railway.app/project/your-project-id

Watch the build logs:
```
✅ Building...
✅ Running migrations...
✅ Starting server...
✅ Deployment successful!
```

### Step 4: Verify Migration Ran

Check Railway logs for:
```
🚀 Starting Railway post-deployment tasks...
⏳ Waiting for database connection...
📦 Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade 1234 -> 5678, add_mesh_protocol_tables
✅ Migrations completed successfully!
🌱 Checking for initial data...
🎉 Post-deployment tasks complete!
```

### Step 5: Test New Endpoints

```bash
# Replace with your Railway URL
curl https://hermes-production.railway.app/api/v1/marketplace/leaderboard

# Expected response:
{
  "metric": "trust_score",
  "leaderboard": []  // Empty at first, will populate as agents earn trust
}
```

---

## What Gets Deployed Automatically

When you push to GitHub, Railway will:

✅ **Install dependencies** (from requirements.txt)  
✅ **Run database migrations** (alembic upgrade head)  
✅ **Seed initial data** (scripts/init_database.py)  
✅ **Start the server** (uvicorn backend.main:app)  

**All tables will be created automatically:**
- ✅ contracts
- ✅ bids  
- ✅ deliveries
- ✅ user_preferences
- ✅ agent_metrics
- ✅ agent_trust_scores
- ✅ a2a_conversations
- ✅ a2a_messages

---

## Rollback (If Needed)

If something goes wrong:

### Option 1: Revert in Railway Dashboard
1. Go to Railway dashboard
2. Click "Deployments" tab
3. Click "Redeploy" on previous working deployment

### Option 2: Revert Git Commit
```bash
git revert HEAD
git push origin main
# Railway will auto-deploy previous version
```

### Option 3: Manual Migration Rollback
```bash
railway run alembic downgrade -1
```

---

## Environment Variables Needed

Make sure these are set in Railway dashboard:

**Required for Trust Scoring:**
```
DATABASE_URL=postgresql://...     # ✅ Auto-set by Railway
REDIS_URL=redis://...              # ✅ Auto-set by Railway
SECRET_KEY=<generated-key>         # ⚠️ Set manually
GOOGLE_API_KEY=<your-key>          # ⚠️ Set manually
```

**Optional (defaults work):**
```
TRUST_SCORE_CACHE_TTL=300         # Cache trust scores for 5min
ENABLE_TRUST_SCORES=true          # Enable trust system
```

---

## Monitoring Deployment

### Railway Dashboard
https://railway.app/project/your-project-id

**Tabs to watch:**
- **Deployments** - Build status and logs
- **Logs** - Real-time application logs
- **Metrics** - CPU, memory, network usage

### Check Migration Status

```bash
# Via Railway CLI
railway run alembic current

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# 2025_10_25_1500 (head)
```

### Verify Tables Created

```bash
railway run psql $DATABASE_URL -c "\dt"

# Should show:
# contracts
# bids
# deliveries
# user_preferences
# agent_metrics
# agent_trust_scores
# a2a_conversations
# a2a_messages
```

---

## Troubleshooting

### Migration Fails

**Error:** `alembic.util.exc.CommandError: Can't locate revision identified by '...'`

**Solution:**
```bash
# Reset migration history
railway run alembic stamp head

# Then redeploy
git commit --allow-empty -m "Trigger redeploy"
git push origin main
```

### Database Connection Timeout

**Error:** `connection to server at "..." failed`

**Solution:** Increase wait time in `railway_migrate.sh`:
```bash
# Change from 5 to 10 seconds
sleep 10
```

### Permission Denied

**Error:** `bash: ./railway_migrate.sh: Permission denied`

**Solution:** Already fixed with `chmod +x` in build command. If still fails:
```bash
# Make file executable locally
chmod +x railway_migrate.sh
git add railway_migrate.sh
git commit -m "Fix script permissions"
git push origin main
```

---

## Success Checklist

After deployment, verify:

- [ ] Railway build succeeded (green checkmark)
- [ ] Migration logs show "✅ Migrations completed successfully!"
- [ ] Server started (logs show "Uvicorn running on...")
- [ ] Health endpoint responds: `curl https://your-url.railway.app/health`
- [ ] New endpoints work: `curl https://your-url.railway.app/api/v1/marketplace/leaderboard`
- [ ] Database tables exist: `railway run psql $DATABASE_URL -c "\dt"`

---

## Next Deployment (Sprint 1.3, 1.4, 1.5)

Every future deployment will follow the same pattern:

1. Make code changes
2. Create migration if needed: `alembic revision --autogenerate -m "description"`
3. Commit and push to GitHub
4. Railway automatically runs migration
5. Done! ✨

**No more manual migration commands needed!**

---

## Cost Impact

**Before:** Manual deploys (slower, error-prone)  
**After:** Automatic deploys with migrations (faster, reliable)  

**Railway pricing:** Same cost - no additional charges for automated migrations

---

## Summary

✅ **What changed:** `railway.json` now runs migrations automatically  
✅ **How to deploy:** Just `git push origin main`  
✅ **What happens:** Railway builds → migrates → starts server  
✅ **Monitoring:** Railway dashboard shows full deployment logs  
✅ **Rollback:** Redeploy previous version in dashboard  

**You're now ready to deploy Sprint 1.2 with automatic database migrations!** 🚀

---

## Ready to Deploy?

```bash
# Commit everything
git add .
git commit -m "Sprint 1.2: Trust & Reputation System"

# Push to GitHub (Railway auto-deploys)
git push origin main

# Watch deployment
railway logs --follow
```

**The migration will run automatically and create all 8 new tables!** ✨
