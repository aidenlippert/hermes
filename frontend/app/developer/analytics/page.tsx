"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  LayoutDashboard,
  Bot,
  CreditCard,
  Key,
  FileText,
  TrendingUp,
  Clock,
  AlertCircle,
  Download
} from "lucide-react"

interface AnalyticsData {
  revenue: {
    total: number
    change: string
  }
  activeAgents: {
    total: number
    change: string
  }
  avgLatency: {
    value: number
    change: string
  }
  errorRate: {
    value: number
    change: string
  }
  invocationsChart: {
    total: string
    data: Array<{ timestamp: string; calls: number }>
  }
  topAgents: Array<{
    name: string
    calls: number
    percentage: number
  }>
}

type TimeRange = "24h" | "7d" | "30d" | "90d" | "custom"

const StatCard = ({
  title,
  value,
  change,
  icon: Icon,
  isError = false
}: {
  title: string
  value: string
  change: string
  icon: any
  isError?: boolean
}) => (
  <div className={`flex flex-col gap-3 rounded-xl p-6 border ${isError ? 'border-red-500/30' : 'border-white/10'} bg-white/5`}>
    <div className="flex items-center justify-between">
      <p className="text-white/70 text-sm font-medium">{title}</p>
      <Icon className={`w-5 h-5 ${isError ? 'text-red-400' : 'text-purple-400'}`} />
    </div>
    <p className={`text-3xl font-bold ${isError ? 'text-red-400' : 'text-white'}`}>{value}</p>
    <p className={`text-sm font-medium ${
      isError ? 'text-red-400' :
      change.startsWith('+') ? 'text-green-400' : 'text-orange-400'
    }`}>
      {change} from previous period
    </p>
  </div>
)

