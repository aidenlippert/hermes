"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"

interface ExecutionStep {
  id: string
  step_number: number
  agent_id: string
  agent_name: string
  action: string
  input: any
  output: any
  status: string
  execution_time_ms: number
  cost: number
  quality_score: number
  token_usage: { input: number; output: number }
}

interface ExecutionPlan {
  id: string
  query: string
  status: string
  total_steps: number
  completed_steps: number
  total_cost: number
  execution_time_ms: number
  quality_score: number
  created_at: string
  completed_at?: string
  steps: ExecutionStep[]
  dag: { nodes: any[]; edges: any[] }
}

export default function ExecutionPlanDetailPage() {
  const params = useParams()
  const planId = params.id as string

  const [plan, setPlan] = useState<ExecutionPlan | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPlan()
  }, [planId])

  const loadPlan = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const data = await api.orchestration.getPlan(planId, token)
      setPlan(data)
    } catch (err) {
      console.error("Failed to load execution plan:", err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending": return "bg-gray-500/20 text-gray-400 border-gray-500/20"
      case "running": return "bg-blue-500/20 text-blue-400 border-blue-500/20"
      case "completed": return "bg-green-500/20 text-green-400 border-green-500/20"
      case "failed": return "bg-red-500/20 text-red-400 border-red-500/20"
      default: return "bg-white/10 text-white/60 border-white/10"
    }
  }

  const getQualityColor = (score: number) => {
    if (score >= 0.9) return "text-green-400"
    if (score >= 0.7) return "text-blue-400"
    if (score >= 0.5) return "text-yellow-400"
    return "text-red-400"
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Execution plan not found</div>
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
        <Link href="/orchestration/history" className="text-sm text-white/60 hover:text-white">History</Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">{plan.query}</h1>
              <p className="text-white/60">Execution Plan Details</p>
            </div>
            <span className={`rounded border px-4 py-2 text-sm font-bold ${getStatusColor(plan.status)}`}>
              {plan.status.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Progress</div>
            <div className="text-white text-3xl font-bold">{plan.completed_steps}/{plan.total_steps}</div>
            <div className="mt-2 h-2 bg-white/10 rounded overflow-hidden">
              <div
                className="h-full bg-primary"
                style={{ width: `${(plan.completed_steps / plan.total_steps) * 100}%` }}
              />
            </div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Cost</div>
            <div className="text-white text-3xl font-bold">${plan.total_cost.toFixed(2)}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Execution Time</div>
            <div className="text-white text-3xl font-bold">{(plan.execution_time_ms / 1000).toFixed(1)}s</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Quality Score</div>
            <div className={`text-3xl font-bold ${getQualityColor(plan.quality_score)}`}>
              {plan.quality_score.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Workflow Visualization</h2>
            <div className="rounded border border-white/5 bg-white/5 p-8">
              <div className="flex flex-col gap-4">
                {plan.steps && plan.steps.map((step, idx) => (
                  <div key={step.id} className="flex items-center gap-3">
                    <div className={`size-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      step.status === "completed" ? "bg-green-500/20 text-green-400" :
                      step.status === "running" ? "bg-blue-500/20 text-blue-400" :
                      step.status === "failed" ? "bg-red-500/20 text-red-400" :
                      "bg-white/10 text-white/60"
                    }`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="text-white font-bold text-sm">{step.agent_name}</div>
                      <div className="text-white/60 text-xs">{step.action}</div>
                    </div>
                    {idx < plan.steps.length - 1 && (
                      <div className="text-white/40">→</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Execution Details</h2>
            <div className="space-y-3">
              <div>
                <div className="text-white/60 text-sm">Plan ID</div>
                <div className="text-white font-mono text-sm">{plan.id}</div>
              </div>
              <div>
                <div className="text-white/60 text-sm">Created</div>
                <div className="text-white">{new Date(plan.created_at).toLocaleString()}</div>
              </div>
              {plan.completed_at && (
                <div>
                  <div className="text-white/60 text-sm">Completed</div>
                  <div className="text-green-400">{new Date(plan.completed_at).toLocaleString()}</div>
                </div>
              )}
              <div>
                <div className="text-white/60 text-sm">Total Tokens</div>
                <div className="text-white">
                  {plan.steps?.reduce((sum, s) => sum + (s.token_usage?.input || 0) + (s.token_usage?.output || 0), 0).toLocaleString() || 0}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          <h2 className="text-white text-xl font-bold mb-4">Step-by-Step Breakdown</h2>
          <div className="space-y-3">
            {plan.steps && plan.steps.map((step) => (
              <div key={step.id} className="rounded border border-white/5 bg-white/5 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="text-white font-bold">Step {step.step_number}: {step.agent_name}</div>
                    <span className={`rounded px-2 py-0.5 text-xs font-bold ${getStatusColor(step.status)}`}>
                      {step.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-white/60">{step.execution_time_ms}ms</span>
                    <span className="text-white/60">${step.cost.toFixed(3)}</span>
                    <span className={getQualityColor(step.quality_score)}>
                      Q: {step.quality_score.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="text-white/80 text-sm mb-2">{step.action}</div>
                <div className="grid md:grid-cols-2 gap-3">
                  <div className="rounded border border-white/5 bg-white/5 p-3">
                    <div className="text-white/60 text-xs mb-1">Input</div>
                    <pre className="text-white/80 text-xs overflow-auto max-h-32">
                      {JSON.stringify(step.input, null, 2)}
                    </pre>
                  </div>
                  {step.output && (
                    <div className="rounded border border-white/5 bg-white/5 p-3">
                      <div className="text-white/60 text-xs mb-1">Output</div>
                      <pre className="text-white/80 text-xs overflow-auto max-h-32">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
                {step.token_usage && (
                  <div className="mt-2 text-xs text-white/40">
                    Tokens: {step.token_usage.input} in / {step.token_usage.output} out
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
