"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { api } from "@/lib/api"

interface Transaction {
  id: string
  transaction_type: string
  amount: number
  balance_after: number
  description: string
  created_at: string
  status: string
}

export default function CreditsDashboard() {
  const [balance, setBalance] = useState(0)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      const [balanceData, transData] = await Promise.all([
        api.payments.getBalance(token),
        api.payments.getTransactions(token)
      ])

      setBalance(balanceData.balance)
      setTransactions(transData.transactions || [])
    } catch (err) {
      console.error("Failed to load data:", err)
    } finally {
      setLoading(false)
    }
  }

  const filteredTransactions = transactions.filter(t => {
    if (filter === "all") return true
    return t.transaction_type === filter
  })

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case "purchase": return "💳"
      case "usage": return "⚡"
      case "refund": return "↩️"
      case "bonus": return "🎁"
      default: return "•"
    }
  }

  const getTransactionColor = (type: string) => {
    switch (type) {
      case "purchase": return "text-green-400"
      case "usage": return "text-blue-400"
      case "refund": return "text-yellow-400"
      case "bonus": return "text-purple-400"
      default: return "text-white/60"
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
        <Link href="/payments/purchase-credits" className="rounded h-10 px-4 bg-primary hover:opacity-90 text-white text-sm font-bold flex items-center">
          Buy Credits
        </Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Credits Dashboard</h1>
          <p className="text-white/60">Manage your ASTRAEUS credits and view transaction history</p>
        </div>

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-8 mb-8 text-center">
          <div className="text-white/60 text-sm mb-2">Current Balance</div>
          <div className="text-white text-6xl font-black mb-2">{balance.toFixed(2)}</div>
          <div className="text-white/40 text-sm">CREDITS</div>
          <div className="mt-6">
            <Link href="/payments/purchase-credits" className="inline-flex rounded h-12 px-6 bg-primary hover:opacity-90 text-white font-bold items-center">
              Purchase More Credits
            </Link>
          </div>
        </div>

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-white text-xl font-bold">Transaction History</h2>
            <div className="flex gap-2">
              {["all", "purchase", "usage", "refund"].map((f) => (
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

          {filteredTransactions.length === 0 ? (
            <div className="text-center py-12 text-white/40">
              No transactions yet. <Link href="/payments/purchase-credits" className="text-primary hover:underline">Purchase credits</Link> to get started!
            </div>
          ) : (
            <div className="space-y-2">
              {filteredTransactions.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-4 hover:border-white/10 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">{getTransactionIcon(t.transaction_type)}</div>
                    <div>
                      <div className="text-white font-bold">{t.description}</div>
                      <div className="text-white/40 text-sm">
                        {new Date(t.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${getTransactionColor(t.transaction_type)}`}>
                      {t.amount >= 0 ? "+" : ""}{t.amount.toFixed(2)}
                    </div>
                    <div className="text-white/40 text-sm">
                      Balance: {t.balance_after.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Purchased</div>
            <div className="text-white text-2xl font-bold">
              {transactions.filter(t => t.transaction_type === "purchase").reduce((sum, t) => sum + t.amount, 0).toFixed(2)}
            </div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Total Used</div>
            <div className="text-white text-2xl font-bold">
              {Math.abs(transactions.filter(t => t.transaction_type === "usage").reduce((sum, t) => sum + t.amount, 0)).toFixed(2)}
            </div>
          </div>
          <div className="rounded border border-white/10 bg-[#1A1A1A] p-4">
            <div className="text-white/60 text-sm mb-1">Transactions</div>
            <div className="text-white text-2xl font-bold">{transactions.length}</div>
          </div>
        </div>
      </main>
    </div>
  )
}
