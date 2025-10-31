import Link from "next/link"

export default function DeveloperHub() {
  const resources = [
    {
      title: "API Documentation",
      description: "Complete API reference with examples and authentication guides",
      href: "/developer/api-docs",
      icon: "📚"
    },
    {
      title: "Publishing Guide",
      description: "Step-by-step guide to publish your agent to the marketplace",
      href: "/developer/guide",
      icon: "🚀"
    },
    {
      title: "Workflow Builder",
      description: "Visual tool to design and test agent orchestration workflows",
      href: "/developer/workflow-builder",
      icon: "🔧"
    },
    {
      title: "Analytics Dashboard",
      description: "Monitor your agent's performance, usage, and revenue",
      href: "/developer/analytics",
      icon: "📊"
    }
  ]

  const quickStart = [
    {
      step: "1",
      title: "Implement A2A Protocol",
      description: "Add /health and /execute endpoints to your agent"
    },
    {
      step: "2",
      title: "Register Your Agent",
      description: "Submit your agent details and capabilities"
    },
    {
      step: "3",
      title: "Set Pricing",
      description: "Choose free or paid model with per-request pricing"
    },
    {
      step: "4",
      title: "Start Earning",
      description: "Get discovered and earn credits from usage"
    }
  ]

  return (
    <main className="min-h-screen px-6 py-16 text-white max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-16">
        <h1 className="text-5xl md:text-6xl font-black mb-6">Developer Hub</h1>
        <p className="text-xl text-white/70 max-w-3xl mx-auto">
          Build and publish AI agents to the ASTRAEUS network. Get discovery, auth, streaming, and metering out of the box.
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <Link
            href="/developer/api-docs"
            className="px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold text-lg"
          >
            API Docs
          </Link>
          <Link
            href="/developer/guide"
            className="px-8 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-bold text-lg"
          >
            Publishing Guide
          </Link>
        </div>
      </div>

      {/* Quick Start */}
      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8 text-center">Quick Start</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {quickStart.map((item) => (
            <div key={item.step} className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="w-12 h-12 rounded-full bg-purple-600 flex items-center justify-center text-xl font-black mb-4">
                {item.step}
              </div>
              <h3 className="text-lg font-bold mb-2">{item.title}</h3>
              <p className="text-white/70 text-sm">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Resources Grid */}
      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8 text-center">Developer Resources</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {resources.map((resource) => (
            <Link
              key={resource.href}
              href={resource.href}
              className="bg-white/5 rounded-xl p-8 border border-white/10 hover:bg-white/10 transition-colors group"
            >
              <div className="text-5xl mb-4">{resource.icon}</div>
              <h3 className="text-2xl font-bold mb-3 group-hover:text-purple-400 transition-colors">
                {resource.title}
              </h3>
              <p className="text-white/70">{resource.description}</p>
              <div className="mt-4 text-purple-400 font-bold">
                Learn More →
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section className="mb-20">
        <div className="bg-gradient-to-r from-purple-600/10 to-blue-600/10 rounded-2xl p-12 border border-purple-500/20">
          <h2 className="text-3xl font-black mb-8 text-center">Join the Ecosystem</h2>
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-black text-purple-400 mb-2">100+</div>
              <div className="text-white/70">Published Agents</div>
            </div>
            <div>
              <div className="text-4xl font-black text-purple-400 mb-2">$50K+</div>
              <div className="text-white/70">Developer Earnings</div>
            </div>
            <div>
              <div className="text-4xl font-black text-purple-400 mb-2">10K+</div>
              <div className="text-white/70">API Calls/Day</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="text-center">
        <h2 className="text-3xl font-black mb-4">Ready to Publish Your Agent?</h2>
        <p className="text-white/70 mb-8 text-lg">
          Join developers building the future of AI agent orchestration.
        </p>
        <Link
          href="/my-agents/create"
          className="inline-block px-10 py-4 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold text-xl"
        >
          Publish Your Agent
        </Link>
      </section>
    </main>
  )
}
