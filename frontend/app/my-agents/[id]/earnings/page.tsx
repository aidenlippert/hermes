"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"

interface Earnings {
  total_revenue: number
  total_calls: number
  average_per_call: number
  revenue_trend: { date: string; revenue: number; calls: number }[]
  top_clients: { user_id: string; revenue: number; calls: number }[]
  transactions: { id: string; amount: number; user_id: string; created_at: string; description: string }[]
  payout_history: { id: string; amount: number; status: string; created_at: string; paid_at?: string }[]
}

export default function AgentEarningsPage() {
  const params = useParams()
  const agentId = params.id as string

  const [earnings, setEarnings] = useState<Earnings | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState("30d")

  useEffect(() => {
    loadEarnings()
  }, [agentId, timeRange])

  const loadEarnings = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const data = await api.analytics.getAgentAnalytics(agentId, token)
      setEarnings(data)
    } catch (err) {
      console.error("Failed to load earnings:", err)
    } finally {
      setLoading(false)
    }
  }

  const getPayoutStatusColor = (status: string) => {
    switch (status) {
      case "pending": return "bg-yellow-500/20 text-yellow-400"
      case "processing": return "bg-blue-500/20 text-blue-400"
      case "completed": return "bg-green-500/20 text-green-400"
      case "failed": return "bg-red-500/20 text-red-400"
      default: return "bg-white/10 text-white/60"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    )
  }

  if (!earnings) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">No earnings data available</div>
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
          <Link href={`/my-agents/${agentId}/settings`} className="text-sm text-white/60 hover:text-white">Settings</Link>
          <Link href={`/my-agents/${agentId}/analytics`} className="text-sm text-white/60 hover:text-white">Analytics</Link>
          <Link href="/my-agents" className="text-sm text-white/60 hover:text-white">My Agents</Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Agent Earnings</h1>
            <p className="text-white/60">Revenue and payout information</p>
          </div>
          <div className="flex gap-2">
            {["7d", "30d", "90d", "all"].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`rounded px-3 py-1.5 text-sm font-bold transition-all ${
                  timeRange === range
                    ? "bg-primary text-white"
                    : "bg-white/10 text-white/60 hover:text-white"
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Revenue</div>
            <div className="text-white text-3xl font-bold">${earnings.total_revenue?.toFixed(2) || "0.00"}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Calls</div>
            <div className="text-white text-3xl font-bold">{earnings.total_calls?.toLocaleString() || 0}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Avg Per Call</div>
            <div className="text-white text-3xl font-bold">${earnings.average_per_call?.toFixed(2) || "0.00"}</div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Revenue Trend</h2>
            {earnings.revenue_trend && earnings.revenue_trend.length > 0 ? (
              <div className="space-y-2">
                {earnings.revenue_trend.map((day, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="text-white/60 text-sm w-24">{new Date(day.date).toLocaleDateString()}</div>
                    <div className="flex-1 h-8 bg-white/5 rounded overflow-hidden">
                      <div
                        className="h-full bg-green-500"
                        style={{ width: `${(day.revenue / Math.max(...earnings.revenue_trend.map(d => d.revenue))) * 100}%` }}
                      />
                    </div>
                    <div className="text-white font-bold w-20 text-right">${day.revenue.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No revenue data available</div>
            )}
          </div>

          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Top Clients</h2>
            {earnings.top_clients && earnings.top_clients.length > 0 ? (
              <div className="space-y-3">
                {earnings.top_clients.map((client, idx) => (
                  <div key={idx} className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-3">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : "👤"}</div>
                      <div>
                        <div className="text-white font-mono text-sm">{client.user_id.slice(0, 8)}...</div>
                        <div className="text-white/60 text-xs">{client.calls} calls</div>
                      </div>
                    </div>
                    <div className="text-green-400 font-bold">${client.revenue.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No client data available</div>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Recent Transactions</h2>
            {earnings.transactions && earnings.transactions.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {earnings.transactions.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-3">
                    <div>
                      <div className="text-white text-sm">{tx.description}</div>
                      <div className="text-white/40 text-xs">{new Date(tx.created_at).toLocaleString()}</div>
                    </div>
                    <div className="text-green-400 font-bold">+${tx.amount.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No transactions yet</div>
            )}
          </div>

          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white text-xl font-bold">Payout History</h2>
              <button className="rounded h-8 px-3 bg-primary hover:opacity-90 text-white text-sm font-bold">
                Request Payout
              </button>
            </div>
            {earnings.payout_history && earnings.payout_history.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {earnings.payout_history.map((payout) => (
                  <div key={payout.id} className="rounded border border-white/5 bg-white/5 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-white font-bold">${payout.amount.toFixed(2)}</div>
                      <span className={`rounded px-2 py-0.5 text-xs font-bold ${getPayoutStatusColor(payout.status)}`}>
                        {payout.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-white/60 text-xs">
                      Requested: {new Date(payout.created_at).toLocaleDateString()}
                    </div>
                    {payout.paid_at && (
                      <div className="text-green-400 text-xs">
                        Paid: {new Date(payout.paid_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No payouts yet</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
