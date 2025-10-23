# 🚀 Google Cloud Run Deployment Guide

Complete guide to deploying Hermes backend to Google Cloud Run.

## Why Cloud Run?

- ✅ **2 million requests/month FREE**
- ✅ **Scale to zero** = $0 when not in use
- ✅ **Same network as Gemini API** = faster
- ✅ **Serverless** = no server management
- ✅ **Auto-scaling** = handles traffic spikes

---

## Prerequisites

1. **Google Cloud Account**: https://console.cloud.google.com
2. **gcloud CLI**: https://cloud.google.com/sdk/install
3. **Enable billing** on your GCP project

---

## 🎯 Quick Deploy (5 Minutes)

### 1. Install gcloud CLI

**Mac:**
```bash
brew install --cask google-cloud-sdk
```

**Windows:**
Download from: https://cloud.google.com/sdk/install

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 2. Initialize gcloud

```bash
# Login
gcloud auth login

# Create new project (or use existing)
gcloud projects create hermes-backend-prod --name="Hermes Backend"

# Set active project
gcloud config set project hermes-backend-prod

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com
```

### 3. Deploy Backend

```bash
# From project root
./deploy.sh
```

**Or manually:**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/hermes-backend-prod/hermes-backend

# Deploy to Cloud Run
gcloud run deploy hermes-backend \
  --image gcr.io/hermes-backend-prod/hermes-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

**You'll get a URL like:** `https://hermes-backend-abc123.run.app`

---

## 📊 Set Up Database

### Option 1: Supabase (Easiest - Recommended)

**Free tier: 500MB database**

1. Go to https://supabase.com
2. Click **"New Project"**
3. Choose organization, name: `hermes-db`
4. Wait 2 minutes for setup
5. Go to **Settings → Database**
6. Copy **Connection String** (URI format)
7. Enable pgvector:
   - Go to **SQL Editor**
   - Run: `CREATE EXTENSION IF NOT EXISTS vector;`

### Option 2: Cloud SQL (Google Native)

**Cost: ~$7-10/month**

```bash
# Create Cloud SQL instance
gcloud sql instances create hermes-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create hermes --instance=hermes-db

# Create user
gcloud sql users create hermes \
  --instance=hermes-db \
  --password=YOUR_SECURE_PASSWORD

# Get connection name
gcloud sql instances describe hermes-db --format='value(connectionName)'

# Enable Cloud SQL Admin API
gcloud services enable sqladmin.googleapis.com
```

**Connection String:**
```
postgresql://hermes:YOUR_PASSWORD@/hermes?host=/cloudsql/PROJECT_ID:us-central1:hermes-db
```

---

## 🔴 Set Up Redis

### Use Upstash (Recommended - FREE)

1. Go to https://upstash.com
2. Sign up with GitHub
3. Click **"Create Database"**
4. Choose:
   - Name: `hermes-redis`
   - Region: **US East** (close to Cloud Run)
   - Type: **Regional** (free tier)
5. Copy **REST URL** (for serverless)

---

## 🔐 Set Environment Variables

```bash
# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Set all environment variables
gcloud run services update hermes-backend \
  --region us-central1 \
  --set-env-vars "\
SECRET_KEY=$SECRET_KEY,\
ALGORITHM=HS256,\
ACCESS_TOKEN_EXPIRE_MINUTES=30,\
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY,\
DATABASE_URL=postgresql://user:pass@host/db,\
REDIS_URL=redis://host:port"
```

**Or set them in Cloud Console:**
1. Go to https://console.cloud.google.com/run
2. Click **hermes-backend**
3. Click **"Edit & Deploy New Revision"**
4. Scroll to **"Variables & Secrets"**
5. Add each variable

---

## 🗃️ Run Database Migrations

### Option 1: Cloud Run Job (One-time)

```bash
gcloud run jobs create hermes-db-init \
  --image gcr.io/hermes-backend-prod/hermes-backend \
  --region us-central1 \
  --set-env-vars "DATABASE_URL=your_connection_string" \
  --command "python,scripts/init_database.py"

# Execute
gcloud run jobs execute hermes-db-init --region us-central1
```

### Option 2: Local (via Cloud SQL Proxy)

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.2/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

# Start proxy (replace with your connection name)
./cloud-sql-proxy PROJECT_ID:us-central1:hermes-db

# In another terminal, run migrations
export DATABASE_URL="postgresql://hermes:password@127.0.0.1:5432/hermes"
python scripts/init_database.py
```

### Option 3: Supabase (Easiest)

```bash
# Set DATABASE_URL from Supabase
export DATABASE_URL="postgresql://postgres:password@db.abc.supabase.co:5432/postgres"

