"use client"

import { useState } from "react"
import Link from "next/link"
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

export default function CreateAgentPage() {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "",
    capabilities: "",
    api_endpoint: "",
    pricing_model: "free",
    cost_per_request: 0,
    is_public: true,
  })
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const testEndpoint = async () => {
    setTesting(true)
    setTestResult(null)
    setError(null)

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

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)

    try {
      const token = localStorage.getItem("token")
      if (!token) {
        setError("Please login to create an agent")
        return
      }

      const capabilities = formData.capabilities.split(",").map(c => c.trim()).filter(Boolean)

      await api.agents.create({
        name: formData.name,
        description: formData.description,
        category: formData.category,
        capabilities,
        api_endpoint: formData.api_endpoint,
        pricing_model: formData.pricing_model,
        cost_per_request: formData.cost_per_request,
        is_public: formData.is_public,
      }, token)

      window.location.href = "/my-agents"
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create agent")
    } finally {
      setSubmitting(false)
    }
  }

  const canProceed = () => {
    if (step === 1) return formData.name && formData.description && formData.category
    if (step === 2) return formData.capabilities && formData.pricing_model
    if (step === 3) return formData.api_endpoint && testResult?.success
    return true
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
        <Link href="/my-agents" className="text-sm text-white/60 hover:text-white">My Agents</Link>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Create New Agent</h1>
          <p className="text-white/60">Publish your agent to the ASTRAEUS marketplace</p>
        </div>

        <div className="flex items-center justify-between mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center flex-1">
              <div className={`flex items-center justify-center size-10 rounded-full font-bold ${
                step >= s ? "bg-primary text-white" : "bg-white/10 text-white/40"
              }`}>
                {s}
              </div>
              {s < 4 && (
                <div className={`flex-1 h-0.5 mx-2 ${step > s ? "bg-primary" : "bg-white/10"}`} />
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-6 rounded border border-red-500/20 bg-red-500/10 p-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          {step === 1 && (
            <div className="space-y-6">
              <h2 className="text-white text-xl font-bold">Basic Information</h2>

              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">Agent Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="My Awesome Agent"
                  className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">Description *</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Describe what your agent does and how it helps users..."
                  rows={4}
                  className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">Category *</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white focus:border-primary focus:outline-none"
                >
                  <option value="">Select a category</option>
                  {CATEGORIES.map(cat => (
                    <option key={cat} value={cat}>{cat.replace("_", " ").toUpperCase()}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-white text-xl font-bold">Capabilities & Pricing</h2>

              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">Capabilities * (comma-separated)</label>
                <input
                  type="text"
                  name="capabilities"
                  value={formData.capabilities}
                  onChange={handleChange}
                  placeholder="translate, detect_language, summarize"
                  className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                />
                <p className="text-white/40 text-sm mt-1">List the actions your agent can perform</p>
              </div>

              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">Pricing Model *</label>
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
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-white text-xl font-bold">API Configuration</h2>

              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">API Endpoint *</label>
                <input
                  type="url"
                  name="api_endpoint"
                  value={formData.api_endpoint}
                  onChange={handleChange}
                  placeholder="https://api.example.com"
                  className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                />
                <p className="text-white/40 text-sm mt-1">Your agent must implement /health and /execute endpoints</p>
              </div>

              <button
                onClick={testEndpoint}
                disabled={!formData.api_endpoint || testing}
                className="rounded h-10 px-4 bg-white/10 hover:bg-white/20 text-white font-bold disabled:opacity-50"
              >
                {testing ? "Testing..." : "Test Endpoint"}
              </button>

              {testResult && (
                <div className={`rounded border p-4 ${
                  testResult.success
                    ? "border-green-500/20 bg-green-500/10"
                    : "border-red-500/20 bg-red-500/10"
                }`}>
                  <div className={testResult.success ? "text-green-400" : "text-red-400"}>
                    {testResult.success ? "✅ Endpoint healthy!" : `❌ ${testResult.error}`}
                  </div>
                  {testResult.data && (
                    <pre className="text-white/60 text-xs mt-2 overflow-auto">
                      {JSON.stringify(testResult.data, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )}

          {step === 4 && (
            <div className="space-y-6">
              <h2 className="text-white text-xl font-bold">Review & Publish</h2>

              <div className="rounded border border-white/10 bg-white/5 p-4 space-y-4">
                <div>
                  <div className="text-white/60 text-sm">Name</div>
                  <div className="text-white font-bold">{formData.name}</div>
                </div>
                <div>
                  <div className="text-white/60 text-sm">Description</div>
                  <div className="text-white">{formData.description}</div>
                </div>
                <div>
                  <div className="text-white/60 text-sm">Category</div>
                  <div className="text-white">{formData.category}</div>
                </div>
                <div>
                  <div className="text-white/60 text-sm">Capabilities</div>
                  <div className="text-white">{formData.capabilities}</div>
                </div>
                <div>
                  <div className="text-white/60 text-sm">Pricing</div>
                  <div className="text-white">
                    {formData.pricing_model === "free" ? "Free" : `$${formData.cost_per_request} per request`}
                  </div>
                </div>
                <div>
                  <div className="text-white/60 text-sm">API Endpoint</div>
                  <div className="text-white font-mono text-sm">{formData.api_endpoint}</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="size-4"
                />
                <label className="text-white/80 text-sm">Make agent publicly visible in marketplace</label>
              </div>
            </div>
          )}

          <div className="flex gap-4 mt-8">
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="flex-1 rounded h-12 bg-white/10 hover:bg-white/20 text-white font-bold"
              >
                Back
              </button>
            )}
            {step < 4 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed()}
                className="flex-1 rounded h-12 bg-primary hover:opacity-90 text-white font-bold disabled:opacity-50"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 rounded h-12 bg-primary hover:opacity-90 text-white font-bold disabled:opacity-50"
              >
                {submitting ? "Publishing..." : "Publish Agent"}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
