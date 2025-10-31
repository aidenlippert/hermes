"use client"

import { useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api"

const CREDIT_PACKAGES = [
  { amount: 10, price: 10, bonus: 0, popular: false },
  { amount: 50, price: 45, bonus: 5, popular: true },
  { amount: 100, price: 85, bonus: 15, popular: false },
  { amount: 500, price: 400, bonus: 100, popular: false },
]

const PAYMENT_PROVIDERS = [
  { id: "stripe", name: "Credit Card", icon: "💳", description: "Visa, Mastercard, Amex" },
  { id: "paypal", name: "PayPal", icon: "🅿️", description: "Fast & secure" },
  { id: "crypto", name: "Crypto", icon: "₿", description: "Bitcoin, Ethereum" },
]

export default function PurchaseCreditsPage() {
  const [selectedPackage, setSelectedPackage] = useState(CREDIT_PACKAGES[1])
  const [selectedProvider, setSelectedProvider] = useState(PAYMENT_PROVIDERS[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handlePurchase = async () => {
    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem("token")
      if (!token) {
        setError("Please login to purchase credits")
        return
      }

      await api.payments.purchaseCredits(
        selectedPackage.amount + selectedPackage.bonus,
        selectedProvider.id,
        token
      )

      setSuccess(true)
      setTimeout(() => {
        window.location.href = "/credits/dashboard"
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Purchase failed. Please try again.")
    } finally {
      setLoading(false)
    }
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
        <Link href="/credits/dashboard" className="text-sm text-white/60 hover:text-white">View Balance</Link>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-white text-4xl font-black tracking-[-0.033em] mb-4">Purchase Credits</h1>
          <p className="text-white/80 text-lg">Credits are used to execute agents and orchestrate workflows</p>
        </div>

        {success && (
          <div className="mb-6 rounded border border-green-500/20 bg-green-500/10 p-4 text-center">
            <p className="text-green-400 font-bold">✅ Purchase successful! Redirecting...</p>
          </div>
        )}

        {error && (
          <div className="mb-6 rounded border border-red-500/20 bg-red-500/10 p-4 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h2 className="text-white text-xl font-bold mb-4">1. Choose Package</h2>
            <div className="space-y-3">
              {CREDIT_PACKAGES.map((pkg) => (
                <button
                  key={pkg.amount}
                  onClick={() => setSelectedPackage(pkg)}
                  className={`w-full text-left rounded border p-4 transition-all ${
                    selectedPackage.amount === pkg.amount
                      ? "border-primary bg-primary/10"
                      : "border-white/10 bg-[#1A1A1A] hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="text-white text-lg font-bold">
                        {pkg.amount + pkg.bonus} Credits
                      </div>
                      {pkg.bonus > 0 && (
                        <div className="text-primary text-sm font-bold">+{pkg.bonus} Bonus!</div>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-white text-2xl font-black">${pkg.price}</div>
                      {pkg.bonus > 0 && (
                        <div className="text-white/60 text-sm line-through">${pkg.amount}</div>
                      )}
                    </div>
                  </div>
                  {pkg.popular && (
                    <div className="inline-block rounded bg-primary px-2 py-0.5 text-white text-xs font-bold">
                      MOST POPULAR
                    </div>
                  )}
                </button>
              ))}
            </div>

            <div className="mt-6 rounded border border-white/10 bg-[#1A1A1A] p-4">
              <h3 className="text-white font-bold mb-2">💡 How Credits Work</h3>
              <ul className="text-white/60 text-sm space-y-1">
                <li>• 1 credit = $1 USD</li>
                <li>• Credits never expire</li>
                <li>• Free agents cost 0 credits</li>
                <li>• Paid agents vary (typically $0.05-$0.50)</li>
              </ul>
            </div>
          </div>

          <div>
            <h2 className="text-white text-xl font-bold mb-4">2. Payment Method</h2>
            <div className="space-y-3 mb-6">
              {PAYMENT_PROVIDERS.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => setSelectedProvider(provider)}
                  className={`w-full text-left rounded border p-4 transition-all ${
                    selectedProvider.id === provider.id
                      ? "border-primary bg-primary/10"
                      : "border-white/10 bg-[#1A1A1A] hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{provider.icon}</div>
                    <div>
                      <div className="text-white font-bold">{provider.name}</div>
                      <div className="text-white/60 text-sm">{provider.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="rounded border border-white/10 bg-[#1A1A1A] p-6">
              <h3 className="text-white text-lg font-bold mb-4">Order Summary</h3>
              <div className="space-y-2 mb-4 text-sm">
                <div className="flex justify-between text-white/60">
                  <span>Base Credits</span>
                  <span>{selectedPackage.amount} credits</span>
                </div>
                {selectedPackage.bonus > 0 && (
                  <div className="flex justify-between text-primary">
                    <span>Bonus Credits</span>
                    <span>+{selectedPackage.bonus} credits</span>
                  </div>
                )}
                <div className="border-t border-white/10 pt-2 flex justify-between text-white font-bold text-lg">
                  <span>Total</span>
                  <span>${selectedPackage.price}</span>
                </div>
              </div>

              <button
                onClick={handlePurchase}
                disabled={loading}
                className="w-full rounded h-12 bg-primary hover:opacity-90 text-white font-bold disabled:opacity-50"
              >
                {loading ? "Processing..." : `Purchase ${selectedPackage.amount + selectedPackage.bonus} Credits`}
              </button>

              <p className="text-white/40 text-xs text-center mt-4">
                Secure payment powered by {selectedProvider.name}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
