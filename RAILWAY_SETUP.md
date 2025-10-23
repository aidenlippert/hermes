# Railway Deployment Guide

Complete guide to deploying Hermes backend to Railway.

## Prerequisites

- Railway CLI installed: `npm install -g @railway/cli`
- Railway account: https://railway.app
- GitHub repository pushed

## Step 1: Login to Railway

```bash
railway login
```

This will open your browser to authenticate.

## Step 2: Initialize Railway Project

```bash
# From project root
railway init
```

Choose:
- **Create new project**: Yes
- **Project name**: hermes-backend (or your preference)
- **Link to GitHub**: Yes (select aidenlippert/hermes)

## Step 3: Add PostgreSQL Database

```bash
railway add --database postgres
```

This creates a PostgreSQL instance and automatically sets `DATABASE_URL` environment variable.

## Step 4: Add Redis

```bash
railway add --database redis
```

This creates a Redis instance and automatically sets `REDIS_URL` environment variable.

## Step 5: Set Environment Variables

```bash
# Generate a secure secret key
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Set algorithm
railway variables set ALGORITHM=HS256

# Set token expiration
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30

# Set Google API key (replace with your key)
railway variables set GOOGLE_API_KEY=your_gemini_api_key_here
```

Or set them in Railway dashboard:
1. Go to https://railway.app/project/your-project
2. Click on your service
3. Go to "Variables" tab
4. Add:
   - `SECRET_KEY` (generate with `openssl rand -hex 32`)
   - `ALGORITHM` = `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `30`
   - `GOOGLE_API_KEY` = your Gemini API key

## Step 6: Deploy

```bash
railway up
```

This will:
1. Build your application
2. Deploy to Railway
3. Run database migrations automatically

## Step 7: Run Database Migrations

After first deployment:

```bash
# Connect to your Railway project
railway shell

# Run migrations
python scripts/init_database.py
```

Or use Railway's web terminal:
1. Go to your project dashboard
2. Click "Terminal" tab
3. Run: `python scripts/init_database.py`

## Step 8: Get Your Backend URL

```bash
railway domain
```

This will show your backend URL, e.g., `https://hermes-backend-production.up.railway.app`

## Step 9: Update Frontend

Update your Vercel environment variable:

```
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
```

Then redeploy frontend in Vercel dashboard.

## Verify Deployment

Test your backend:

```bash
# Health check
curl https://your-railway-url.up.railway.app/health

# Register a user
curl -X POST https://your-railway-url.up.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@hermes.ai", "password": "test123"}'
```

## Railway Dashboard

Access your project at: https://railway.app/project/your-project-id

Features:
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, network usage
- **Variables**: Environment variables
- **Deployments**: Deployment history
- **Settings**: Custom domains, webhooks

## Custom Domain (Optional)

1. Go to Railway dashboard
2. Click "Settings" tab
3. Click "Generate Domain" or add custom domain
4. Update DNS records if using custom domain

## Environment Variables Checklist

- ✅ `DATABASE_URL` (auto-set by Railway)
- ✅ `REDIS_URL` (auto-set by Railway)
- ⚠️ `SECRET_KEY` (generate with `openssl rand -hex 32`)
- ⚠️ `GOOGLE_API_KEY` (your Gemini API key)
- ✅ `ALGORITHM` (set to `HS256`)
- ✅ `ACCESS_TOKEN_EXPIRE_MINUTES` (set to `30`)

## Troubleshooting

### Build Fails

Check `railway.json` and ensure:
- Python version is compatible (3.10+)
- All dependencies in `requirements.txt`

### Database Connection Error

Ensure migrations ran:
```bash
railway shell
python scripts/init_database.py
```

### API Key Error

Set `GOOGLE_API_KEY`:
```bash
railway variables set GOOGLE_API_KEY=your_key_here
```

### Port Error

Railway automatically sets `$PORT` environment variable. Ensure your app uses it:
```python
uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

## Cost

Railway pricing:
- **Free Trial**: $5 credit (good for testing)
- **Hobby Plan**: $5/month base + usage
- **Pro Plan**: $20/month base + usage

Estimated monthly cost for Hermes:
- Backend service: ~$5-10
- PostgreSQL: ~$5-10
- Redis: ~$5
- **Total**: ~$15-25/month

## Monitoring

Railway provides:
- Real-time logs
- CPU/memory/network metrics
- Deployment history
- Error tracking

## Scaling

Railway auto-scales based on traffic. Configure in dashboard:
1. Go to "Settings" tab
2. Adjust "Resource Limits"
3. Set horizontal scaling rules

---

**Quick Deploy**: `railway login` → `railway init` → `railway add postgres redis` → `railway up`
