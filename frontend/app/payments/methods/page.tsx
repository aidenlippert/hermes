"use client"

import { useState, useEffect } from "react"
import Link from "next/link"

interface PaymentMethod {
  id: string
  type: string
  last4: string
  brand: string
  exp_month: number
  exp_year: number
  is_default: boolean
  created_at: string
}

export default function PaymentMethodsPage() {
  const [methods, setMethods] = useState<PaymentMethod[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)

  useEffect(() => {
    loadMethods()
  }, [])

  const loadMethods = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        window.location.href = "/auth/login"
        return
      }

      setMethods([])
    } catch (err) {
      console.error("Failed to load payment methods:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleSetDefault = async (methodId: string) => {
    try {
      const token = localStorage.getItem("token")
      if (!token) return

      setMethods(methods.map(m => ({ ...m, is_default: m.id === methodId })))
    } catch (err) {
      console.error("Failed to set default method:", err)
    }
  }

  const handleDelete = async (methodId: string) => {
    if (!confirm("Are you sure you want to delete this payment method?")) {
      return
    }

    try {
      const token = localStorage.getItem("token")
      if (!token) return

      setMethods(methods.filter(m => m.id !== methodId))
    } catch (err) {
      console.error("Failed to delete payment method:", err)
    }
  }

  const getCardIcon = (brand: string) => {
    switch (brand.toLowerCase()) {
      case "visa": return "💳"
      case "mastercard": return "💳"
      case "amex": return "💳"
      case "paypal": return "🅿️"
      default: return "💳"
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
        <Link href="/credits/dashboard" className="text-sm text-white/60 hover:text-white">Credits</Link>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-white text-3xl font-black tracking-[-0.033em] mb-2">Payment Methods</h1>
            <p className="text-white/60">Manage your saved payment methods</p>
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="rounded h-10 px-4 bg-primary hover:opacity-90 text-white text-sm font-bold"
          >
            Add Payment Method
          </button>
        </div>

        {showAddForm && (
          <div className="mb-6 rounded border border-white/10 bg-[#1A1A1A] p-6">
            <h2 className="text-white text-xl font-bold mb-4">Add New Payment Method</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-white/80 text-sm font-bold mb-2">Card Number</label>
                <input
                  type="text"
                  placeholder="1234 5678 9012 3456"
                  className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                />
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-white/80 text-sm font-bold mb-2">Expiry Month</label>
                  <input
                    type="text"
                    placeholder="MM"
                    className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-white/80 text-sm font-bold mb-2">Expiry Year</label>
                  <input
                    type="text"
                    placeholder="YYYY"
                    className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-white/80 text-sm font-bold mb-2">CVV</label>
                  <input
                    type="text"
                    placeholder="123"
                    className="w-full rounded border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-white/40 focus:border-primary focus:outline-none"
                  />
                </div>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 rounded h-10 bg-white/10 hover:bg-white/20 text-white font-bold"
                >
                  Cancel
                </button>
                <button className="flex-1 rounded h-10 bg-primary hover:opacity-90 text-white font-bold">
                  Add Card
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
          <h2 className="text-white text-xl font-bold mb-4">Saved Payment Methods</h2>

          {methods.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-white/40 mb-4">No payment methods saved</div>
              <button
                onClick={() => setShowAddForm(true)}
                className="inline-flex rounded h-10 px-4 bg-primary hover:opacity-90 text-white font-bold items-center"
              >
                Add Your First Payment Method
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {methods.map((method) => (
                <div
                  key={method.id}
                  className="flex items-center justify-between rounded border border-white/5 bg-white/5 p-4 hover:border-white/10 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">{getCardIcon(method.brand)}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <div className="text-white font-bold">
                          {method.brand} •••• {method.last4}
                        </div>
                        {method.is_default && (
                          <span className="rounded bg-primary px-2 py-0.5 text-white text-xs font-bold">
                            DEFAULT
                          </span>
                        )}
                      </div>
                      <div className="text-white/60 text-sm">
                        Expires {method.exp_month}/{method.exp_year}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!method.is_default && (
                      <button
                        onClick={() => handleSetDefault(method.id)}
                        className="rounded h-8 px-3 bg-white/10 hover:bg-white/20 text-white text-sm font-bold"
                      >
                        Set as Default
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(method.id)}
                      className="rounded h-8 px-3 bg-red-500 hover:opacity-90 text-white text-sm font-bold"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 rounded border border-white/10 bg-[#1A1A1A] p-4">
          <h3 className="text-white font-bold mb-2">🔒 Secure Payment Processing</h3>
          <p className="text-white/60 text-sm">
            Your payment information is encrypted and securely processed by our payment partners.
            We never store your full card details on our servers.
          </p>
        </div>
      </main>
    </div>
  )
}
