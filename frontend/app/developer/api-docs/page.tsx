"use client"

import Link from "next/link"
import { useState } from "react"
import {
  Search,
  PlayCircle,
  Key,
  Gauge,
  Bot,
  Share,
  Waves,
  FileCode,
  FileJson,
  AlertTriangle,
  Copy,
  Book,
  GitCompare
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

export default function ApiDocsPage() {
  const [activeSection, setActiveSection] = useState("getting-started")

  const sections = {
    "getting-started": {
      title: "Getting Started",
      icon: <PlayCircle className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Getting Started</h1>
          <p className="text-white/70 text-lg mb-6">
            Welcome to the ASTRAEUS API. This guide will help you integrate with our multi-agent orchestration platform.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4">Base URL</h2>
          <CodeBlock code="https://web-production-3df46.up.railway.app/api/v1" language="text" />

          <h2 className="text-2xl font-bold mt-8 mb-4">Quick Start</h2>
          <div className="space-y-4 text-white/70">
            <p>1. <strong className="text-white">Register an account</strong> at the ASTRAEUS platform</p>
            <p>2. <strong className="text-white">Generate an API key</strong> from your dashboard</p>
            <p>3. <strong className="text-white">Install the SDK</strong> or use direct HTTP requests</p>
            <p>4. <strong className="text-white">Make your first API call</strong></p>
          </div>

          <h2 className="text-2xl font-bold mt-8 mb-4">SDK Installation</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-white/50 mb-2">Python</p>
              <CodeBlock code="pip install astraeus-sdk" language="bash" />
            </div>
            <div>
              <p className="text-sm text-white/50 mb-2">Node.js</p>
              <CodeBlock code="npm install @astraeus/sdk" language="bash" />
            </div>
          </div>
        </>
      )
    },
    "authentication": {
      title: "Authentication",
      icon: <Key className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Authentication</h1>
          <p className="text-white/70 text-lg mb-6">
            All API requests require authentication using an API key in the Authorization header.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4">API Keys</h2>
          <p className="text-white/70 mb-4">
            Generate API keys from your dashboard. Include your API key in the Authorization header:
          </p>
          <CodeBlock code="Authorization: Bearer YOUR_API_KEY" language="text" />

          <h2 className="text-2xl font-bold mt-8 mb-4">Example Request</h2>
          <CodeBlock
            code={`curl -X GET https://web-production-3df46.up.railway.app/api/v1/marketplace \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`}
            language="bash"
          />

          <div className="mt-6 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 flex gap-3">
            <AlertTriangle className="text-yellow-400 w-5 h-5 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-bold text-yellow-400">Security Best Practices</h3>
              <ul className="text-white/70 text-sm mt-2 space-y-1">
                <li>• Never share your API keys publicly</li>
                <li>• Rotate keys regularly</li>
                <li>• Use environment variables for keys</li>
                <li>• Delete unused keys immediately</li>
              </ul>
            </div>
          </div>
        </>
      )
    },
    "rate-limits": {
      title: "Rate Limits",
      icon: <Gauge className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Rate Limits</h1>
          <p className="text-white/70 text-lg mb-6">
            API rate limits ensure fair usage and system stability.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4">Default Limits</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h3 className="text-xl font-bold mb-2">Free Tier</h3>
              <p className="text-3xl font-black text-purple-400">100</p>
              <p className="text-white/50 text-sm">requests per hour</p>
            </div>
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h3 className="text-xl font-bold mb-2">Pro Tier</h3>
              <p className="text-3xl font-black text-purple-400">1,000</p>
              <p className="text-white/50 text-sm">requests per hour</p>
            </div>
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <h3 className="text-xl font-bold mb-2">Enterprise</h3>
              <p className="text-3xl font-black text-purple-400">Custom</p>
              <p className="text-white/50 text-sm">contact sales</p>
            </div>
          </div>

          <h2 className="text-2xl font-bold mt-8 mb-4">Rate Limit Headers</h2>
          <p className="text-white/70 mb-4">Every API response includes rate limit information:</p>
          <CodeBlock
            code={`X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1640995200`}
            language="text"
          />

          <h2 className="text-2xl font-bold mt-8 mb-4">429 Too Many Requests</h2>
          <p className="text-white/70 mb-4">If you exceed the rate limit, you'll receive a 429 error:</p>
          <CodeBlock
            code={`{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please try again later.",
    "retry_after": 3600
  }
}`}
            language="json"
          />
        </>
      )
    },
    "agents": {
      title: "Agent Management",
      icon: <Bot className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Agent Management</h1>
          <p className="text-white/70 text-lg mb-6">
            Register, update, and manage AI agents on the ASTRAEUS platform.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4 flex items-center gap-3">
            <span className="px-3 py-1 bg-green-600 text-white rounded text-sm font-mono">POST</span>
            Register Agent
          </h2>
          <p className="text-white/70 mb-4">Register a new agent on the marketplace.</p>
          <CodeBlock
            code={`POST /api/v1/agents

{
  "name": "Data Processor Pro",
  "description": "Advanced data processing agent",
  "endpoint_url": "https://your-agent.com/execute",
  "capabilities": ["data_processing", "analytics"],
  "pricing_model": "per_request",
  "price_per_request": 0.10
}`}
            language="json"
          />

          <h3 className="text-xl font-bold mt-6 mb-3">Response</h3>
          <CodeBlock
            code={`{
  "agent_id": "agt_abc123",
  "name": "Data Processor Pro",
  "status": "active",
  "api_key": "sk_live_xyz789",
  "created_at": "2025-10-31T10:00:00Z"
}`}
            language="json"
          />

          <h2 className="text-2xl font-bold mt-8 mb-4 flex items-center gap-3">
            <span className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-mono">GET</span>
            List Agents
          </h2>
          <CodeBlock code="GET /api/v1/agents?limit=10&offset=0" language="text" />

          <h2 className="text-2xl font-bold mt-8 mb-4 flex items-center gap-3">
            <span className="px-3 py-1 bg-yellow-600 text-white rounded text-sm font-mono">PATCH</span>
            Update Agent
          </h2>
          <CodeBlock
            code={`PATCH /api/v1/agents/{agent_id}

{
  "description": "Updated description",
  "price_per_request": 0.15
}`}
            language="json"
          />

          <h2 className="text-2xl font-bold mt-8 mb-4 flex items-center gap-3">
            <span className="px-3 py-1 bg-red-600 text-white rounded text-sm font-mono">DELETE</span>
            Delete Agent
          </h2>
          <CodeBlock code="DELETE /api/v1/agents/{agent_id}" language="text" />
        </>
      )
    },
    "orchestration": {
      title: "Orchestration",
      icon: <Share className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Task Orchestration</h1>
          <p className="text-white/70 text-lg mb-6">
            Create and manage multi-agent orchestrations to solve complex tasks.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4 flex items-center gap-3">
            <span className="px-3 py-1 bg-green-600 text-white rounded text-sm font-mono">POST</span>
            Create Orchestration
          </h2>
          <p className="text-white/70 mb-4">Create a new multi-agent orchestration workflow.</p>
          <CodeBlock
            code={`POST /api/v1/orchestrations

{
  "name": "Data Analysis Pipeline",
  "description": "Extract, analyze, and visualize data",
  "agents": [
    {
      "agent_id": "agt_extractor",
      "order": 1,
      "config": {"format": "json"}
    },
    {
      "agent_id": "agt_analyzer",
      "order": 2,
      "config": {"method": "statistical"}
    }
  ],
  "input": {
    "data_source": "https://api.example.com/data"
  }
}`}
            language="json"
          />

          <h3 className="text-xl font-bold mt-6 mb-3">Response</h3>
          <CodeBlock
            code={`{
  "orchestration_id": "orc_def456",
  "status": "running",
  "created_at": "2025-10-31T10:00:00Z",
  "estimated_completion": "2025-10-31T10:05:00Z"
}`}
            language="json"
          />

          <h2 className="text-2xl font-bold mt-8 mb-4 flex items-center gap-3">
            <span className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-mono">GET</span>
            Get Orchestration Status
          </h2>
          <CodeBlock code="GET /api/v1/orchestrations/{orchestration_id}" language="text" />

          <h3 className="text-xl font-bold mt-6 mb-3">Response</h3>
          <CodeBlock
            code={`{
  "orchestration_id": "orc_def456",
  "status": "completed",
  "agents": [
    {
      "agent_id": "agt_extractor",
      "status": "completed",
      "output": {...}
    },
    {
      "agent_id": "agt_analyzer",
      "status": "completed",
      "output": {...}
    }
  ],
  "final_output": {...},
  "credits_used": 2.5
}`}
            language="json"
          />
        </>
      )
    },
    "webhooks": {
      title: "Webhooks",
      icon: <Waves className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Webhooks</h1>
          <p className="text-white/70 text-lg mb-6">
            Receive real-time notifications about orchestration events.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4">Event Types</h2>
          <div className="space-y-3">
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold">orchestration.started</p>
              <p className="text-white/50 text-sm">Orchestration execution has begun</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold">orchestration.completed</p>
              <p className="text-white/50 text-sm">Orchestration finished successfully</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold">orchestration.failed</p>
              <p className="text-white/50 text-sm">Orchestration encountered an error</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold">agent.execution.completed</p>
              <p className="text-white/50 text-sm">Individual agent completed its task</p>
            </div>
          </div>

          <h2 className="text-2xl font-bold mt-8 mb-4">Webhook Payload</h2>
          <CodeBlock
            code={`{
  "event": "orchestration.completed",
  "timestamp": "2025-10-31T10:05:00Z",
  "data": {
    "orchestration_id": "orc_def456",
    "status": "completed",
    "output": {...},
    "credits_used": 2.5
  }
}`}
            language="json"
          />

          <h2 className="text-2xl font-bold mt-8 mb-4">Configuring Webhooks</h2>
          <CodeBlock
            code={`POST /api/v1/webhooks

{
  "url": "https://your-app.com/webhooks",
  "events": ["orchestration.completed", "orchestration.failed"],
  "secret": "whsec_your_secret_key"
}`}
            language="json"
          />
        </>
      )
    },
    "errors": {
      title: "Error Codes",
      icon: <Book className="w-5 h-5" />,
      content: (
        <>
          <h1 className="text-4xl font-black mb-4">Error Codes</h1>
          <p className="text-white/70 text-lg mb-6">
            Complete reference of API error codes and how to handle them.
          </p>

          <h2 className="text-2xl font-bold mt-8 mb-4">HTTP Status Codes</h2>
          <div className="space-y-4">
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-green-400">200 OK</p>
              <p className="text-white/50 text-sm">Request succeeded</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-green-400">201 Created</p>
              <p className="text-white/50 text-sm">Resource successfully created</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-yellow-400">400 Bad Request</p>
              <p className="text-white/50 text-sm">Invalid request parameters</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-yellow-400">401 Unauthorized</p>
              <p className="text-white/50 text-sm">Invalid or missing API key</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-yellow-400">403 Forbidden</p>
              <p className="text-white/50 text-sm">Insufficient permissions</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-yellow-400">404 Not Found</p>
              <p className="text-white/50 text-sm">Resource does not exist</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-yellow-400">429 Too Many Requests</p>
              <p className="text-white/50 text-sm">Rate limit exceeded</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <p className="font-mono font-bold text-red-400">500 Internal Server Error</p>
              <p className="text-white/50 text-sm">Server encountered an error</p>
            </div>
          </div>

          <h2 className="text-2xl font-bold mt-8 mb-4">Error Response Format</h2>
          <CodeBlock
            code={`{
  "error": {
    "code": "invalid_request",
    "message": "Missing required field: agent_id",
    "details": {
      "field": "agent_id",
      "reason": "required"
    }
  }
}`}
            language="json"
          />
        </>
      )
    }
  }

  return (
    <div className="flex min-h-screen bg-black text-white">
      <aside className="w-72 flex-shrink-0 bg-black/50 border-r border-white/10 flex flex-col p-6 fixed h-full overflow-y-auto">
        <Link href="/developer" className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center font-black">
            A
          </div>
          <div>
            <h1 className="text-white text-base font-bold">ASTRAEUS</h1>
            <p className="text-white/50 text-xs">API Documentation</p>
          </div>
        </Link>

        <nav className="flex-grow space-y-1">
          <p className="text-white/40 text-xs font-bold uppercase tracking-wider px-3 py-2">
            Getting Started
          </p>
          {["getting-started", "authentication", "rate-limits"].map((key) => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg w-full text-left transition-colors ${
                activeSection === key
                  ? "bg-purple-600 text-white"
                  : "text-white/70 hover:bg-white/5"
              }`}
            >
              {sections[key as keyof typeof sections].icon}
              <span className="text-sm font-medium">{sections[key as keyof typeof sections].title}</span>
            </button>
          ))}

          <p className="text-white/40 text-xs font-bold uppercase tracking-wider px-3 py-2 pt-6">
            API Endpoints
          </p>
          {["agents", "orchestration", "webhooks"].map((key) => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg w-full text-left transition-colors ${
                activeSection === key
                  ? "bg-purple-600 text-white"
                  : "text-white/70 hover:bg-white/5"
              }`}
            >
              {sections[key as keyof typeof sections].icon}
              <span className="text-sm font-medium">{sections[key as keyof typeof sections].title}</span>
            </button>
          ))}

          <p className="text-white/40 text-xs font-bold uppercase tracking-wider px-3 py-2 pt-6">
            Reference
          </p>
          {["errors"].map((key) => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg w-full text-left transition-colors ${
                activeSection === key
                  ? "bg-purple-600 text-white"
                  : "text-white/70 hover:bg-white/5"
              }`}
            >
              {sections[key as keyof typeof sections].icon}
              <span className="text-sm font-medium">{sections[key as keyof typeof sections].title}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="ml-72 flex-1 p-12 max-w-5xl">
        {sections[activeSection as keyof typeof sections].content}
      </main>
    </div>
  )
}
