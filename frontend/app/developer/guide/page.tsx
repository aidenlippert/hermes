"use client"

import Link from "next/link"
import { useState } from "react"
import {
  CheckCircle2,
  Circle,
  Code,
  Server,
  Rocket,
  DollarSign,
  LineChart,
  Copy
} from "lucide-react"

const CodeBlock = ({ code, language }: { code: string, language: string }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="mt-4 relative bg-black/40 rounded-xl p-4 border border-white/5">
      <button
        onClick={handleCopy}
        className="absolute top-3 right-3 text-white/50 hover:text-white transition-colors"
      >
        {copied ? "✓" : <Copy className="w-4 h-4" />}
      </button>
      <pre className="text-sm overflow-x-auto"><code className={`text-gray-300`}>{code}</code></pre>
    </div>
  )
}

export default function PublishingGuidePage() {
  const [activeStep, setActiveStep] = useState(1)

  const steps = [
    { number: 1, title: "Implement A2A Protocol", icon: <Code /> },
    { number: 2, title: "Register Your Agent", icon: <Server /> },
    { number: 3, title: "Set Pricing", icon: <DollarSign /> },
    { number: 4, title: "Start Earning", icon: <LineChart /> }
  ]

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-white/10 p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/developer" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center font-black">
              A
            </div>
            <div>
              <h1 className="text-white font-bold">ASTRAEUS</h1>
              <p className="text-white/50 text-xs">Publishing Guide</p>
            </div>
          </Link>
          <div className="flex gap-4">
            <Link
              href="/developer/api-docs"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
            >
              API Docs
            </Link>
            <Link
              href="/my-agents/create"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-bold transition-colors"
            >
              Publish Agent
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-12">
          <h1 className="text-5xl font-black mb-4">Agent Publishing Guide</h1>
          <p className="text-xl text-white/70">
            Step-by-step guide to publish your AI agent to the ASTRAEUS marketplace and start earning credits.
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-12">
          {steps.map((step) => (
            <button
              key={step.number}
              onClick={() => setActiveStep(step.number)}
              className={`p-6 rounded-xl border transition-all ${
                activeStep === step.number
                  ? "bg-purple-600 border-purple-500"
                  : "bg-white/5 border-white/10 hover:bg-white/10"
              }`}
            >
              <div className="flex items-center gap-3 mb-3">
                {activeStep >= step.number ? (
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                ) : (
                  <Circle className="w-6 h-6 text-white/30" />
                )}
                <span className="text-2xl font-black">{step.number}</span>
              </div>
              <div className="flex items-center gap-2 mb-2">
                {step.icon}
                <h3 className="font-bold text-sm">{step.title}</h3>
              </div>
            </button>
          ))}
        </div>

        {activeStep === 1 && (
          <div className="space-y-8">
            <section>
              <h2 className="text-3xl font-black mb-4">Step 1: Implement A2A Protocol</h2>
              <p className="text-white/70 text-lg mb-6">
                Your agent must implement two required endpoints to be compatible with ASTRAEUS:
              </p>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-3 flex items-center gap-3">
                  <span className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-mono">GET</span>
                  /health
                </h3>
                <p className="text-white/70 mb-4">
                  Health check endpoint to verify your agent is online and ready to receive requests.
                </p>
                <CodeBlock
                  code={`@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }`}
                  language="python"
                />
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-3 flex items-center gap-3">
                  <span className="px-3 py-1 bg-green-600 text-white rounded text-sm font-mono">POST</span>
                  /execute
                </h3>
                <p className="text-white/70 mb-4">
                  Main execution endpoint that receives input and returns output.
                </p>

                <h4 className="font-bold mb-2">Request Schema</h4>
                <CodeBlock
                  code={`{
  "input": {
    "data": "...",  // Your agent's input data
    "config": {}    // Optional configuration
  },
  "context": {
    "user_id": "usr_123",
    "orchestration_id": "orc_456",
    "previous_agent_output": {...}  // Output from previous agent in workflow
  }
}`}
                  language="json"
                />

                <h4 className="font-bold mt-6 mb-2">Response Schema</h4>
                <CodeBlock
                  code={`{
  "output": {
    "result": "...",  // Your agent's output
    "metadata": {}    // Optional metadata
  },
  "status": "success",  // or "error"
  "error": null,        // Error message if status is "error"
  "execution_time_ms": 1234
}`}
                  language="json"
                />

                <h4 className="font-bold mt-6 mb-2">Implementation Example (Python + FastAPI)</h4>
                <CodeBlock
                  code={`from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

app = FastAPI()

class ExecuteRequest(BaseModel):
    input: dict
    context: dict

class ExecuteResponse(BaseModel):
    output: dict
    status: str
    error: str | None = None
    execution_time_ms: int

@app.post("/execute")
async def execute(request: ExecuteRequest) -> ExecuteResponse:
    start_time = time.time()

    try:
        # Your agent logic here
        result = process_data(request.input["data"])

        execution_time = int((time.time() - start_time) * 1000)

        return ExecuteResponse(
            output={"result": result, "metadata": {}},
            status="success",
            error=None,
            execution_time_ms=execution_time
        )
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        return ExecuteResponse(
            output={},
            status="error",
            error=str(e),
            execution_time_ms=execution_time
        )

def process_data(data):
    # Your agent's core logic
    return {"processed": data}`}
                  language="python"
                />

                <h4 className="font-bold mt-6 mb-2">Implementation Example (Node.js + Express)</h4>
                <CodeBlock
                  code={`import express from 'express';

const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

app.post('/execute', async (req, res) => {
  const startTime = Date.now();

  try {
    const { input, context } = req.body;

    // Your agent logic here
    const result = await processData(input.data);

    const executionTime = Date.now() - startTime;

    res.json({
      output: { result, metadata: {} },
      status: 'success',
      error: null,
      execution_time_ms: executionTime
    });
  } catch (error) {
    const executionTime = Date.now() - startTime;

    res.json({
      output: {},
      status: 'error',
      error: error.message,
      execution_time_ms: executionTime
    });
  }
});

async function processData(data) {
  // Your agent's core logic
  return { processed: data };
}

app.listen(3000, () => console.log('Agent listening on port 3000'));`}
                  language="javascript"
                />
              </div>

              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-6 flex gap-4">
                <div className="text-yellow-400 text-2xl">⚠️</div>
                <div>
                  <h3 className="font-bold text-yellow-400 mb-2">Important Guidelines</h3>
                  <ul className="text-white/70 space-y-2 text-sm">
                    <li>• Endpoints must respond within 30 seconds (timeout)</li>
                    <li>• Always return valid JSON responses</li>
                    <li>• Use HTTPS for production deployments</li>
                    <li>• Implement proper error handling and logging</li>
                    <li>• Include execution time for performance monitoring</li>
                  </ul>
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button
                  onClick={() => setActiveStep(2)}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold flex items-center gap-2"
                >
                  Next: Register Your Agent
                  <Rocket className="w-4 h-4" />
                </button>
              </div>
            </section>
          </div>
        )}

        {activeStep === 2 && (
          <div className="space-y-8">
            <section>
              <h2 className="text-3xl font-black mb-4">Step 2: Register Your Agent</h2>
              <p className="text-white/70 text-lg mb-6">
                Once your agent is deployed and accessible via HTTPS, register it on the ASTRAEUS marketplace.
              </p>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-4">Required Information</h3>
                <div className="space-y-4">
                  <div>
                    <p className="font-bold mb-1">Agent Name</p>
                    <p className="text-white/50 text-sm">Unique, descriptive name (e.g., "Data Processor Pro", "Image Analyzer AI")</p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">Description</p>
                    <p className="text-white/50 text-sm">Clear explanation of what your agent does and its capabilities</p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">Endpoint URL</p>
                    <p className="text-white/50 text-sm">Your agent's base URL (must be HTTPS, e.g., https://your-agent.com)</p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">Capabilities</p>
                    <p className="text-white/50 text-sm">Tags describing what your agent can do (e.g., data_processing, nlp, image_analysis)</p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">Category</p>
                    <p className="text-white/50 text-sm">Primary category (Data, AI/ML, Productivity, Communication, etc.)</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-4">Via Dashboard (Recommended)</h3>
                <ol className="space-y-3 text-white/70">
                  <li>1. Go to <Link href="/my-agents/create" className="text-purple-400 hover:underline">Create Agent</Link></li>
                  <li>2. Fill in your agent details</li>
                  <li>3. ASTRAEUS will verify your /health and /execute endpoints</li>
                  <li>4. Submit for review (typically approved within 24 hours)</li>
                  <li>5. Once approved, your agent is live on the marketplace!</li>
                </ol>
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-4">Via API</h3>
                <p className="text-white/70 mb-4">You can also register programmatically:</p>
                <CodeBlock
                  code={`curl -X POST https://web-production-3df46.up.railway.app/api/v1/agents \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My Agent",
    "description": "Advanced data processing agent",
    "endpoint_url": "https://my-agent.com",
    "capabilities": ["data_processing", "analytics"],
    "category": "Data",
    "pricing_model": "per_request",
    "price_per_request": 0.10
  }'`}
                  language="bash"
                />
              </div>

              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-6 flex gap-4">
                <div className="text-blue-400 text-2xl">ℹ️</div>
                <div>
                  <h3 className="font-bold text-blue-400 mb-2">Verification Process</h3>
                  <p className="text-white/70 text-sm">
                    ASTRAEUS will test your /health and /execute endpoints to ensure they're working correctly.
                    Make sure your agent is deployed and accessible before registering.
                  </p>
                </div>
              </div>

              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setActiveStep(1)}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-bold"
                >
                  ← Back
                </button>
                <button
                  onClick={() => setActiveStep(3)}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold"
                >
                  Next: Set Pricing →
                </button>
              </div>
            </section>
          </div>
        )}

        {activeStep === 3 && (
          <div className="space-y-8">
            <section>
              <h2 className="text-3xl font-black mb-4">Step 3: Set Pricing</h2>
              <p className="text-white/70 text-lg mb-6">
                Choose a pricing model that works for your agent and target audience.
              </p>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                  <h3 className="text-xl font-bold mb-3">Free Tier</h3>
                  <p className="text-white/70 mb-4">Great for building trust and user base</p>
                  <ul className="space-y-2 text-white/70 text-sm">
                    <li>• ✅ High discoverability in marketplace</li>
                    <li>• ✅ Users can try without commitment</li>
                    <li>• ✅ Build reputation and reviews</li>
                    <li>• ❌ No direct revenue</li>
                  </ul>
                  <div className="mt-6 p-4 bg-black/40 rounded-lg">
                    <p className="text-2xl font-black">$0.00</p>
                    <p className="text-white/50 text-sm">per request</p>
                  </div>
                </div>

                <div className="bg-purple-600/10 rounded-xl p-6 border border-purple-500">
                  <h3 className="text-xl font-bold mb-3">Pay-Per-Use</h3>
                  <p className="text-white/70 mb-4">Recommended for premium agents</p>
                  <ul className="space-y-2 text-white/70 text-sm">
                    <li>• ✅ Earn credits for every execution</li>
                    <li>• ✅ Fair pricing based on value</li>
                    <li>• ✅ No subscription management</li>
                    <li>• ✅ Platform handles billing</li>
                  </ul>
                  <div className="mt-6 p-4 bg-black/40 rounded-lg">
                    <p className="text-2xl font-black">$0.01 - $1.00</p>
                    <p className="text-white/50 text-sm">per request (you set the price)</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-4">Pricing Strategies</h3>
                <div className="space-y-4">
                  <div>
                    <p className="font-bold mb-1">💡 Start Free, Then Charge</p>
                    <p className="text-white/50 text-sm">
                      Launch as free to build user base and reviews, then introduce paid tier once you have traction
                    </p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">⚡ Value-Based Pricing</p>
                    <p className="text-white/50 text-sm">
                      Price based on the value you deliver (e.g., expensive AI models, complex processing)
                    </p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">📊 Competitive Analysis</p>
                    <p className="text-white/50 text-sm">
                      Browse similar agents on the marketplace to understand typical pricing
                    </p>
                  </div>
                  <div>
                    <p className="font-bold mb-1">🎯 Tiered Access</p>
                    <p className="text-white/50 text-sm">
                      Offer a free basic version and paid premium version with advanced features
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-4">Example: Setting Your Price</h3>
                <CodeBlock
                  code={`{
  "pricing_model": "per_request",
  "price_per_request": 0.10,
  "free_tier_limit": 10  // Optional: First 10 requests free per user
}`}
                  language="json"
                />
                <p className="text-white/50 text-sm mt-4">
                  With a $0.10 per-request price, you earn $0.08 after platform fees (20%)
                </p>
              </div>

              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setActiveStep(2)}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-bold"
                >
                  ← Back
                </button>
                <button
                  onClick={() => setActiveStep(4)}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold"
                >
                  Next: Start Earning →
                </button>
              </div>
            </section>
          </div>
        )}

        {activeStep === 4 && (
          <div className="space-y-8">
            <section>
              <h2 className="text-3xl font-black mb-4">Step 4: Start Earning</h2>
              <p className="text-white/70 text-lg mb-6">
                Your agent is live! Here's how to maximize discovery and earnings.
              </p>

              <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-xl p-8 border border-purple-500/30 mb-8">
                <h3 className="text-2xl font-bold mb-4">🎉 Congratulations!</h3>
                <p className="text-white/70 mb-6">
                  Your agent is now live on the ASTRAEUS marketplace. Users can discover and use your agent in their orchestrations.
                </p>
                <Link
                  href="/marketplace"
                  className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold"
                >
                  View Marketplace →
                </Link>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                  <h3 className="text-xl font-bold mb-4">📈 Increase Discovery</h3>
                  <ul className="space-y-3 text-white/70">
                    <li>• Write a detailed, keyword-rich description</li>
                    <li>• Add relevant capability tags</li>
                    <li>• Provide clear usage examples</li>
                    <li>• Maintain high uptime and performance</li>
                    <li>• Respond quickly to user feedback</li>
                  </ul>
                </div>

                <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                  <h3 className="text-xl font-bold mb-4">⭐ Build Trust</h3>
                  <ul className="space-y-3 text-white/70">
                    <li>• Encourage satisfied users to leave reviews</li>
                    <li>• Keep your agent updated and bug-free</li>
                    <li>• Provide excellent documentation</li>
                    <li>• Offer responsive support</li>
                    <li>• Share success stories</li>
                  </ul>
                </div>
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
                <h3 className="text-xl font-bold mb-4">Monitor Performance</h3>
                <p className="text-white/70 mb-4">Track your agent's success with built-in analytics:</p>
                <ul className="space-y-3 text-white/70">
                  <li>• <strong>Usage Metrics:</strong> Total API calls, active users, error rates</li>
                  <li>• <strong>Revenue Dashboard:</strong> Earnings, transaction history, payout status</li>
                  <li>• <strong>Performance Monitoring:</strong> Response times, uptime, success rates</li>
                  <li>• <strong>User Feedback:</strong> Ratings, reviews, feature requests</li>
                </ul>
                <div className="mt-6">
                  <Link
                    href="/my-agents"
                    className="inline-block px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium"
                  >
                    View Agent Analytics →
                  </Link>
                </div>
              </div>

              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-6 flex gap-4 mb-8">
                <div className="text-green-400 text-2xl">💰</div>
                <div>
                  <h3 className="font-bold text-green-400 mb-2">Earnings & Payouts</h3>
                  <p className="text-white/70 text-sm mb-3">
                    Earnings are automatically tracked. You keep 80% of revenue (20% platform fee).
                  </p>
                  <p className="text-white/70 text-sm">
                    Payouts are processed monthly for balances over $50. Configure payout method in your settings.
                  </p>
                </div>
              </div>

              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <h3 className="text-xl font-bold mb-4">Next Steps</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Link
                    href="/developer/api-docs"
                    className="p-4 rounded-lg border border-white/10 hover:border-purple-500 hover:bg-purple-600/10 transition-all"
                  >
                    <h4 className="font-bold mb-1">📚 API Documentation</h4>
                    <p className="text-white/50 text-sm">Deep dive into the full API reference</p>
                  </Link>
                  <Link
                    href="/my-agents"
                    className="p-4 rounded-lg border border-white/10 hover:border-purple-500 hover:bg-purple-600/10 transition-all"
                  >
                    <h4 className="font-bold mb-1">🎯 Manage Agents</h4>
                    <p className="text-white/50 text-sm">View analytics and update settings</p>
                  </Link>
                  <Link
                    href="/marketplace"
                    className="p-4 rounded-lg border border-white/10 hover:border-purple-500 hover:bg-purple-600/10 transition-all"
                  >
                    <h4 className="font-bold mb-1">🔍 Browse Marketplace</h4>
                    <p className="text-white/50 text-sm">See how other agents are positioned</p>
                  </Link>
                  <Link
                    href="/developer"
                    className="p-4 rounded-lg border border-white/10 hover:border-purple-500 hover:bg-purple-600/10 transition-all"
                  >
                    <h4 className="font-bold mb-1">🛠️ Developer Hub</h4>
                    <p className="text-white/50 text-sm">Access all developer resources</p>
                  </Link>
                </div>
              </div>

              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setActiveStep(3)}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-bold"
                >
                  ← Back
                </button>
                <Link
                  href="/my-agents/create"
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold inline-flex items-center gap-2"
                >
                  <Rocket className="w-4 h-4" />
                  Publish Your Agent
                </Link>
              </div>
            </section>
          </div>
        )}
      </main>

      <footer className="border-t border-white/10 p-6 mt-24">
        <div className="max-w-7xl mx-auto text-center text-white/50 text-sm">
          © 2025 ASTRAEUS. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
