"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"

interface Contract {
  id: string
  title: string
  description: string
  budget: number
  escrow_amount: number
  status: string
  client_id: string
  developer_id?: string
  agent_id?: string
  created_at: string
  updated_at: string
  completed_at?: string
  milestones?: Milestone[]
  timeline?: TimelineEvent[]
}

interface Milestone {
  id: string
  title: string
  description: string
  amount: number
  status: string
  due_date?: string
}

interface TimelineEvent {
  id: string
  event_type: string
  description: string
  timestamp: string
  user_id: string
}

export default function ContractDetailPage() {
  const params = useParams()
  const contractId = params.id as string

  const [contract, setContract] = useState<Contract | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadContract()
  }, [contractId])

  const loadContract = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const data = await api.contracts.get(contractId, token)
      setContract(data)
    } catch (err) {
      console.error("Failed to load contract:", err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft": return "bg-gray-500/20 text-gray-400 border-gray-500/20"
      case "active": return "bg-blue-500/20 text-blue-400 border-blue-500/20"
      case "completed": return "bg-green-500/20 text-green-400 border-green-500/20"
      case "disputed": return "bg-red-500/20 text-red-400 border-red-500/20"
      case "cancelled": return "bg-gray-500/20 text-gray-400 border-gray-500/20"
      default: return "bg-white/10 text-white/60 border-white/10"
    }
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case "created": return "📝"
      case "funded": return "💰"
      case "assigned": return "👤"
      case "milestone_completed": return "✅"
      case "payment_released": return "💸"
      case "disputed": return "⚠️"
      case "resolved": return "🤝"
      case "completed": return "🎉"
      default: return "•"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <div className="text-white/60">Contract not found</div>
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
        <Link href="/contracts/my-contracts" className="text-sm text-white/60 hover:text-white">My Contracts</Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">{contract.title}</h1>
              <p className="text-white/60">{contract.description}</p>
            </div>
            <span className={`rounded border px-4 py-2 text-sm font-bold ${getStatusColor(contract.status)}`}>
              {contract.status.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Budget</div>
            <div className="text-white text-3xl font-bold">${contract.budget.toLocaleString()}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Escrow Balance</div>
            <div className="text-white text-3xl font-bold">${contract.escrow_amount.toLocaleString()}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Released</div>
            <div className="text-white text-3xl font-bold">${(contract.budget - contract.escrow_amount).toLocaleString()}</div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Contract Details</h2>
            <div className="space-y-3">
              <div>
                <div className="text-white/60 text-sm">Contract ID</div>
                <div className="text-white font-mono text-sm">{contract.id}</div>
              </div>
              <div>
                <div className="text-white/60 text-sm">Created</div>
                <div className="text-white">{new Date(contract.created_at).toLocaleString()}</div>
              </div>
              <div>
                <div className="text-white/60 text-sm">Last Updated</div>
                <div className="text-white">{new Date(contract.updated_at).toLocaleString()}</div>
              </div>
              {contract.completed_at && (
                <div>
                  <div className="text-white/60 text-sm">Completed</div>
                  <div className="text-green-400">{new Date(contract.completed_at).toLocaleString()}</div>
                </div>
              )}
              {contract.agent_id && (
                <div>
                  <div className="text-white/60 text-sm">Assigned Agent</div>
                  <div className="text-white">{contract.agent_id}</div>
                </div>
              )}
            </div>

            {contract.status === "active" && (
              <div className="mt-6 space-y-2">
                <button className="w-full rounded h-10 bg-green-500 hover:opacity-90 text-white font-bold">
                  Mark as Completed
                </button>
                <button className="w-full rounded h-10 bg-red-500 hover:opacity-90 text-white font-bold">
                  Dispute Contract
                </button>
              </div>
            )}
          </div>

          <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Timeline</h2>
            {contract.timeline && contract.timeline.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {contract.timeline.map((event) => (
                  <div key={event.id} className="flex gap-3 pb-3 border-b border-white/5 last:border-0">
                    <div className="text-2xl">{getEventIcon(event.event_type)}</div>
                    <div className="flex-1">
                      <div className="text-white font-bold">{event.description}</div>
                      <div className="text-white/40 text-sm">{new Date(event.timestamp).toLocaleString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40">
                No timeline events yet
              </div>
            )}
          </div>
        </div>

        {contract.milestones && contract.milestones.length > 0 && (
          <div className="mt-6 rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Milestones</h2>
            <div className="space-y-3">
              {contract.milestones.map((milestone) => (
                <div
                  key={milestone.id}
                  className="rounded border border-white/5 bg-white/5 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-white font-bold">{milestone.title}</div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded px-2 py-0.5 text-xs font-bold ${getStatusColor(milestone.status)}`}>
                        {milestone.status}
                      </span>
                      <div className="text-white font-bold">${milestone.amount.toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="text-white/60 text-sm mb-2">{milestone.description}</div>
                  {milestone.due_date && (
                    <div className="text-white/40 text-xs">
                      Due: {new Date(milestone.due_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
