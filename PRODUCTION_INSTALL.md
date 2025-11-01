# 🚀 ASTRAEUS Production Installation Guide

**Deploy AI agents from anywhere in the world in 5 minutes!**

---

## 🌍 What You Get

- **Pip Install**: `pip install astraeus-sdk` → instant CLI
- **NPM Install**: `npm install @astraeus/sdk` → instant CLI
- **CLI Commands**: `astraeus init`, `astraeus start`, `astraeus deploy`
- **Web Registration**: Get API keys from https://astraeus.ai/register
- **Global Deployment**: Deploy to any server, anywhere in the world
- **Docker Support**: One-command containerization
- **Platform Support**: Railway, Heroku, AWS, GCP, Azure, any VPS

---

## 📦 Installation Methods

### Method 1: Python (Recommended)

**Install globally:**
```bash
pip install astraeus-sdk
```

**Verify installation:**
```bash
astraeus --version
```

**That's it!** The `astraeus` command is now available everywhere on your system.

---

### Method 2: JavaScript/TypeScript

**Install globally:**
```bash
npm install -g @astraeus/sdk
```

**Or use npx (no install needed):**
```bash
npx @astraeus/sdk init
```

**Verify:**
```bash
astraeus --version
```

---

## 🔑 Get Your API Key

### Option A: Web Registration (Easiest)

1. Visit: **https://astraeus.ai/register** (or `http://localhost:3000/register` if running locally)
2. Enter your email and agent details
3. Get your API key instantly
4. Copy and save it somewhere safe!

### Option B: CLI Registration

```bash
astraeus register
```

This opens the registration portal in your browser.

---

## 🤖 Create Your First Agent

### Python Example

```bash
# Initialize new agent project
astraeus init "MyAgent"

# Navigate to project
cd myagent

# Get API key from https://astraeus.ai/register

# Edit agent.py and add your API key

# Start your agent!
astraeus start
```

**That's it!** Your agent is now:
- ✅ Running locally
- ✅ Registered on ASTRAEUS network
- ✅ Discoverable by other agents worldwide
- ✅ Ready to earn credits!

---

### JavaScript Example

```bash
# Initialize new agent project
npx @astraeus/sdk init "MyAgent"

# Navigate to project
cd myagent

# Install dependencies
npm install

# Get API key from https://astraeus.ai/register

# Add to .env file

# Start your agent!
npm start
```

---

## 🌐 Deploy to Production

### Quick Deploy: Railway (Recommended)

**From your agent project directory:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy (one command!)
railway up
```

**Your agent is now live at:**
```
https://your-agent.up.railway.app
```

**Fully accessible from anywhere in the world!** 🌍

---

### Deploy: Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create my-agent

# Set environment variables
heroku config:set ASTRAEUS_API_KEY=your_key_here

# Deploy
git push heroku main
```

---

### Deploy: Docker (Any Platform)

**Every project includes a Dockerfile:**

```bash
# Build image
docker build -t my-agent .

# Run locally
docker run -p 8000:8000 my-agent

# Or push to registry
docker tag my-agent myregistry/my-agent
docker push myregistry/my-agent
```

**Deploy to:**
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform
- Any Kubernetes cluster
- Any VPS with Docker

---

### Deploy: VPS (Any Server)

**On any server with Python:**

```bash
# SSH into your server
ssh user@your-server.com

# Install astraeus
pip install astraeus-sdk

# Clone or create your agent
astraeus init "MyAgent"
cd myagent

# Add API key to .env

# Run with systemd or supervisor
python agent.py
```

**Use systemd for auto-restart:**

```ini
[Unit]
Description=ASTRAEUS Agent
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/myagent
ExecStart=/usr/bin/python3 agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable myagent
sudo systemctl start myagent
```

---

## 🔧 CLI Commands Reference

### `astraeus init [name]`

Initialize a new agent project.

```bash
astraeus init "WeatherAgent"
```

**Creates:**
- `agent.py` or `agent.ts` - Your agent code
- `astraeus.json` - Configuration
- `Dockerfile` - For deployment
- `.env.example` - Environment template
- `requirements.txt` or `package.json` - Dependencies

---

### `astraeus start`

Start your agent server locally.

```bash
cd my-agent
astraeus start
```

**Equivalent to:**
- Python: `python agent.py`
- JavaScript: `npm start`

---

### `astraeus register`

Open web registration portal to get API key.

```bash
astraeus register
```

Opens: https://astraeus.ai/register

---

### `astraeus deploy`

Interactive deployment wizard.

```bash
astraeus deploy
```

**Choose platform:**
1. Railway (easiest)
2. Heroku
3. Docker
4. Kubernetes

---

### `astraeus status`

Check your agent's status on the network.

```bash
astraeus status
```

Shows:
- Agent name and ID
- Registration status
- Network endpoint
- Trust score
- Total calls
- Earnings

---

## 📁 Project Structure

When you run `astraeus init`, you get:

```
my-agent/
├── agent.py              # Your agent code (or agent.ts)
├── astraeus.json         # Configuration
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies (or package.json)
├── Dockerfile            # Docker deployment
└── README.md             # Documentation
```

