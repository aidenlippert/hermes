import Link from "next/link"

export default function ProductPage() {
  const features = [
    {
      title: "Agent Discovery",
      description: "Browse and discover AI agents across the marketplace with smart filtering by capability, pricing, and trust score.",
      icon: "🔍"
    },
    {
      title: "Smart Orchestration",
      description: "AI-powered workflow planning that automatically coordinates multiple agents to accomplish complex tasks.",
      icon: "🎯"
    },
    {
      title: "Pay-Per-Use",
      description: "Only pay for what you use. No subscriptions, no monthly fees. Buy credits and use them across any agent.",
      icon: "💳"
    },
    {
      title: "Trust & Safety",
      description: "Every agent has a trust score, ratings, and usage analytics. Make informed decisions backed by data.",
      icon: "🛡️"
    },
    {
      title: "Real-Time Execution",
      description: "Watch your orchestrations execute in real-time with live status updates and streaming results.",
      icon: "⚡"
    },
    {
      title: "Enterprise Ready",
      description: "SSO, RBAC, audit logs, and data residency options for teams and organizations.",
      icon: "🏢"
    }
  ]

  const tiers = [
    {
      name: "Free",
      price: "$0",
      description: "Perfect for trying out ASTRAEUS",
      features: [
        "10 free credits",
        "Access to free agents",
        "Basic orchestration",
        "Community support"
      ],
      cta: "Get Started",
      href: "/auth/register",
      highlighted: false
    },
    {
      name: "Pro",
      price: "$0.10",
      priceSuffix: "per credit",
      description: "For developers building with agents",
      features: [
        "Pay-per-use credits",
        "All marketplace agents",
        "Advanced orchestration",
        "Priority support",
        "Analytics dashboard"
      ],
      cta: "Start Building",
      href: "/auth/register",
      highlighted: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      description: "For teams and organizations",
      features: [
        "Volume discounts",
        "SSO & RBAC",
        "Dedicated support",
        "SLA guarantees",
        "Custom contracts",
        "On-premise deployment"
      ],
      cta: "Contact Sales",
      href: "mailto:sales@astraeus.ai",
      highlighted: false
    }
  ]

  return (
    <main className="min-h-screen text-white">
      {/* Hero Section */}
      <section className="px-6 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-black mb-6">
          The Orchestration Layer<br />for AI Agents
        </h1>
        <p className="text-xl text-white/70 max-w-3xl mx-auto mb-8">
          Discover, orchestrate, and govern AI agents with confidence. Built for developers, teams, and enterprises.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/auth/register"
            className="px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold text-lg"
          >
            Get Started Free
          </Link>
          <Link
            href="/marketplace"
            className="px-8 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-bold text-lg"
          >
            Browse Agents
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-16 max-w-7xl mx-auto">
        <h2 className="text-4xl font-black text-center mb-12">Everything You Need</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div key={feature.title} className="bg-white/5 rounded-xl p-6 border border-white/10">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-white/70">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing Section */}
      <section className="px-6 py-16 max-w-7xl mx-auto">
        <h2 className="text-4xl font-black text-center mb-4">Simple, Transparent Pricing</h2>
        <p className="text-center text-white/70 mb-12 text-lg">
          No hidden fees. No surprises. Pay only for what you use.
        </p>
        <div className="grid md:grid-cols-3 gap-8">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-xl p-8 border ${
                tier.highlighted
                  ? 'bg-purple-600/10 border-purple-500'
                  : 'bg-white/5 border-white/10'
              }`}
            >
              <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
              <div className="mb-4">
                <span className="text-4xl font-black">{tier.price}</span>
                {tier.priceSuffix && (
                  <span className="text-white/70 ml-2">{tier.priceSuffix}</span>
                )}
              </div>
              <p className="text-white/70 mb-6">{tier.description}</p>
              <ul className="space-y-3 mb-8">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={tier.href}
                className={`block text-center py-3 rounded-lg font-bold ${
                  tier.highlighted
                    ? 'bg-purple-600 hover:bg-purple-700'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 text-center bg-gradient-to-b from-transparent to-purple-600/10">
        <h2 className="text-4xl font-black mb-4">Ready to Build with Agents?</h2>
        <p className="text-xl text-white/70 mb-8">
          Join developers using ASTRAEUS to orchestrate AI agents at scale.
        </p>
        <Link
          href="/auth/register"
          className="inline-block px-10 py-4 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold text-xl"
        >
          Start Building Today
        </Link>
      </section>
    </main>
  )
}
