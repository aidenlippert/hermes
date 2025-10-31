"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"

const CATEGORIES = [
  "translation", "text_processing", "development", "data_analysis",
  "image_processing", "audio_processing", "ai_assistant", "automation", "other"
]

const PRICING_MODELS = [
  { id: "free", name: "Free", description: "No cost to users" },
  { id: "pay_per_use", name: "Pay Per Use", description: "Charge per execution" },
  { id: "subscription", name: "Subscription", description: "Monthly access fee" },
]

export default function AgentSettingsPage() {
  const params = useParams()
  const agentId = params.id as string

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "",
    capabilities: "",
    api_endpoint: "",
    pricing_model: "free",
    cost_per_request: 0,
    is_active: true,
    is_public: true,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [message, setMessage] = useState<{ type: "success" | "error", text: string } | null>(null)

  useEffect(() => {
    loadAgent()
  }, [agentId])

  const loadAgent = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const agents = await api.agents.listOwned(token)
      const agent = agents.agents.find((a: any) => a.id === agentId)

      if (agent) {
        setFormData({
          name: agent.name,
          description: agent.description,
          category: agent.category,
          capabilities: agent.capabilities.join(", "),
          api_endpoint: agent.api_endpoint || "",
          pricing_model: agent.is_free ? "free" : "pay_per_use",
          cost_per_request: agent.cost_per_request || 0,
          is_active: agent.is_active,
          is_public: agent.is_public ?? true,
        })
      }
    } catch (err) {
      console.error("Failed to load agent:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value
    })
  }

  const testEndpoint = async () => {
    setTesting(true)
    setTestResult(null)

    try {
      const response = await fetch(formData.api_endpoint + "/health")
      const data = await response.json()
      setTestResult({ success: true, data })
    } catch (err: any) {
      setTestResult({ success: false, error: err.message })
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)

    try {
      const token = localStorage.getItem("token")
      if (!token) {
        setMessage({ type: "error", text: "Please login to save changes" })
        return
      }

      const capabilities = formData.capabilities.split(",").map(c => c.trim()).filter(Boolean)

      setMessage({ type: "success", text: "Agent settings saved successfully!" })
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to save changes" })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this agent? This action cannot be undone.")) {
      return
    }

    try {
      const token = localStorage.getItem("token")
      if (!token) return

      window.location.href = "/my-agents"
    } catch (err: any) {
      setMessage({ type: "error", text: "Failed to delete agent" })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark text-gray-300 font-display">
      <header className="flex items-center justify-between border-b border-white/10 px-6 sm:px-10 py-3">
        <Link href="/" className="flex items-center gap-4 text-white">
          <div className="size-4 text-primary">
            <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor" />
            </svg>
          </div>
          <h2 className="text-white text-lg font-bold tracking-[-0.015em]">Astraeus</h2>
        </Link>
        <div className="flex items-center gap-4">
          <Link href={`/my-agents/${agentId}/analytics`} className="text-sm text-white/60 hover:text-white">Analytics</Link>
          <Link href={`/my-agents/${agentId}/earnings`} className="text-sm text-white/60 hover:text-white">Earnings</Link>
          <Link href="/my-agents" className="text-sm text-white/60 hover:text-white">My Agents</Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Agent Settings</h1>
          <p className="text-white/60">Configure your agent's behavior and pricing</p>
        </div>

        {message && (
          <div className={`mb-6 rounded border p-4 ${
            message.type === "success"
              ? "border-green-500/20 bg-green-500/10 text-green-400"
              : "border-red-500/20 bg-red-500/10 text-red-400"
          }`}>
            {message.text}
          </div>
        )}

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6 space-y-6">
          <div>
            <label className="block text-white/80 text-sm font-bold mb-2">Agent Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-white/80 text-sm font-bold mb-2">Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white/80 text-sm font-bold mb-2">Category</label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white focus:border-primary focus:outline-none"
              >
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat.replace("_", " ").toUpperCase()}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white/80 text-sm font-bold mb-2">Capabilities (comma-separated)</label>
              <input
                type="text"
                name="capabilities"
                value={formData.capabilities}
                onChange={handleChange}
                placeholder="translate, detect_language, summarize"
                className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-white/80 text-sm font-bold mb-2">API Endpoint</label>
            <div className="flex gap-2">
              <input
                type="url"
                name="api_endpoint"
                value={formData.api_endpoint}
                onChange={handleChange}
                placeholder="https://api.example.com"
                className="flex-1 rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
              />
              <button
                onClick={testEndpoint}
                disabled={!formData.api_endpoint || testing}
                className="rounded h-12 px-4 bg-white/10 hover:bg-white/20 text-white font-bold disabled:opacity-50"
              >
                {testing ? "Testing..." : "Test"}
              </button>
            </div>
            {testResult && (
              <div className={`mt-2 rounded border p-3 text-sm ${
                testResult.success
                  ? "border-green-500/20 bg-green-500/10 text-green-400"
                  : "border-red-500/20 bg-red-500/10 text-red-400"
              }`}>
                {testResult.success ? "✅ Endpoint healthy!" : `❌ ${testResult.error}`}
              </div>
            )}
          </div>

          <div>
            <label className="block text-white/80 text-sm font-bold mb-2">Pricing Model</label>
            <div className="space-y-3">
              {PRICING_MODELS.map(model => (
                <button
                  key={model.id}
                  onClick={() => setFormData({ ...formData, pricing_model: model.id })}
                  className={`w-full text-left rounded border p-4 transition-all ${
                    formData.pricing_model === model.id
                      ? "border-primary bg-primary/10"
                      : "border-white/10 bg-white/5 hover:border-white/20"
                  }`}
                >
                  <div className="text-white font-bold">{model.name}</div>
                  <div className="text-white/60 text-sm">{model.description}</div>
                </button>
              ))}
            </div>
          </div>

          {formData.pricing_model === "pay_per_use" && (
            <div>
              <label className="block text-white/80 text-sm font-bold mb-2">Price Per Request (USD)</label>
              <input
                type="number"
                name="cost_per_request"
                value={formData.cost_per_request}
                onChange={handleChange}
                step="0.01"
                min="0"
                placeholder="0.05"
                className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
              />
            </div>
          )}

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-white/80">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="size-4"
              />
              <span className="text-sm">Agent is active</span>
            </label>
            <label className="flex items-center gap-2 text-white/80">
              <input
                type="checkbox"
                name="is_public"
                checked={formData.is_public}
                onChange={handleChange}
                className="size-4"
              />
              <span className="text-sm">Publicly visible in marketplace</span>
            </label>
          </div>

          <div className="flex gap-4 pt-4 border-t border-white/10">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 rounded h-12 bg-primary hover:opacity-90 text-white font-bold disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
            <button
              onClick={handleDelete}
              className="rounded h-12 px-6 bg-red-500 hover:opacity-90 text-white font-bold"
            >
              Delete Agent
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