# Run migrations
python scripts/init_database.py
```

---

## 🌐 Update Vercel Frontend

1. Go to https://vercel.com/dashboard
2. Find your `hermes` project
3. **Settings → General**
   - Set **Root Directory**: `frontend`
4. **Settings → Environment Variables**
   - Add: `NEXT_PUBLIC_API_URL` = `https://hermes-backend-abc123.run.app`
5. **Deployments → Redeploy**

---

## ✅ Test Your Deployment

### Test Backend Health

```bash
curl https://hermes-backend-abc123.run.app/health
```

**Expected:** `{"status":"healthy"}`

### Test Registration

```bash
curl -X POST https://hermes-backend-abc123.run.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@hermes.ai","password":"test123"}'
```

### Test Frontend

1. Open your Vercel URL
2. Click **"Get Started"**
3. Register/Login
4. Send message: **"Hello Hermes!"**

---

## 💰 Cost Breakdown

### Free Tier Usage (Perfect for Development)

**Cloud Run:**
- 2 million requests/month FREE
- 360,000 GB-seconds/month FREE
- 180,000 vCPU-seconds/month FREE

**Supabase:**
- 500MB database FREE
- 2GB file storage FREE
- 50MB egress/month FREE

**Upstash Redis:**
- 10K requests/day FREE
- 256MB storage FREE

**Total: $0/month for light usage!** 🎉

### Production Scale (~1000 users)

- Cloud Run: ~$5-10/month
- Supabase Pro: $25/month (8GB database)
- Upstash Pro: $10/month
- **Total: ~$40-45/month**

---

## 📊 Monitoring

### View Logs

```bash
# Cloud Run logs
gcloud run services logs read hermes-backend --region us-central1 --limit 50

# Real-time logs
gcloud run services logs tail hermes-backend --region us-central1
```

### Cloud Console

https://console.cloud.google.com/run

- View metrics (requests, latency, errors)
- Set up alerts
- Monitor costs

---

## 🔧 Useful Commands

### Update Service

```bash
# Deploy new version
./deploy.sh

# Update environment variables
gcloud run services update hermes-backend \
  --region us-central1 \
  --set-env-vars KEY=value

# Scale settings
gcloud run services update hermes-backend \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 20 \
  --memory 2Gi \
  --cpu 2
```

### View Service Info

```bash
# Get URL
gcloud run services describe hermes-backend --region us-central1 --format='value(status.url)'

# View configuration
gcloud run services describe hermes-backend --region us-central1
```

### Delete Service

```bash
gcloud run services delete hermes-backend --region us-central1
```

---

## 🆘 Troubleshooting

### Build Fails

**Error:** Dependencies not installing
**Fix:** Check `requirements.txt` and Dockerfile

### Service Crashes on Start

**Check logs:**
```bash
gcloud run services logs read hermes-backend --region us-central1
```

**Common issues:**
- Missing environment variables
- Database connection failed
- Port not set correctly (must use `$PORT`)

### Database Connection Error

**For Cloud SQL:**
1. Enable Cloud SQL Admin API
2. Add Cloud SQL connection in Cloud Run:
```bash
gcloud run services update hermes-backend \
  --add-cloudsql-instances PROJECT_ID:us-central1:hermes-db
```

**For Supabase:**
- Verify connection string format
- Check firewall rules

### "Permission Denied" Errors

```bash
# Add required permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/run.admin"
```

---

## 🎯 Quick Summary

```bash
# 1. Setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# 2. Deploy
./deploy.sh

# 3. Set env vars (update with your values)
gcloud run services update hermes-backend --region us-central1 \
  --set-env-vars "SECRET_KEY=xxx,GOOGLE_API_KEY=xxx,DATABASE_URL=xxx,REDIS_URL=xxx"

# 4. Get URL
gcloud run services describe hermes-backend --region us-central1 --format='value(status.url)'

# 5. Update Vercel
# Add NEXT_PUBLIC_API_URL with your Cloud Run URL
```

---

## 🚀 Next Steps

1. ✅ Deploy backend to Cloud Run
2. ✅ Set up Supabase database
3. ✅ Set up Upstash Redis
4. ✅ Configure environment variables
5. ✅ Run database migrations
6. ✅ Update Vercel frontend
7. ✅ Test end-to-end
8. 📊 Set up monitoring and alerts
9. 🔒 Configure custom domain (optional)
10. 🌍 Deploy to multiple regions (optional)

---

**Start here:** Install gcloud CLI → `./deploy.sh` → Set env vars → Done! 🎉
