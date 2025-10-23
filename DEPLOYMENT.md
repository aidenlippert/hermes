# Hermes Deployment Guide

Complete guide to deploying Hermes to production.

## Architecture

```
Frontend (Vercel)
  ↓ HTTPS
Backend (Google Cloud Run / Railway)
  ↓
PostgreSQL (Supabase / Neon)
  ↓
Redis (Upstash)
```

## Option 1: Quick Deploy (Vercel Frontend Only)

### Step 1: Push to GitHub

```bash
# From project root
git add .
git commit -m "Initial commit - Hermes platform"
git branch -M main
git remote add origin https://github.com/aidenlippert/hermes.git
git push -u origin main
```

### Step 2: Deploy Frontend to Vercel

1. Go to https://vercel.com
2. Click "Import Project"
3. Select your GitHub repo: `aidenlippert/hermes`
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

5. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL` = `http://localhost:8000` (temporary)

6. Click "Deploy"

Your frontend will be live at: `https://hermes-*.vercel.app`

**Note**: Backend still needs to be deployed for full functionality.

## Option 2: Full Stack Deploy

### Backend Deployment Options

#### Option A: Google Cloud Run (Recommended)

**Pros**: Serverless, auto-scaling, pay-per-use
**Cons**: Cold starts

```bash
# 1. Create Dockerfile
cd backend
cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main_v2:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 2. Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/hermes-backend
gcloud run deploy hermes-backend \
  --image gcr.io/PROJECT_ID/hermes-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Option B: Railway (Easiest)

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repo
5. Railway auto-detects Python
6. Add environment variables:
   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   GOOGLE_API_KEY=your_key
   SECRET_KEY=your_secret
   ```

#### Option C: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
cd backend
fly launch
fly deploy
```

### Database: Supabase (PostgreSQL + pgvector)

1. Go to https://supabase.com
2. Create new project
3. Wait for database to be ready
4. Go to Settings > Database
5. Copy connection string
6. Enable pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

7. Run migrations:
   ```bash
   # Update DATABASE_URL in .env
   alembic upgrade head
   ```

8. Seed database:
   ```bash
   python scripts/init_database.py
   ```

### Redis: Upstash

1. Go to https://upstash.com
2. Create new Redis database
3. Copy connection URL
4. Add to backend environment variables

### Update Frontend Environment

Once backend is deployed, update Vercel environment variable:

```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

Redeploy frontend.

## Environment Variables Checklist

### Frontend (Vercel)

- `NEXT_PUBLIC_API_URL` - Your backend URL

### Backend (Cloud Run / Railway)

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `GOOGLE_API_KEY` - Gemini API key
- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- `ALGORITHM` - `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` - `30`

## Agents Deployment

Agents can run on:

1. **Same backend** - Include in main app
2. **Separate services** - Deploy each agent individually
3. **Serverless functions** - AWS Lambda, Cloud Functions

For simplicity, deploy agents with backend initially.

## Post-Deployment

### 1. Test Authentication

```bash
curl -X POST https://your-backend.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

### 2. Test Chat

```bash
curl -X POST https://your-backend.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "Write a hello world function"}'
```

### 3. Test WebSocket

Use the frontend to test WebSocket streaming.

## Monitoring

### Vercel

- View logs in Vercel dashboard
- Analytics built-in

### Backend

Set up monitoring:

1. **Sentry** - Error tracking
2. **LogRocket** - Session replay
3. **Datadog** - APM monitoring

## Custom Domain

### Frontend (Vercel)

1. Go to Vercel project settings
2. Add custom domain
3. Update DNS records

### Backend (Cloud Run)

1. Set up Cloud Load Balancer
2. Map custom domain
3. Add SSL certificate

## Cost Estimates

### Free Tier Deployment

- **Vercel**: Free (Hobby plan)
- **Supabase**: Free (500MB database)
- **Upstash**: Free (10K requests/day)
- **Railway**: $5/month credit free

**Total**: $0-5/month for light usage

### Production Scale

- **Vercel Pro**: $20/month
- **Supabase Pro**: $25/month
- **Cloud Run**: ~$10-50/month
- **Upstash Pro**: $10/month

**Total**: ~$65-105/month

## Scaling

### Frontend

Vercel auto-scales globally via CDN.

### Backend

1. **Cloud Run**: Auto-scales 0-1000 instances
2. **Database**: Upgrade Supabase plan
3. **Redis**: Upgrade Upstash plan
4. **Agents**: Deploy separately, scale independently

## Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Enable CORS for specific origins only
- [ ] Use HTTPS everywhere
- [ ] Set secure headers
- [ ] Enable rate limiting
- [ ] Set up WAF (Web Application Firewall)
- [ ] Regular security audits
- [ ] Keep dependencies updated

## Backup Strategy

### Database

Supabase provides automatic backups:
- Daily backups (7 days retention)
- Point-in-time recovery

### Code

- GitHub as source of truth
- Tag releases: `git tag v1.0.0`

## Rollback Plan

### Frontend

Vercel keeps all deployments - instant rollback via dashboard.

### Backend

```bash
# Railway
railway rollback

# Cloud Run
gcloud run services update-traffic hermes-backend \
  --to-revisions=PREVIOUS_REVISION=100
```

## Support

- Frontend issues: Check Vercel logs
- Backend issues: Check Cloud Run / Railway logs
- Database issues: Check Supabase logs
- WebSocket issues: Check connection in browser dev tools

---

**Quick Start**: Deploy frontend to Vercel first, then add backend later.
**Full Stack**: Follow Option 2 for complete deployment.
