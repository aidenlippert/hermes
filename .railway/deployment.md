# 🚂 Railway Deployment Guide

## Environment Variables Required

### Backend (FastAPI)
```
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://default:password@host:port/0
GOOGLE_API_KEY=your_google_api_key_here
FRONTEND_URL=https://your-vercel-url.vercel.app
USE_PGVECTOR=false
```

## Railway Setup Steps

### 1. Create New Project
```bash
railway login
railway init
```

### 2. Add PostgreSQL
- Go to Railway dashboard
- Click "New" → "Database" → "PostgreSQL"
- Railway will automatically set `DATABASE_URL`

### 3. Add Redis (Optional)
- Click "New" → "Database" → "Redis"
- Railway will automatically set `REDIS_URL`

### 4. Deploy Backend
```bash
railway up
```

### 5. Set Custom Environment Variables
```bash
railway variables set GOOGLE_API_KEY=your_key_here
railway variables set FRONTEND_URL=https://your-frontend.vercel.app
```

## Health Check

Once deployed, check:
- Health: `https://your-app.railway.app/api/v1/health`
- Docs: `https://your-app.railway.app/docs`

## Frontend Setup (Vercel)

1. Go to Vercel dashboard
2. Import your GitHub repo
3. Framework Preset: Next.js
4. Root Directory: `frontend`
5. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```

## Post-Deployment

1. Update CORS in backend/main.py line 103:
   ```python
   FRONTEND_URL = os.getenv("FRONTEND_URL", "https://your-actual-vercel-url.vercel.app")
   ```

2. Test full integration:
   ```bash
   curl https://your-backend.railway.app/api/v1/health
   ```

3. Visit frontend: `https://your-frontend.vercel.app`
