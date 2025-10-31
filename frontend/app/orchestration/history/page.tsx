"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { api } from "@/lib/api"

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
  agents_used: string[]
}

export default function OrchestrationHistoryPage() {
  const [plans, setPlans] = useState<ExecutionPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")

  useEffect(() => {
    loadPlans()
  }, [])

  const loadPlans = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      setPlans([])
    } catch (err) {
      console.error("Failed to load orchestration history:", err)
    } finally {
      setLoading(false)
    }
  }

  const filteredPlans = plans.filter(p => {
    if (filter === "all") return true
    return p.status === filter
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending": return "bg-gray-500/20 text-gray-400"
      case "running": return "bg-blue-500/20 text-blue-400"
      case "completed": return "bg-green-500/20 text-green-400"
      case "failed": return "bg-red-500/20 text-red-400"
      default: return "bg-white/10 text-white/60"
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
        <Link href="/chat" className="text-sm text-white/60 hover:text-white">Chat</Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Orchestration History</h1>
          <p className="text-white/60">View past multi-agent execution plans</p>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Executions</div>
            <div className="text-white text-3xl font-bold">{plans.length}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Success Rate</div>
            <div className="text-white text-3xl font-bold">
              {plans.length > 0
                ? ((plans.filter(p => p.status === "completed").length / plans.length) * 100).toFixed(0)
                : 0}%
            </div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Cost</div>
            <div className="text-white text-3xl font-bold">
              ${plans.reduce((sum, p) => sum + p.total_cost, 0).toFixed(2)}
            </div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Avg Quality</div>
            <div className="text-white text-3xl font-bold">
              {plans.length > 0
                ? (plans.reduce((sum, p) => sum + p.quality_score, 0) / plans.length).toFixed(2)
                : "N/A"}
            </div>
          </div>
        </div>

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-white text-xl font-bold">Execution Plans</h2>
            <div className="flex gap-2">
              {["all", "pending", "running", "completed", "failed"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`rounded px-3 py-1.5 text-sm font-bold transition-all ${
                    filter === f
                      ? "bg-primary text-white"
                      : "bg-white/10 text-white/60 hover:text-white"
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {filteredPlans.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-white/40 mb-4">No orchestration executions yet</div>
              <Link href="/chat" className="inline-flex rounded h-10 px-4 bg-primary hover:opacity-90 text-white font-bold items-center">
                Start a Complex Task
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredPlans.map((plan) => (
                <Link
                  key={plan.id}
                  href={`/orchestration/plans/${plan.id}`}
                  className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-4 hover:border-primary hover:bg-primary/5 transition-all group"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="text-white font-bold group-hover:text-primary">{plan.query}</div>
                      <span className={`rounded px-2 py-0.5 text-xs font-bold ${getStatusColor(plan.status)}`}>
                        {plan.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-white/40">
                      <span>{plan.completed_steps}/{plan.total_steps} steps</span>
                      <span>{plan.agents_used?.length || 0} agents</span>
                      <span>{plan.execution_time_ms}ms</span>
                      <span>Quality: <span className={getQualityColor(plan.quality_score)}>{plan.quality_score.toFixed(2)}</span></span>
                      <span>{new Date(plan.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white text-lg font-bold">${plan.total_cost.toFixed(2)}</div>
                    {plan.completed_at && (
                      <div className="text-green-400 text-sm">✓ Completed</div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