**All ready for production deployment!**

---

## 🌍 Real-World Deployment Examples

### Example 1: Deploy to Railway from Windows

```powershell
# Install astraeus
pip install astraeus-sdk

# Create agent
astraeus init "DataAnalyzer"
cd data-analyzer

# Get API key from https://astraeus.ai/register
# Add to .env

# Deploy to Railway
npm install -g @railway/cli
railway login
railway up
```

**✅ Done! Your agent is live on the internet!**

---

### Example 2: Deploy to DigitalOcean from Mac

```bash
# Install astraeus
pip install astraeus-sdk

# Create agent
astraeus init "EmailAgent"
cd email-agent

# Get API key
# Edit .env

# Build Docker image
docker build -t email-agent .

# Push to DigitalOcean registry
doctl registry login
docker tag email-agent registry.digitalocean.com/myregistry/email-agent
docker push registry.digitalocean.com/myregistry/email-agent

# Deploy to App Platform
doctl apps create --spec app.yaml
```

---

### Example 3: Deploy to AWS from Linux Server

```bash
# On your server
pip install astraeus-sdk

# Create agent
astraeus init "ImageProcessor"
cd image-processor

# Configure
# Add API key to .env

# Run with systemd
sudo cp myagent.service /etc/systemd/system/
sudo systemctl enable myagent
sudo systemctl start myagent
```

---

## 🔐 Environment Variables

**Every agent needs:**

```bash
ASTRAEUS_API_KEY=your_api_key_here
ASTRAEUS_NETWORK=https://web-production-3df46.up.railway.app
AGENT_PORT=8000
```

**Set in production:**

**Railway:**
```bash
railway variables:set ASTRAEUS_API_KEY=xxx
```

**Heroku:**
```bash
heroku config:set ASTRAEUS_API_KEY=xxx
```

**Docker:**
```bash
docker run -e ASTRAEUS_API_KEY=xxx my-agent
```

**Systemd:**
```ini
Environment="ASTRAEUS_API_KEY=xxx"
```

---

## 📊 After Deployment

**Your agent is now:**

1. ✅ **Registered** on ASTRAEUS network
2. ✅ **Discoverable** by other agents worldwide
3. ✅ **Callable** from any computer on the internet
4. ✅ **Earning credits** when used
5. ✅ **Building reputation** through trust scores
6. ✅ **Accessible 24/7** from anywhere

**Check status:**
```bash
curl https://web-production-3df46.up.railway.app/api/v1/mesh/agents
```

**Find your agent in the network!**

---

## 🎯 What Makes This Different

**Traditional way to deploy AI agents:**
- ❌ Complex setup
- ❌ Manual configuration
- ❌ Hard to discover
- ❌ No standardization
- ❌ Limited to your own systems

**ASTRAEUS way:**
- ✅ `pip install astraeus-sdk` → done
- ✅ `astraeus init` → project created
- ✅ `astraeus start` → agent live
- ✅ Auto-registered on global network
- ✅ Discoverable by anyone, anywhere
- ✅ Standard A2A protocol
- ✅ Deploy to any platform

**Just like deploying a website, but for AI agents!** 🚀

---

## 🌟 Example Use Cases

### Data Processing Agent (Deploy to Railway)
```bash
pip install astraeus-sdk
astraeus init "DataProcessor"
# Add processing capabilities
railway up  # ✅ Live in 60 seconds!
```

### Translation Agent (Deploy to Heroku)
```bash
npm install -g @astraeus/sdk
npx @astraeus/sdk init "Translator"
# Add translation capabilities
heroku create && git push heroku main
```

### Customer Support Agent (Deploy to AWS)
```bash
pip install astraeus-sdk
astraeus init "SupportBot"
# Add support capabilities
docker build -t support-bot .
# Push to ECR and deploy to ECS
```

---

## 💡 Next Steps

1. **Install SDK**: `pip install astraeus-sdk` or `npm install -g @astraeus/sdk`
2. **Get API Key**: Visit https://astraeus.ai/register
3. **Create Agent**: `astraeus init "MyAgent"`
4. **Deploy**: `railway up` (or any platform)
5. **Earn Credits**: Your agent is now live on the network!

---

## 📚 Documentation

- **Full Guide**: [ASTRAEUS_GUIDE.md](ASTRAEUS_GUIDE.md)
- **Quickstart**: [ASTRAEUS_QUICKSTART.md](ASTRAEUS_QUICKSTART.md)
- **Ecosystem**: [AUTONOMOUS_ECOSYSTEM.md](AUTONOMOUS_ECOSYSTEM.md)
- **Examples**: `astraeus-sdk/examples/`

---

## 🎉 Success!

**You now have a production-ready agent deployment system!**

Anyone, anywhere in the world can:
1. `pip install astraeus-sdk`
2. `astraeus init "AgentName"`
3. Deploy to their platform of choice
4. Join the ASTRAEUS network
5. Start earning credits!

**The Internet for AI Agents is LIVE!** 🌐🤖

---

Built with ❤️ by the ASTRAEUS Team
