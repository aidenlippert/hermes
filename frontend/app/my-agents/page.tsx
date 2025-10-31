"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { api } from "@/lib/api"

interface Agent {
  id: string
  name: string
  description: string
  category: string
  total_calls: number
  average_rating: number
  is_free: boolean
  cost_per_request: number
  is_active: boolean
  total_revenue?: number
}

export default function MyAgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const data = await api.agents.listOwned(token)
      setAgents(data.agents || [])
    } catch (err) {
      console.error("Failed to load agents:", err)
    } finally {
      setLoading(false)
    }
  }

  const filteredAgents = agents.filter(a => {
    if (filter === "all") return true
    if (filter === "active") return a.is_active
    if (filter === "inactive") return !a.is_active
    if (filter === "free") return a.is_free
    if (filter === "paid") return !a.is_free
    return true
  })

  const totalCalls = agents.reduce((sum, a) => sum + a.total_calls, 0)
  const totalRevenue = agents.reduce((sum, a) => sum + (a.total_revenue || 0), 0)
  const avgRating = agents.length > 0
    ? agents.reduce((sum, a) => sum + a.average_rating, 0) / agents.length
    : 0

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
        <Link href="/my-agents/create" className="rounded h-10 px-4 bg-primary hover:opacity-90 text-white text-sm font-bold flex items-center">
          Create Agent
        </Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">My Agents</h1>
          <p className="text-white/60">Manage your agents and track performance</p>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Agents</div>
            <div className="text-white text-3xl font-bold">{agents.length}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Calls</div>
            <div className="text-white text-3xl font-bold">{totalCalls.toLocaleString()}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Avg Rating</div>
            <div className="text-white text-3xl font-bold">{avgRating.toFixed(1)} ⭐</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Revenue</div>
            <div className="text-white text-3xl font-bold">${totalRevenue.toFixed(2)}</div>
          </div>
        </div>

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-white text-xl font-bold">Your Agents</h2>
            <div className="flex gap-2">
              {["all", "active", "inactive", "free", "paid"].map((f) => (
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

          {filteredAgents.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-white/40 mb-4">No agents yet</div>
              <Link href="/my-agents/create" className="inline-flex rounded h-10 px-4 bg-primary hover:opacity-90 text-white font-bold items-center">
                Create Your First Agent
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredAgents.map((agent) => (
                <Link
                  key={agent.id}
                  href={`/my-agents/${agent.id}/settings`}
                  className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-4 hover:border-primary hover:bg-primary/5 transition-all group"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`size-12 rounded-full flex items-center justify-center text-2xl ${
                      agent.is_active ? "bg-green-500/20" : "bg-red-500/20"
                    }`}>
                      {agent.is_free ? "🆓" : "💰"}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="text-white font-bold group-hover:text-primary">{agent.name}</div>
                        {!agent.is_active && (
                          <span className="rounded bg-red-500/20 px-2 py-0.5 text-red-400 text-xs font-bold">
                            INACTIVE
                          </span>
                        )}
                      </div>
                      <div className="text-white/60 text-sm">{agent.description}</div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                        <span>{agent.total_calls} calls</span>
                        <span>⭐ {agent.average_rating.toFixed(1)}</span>
                        <span>{agent.category}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white text-lg font-bold">
                      {agent.is_free ? "Free" : `$${agent.cost_per_request}/call`}
                    </div>
                    {agent.total_revenue && agent.total_revenue > 0 && (
                      <div className="text-green-400 text-sm">${agent.total_revenue.toFixed(2)} earned</div>
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
