"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  CreditCard,
  Lock,
  AlertCircle,
  ArrowLeft,
  Check
} from "lucide-react"

interface CreditPack {
  id: string
  credits: number
  price: number
  discount?: number
  selected?: boolean
}

interface PaymentDetails {
  cardNumber: string
  cardName: string
  expiryDate: string
  cvc: string
}

const CREDIT_PACKS: CreditPack[] = [
  { id: "100", credits: 100, price: 10.00 },
  { id: "500", credits: 500, price: 45.00, discount: 10 },
  { id: "1000", credits: 1000, price: 80.00, discount: 20 }
]

const TAX_RATE = 0.05

export default function CheckoutPage() {
  const router = useRouter()
  const [selectedPack, setSelectedPack] = useState<string>("100")
  const [customAmount, setCustomAmount] = useState<string>("")
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails>({
    cardNumber: "",
    cardName: "",
    expiryDate: "",
    cvc: ""
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [paymentError, setPaymentError] = useState<string>("")

  const getSelectedAmount = () => {
    if (customAmount) {
      const credits = parseInt(customAmount)
      return { credits, price: credits * 0.10 }
    }
    const pack = CREDIT_PACKS.find(p => p.id === selectedPack)
    return pack ? { credits: pack.credits, price: pack.price } : { credits: 0, price: 0 }
  }

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, "")
    const chunks = cleaned.match(/.{1,4}/g)
    return chunks ? chunks.join(" ") : cleaned
  }

  const formatExpiryDate = (value: string) => {
    const cleaned = value.replace(/\D/g, "")
    if (cleaned.length >= 2) {
      return `${cleaned.slice(0, 2)} / ${cleaned.slice(2, 4)}`
    }
    return cleaned
  }

  const handleCardNumberChange = (value: string) => {
    const cleaned = value.replace(/\s/g, "")
    if (cleaned.length <= 16 && /^\d*$/.test(cleaned)) {
      setPaymentDetails(prev => ({
        ...prev,
        cardNumber: formatCardNumber(cleaned)
      }))
      if (errors.cardNumber) {
        setErrors(prev => ({ ...prev, cardNumber: "" }))
      }
    }
  }

  const handleExpiryChange = (value: string) => {
    const cleaned = value.replace(/\D/g, "")
    if (cleaned.length <= 4) {
      setPaymentDetails(prev => ({
        ...prev,
        expiryDate: formatExpiryDate(cleaned)
      }))
      if (errors.expiryDate) {
        setErrors(prev => ({ ...prev, expiryDate: "" }))
      }
    }
  }

  const handleCvcChange = (value: string) => {
    if (value.length <= 4 && /^\d*$/.test(value)) {
      setPaymentDetails(prev => ({ ...prev, cvc: value }))
      if (errors.cvc) {
        setErrors(prev => ({ ...prev, cvc: "" }))
      }
    }
  }

  const validatePaymentDetails = (): boolean => {
    const newErrors: Record<string, string> = {}

    const cardNumberClean = paymentDetails.cardNumber.replace(/\s/g, "")
    if (!cardNumberClean || cardNumberClean.length !== 16) {
      newErrors.cardNumber = "Card number must be 16 digits"
    }

    if (!paymentDetails.cardName.trim()) {
      newErrors.cardName = "Name on card is required"
    }

    const expiryClean = paymentDetails.expiryDate.replace(/\D/g, "")
    if (!expiryClean || expiryClean.length !== 4) {
      newErrors.expiryDate = "Expiry date must be MM/YY format"
    } else {
      const month = parseInt(expiryClean.slice(0, 2))
      const year = parseInt("20" + expiryClean.slice(2, 4))
      const now = new Date()
      const currentYear = now.getFullYear()
      const currentMonth = now.getMonth() + 1

      if (month < 1 || month > 12) {
        newErrors.expiryDate = "Invalid month"
      } else if (year < currentYear || (year === currentYear && month < currentMonth)) {
        newErrors.expiryDate = "Card has expired"
      }
    }

    if (!paymentDetails.cvc || paymentDetails.cvc.length < 3) {
      newErrors.cvc = "CVC must be 3-4 digits"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    setPaymentError("")

    if (!validatePaymentDetails()) {
      return
    }

    setIsProcessing(true)

    try {
      const amount = getSelectedAmount()
      const total = amount.price + (amount.price * TAX_RATE)

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/payments/purchase`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            credits: amount.credits,
            amount: total,
            paymentMethod: {
              cardNumber: paymentDetails.cardNumber.replace(/\s/g, ""),
              cardName: paymentDetails.cardName,
              expiryDate: paymentDetails.expiryDate,
              cvc: paymentDetails.cvc
            }
          })
        }
      )

      if (response.ok) {
        const data = await response.json()
        router.push(`/payments/success?transactionId=${data.transactionId}&credits=${amount.credits}`)
      } else {
        const error = await response.json()
        setPaymentError(error.message || "Your card was declined. Please try a different card.")
      }
    } catch (error) {
      console.error("Payment failed:", error)
      setPaymentError("Payment processing failed. Please try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  const { credits, price } = getSelectedAmount()
  const taxes = price * TAX_RATE
  const total = price + taxes

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <header className="border-b border-white/10 px-6 sm:px-10 md:px-20 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 48 48">
                <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold">Astraeus</h2>
          </div>
          <Link href="/developer" className="flex items-center gap-2 text-sm font-medium text-white/70 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </header>

      <main className="px-6 sm:px-10 md:px-20 py-10">
        <div className="mx-auto max-w-6xl">
          <h1 className="text-4xl font-black mb-8">Purchase Astraeus Credits</h1>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
            <div className="lg:col-span-2 space-y-8">
              <section>
                <h2 className="text-2xl font-bold mb-4">Choose Your Credit Pack</h2>
                <div className="space-y-3">
                  {CREDIT_PACKS.map(pack => (
                    <label
                      key={pack.id}
                      className={`flex items-center gap-4 rounded-lg border p-4 cursor-pointer transition-all ${
                        selectedPack === pack.id && !customAmount
                          ? 'border-purple-600 bg-purple-600/10 ring-2 ring-purple-600/20'
                          : 'border-white/10 bg-white/5 hover:border-purple-600/50'
                      }`}
                    >
                      <input
                        type="radio"
                        name="credit-pack"
                        checked={selectedPack === pack.id && !customAmount}
                        onChange={() => {
                          setSelectedPack(pack.id)
                          setCustomAmount("")
                        }}
                        className="w-5 h-5 text-purple-600 border-white/20 bg-transparent focus:ring-purple-600"
                      />
                      <div className="flex-1">
                        <p className="text-base font-medium">
                          {pack.credits} Credits
                          {pack.discount && (
                            <span className="ml-2 text-xs text-purple-400">(Save {pack.discount}%)</span>
                          )}
                        </p>
                        <p className="text-sm text-white/50">${pack.price.toFixed(2)}</p>
                      </div>
                    </label>
                  ))}
                </div>

                <div className="mt-4">
                  <label className="block">
                    <p className="text-base font-medium mb-2">Or Enter a Custom Amount</p>
                    <input
                      type="number"
                      value={customAmount}
                      onChange={(e) => {
                        setCustomAmount(e.target.value)
                        if (e.target.value) {
                          setSelectedPack("")
                        }
                      }}
                      placeholder="e.g., 250"
                      className="w-full rounded-lg h-12 px-4 bg-white/5 border border-white/10 text-white placeholder:text-white/50 focus:border-purple-600 focus:ring-2 focus:ring-purple-600/30 transition-colors"
                    />
                  </label>
                </div>
              </section>

              <section>
                <h2 className="text-2xl font-bold mb-4">Payment Details</h2>
                <div className="bg-white/5 border border-white/10 rounded-lg p-6 space-y-5">
                  <div className="space-y-4">
                    <label className="block">
                      <span className="font-medium text-sm mb-2 block">Card Number</span>
                      <div className="relative">
                        <input
                          type="text"
                          value={paymentDetails.cardNumber}
                          onChange={(e) => handleCardNumberChange(e.target.value)}
                          placeholder="0000 0000 0000 0000"
                          className={`w-full rounded-lg h-12 px-4 pr-12 bg-[#111111] border ${
                            errors.cardNumber ? 'border-red-500' : 'border-white/10'
                          } text-white placeholder:text-white/50 focus:border-purple-600 focus:ring-2 focus:ring-purple-600/30 transition-colors`}
                        />
                        <CreditCard className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
                      </div>
                      {errors.cardNumber && (
                        <p className="text-red-400 text-sm mt-1">{errors.cardNumber}</p>
                      )}
                    </label>

                    <label className="block">
                      <span className="font-medium text-sm mb-2 block">Name on Card</span>
                      <input
                        type="text"
                        value={paymentDetails.cardName}
                        onChange={(e) => setPaymentDetails(prev => ({ ...prev, cardName: e.target.value }))}
                        placeholder="John Doe"
                        className={`w-full rounded-lg h-12 px-4 bg-[#111111] border ${
                          errors.cardName ? 'border-red-500' : 'border-white/10'
                        } text-white placeholder:text-white/50 focus:border-purple-600 focus:ring-2 focus:ring-purple-600/30 transition-colors`}
                      />
                      {errors.cardName && (
                        <p className="text-red-400 text-sm mt-1">{errors.cardName}</p>
                      )}
                    </label>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <label className="block">
                        <span className="font-medium text-sm mb-2 block">Expiration Date</span>
                        <input
                          type="text"
                          value={paymentDetails.expiryDate}
                          onChange={(e) => handleExpiryChange(e.target.value)}
                          placeholder="MM / YY"
                          className={`w-full rounded-lg h-12 px-4 bg-[#111111] border ${
                            errors.expiryDate ? 'border-red-500' : 'border-white/10'
                          } text-white placeholder:text-white/50 focus:border-purple-600 focus:ring-2 focus:ring-purple-600/30 transition-colors`}
                        />
                        {errors.expiryDate && (
                          <p className="text-red-400 text-sm mt-1">{errors.expiryDate}</p>
                        )}
                      </label>

                      <label className="block">
                        <span className="font-medium text-sm mb-2 block">CVC / CVV</span>
                        <div className="relative">
                          <input
                            type="text"
                            value={paymentDetails.cvc}
                            onChange={(e) => handleCvcChange(e.target.value)}
                            placeholder="123"
                            className={`w-full rounded-lg h-12 px-4 pr-12 bg-[#111111] border ${
                              errors.cvc ? 'border-red-500' : 'border-white/10'
                            } text-white placeholder:text-white/50 focus:border-purple-600 focus:ring-2 focus:ring-purple-600/30 transition-colors`}
                          />
                          <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
                        </div>
                        {errors.cvc && (
                          <p className="text-red-400 text-sm mt-1">{errors.cvc}</p>
                        )}
                      </label>
                    </div>
                  </div>

                  {paymentError && (
                    <div className="flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                      <AlertCircle className="w-5 h-5 flex-shrink-0" />
                      <p className="text-sm font-medium">{paymentError}</p>
                    </div>
                  )}
                </div>
              </section>
            </div>

            <div className="lg:col-span-1">
              <aside className="sticky top-10">
                <h2 className="text-2xl font-bold mb-4">Order Summary</h2>
                <div className="bg-white/5 border border-white/10 rounded-lg p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <p>{credits} Credits</p>
                    <p className="font-medium">${price.toFixed(2)}</p>
                  </div>
                  <div className="flex justify-between items-center text-white/50">
                    <p>Taxes &amp; Fees</p>
                    <p className="font-medium">${taxes.toFixed(2)}</p>
                  </div>
                  <div className="border-t border-white/10 my-4"></div>
                  <div className="flex justify-between items-center font-bold text-lg">
                    <p>Total</p>
                    <p>${total.toFixed(2)}</p>
                  </div>
                  <button
                    onClick={handleSubmit}
                    disabled={isProcessing || credits === 0}
                    className="w-full flex items-center justify-center gap-2 rounded-lg h-12 bg-purple-600 hover:bg-purple-700 text-white font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isProcessing ? (
                      <>Processing...</>
                    ) : (
                      <>
                        <Check className="w-5 h-5" />
                        Complete Purchase
                      </>
                    )}
                  </button>
                  <div className="flex items-center justify-center gap-2 pt-2 text-xs text-white/50">
                    <Lock className="w-4 h-4" />
                    <span>SSL Secured Payment</span>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </div>
      </main>

      <footer className="text-center px-6 sm:px-10 md:px-20 py-6 border-t border-white/10 mt-10">
        <p className="text-sm text-white/50">
          By completing your purchase, you agree to our{" "}
          <Link href="/terms" className="underline hover:text-purple-400 transition-colors">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="underline hover:text-purple-400 transition-colors">
            Privacy Policy
          </Link>
          .
        </p>
      </footer>
    </div>
  )
}
