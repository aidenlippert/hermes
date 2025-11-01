# 🚀 ASTRAEUS Deployment Guide

Complete guide for deploying ASTRAEUS to production.

## 📋 Overview

**Architecture:**
- Frontend → Vercel (FREE)
- Backend API → Railway ($5-20/month)
- AI Orchestration → Groq API (FREE!)
- Database → Railway PostgreSQL (included)

---

## 🎯 Step 1: Deploy Frontend to Vercel (FREE)

### Install Vercel CLI
```bash
npm install -g vercel
```

### Deploy
```bash
cd /home/rocz/Astraeus/hermes/frontend

# Login to Vercel
vercel login

# Deploy
vercel --prod

# Follow prompts:
# - Project name: astraeus
# - Framework: Next.js
# - Build command: (auto-detected)
# - Output directory: (auto-detected)
```

**Result:** You'll get a URL like `https://astraeus.vercel.app`

---

## 🚂 Step 2: Deploy Backend to Railway ($5-20/month)

### Install Railway CLI
```bash
npm install -g @railway/cli
```

### Deploy
```bash
cd /home/rocz/Astraeus/hermes/backend

# Login to Railway
railway login

# Initialize project
railway init

# Add PostgreSQL database
railway add

# Select: PostgreSQL

# Set environment variables
railway variables set GROQ_API_KEY=your_groq_api_key_here

# Deploy
railway up

# Get your URL
railway domain
```

**Result:** You'll get a URL like `https://astraeus-backend.up.railway.app`

---

## 🔧 Step 3: Configure Environment Variables

### Railway (Backend)
Set these in Railway dashboard:

```bash
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=(auto-set by Railway)
PORT=8000
```

### Vercel (Frontend)
Set these in Vercel dashboard:

```bash
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
```

---

## ✅ Step 4: Verify Deployment

### Test Backend
```bash
# Health check
curl https://your-backend.up.railway.app/health

# List agents
curl https://your-backend.up.railway.app/api/v1/mesh/agents
```

### Test Frontend
Visit: `https://your-frontend.vercel.app`

### Test Groq Orchestration
```bash
curl -X POST https://your-backend.up.railway.app/api/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"query": "Get weather for Tokyo"}'
```

---

## 🤖 Step 5: Deploy Your First Agent

### Option 1: Deploy to Railway
```bash
cd /home/rocz/Astraeus/hermes

# Create new Railway service for your agent
railway init --name weather-agent

# Deploy
railway up

# Your agent will be at: https://weather-agent.up.railway.app
```

### Option 2: Deploy to VPS
```bash
# On your VPS
git clone https://github.com/your-username/astraeus.git
cd astraeus
pip install -r requirements.txt

# Run agent
PYTHONPATH="/path/to/astraeus-sdk:$PYTHONPATH" python3 weather_agent.py
```

### Option 3: Use Cloudflare Tunnel (FREE!)
```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Run agent locally
python3 weather_agent.py &

# Expose via tunnel
./cloudflared tunnel --url http://localhost:8005

# You'll get a public URL like: https://xyz.trycloudflare.com
```

---

## 💰 Cost Breakdown

### FREE Tier
- ✅ Vercel (Frontend): $0/month
- ✅ Groq API (Orchestration): $0/month
- ✅ Cloudflare Tunnel (Agent hosting): $0/month

**Total FREE: $0/month** 🎉

### Paid Tier (Production-Ready)
- Frontend (Vercel): $0/month (free)
- Backend (Railway): $5-20/month
- Database (Railway PostgreSQL): Included
- Groq API: $0/month (free tier)

**Total: $5-20/month**

---

## 🔒 Security Checklist

- [ ] Set strong DATABASE_URL password
- [ ] Keep GROQ_API_KEY secret (use environment variables)
- [ ] Enable CORS only for your frontend domain
- [ ] Set up rate limiting
- [ ] Use HTTPS (automatic on Vercel/Railway)

---

## 📊 Monitoring

### Railway Dashboard
- View logs: `railway logs`
- Monitor usage: Railway dashboard
- Database metrics: PostgreSQL plugin

### Vercel Dashboard
- View deployments
- Monitor performance
- Check analytics

### Groq Dashboard
- Track API usage at: https://console.groq.com
- Monitor rate limits
- View usage analytics

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
railway logs

# Verify DATABASE_URL is set
railway variables

# Test locally first
python main.py
```

### Frontend can't connect to backend
```bash
# Verify NEXT_PUBLIC_API_URL is set in Vercel
# Check CORS settings in backend
# Test backend directly with curl
```

### Groq API errors
```bash
# Check API key is valid
# Verify quota hasn't been exceeded
# Check Groq status: https://status.groq.com
```

---

## 🚀 Quick Deploy Commands

```bash
# Frontend
cd frontend && vercel --prod

# Backend
cd backend && railway up

# View logs
railway logs --tail

# Open backend in browser
railway open
```

---

## 📚 Additional Resources

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Groq API Docs: https://console.groq.com/docs
- ASTRAEUS Docs: See GETTING_STARTED.md

---

**Ready to deploy? Let's ship it!** 🎉

Start with: `cd frontend && vercel --prod`
