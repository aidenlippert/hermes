"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  XCircle,
  LayoutDashboard,
  Bot,
  GitBranch,
  CreditCard,
  Key,
  BookOpen,
  Settings,
  X
} from "lucide-react"

export default function PaymentFailedPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [errorMessage, setErrorMessage] = useState<string>("")
  const [errorCode, setErrorCode] = useState<string>("")

  useEffect(() => {
    const error = searchParams.get("error")
    const code = searchParams.get("code")

    setErrorMessage(error || "Your credit purchase could not be processed.")
    setErrorCode(code || "PAYMENT_DECLINED")
  }, [searchParams])

  const getErrorDetails = () => {
    switch (errorCode) {
      case "CARD_DECLINED":
        return [
          "Your card was declined by the issuing bank.",
          "Please try a different payment method.",
          "Contact your bank if the issue persists."
        ]
      case "INSUFFICIENT_FUNDS":
        return [
          "Insufficient funds available on the card.",
          "Please check your account balance.",
          "Try a different payment method."
        ]
      case "INVALID_CARD":
        return [
          "Card information may be incorrect.",
          "Please verify card number, expiry date, and CVV.",
          "Ensure billing address matches card details."
        ]
      default:
        return [
          "Card information may be incorrect.",
          "Insufficient funds available.",
          "Transaction was declined by your bank."
        ]
    }
  }

  const handleTryAgain = () => {
    router.push("/payments/checkout")
  }

  const handleContactSupport = () => {
    router.push("/support")
  }

  const handleClose = () => {
    router.push("/developer")
  }

  return (
    <div className="flex min-h-screen bg-[#0a0a0a]">
      <aside className="flex w-64 flex-col justify-between bg-[#111111]/50 p-4 border-r border-white/10">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 48 48">
                <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" />
              </svg>
            </div>
            <div>
              <h1 className="text-white font-bold">Astraeus</h1>
              <p className="text-white/50 text-xs">Developer Workspace</p>
            </div>
          </div>

          <nav className="flex flex-col gap-2">
            <Link
              href="/developer"
              className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
            >
              <LayoutDashboard className="w-5 h-5" />
              <p className="text-sm font-medium">Dashboard</p>
            </Link>
            <Link
              href="/my-agents"
              className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
            >
              <Bot className="w-5 h-5" />
              <p className="text-sm font-medium">Agents</p>
            </Link>
            <Link
              href="/developer/workflow-builder"
              className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
            >
              <GitBranch className="w-5 h-5" />
              <p className="text-sm font-medium">Workflows</p>
            </Link>
            <Link
              href="/settings/billing"
              className="flex items-center gap-3 px-3 py-2 rounded-lg bg-red-600/20 text-white"
            >
              <CreditCard className="w-5 h-5" />
              <p className="text-sm font-medium">Payments</p>
            </Link>
            <Link
              href="/developer/api-docs"
              className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
            >
              <Key className="w-5 h-5" />
              <p className="text-sm font-medium">API Keys</p>
            </Link>
          </nav>
        </div>

        <div className="flex flex-col gap-4">
          <button className="w-full flex items-center justify-center rounded-lg h-10 px-4 bg-purple-600 hover:bg-purple-700 text-white text-sm font-bold transition-colors">
            New Workflow
          </button>
          <div className="flex flex-col gap-1">
            <Link
              href="/developer/guide"
              className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
            >
              <BookOpen className="w-5 h-5" />
              <p className="text-sm font-medium">Docs</p>
            </Link>
            <Link
              href="/settings"
              className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
              <p className="text-sm font-medium">Settings</p>
            </Link>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex items-center justify-center p-8">
        <div className="relative w-full max-w-lg rounded-xl border border-white/10 bg-[#111111]/30 p-8 shadow-2xl">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-white/50 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>

          <div className="flex flex-col items-center gap-6 text-center">
            <div className="flex items-center justify-center w-20 h-20 rounded-full border-2 border-red-500 bg-red-500/20">
              <XCircle className="w-12 h-12 text-red-500" />
            </div>

            <div className="flex flex-col items-center gap-2">
              <h2 className="text-white text-2xl font-bold">Purchase Unsuccessful</h2>
              <p className="text-white/60 text-sm max-w-md">
                {errorMessage} Please review the potential issues below and try again.
                If the problem persists, contact our support team for assistance.
              </p>
            </div>

            <div className="w-full text-left text-sm bg-white/5 p-4 rounded-lg border border-white/10">
              <p className="font-medium text-white mb-2">Common reasons for failure:</p>
              <ul className="list-disc list-inside space-y-1 text-white/60">
                {getErrorDetails().map((detail, index) => (
                  <li key={index}>{detail}</li>
                ))}
              </ul>
            </div>

            <div className="flex flex-col items-center gap-3 w-full pt-2">
              <button
                onClick={handleTryAgain}
                className="w-full flex items-center justify-center rounded-lg h-10 px-4 bg-purple-600 hover:bg-purple-700 text-white text-sm font-bold transition-colors"
              >
                Try Again With a Different Card
              </button>
              <button
                onClick={handleContactSupport}
                className="flex items-center justify-center rounded-lg h-10 px-4 bg-transparent text-white/70 hover:text-white text-sm font-bold transition-colors"
              >
                Contact Support
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
