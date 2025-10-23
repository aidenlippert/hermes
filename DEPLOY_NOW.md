# Deploy Hermes - Quick Commands

## ✅ Fixed Issues

1. **Vercel build error** - Fixed `vercel.json` to use frontend directory as root
2. **Railway config** - Added `railway.json` and `Procfile`

## 🚀 Deploy Backend to Railway

Run these commands in order:

### 1. Login to Railway
```bash
railway login
```
This opens your browser to authenticate with Railway.

### 2. Initialize Project
```bash
railway init
```
- Choose: **Create new project**
- Name: `hermes-backend`
- Link to GitHub: **Yes** → select `aidenlippert/hermes`

### 3. Add PostgreSQL
```bash
railway add --database postgres
```

### 4. Add Redis
```bash
railway add --database redis
```

### 5. Set Environment Variables
```bash
# Generate secure secret key
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Set other variables
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30

# Set your Gemini API key (replace with your actual key)
railway variables set GOOGLE_API_KEY=your_gemini_api_key_here
```

### 6. Deploy
```bash
railway up
```

### 7. Run Database Setup
```bash
# Open Railway shell
railway shell

# Run init script
python scripts/init_database.py

# Exit shell
exit
```

### 8. Get Your Backend URL
```bash
railway domain
```

Copy the URL (e.g., `https://hermes-backend-production.up.railway.app`)

---

## 🌐 Update Vercel Frontend

### Option 1: In Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Find your `hermes` project
3. Go to **Settings** → **Environment Variables**
4. Change **Root Directory** to `frontend`
5. Add/Update: `NEXT_PUBLIC_API_URL` = `https://your-railway-url.up.railway.app`
6. Redeploy from **Deployments** tab

### Option 2: Redeploy with Correct Settings
1. Go to https://vercel.com/dashboard
2. Delete current deployment
3. Click **Import Project**
4. Select `aidenlippert/hermes`
5. Configure:
   - **Framework**: Next.js
   - **Root Directory**: `frontend` ⚠️ IMPORTANT
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
6. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-railway-url.up.railway.app`
7. Deploy

---

## ✅ Verification

### Test Backend
```bash
# Health check
curl https://your-railway-url.up.railway.app/health

# Register user
curl -X POST https://your-railway-url.up.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@hermes.ai", "password": "test123"}'
```

### Test Frontend
1. Open `https://your-vercel-url.vercel.app`
2. Click "Get Started"
3. Login with: `test@hermes.ai` / `test123`
4. Send a message: "Hello Hermes!"

---

## 📊 Monitoring

- **Railway**: https://railway.app/project/your-project-id
  - View logs, metrics, deployments
- **Vercel**: https://vercel.com/dashboard
  - View analytics, logs, deployments

---

## 🆘 Troubleshooting

### Vercel Build Fails
- Ensure **Root Directory** is set to `frontend` in project settings
- Check build logs for specific errors

### Railway Build Fails
- Check Railway logs in dashboard
- Verify all environment variables are set
- Ensure `GOOGLE_API_KEY` is valid

### Database Connection Error
- Run `railway shell` → `python scripts/init_database.py`
- Check Railway logs for PostgreSQL connection

### Frontend Can't Connect to Backend
- Verify `NEXT_PUBLIC_API_URL` in Vercel settings
- Check Railway backend is running
- Test backend health endpoint

---

**Start here**: `railway login`
