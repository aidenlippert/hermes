"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
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
  completed_at?: string
}

export default function MyContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")

  useEffect(() => {
    loadContracts()
  }, [])

  const loadContracts = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const data = await api.contracts.list(token)
      setContracts(data.contracts || [])
    } catch (err) {
      console.error("Failed to load contracts:", err)
    } finally {
      setLoading(false)
    }
  }

  const filteredContracts = contracts.filter(c => {
    if (filter === "all") return true
    return c.status === filter
  })

  const totalBudget = contracts.reduce((sum, c) => sum + c.budget, 0)
  const totalEscrow = contracts.reduce((sum, c) => sum + c.escrow_amount, 0)
  const completedCount = contracts.filter(c => c.status === "completed").length

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft": return "bg-gray-500/20 text-gray-400"
      case "active": return "bg-blue-500/20 text-blue-400"
      case "completed": return "bg-green-500/20 text-green-400"
      case "disputed": return "bg-red-500/20 text-red-400"
      case "cancelled": return "bg-gray-500/20 text-gray-400"
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
        <Link href="/contracts/create" className="rounded h-10 px-4 bg-primary hover:opacity-90 text-white text-sm font-bold flex items-center">
          Create Contract
        </Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">My Contracts</h1>
          <p className="text-white/60">Manage your contracts and escrow payments</p>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Contracts</div>
            <div className="text-white text-3xl font-bold">{contracts.length}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Budget</div>
            <div className="text-white text-3xl font-bold">${totalBudget.toLocaleString()}</div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Completed</div>
            <div className="text-white text-3xl font-bold">{completedCount}</div>
          </div>
        </div>

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-white text-xl font-bold">All Contracts</h2>
            <div className="flex gap-2">
              {["all", "draft", "active", "completed", "disputed"].map((f) => (
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

          {filteredContracts.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-white/40 mb-4">No contracts yet</div>
              <Link href="/contracts/create" className="inline-flex rounded h-10 px-4 bg-primary hover:opacity-90 text-white font-bold items-center">
                Create Your First Contract
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredContracts.map((contract) => (
                <Link
                  key={contract.id}
                  href={`/contracts/${contract.id}`}
                  className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-4 hover:border-primary hover:bg-primary/5 transition-all group"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="text-white font-bold group-hover:text-primary">{contract.title}</div>
                      <span className={`rounded px-2 py-0.5 text-xs font-bold ${getStatusColor(contract.status)}`}>
                        {contract.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-white/60 text-sm mb-2">{contract.description}</div>
                    <div className="flex items-center gap-4 text-xs text-white/40">
                      <span>Budget: ${contract.budget.toLocaleString()}</span>
                      <span>Escrow: ${contract.escrow_amount.toLocaleString()}</span>
                      <span>Created: {new Date(contract.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white text-lg font-bold">${contract.budget.toLocaleString()}</div>
                    {contract.completed_at && (
                      <div className="text-green-400 text-sm">Completed {new Date(contract.completed_at).toLocaleDateString()}</div>
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
