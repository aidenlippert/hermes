# 🚂 Railway Deployment - Simple Guide

## Step-by-Step Manual Setup

### 1. Create Project
1. Go to https://railway.app
2. Sign in with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose **`aidenlippert/hermes`**
6. Railway will start building automatically

### 2. Add PostgreSQL
1. In project dashboard, click **"+ New"**
2. Select **"Database"**
3. Choose **"PostgreSQL"**
4. Done! `DATABASE_URL` is automatically set

### 3. Add Redis
1. Click **"+ New"** again
2. Select **"Database"**
3. Choose **"Redis"**
4. Done! `REDIS_URL` is automatically set

### 4. Configure Your Service
1. Click on your **main service** (Python app)
2. Go to **"Settings"** tab
3. Set **Start Command**:
   ```
   uvicorn backend.main_v2:app --host 0.0.0.0 --port $PORT
   ```

### 5. Add Environment Variables
1. Still in your service, go to **"Variables"** tab
2. Click **"+ New Variable"** for each:

```
SECRET_KEY = [paste any random 64-character string]
ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30
GOOGLE_API_KEY = [your Gemini API key]
```

**Generate SECRET_KEY:**
- Windows: Use any password generator
- Mac/Linux: `openssl rand -hex 32`
- Or use: https://www.random.org/strings/ (64 chars, hex)

### 6. Deploy
Service will auto-deploy after you save variables (2-3 min)

### 7. Get Your URL
1. In your service, go to **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. Copy URL (e.g., `https://hermes-backend-production.up.railway.app`)

### 8. Initialize Database
1. In your service, click **"Settings"**
2. Find **"One-off Commands"**
3. Run: `python scripts/init_database.py`

### 9. Update Vercel
1. Go to https://vercel.com/dashboard
2. Find `hermes` project
3. **Settings → General** → Set **Root Directory** = `frontend`
4. **Settings → Environment Variables**
5. Add: `NEXT_PUBLIC_API_URL` = `https://your-railway-url.up.railway.app`
6. **Deployments** → Redeploy

## ✅ Test It

```bash
# Test backend (replace with your URL)
curl https://your-railway-url.up.railway.app/health

# Should return: {"status":"healthy"}
```

Then test frontend:
1. Open your Vercel URL
2. Register/Login
3. Send message!

## 💰 Cost
- Free: $5 credit (good for testing)
- After: ~$20-30/month

---

**Start at**: https://railway.app → New Project → Done!
