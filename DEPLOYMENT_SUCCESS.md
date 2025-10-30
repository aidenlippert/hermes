# 🚀 Deployment Guide

## ✅ Current Status

**Backend (Railway):** ✅ DEPLOYED & RUNNING  
**Frontend (Vercel):** 🔄 Ready to deploy

---

## Backend Deployment (Railway)

### Status: ✅ LIVE
- **URL:** https://web-production-3df46.up.railway.app
- **Health:** https://web-production-3df46.up.railway.app/health
- **API Docs:** https://web-production-3df46.up.railway.app/docs

### Auto-Deployment
Railway is connected to your GitHub repo. Every push to `main` automatically triggers a new deployment.

### Environment Variables (Already Set)
- `DATABASE_URL` - PostgreSQL database (Railway managed)
- `REDIS_URL` - Redis cache (Railway managed)
- `GOOGLE_API_KEY` - For Gemini AI features
- `PORT` - Set to 8080 by Railway

---

## Frontend Deployment (Vercel)

### Quick Deploy

#### Option 1: Automatic (Recommended)
Vercel is connected to your GitHub. Just set the environment variable:

1. Go to your Vercel project settings
2. Navigate to **Environment Variables**
3. Add:
   ```
   NEXT_PUBLIC_API_URL=https://web-production-3df46.up.railway.app
   ```
4. Trigger redeploy or push to `main`

#### Option 2: Manual Deploy
```bash
cd frontend
vercel --prod
```

### Environment Variables

**Production (.env.production):**
```env
NEXT_PUBLIC_API_URL=https://web-production-3df46.up.railway.app
```

**Local (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## Testing Deployments

### Test Backend
```bash
curl https://web-production-3df46.up.railway.app/health
```

**Expected:**
```json
{"status":"healthy","version":"2.0.0","startup_complete":true}
```

### Test Frontend
Once deployed, visit your Vercel URL and:
1. Register a new account
2. Navigate to `/workflows`
3. Create a test workflow
4. Verify it connects to Railway backend

---

## Monitoring

### Railway Logs
```
Railway Dashboard → Your Project → Deployments → Deploy Logs
```

### Vercel Logs
```
Vercel Dashboard → Your Project → Deployments → Function Logs
```

---

## Database Migrations

### Automatic
Migrations run automatically on every Railway deployment via `entrypoint.sh`

### Manual (if needed)
```bash
# In Railway console
alembic upgrade head
```

### Force Reset (DANGER - wipes data!)
Set Railway environment variable:
```
FORCE_DB_RESET=true
```
Then redeploy. **Remove this variable after deployment!**

---

## Rollback

### Railway
```
Railway Dashboard → Deployments → Click previous deployment → Redeploy
```

### Vercel
```
Vercel Dashboard → Deployments → Click previous deployment → Promote to Production
```

---

## Common Issues

### Issue: Frontend can't reach backend
**Fix:** Check CORS settings in `backend/main_v2.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should allow Vercel
    ...
)
```

### Issue: Database migration fails
**Fix:** Check Railway logs for specific error. May need to set `FORCE_DB_RESET=true`

### Issue: 502 Bad Gateway
**Fix:** Backend is starting up. Wait 30-60 seconds and retry.

---

## URLs Reference

**Production Backend:** https://web-production-3df46.up.railway.app  
**Production Frontend:** (Your Vercel URL)  
**Local Backend:** http://127.0.0.1:8000  
**Local Frontend:** http://localhost:3000

---

## Architecture

```
┌─────────────────┐
│  Vercel CDN     │  ← Frontend (Next.js)
│  (Global Edge)  │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Railway        │  ← Backend (FastAPI)
│  (us-west2)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Postgres│ │ Redis  │
└────────┘ └────────┘
```

---

**🎉 Both services are production-ready!**
