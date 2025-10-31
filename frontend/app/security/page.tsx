import Link from "next/link"

export default function SecurityPage() {
  const features = [
    {
      title: "SSO & SCIM",
      description: "Enterprise Single Sign-On with SAML 2.0, OAuth 2.0, and automated user provisioning via SCIM",
      icon: "🔐"
    },
    {
      title: "Role-Based Access Control",
      description: "Granular permissions system with custom roles and resource-level access controls",
      icon: "👥"
    },
    {
      title: "Encryption",
      description: "TLS 1.3 for data in transit, AES-256 for data at rest, and end-to-end encryption options",
      icon: "🔒"
    },
    {
      title: "Audit Logs",
      description: "Complete activity logging with tamper-proof audit trails and SIEM integration",
      icon: "📝"
    },
    {
      title: "Data Residency",
      description: "Choose where your data is stored with regional deployment options for compliance",
      icon: "🌍"
    },
    {
      title: "Compliance",
      description: "SOC 2 Type II, GDPR, HIPAA, and ISO 27001 certified security practices",
      icon: "✅"
    }
  ]

  const practices = [
    "Regular third-party security audits",
    "Penetration testing and vulnerability scanning",
    "Bug bounty program with responsible disclosure",
    "24/7 security monitoring and incident response",
    "Automated security patching and updates",
    "Data backup and disaster recovery planning"
  ]

  return (
    <main className="min-h-screen px-6 py-16 text-white max-w-7xl mx-auto">
      <div className="text-center mb-16">
        <h1 className="text-5xl md:text-6xl font-black mb-6">Enterprise Security</h1>
        <p className="text-xl text-white/70 max-w-3xl mx-auto">
          Bank-level security with SSO, RBAC, encryption, audit logs, and compliance certifications for teams and enterprises.
        </p>
      </div>

      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Security Features</h2>
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

      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Security Practices</h2>
        <div className="bg-white/5 rounded-xl p-8 border border-white/10">
          <ul className="grid md:grid-cols-2 gap-4">
            {practices.map((practice) => (
              <li key={practice} className="flex items-start gap-3">
                <span className="text-green-400 mt-1">✓</span>
                <span>{practice}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mb-20">
        <h2 className="text-3xl font-black mb-8">Certifications</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { name: "SOC 2 Type II", status: "Certified" },
            { name: "GDPR", status: "Compliant" },
            { name: "HIPAA", status: "Ready" },
            { name: "ISO 27001", status: "In Progress" }
          ].map((cert) => (
            <div key={cert.name} className="bg-white/5 rounded-xl p-6 border border-white/10 text-center">
              <h3 className="text-xl font-bold mb-2">{cert.name}</h3>
              <span className="text-green-400 text-sm">{cert.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="text-center bg-gradient-to-r from-purple-600/10 to-blue-600/10 rounded-2xl p-12 border border-purple-500/20">
        <h2 className="text-3xl font-black mb-4">Enterprise Security</h2>
        <p className="text-white/70 mb-8 max-w-2xl mx-auto">
          Need custom security requirements? Contact our team for enterprise security options.
        </p>
        <Link
          href="mailto:security@astraeus.ai"
          className="inline-block px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold"
        >
          Contact Security Team
        </Link>
      </section>
    </main>
  )
}
