"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"

interface Analytics {
  total_calls: number
  success_rate: number
  average_response_time: number
  average_rating: number
  total_reviews: number
  call_volume_trend: { date: string; calls: number }[]
  top_users: { user_id: string; calls: number }[]
  error_distribution: { error_type: string; count: number }[]
  reviews: { user_id: string; rating: number; comment: string; created_at: string }[]
}

export default function AgentAnalyticsPage() {
  const params = useParams()
  const agentId = params.id as string

  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState("7d")

  useEffect(() => {
    loadAnalytics()
  }, [agentId, timeRange])

  const loadAnalytics = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const data = await api.analytics.getAgentAnalytics(agentId, token)
      setAnalytics(data)
    } catch (err) {
      console.error("Failed to load analytics:", err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">No analytics data available</div>
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
          <Link href={`/my-agents/${agentId}/earnings`} className="text-sm text-white/60 hover:text-white">Earnings</Link>
          <Link href="/my-agents" className="text-sm text-white/60 hover:text-white">My Agents</Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Agent Analytics</h1>
            <p className="text-white/60">Performance metrics and user feedback</p>
          </div>
          <div className="flex gap-2">
            {["24h", "7d", "30d", "90d"].map((range) => (
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

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Calls</div>
            <div className="text-white text-3xl font-bold">{analytics.total_calls.toLocaleString()}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Success Rate</div>
            <div className="text-white text-3xl font-bold">{analytics.success_rate.toFixed(1)}%</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Avg Response Time</div>
            <div className="text-white text-3xl font-bold">{analytics.average_response_time}ms</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Average Rating</div>
            <div className="text-white text-3xl font-bold">{analytics.average_rating.toFixed(1)} ⭐</div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Call Volume Trend</h2>
            {analytics.call_volume_trend && analytics.call_volume_trend.length > 0 ? (
              <div className="space-y-2">
                {analytics.call_volume_trend.map((day, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="text-white/60 text-sm w-24">{new Date(day.date).toLocaleDateString()}</div>
                    <div className="flex-1 h-8 bg-white/5 rounded overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${(day.calls / Math.max(...analytics.call_volume_trend.map(d => d.calls))) * 100}%` }}
                      />
                    </div>
                    <div className="text-white font-bold w-16 text-right">{day.calls}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No call data available</div>
            )}
          </div>

          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Top Users</h2>
            {analytics.top_users && analytics.top_users.length > 0 ? (
              <div className="space-y-3">
                {analytics.top_users.map((user, idx) => (
                  <div key={idx} className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-3">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : "👤"}</div>
                      <div className="text-white font-mono text-sm">{user.user_id.slice(0, 8)}...</div>
                    </div>
                    <div className="text-white font-bold">{user.calls} calls</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No user data available</div>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Error Distribution</h2>
            {analytics.error_distribution && analytics.error_distribution.length > 0 ? (
              <div className="space-y-2">
                {analytics.error_distribution.map((error, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="text-white/60 text-sm flex-1">{error.error_type}</div>
                    <div className="text-red-400 font-bold">{error.count}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-green-400">No errors recorded! 🎉</div>
            )}
          </div>

          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Recent Reviews</h2>
            {analytics.reviews && analytics.reviews.length > 0 ? (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {analytics.reviews.map((review, idx) => (
                  <div key={idx} className="rounded border border-white/5 bg-white/5 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-white/60 text-sm font-mono">{review.user_id.slice(0, 8)}...</div>
                      <div className="text-yellow-400">{"⭐".repeat(review.rating)}</div>
                    </div>
                    <div className="text-white text-sm mb-1">{review.comment}</div>
                    <div className="text-white/40 text-xs">{new Date(review.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">No reviews yet</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
