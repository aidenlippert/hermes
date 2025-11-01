"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { CheckCircle, Download } from "lucide-react"

interface TransactionDetails {
  transactionId: string
  credits: number
  amount: number
  date: string
}

export default function PaymentSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [transaction, setTransaction] = useState<TransactionDetails | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const transactionId = searchParams.get("transactionId")
    const credits = searchParams.get("credits")

    if (transactionId && credits) {
      fetchTransactionDetails(transactionId)
    } else {
      setTransaction({
        transactionId: transactionId || "A2A-TRX-8B4F9C2E",
        credits: parseInt(credits || "1000"),
        amount: parseFloat(searchParams.get("amount") || "100.00"),
        date: new Date().toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric"
        })
      })
      setLoading(false)
    }
  }, [searchParams])

  const fetchTransactionDetails = async (transactionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/payments/transactions/${transactionId}`,
        {
          headers: {
            "Content-Type": "application/json",
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setTransaction({
          transactionId: data.transactionId,
          credits: data.credits,
          amount: data.amount,
          date: new Date(data.createdAt).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric"
          })
        })
      } else {
        setTransaction({
          transactionId: transactionId,
          credits: parseInt(searchParams.get("credits") || "1000"),
          amount: parseFloat(searchParams.get("amount") || "100.00"),
          date: new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric"
          })
        })
      }
    } catch (error) {
      console.error("Failed to fetch transaction details:", error)
      setTransaction({
        transactionId: transactionId,
        credits: parseInt(searchParams.get("credits") || "1000"),
        amount: parseFloat(searchParams.get("amount") || "100.00"),
        date: new Date().toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric"
        })
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadReceipt = () => {
    if (!transaction) return

    const receipt = `
ASTRAEUS PAYMENT RECEIPT
========================

Transaction ID: ${transaction.transactionId}
Date: ${transaction.date}
Credits Acquired: ${transaction.credits.toLocaleString()}
Amount Paid: $${transaction.amount.toFixed(2)} USD

Thank you for your purchase!
    `.trim()

    const blob = new Blob([receipt], { type: "text/plain" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `astraeus-receipt-${transaction.transactionId}.txt`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-white text-xl">Loading transaction details...</div>
      </div>
    )
  }

  if (!transaction) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-xl mb-4">Transaction not found</p>
          <Link
            href="/developer"
            className="text-purple-400 hover:text-purple-300 transition-colors"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <div className="flex flex-col h-full">
        <header className="border-b border-white/10 px-4 sm:px-10 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-white">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 48 48">
                  <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" />
                </svg>
              </div>
              <h2 className="text-lg font-bold">Astraeus</h2>
            </div>
            <div className="flex items-center gap-8">
              <Link
                href="/developer"
                className="text-white text-sm font-medium hover:text-purple-400 transition-colors hidden sm:block"
              >
                Dashboard
              </Link>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500"></div>
            </div>
          </div>
        </header>

        <main className="flex-grow flex flex-col items-center justify-center text-center px-4 py-16 sm:py-24">
          <div className="w-full max-w-lg">
            <div className="flex justify-center mb-8">
              <div className="relative">
                <CheckCircle
                  className="w-24 h-24 text-green-400"
                  style={{
                    filter: "drop-shadow(0 0 10px rgba(34, 197, 94, 0.5)) drop-shadow(0 0 20px rgba(34, 197, 94, 0.3))"
                  }}
                />
                <div className="absolute inset-0 animate-ping opacity-20">
                  <CheckCircle className="w-24 h-24 text-green-400" />
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h1 className="text-green-400 text-4xl font-black mb-4"
                style={{
                  textShadow: "0 0 10px rgba(34, 197, 94, 0.5), 0 0 20px rgba(34, 197, 94, 0.3)"
                }}
              >
                Purchase Complete
              </h1>
              <p className="text-white/60 text-base">
                Your credits have been successfully added to your account.
              </p>
            </div>

            <div className="border-y border-white/10 my-8 py-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2">
                  <p className="text-white/60 text-sm">Credits Acquired</p>
                  <p className="text-white text-sm font-medium">
                    {transaction.credits.toLocaleString()}
                  </p>
                </div>
                <div className="flex justify-between items-center py-2">
                  <p className="text-white/60 text-sm">Amount Paid</p>
                  <p className="text-white text-sm font-medium">
                    ${transaction.amount.toFixed(2)} USD
                  </p>
                </div>
                <div className="flex justify-between items-center py-2">
                  <p className="text-white/60 text-sm">Transaction ID</p>
                  <p className="text-white text-sm font-mono">
                    {transaction.transactionId}
                  </p>
                </div>
                <div className="flex justify-between items-center py-2">
                  <p className="text-white/60 text-sm">Purchase Date</p>
                  <p className="text-white text-sm font-medium">
                    {transaction.date}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={handleDownloadReceipt}
                className="flex items-center justify-center gap-2 rounded-lg h-12 px-5 bg-white/10 hover:bg-white/20 text-white font-bold transition-colors"
              >
                <Download className="w-4 h-4" />
                Download Receipt
              </button>
              <Link
                href="/settings/billing"
                className="flex items-center justify-center rounded-lg h-12 px-5 bg-white/10 hover:bg-white/20 text-white font-bold transition-colors"
              >
                View Balance
              </Link>
              <Link
                href="/developer"
                className="flex items-center justify-center rounded-lg h-12 px-5 bg-purple-600 hover:bg-purple-700 text-white font-bold transition-colors"
              >
                Return to Dashboard
              </Link>
            </div>

            <div className="mt-8 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
              <p className="text-green-400 text-sm">
                🎉 Your account has been credited with {transaction.credits.toLocaleString()} credits.
                You can now use them to access agents in the marketplace.
              </p>
            </div>
          </div>
        </main>

        <footer className="border-t border-white/10 py-6 px-4 text-center">
          <p className="text-white/50 text-sm">
            Need help? Contact our{" "}
            <Link href="/support" className="text-purple-400 hover:text-purple-300 transition-colors">
              support team
            </Link>
            .
          </p>
        </footer>
      </div>
    </div>
  )
}
