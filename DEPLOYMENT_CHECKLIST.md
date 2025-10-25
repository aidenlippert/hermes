# 🚀 DEPLOYMENT CHECKLIST

Use this checklist to deploy Hermes to production.

## 📋 Pre-Deployment

- [ ] Code pushed to GitHub (`aidenlippert/hermes`)
- [ ] All tests passing locally
- [ ] Environment example files reviewed
- [ ] API keys ready (Google AI)
- [ ] Accounts created:
  - [ ] Railway account
  - [ ] Vercel account
  - [ ] Google AI Studio

---

## 🚂 Railway Backend Deployment

### Setup
- [ ] Railway CLI installed: `npm install -g @railway/cli`
- [ ] Logged in: `railway login`
- [ ] Project initialized: `railway init`
- [ ] GitHub linked to Railway

### Services
- [ ] PostgreSQL added: `railway add --database postgres`
- [ ] Redis added: `railway add --database redis`
- [ ] `DATABASE_URL` auto-set (verify in dashboard)
- [ ] `REDIS_URL` auto-set (verify in dashboard)

### Environment Variables
```bash
# Required
- [ ] SECRET_KEY=$(openssl rand -hex 32)
- [ ] ALGORITHM=HS256
- [ ] ACCESS_TOKEN_EXPIRE_MINUTES=30
- [ ] GOOGLE_API_KEY=your_gemini_key

# After Vercel deploy
- [ ] FRONTEND_URL=https://your-app.vercel.app

# Optional
- [ ] USE_PGVECTOR=true
```

Set with:
```bash
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30
railway variables set GOOGLE_API_KEY=your_key_here
```

### Deploy
- [ ] `railway.json` configured (points to `backend.main:app`)
- [ ] Deploy: `railway up`
- [ ] Build succeeded (check logs)
- [ ] Health check passing: `curl https://your-url.railway.app/health`
- [ ] Railway URL saved: `________________________`

### Database Initialization
```bash
# Option 1: Railway shell
- [ ] railway shell
- [ ] python scripts/init_database.py

# Option 2: Local connection
- [ ] Get DATABASE_URL from Railway
- [ ] Run locally: DATABASE_URL=xxx python scripts/init_database.py
```

Verify:
- [ ] Tables created
- [ ] Admin user exists (`admin@hermes.ai` / `admin123`)
- [ ] Sample agents registered

---

## 🎨 Vercel Frontend Deployment

### Setup
- [ ] Vercel CLI installed: `npm install -g vercel`
- [ ] Logged in: `vercel login`
- [ ] In frontend directory: `cd frontend`

### Environment Variables
```bash
# Required
- [ ] NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
```

Set in Vercel:
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter your Railway URL
```

### Deploy
- [ ] Build locally first: `npm run build` (verify no errors)
- [ ] Deploy: `vercel --prod`
- [ ] Build succeeded
- [ ] Deployment URL saved: `________________________`

### Verification
- [ ] Site loads
- [ ] No console errors
- [ ] Can reach login page
- [ ] Static assets loading

---

## 🔄 Connect Frontend & Backend

### Update Backend CORS
```bash
# Set Vercel URL in Railway
railway variables set FRONTEND_URL=https://your-app.vercel.app

# Redeploy
railway up
```

- [ ] CORS updated with Vercel URL
- [ ] Backend redeployed

### End-to-End Test
- [ ] Open Vercel URL in browser
- [ ] Register new account
- [ ] Login successful
- [ ] Send chat message
- [ ] WebSocket connects
- [ ] Real-time updates work
- [ ] Marketplace loads (if implemented)

---

## 🔐 Security Post-Deployment

- [ ] Change default admin password
  - Old: `admin@hermes.ai` / `admin123`
  - New: `________________________`

- [ ] Verify JWT secret is random (not default)
- [ ] HTTPS working on both domains
- [ ] CORS only allows your Vercel URL
- [ ] Rate limiting enabled (if implemented)
- [ ] Database backups configured

---

## 📊 Monitoring Setup

### Railway
- [ ] Check logs: `railway logs`
- [ ] Monitor CPU/memory in dashboard
- [ ] Set up alerts (optional)

### Vercel
- [ ] Check deployment logs
- [ ] Monitor analytics (optional)
- [ ] Set up error tracking (Sentry, etc.)

### Database
- [ ] PostgreSQL accessible
- [ ] Redis responding
- [ ] Backup strategy in place

---

## 🤖 Agent Network Setup

### Register First Agent
```bash
# Test agent registration endpoint
curl -X POST https://your-railway-url.up.railway.app/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestAgent",
    "endpoint": "https://test-agent.example.com/a2a",
    "description": "Test agent",
    "capabilities": ["test"],
    "category": "development",
    "is_free": true
  }'
```

- [ ] Agent registration works
- [ ] Agent appears in database
- [ ] Agent discoverable via API

### Deploy Sample Agents (Optional)
- [ ] Code Generator agent
- [ ] Web Searcher agent
- [ ] Data Analyzer agent

---

## 📝 Documentation

- [ ] Update README with production URLs
- [ ] Document environment variables
- [ ] Create runbook for common issues
- [ ] Set up developer onboarding docs

---

## 🎉 Launch Checklist

### Final Verification
- [ ] All endpoints responding
- [ ] Authentication working
- [ ] Database persisting data
- [ ] WebSockets streaming
- [ ] Agent registration open
- [ ] No critical errors in logs

### Performance
- [ ] Page load < 3 seconds
- [ ] API response < 500ms
- [ ] WebSocket latency < 100ms
- [ ] Database queries optimized

### User Experience
- [ ] Mobile responsive
- [ ] No JavaScript errors
- [ ] Forms validation working
- [ ] Error messages helpful
- [ ] Loading states implemented

---

## 🚀 Post-Launch Tasks

### Week 1
- [ ] Monitor error rates
- [ ] Track user registrations
- [ ] Review agent usage
- [ ] Fix critical bugs
- [ ] Gather user feedback

### Week 2-4
- [ ] Optimize slow queries
- [ ] Add missing features
- [ ] Improve documentation
- [ ] Scale if needed
- [ ] Plan next sprint

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check logs
railway logs

# Common issues:
- Missing environment variable
- Database connection failed
- Invalid GOOGLE_API_KEY
```

### Frontend can't connect
```bash
# Check CORS
curl -I https://your-railway-url.up.railway.app/health

# Verify env variable
vercel env ls
```

### Database connection errors
```bash
# Test connection
railway shell
psql $DATABASE_URL

# Run migrations
python scripts/init_database.py
```

### WebSocket not connecting
```bash
# Check WebSocket URL in frontend
# Should be wss:// for HTTPS
# Verify Railway WebSocket support (it does!)
```

---

## ✅ Deployment Complete!

Once all items are checked:

🎉 **Your decentralized agent network is LIVE!**

- ✅ Backend: `https://________________________.up.railway.app`
- ✅ Frontend: `https://________________________.vercel.app`
- ✅ Database: PostgreSQL + Redis on Railway
- ✅ Agents: Ready to register and process tasks
- ✅ Users: Can sign up and harness the network

**Next**: Share your network! Invite developers to build agents! 🚀

---

## 📞 Support

If you encounter issues:

1. Check Railway logs: `railway logs`
2. Check Vercel logs: `vercel logs`
3. Review this checklist
4. Check `PRODUCTION_DEPLOY.md`
5. See `AGENT_DEVELOPER_GUIDE.md` for agent setup

**Good luck! Build something amazing! 🌟**