const TimeRangeChip = ({
  label,
  value,
  active,
  onClick
}: {
  label: string
  value: TimeRange
  active: boolean
  onClick: (value: TimeRange) => void
}) => (
  <button
    onClick={() => onClick(value)}
    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      active
        ? 'bg-purple-600 text-white'
        : 'bg-white/5 text-white/70 hover:bg-white/10'
    }`}
  >
    {label}
  </button>
)

export default function DeveloperAnalytics() {
  const [timeRange, setTimeRange] = useState<TimeRange>("30d")
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/developers/me/analytics?range=${timeRange}`,
        {
          headers: {
            'Content-Type': 'application/json',
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAnalyticsData(data)
      } else {
        setAnalyticsData(getMockData())
      }
    } catch (error) {
      console.error("Failed to fetch analytics:", error)
      setAnalyticsData(getMockData())
    } finally {
      setLoading(false)
    }
  }

  const getMockData = (): AnalyticsData => ({
    revenue: {
      total: 14780.50,
      change: "+12.5%"
    },
    activeAgents: {
      total: 128,
      change: "+8.3%"
    },
    avgLatency: {
      value: 112,
      change: "-3.2%"
    },
    errorRate: {
      value: 1.2,
      change: "+0.3%"
    },
    invocationsChart: {
      total: "1.2M",
      data: generateMockChartData()
    },
    topAgents: [
      { name: "QueryProcessor-v3", calls: 320000, percentage: 36 },
      { name: "ImageAnalyzer-Pro", calls: 280000, percentage: 31 },
      { name: "TranslationBot", calls: 150000, percentage: 17 },
      { name: "CodeReviewer-AI", calls: 90000, percentage: 10 },
      { name: "DataMiner-v2", calls: 50000, percentage: 6 }
    ]
  })

  const generateMockChartData = () => {
    const data = []
    const now = Date.now()
    const days = timeRange === "24h" ? 1 : timeRange === "7d" ? 7 : timeRange === "30d" ? 30 : 90

    for (let i = days; i >= 0; i--) {
      data.push({
        timestamp: new Date(now - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        calls: Math.floor(Math.random() * 50000) + 30000
      })
    }
    return data
  }

  const handleExport = () => {
    const csvData = [
      ['Metric', 'Value', 'Change'],
      ['Total Revenue', `$${analyticsData?.revenue.total}`, analyticsData?.revenue.change || ''],
      ['Active Agents', analyticsData?.activeAgents.total.toString() || '', analyticsData?.activeAgents.change || ''],
      ['Avg Latency', `${analyticsData?.avgLatency.value}ms`, analyticsData?.avgLatency.change || ''],
      ['Error Rate', `${analyticsData?.errorRate.value}%`, analyticsData?.errorRate.change || ''],
    ]

    const csv = csvData.map(row => row.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-[#0a0a0a] items-center justify-center">
        <div className="text-white text-xl">Loading analytics...</div>
      </div>
    )
  }

  const maxCalls = Math.max(...(analyticsData?.topAgents.map(a => a.calls) || [1]))

  return (
    <div className="flex min-h-screen bg-[#0a0a0a]">
      <aside className="w-64 bg-[#111111] border-r border-white/10 p-4 flex flex-col">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-white font-bold">ASTRAEUS</h1>
            <p className="text-white/50 text-xs">Developer Portal</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          <Link
            href="/developer"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors"
          >
            <LayoutDashboard className="w-5 h-5" />
            <span className="text-sm font-medium">Dashboard</span>
          </Link>
          <Link
            href="/my-agents"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors"
          >
            <Bot className="w-5 h-5" />
            <span className="text-sm font-medium">My Agents</span>
          </Link>
          <Link
            href="/settings/billing"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors"
          >
            <CreditCard className="w-5 h-5" />
            <span className="text-sm font-medium">Billing</span>
          </Link>
          <Link
            href="/developer/api-docs"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors"
          >
            <Key className="w-5 h-5" />
            <span className="text-sm font-medium">API Keys</span>
          </Link>
          <Link
            href="/developer/guide"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors"
          >
            <FileText className="w-5 h-5" />
            <span className="text-sm font-medium">Documentation</span>
          </Link>
        </nav>

        <div className="mt-auto pt-4 border-t border-white/10">
          <div className="px-3 py-2 bg-purple-600/10 border border-purple-500/30 rounded-lg">
            <p className="text-purple-400 text-xs font-medium">Pro Plan</p>
            <p className="text-white/70 text-xs mt-1">$49/month</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-black text-white mb-2">Developer Analytics</h1>
              <p className="text-white/70">Monitor your agent performance and revenue</p>
            </div>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white font-medium transition-colors"
            >
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>

          <div className="flex gap-2 mb-8">
            <TimeRangeChip label="24 Hours" value="24h" active={timeRange === "24h"} onClick={setTimeRange} />
            <TimeRangeChip label="7 Days" value="7d" active={timeRange === "7d"} onClick={setTimeRange} />
            <TimeRangeChip label="30 Days" value="30d" active={timeRange === "30d"} onClick={setTimeRange} />
            <TimeRangeChip label="90 Days" value="90d" active={timeRange === "90d"} onClick={setTimeRange} />
            <TimeRangeChip label="Custom" value="custom" active={timeRange === "custom"} onClick={setTimeRange} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Revenue"
              value={`$${analyticsData?.revenue.total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              change={analyticsData?.revenue.change || "+0%"}
              icon={TrendingUp}
            />
            <StatCard
              title="Active Agents"
              value={analyticsData?.activeAgents.total.toString() || "0"}
              change={analyticsData?.activeAgents.change || "+0%"}
              icon={Bot}
            />
            <StatCard
              title="Avg Latency"
              value={`${analyticsData?.avgLatency.value}ms`}
              change={analyticsData?.avgLatency.change || "+0%"}
              icon={Clock}
            />
            <StatCard
              title="Error Rate"
              value={`${analyticsData?.errorRate.value}%`}
              change={analyticsData?.errorRate.change || "+0%"}
              icon={AlertCircle}
              isError
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-white">API Invocations</h2>
                  <p className="text-white/50 text-sm mt-1">
                    {analyticsData?.invocationsChart.total} total calls
                  </p>
                </div>
              </div>
              <div className="h-64 flex items-end gap-1">
                {analyticsData?.invocationsChart.data.slice(-30).map((point, i) => {
                  const height = (point.calls / 60000) * 100
                  return (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-t from-purple-600 to-purple-400 rounded-t hover:opacity-80 transition-opacity cursor-pointer"
                      style={{ height: `${height}%` }}
                      title={`${point.timestamp}: ${point.calls.toLocaleString()} calls`}
                    />
                  )
                })}
              </div>
              <div className="flex justify-between mt-4 text-white/50 text-xs">
                <span>{analyticsData?.invocationsChart.data[0]?.timestamp}</span>
                <span>Today</span>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-white">Top 5 Agents</h2>
                <p className="text-white/50 text-sm mt-1">
                  {analyticsData?.topAgents.reduce((sum, a) => sum + a.calls, 0).toLocaleString()} total calls
                </p>
              </div>
              <div className="space-y-4">
                {analyticsData?.topAgents.map((agent, i) => (
                  <div key={i}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white text-sm font-medium">{agent.name}</span>
                      <span className="text-white/70 text-sm">{agent.calls.toLocaleString()} calls</span>
                    </div>
                    <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-600 to-pink-600 rounded-full transition-all duration-500"
                        style={{ width: `${(agent.calls / maxCalls) * 100}%` }}
                      />
                    </div>
                    <p className="text-white/50 text-xs mt-1">{agent.percentage}% of total</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-6">
            <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                href="/my-agents/create"
                className="flex items-center gap-3 p-4 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
              >
                <Bot className="w-6 h-6 text-purple-400" />
                <div>
                  <p className="text-white font-medium">Publish New Agent</p>
                  <p className="text-white/50 text-sm">Add to marketplace</p>
                </div>
              </Link>
              <Link
                href="/developer/workflow-builder"
                className="flex items-center gap-3 p-4 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
              >
                <FileText className="w-6 h-6 text-purple-400" />
                <div>
                  <p className="text-white font-medium">Build Workflow</p>
                  <p className="text-white/50 text-sm">Create orchestration</p>
                </div>
              </Link>
              <Link
                href="/developer/api-docs"
                className="flex items-center gap-3 p-4 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
              >
                <Key className="w-6 h-6 text-purple-400" />
                <div>
                  <p className="text-white font-medium">Generate API Key</p>
                  <p className="text-white/50 text-sm">Access credentials</p>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
