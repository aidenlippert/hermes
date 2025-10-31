import Link from "next/link"

export default function ProtocolPage() {
  const endpoints = [
    {
      method: "GET",
      path: "/health",
      description: "Health check endpoint to verify agent availability",
      response: '{ "status": "healthy", "version": "1.0.0" }'
    },
    {
      method: "POST",
      path: "/execute",
      description: "Execute agent with input data and receive results",
      request: '{ "input": {...}, "context": {...} }',
      response: '{ "output": {...}, "status": "success" }'
    }
  ]

  const features = [
    {
      title: "Streaming Events",
      description: "Real-time progress updates via WebSocket for long-running tasks",
      icon: "📡"
    },
    {
      title: "Provenance Tracking",
      description: "Complete audit trail of agent interactions and data flow",
      icon: "📊"
    },
    {
      title: "Policy Hooks",
      description: "Pre-execution validation and post-execution approval workflows",
      icon: "🔒"
    },
    {
      title: "Discovery",
      description: "Automatic agent discovery and capability registration",
      icon: "🔍"
    },
    {
      title: "Versioning",
      description: "Semantic versioning support for backward compatibility",
      icon: "🏷️"
    },
    {
      title: "Authentication",
      description: "Multiple auth methods: API keys, OAuth, JWT tokens",
      icon: "🔑"
    }
  ]

  return (
    <main className="min-h-screen px-6 py-16 text-white max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-16">
        <h1 className="text-5xl md:text-6xl font-black mb-6">
          Astraeus Protocol (A2A)
        </h1>
        <p className="text-xl text-white/70 max-w-3xl mx-auto">
          An open specification for discovering, invoking, and governing agents with streaming events, provenance, and policy hooks.
        </p>
      </div>

      {/* Core Features */}
      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Protocol Features</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div key={feature.title} className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-white/70">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* API Endpoints */}
      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Core API Endpoints</h2>
        <div className="space-y-6">
          {endpoints.map((endpoint) => (
            <div key={endpoint.path} className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="flex items-center gap-3 mb-4">
                <span className={`px-3 py-1 rounded font-mono text-sm font-bold ${
                  endpoint.method === 'GET' ? 'bg-blue-600' : 'bg-green-600'
                }`}>
                  {endpoint.method}
                </span>
                <span className="font-mono text-white/90">{endpoint.path}</span>
              </div>
              <p className="text-white/70 mb-4">{endpoint.description}</p>
              {endpoint.request && (
                <div className="mb-3">
                  <div className="text-sm text-white/50 mb-1">Request:</div>
                  <pre className="bg-black/30 p-3 rounded text-sm overflow-x-auto">
                    <code>{endpoint.request}</code>
                  </pre>
                </div>
              )}
              <div>
                <div className="text-sm text-white/50 mb-1">Response:</div>
                <pre className="bg-black/30 p-3 rounded text-sm overflow-x-auto">
                  <code>{endpoint.response}</code>
                </pre>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Implementation Guide */}
      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Quick Start</h2>
        <div className="bg-white/5 rounded-xl p-8 border border-white/10">
          <h3 className="text-xl font-bold mb-4">Building an A2A-Compatible Agent</h3>
          <ol className="space-y-4 text-white/70">
            <li className="flex gap-3">
              <span className="text-purple-400 font-bold">1.</span>
              <div>
                <strong className="text-white">Implement Required Endpoints</strong>
                <p>Add <code className="bg-black/30 px-2 py-1 rounded text-sm">/health</code> and <code className="bg-black/30 px-2 py-1 rounded text-sm">/execute</code> to your agent</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-purple-400 font-bold">2.</span>
              <div>
                <strong className="text-white">Register on ASTRAEUS</strong>
                <p>Submit your agent endpoint and capabilities to the marketplace</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-purple-400 font-bold">3.</span>
              <div>
                <strong className="text-white">Handle Requests</strong>
                <p>Process incoming execution requests and return structured results</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="text-purple-400 font-bold">4.</span>
              <div>
                <strong className="text-white">Monitor & Optimize</strong>
                <p>Track performance metrics and improve based on user feedback</p>
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* SDKs */}
      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Official SDKs</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-xl font-bold mb-2">Python</h3>
            <pre className="bg-black/30 p-3 rounded text-sm mb-4">
              <code>pip install astraeus-sdk</code>
            </pre>
            <Link href="/developer/guide" className="text-purple-400 hover:text-purple-300">
              View Docs →
            </Link>
          </div>
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-xl font-bold mb-2">TypeScript</h3>
            <pre className="bg-black/30 p-3 rounded text-sm mb-4">
              <code>npm install @astraeus/sdk</code>
            </pre>
            <Link href="/developer/guide" className="text-purple-400 hover:text-purple-300">
              View Docs →
            </Link>
          </div>
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-xl font-bold mb-2">Go</h3>
            <pre className="bg-black/30 p-3 rounded text-sm mb-4">
              <code>go get github.com/astraeus/sdk</code>
            </pre>
            <Link href="/developer/guide" className="text-purple-400 hover:text-purple-300">
              View Docs →
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="text-center bg-gradient-to-r from-purple-600/10 to-blue-600/10 rounded-2xl p-12 border border-purple-500/20">
        <h2 className="text-3xl font-black mb-4">Start Building with A2A</h2>
        <p className="text-white/70 mb-8 max-w-2xl mx-auto">
          Join the ecosystem of interoperable AI agents. Build once, work everywhere.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/developer/guide"
            className="px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold"
          >
            Developer Guide
          </Link>
          <Link
            href="/developer/api-docs"
            className="px-8 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-bold"
          >
            API Reference
          </Link>
        </div>
      </section>
    </main>
  )
}
