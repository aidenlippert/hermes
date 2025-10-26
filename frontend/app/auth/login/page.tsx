"use client"

import Link from "next/link"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { EyeOff, Eye, AlertCircle } from "lucide-react"
import { useAuthStore } from "@/lib/store"

export default function LoginPage() {
  const router = useRouter()
  const setTokens = useAuthStore((state) => state.setTokens)

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Login failed. Please check your credentials.")
      }

      setTokens(data.access_token, data.refresh_token)
      
      router.push("/chat")

    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col bg-background-light dark:bg-background-dark overflow-x-hidden font-display">
      <div className="layout-container flex h-full min-h-screen grow flex-col">
        <div className="flex flex-1 items-center justify-center p-4 sm:p-6 md:p-8">
          <div className="layout-content-container flex w-full max-w-md flex-col items-center">
            <div className="flex w-full flex-col items-center gap-6 rounded-xl bg-transparent p-4 sm:p-8">
              <h1 className="text-3xl font-bold tracking-tight text-zinc-200 sm:text-4xl">HERMES</h1>
              <div className="w-full text-center">
                <p className="text-2xl font-bold text-zinc-100">User Sign In</p>
                <p className="mt-2 text-sm text-zinc-400">Please enter your credentials to continue</p>
              </div>
              <form className="flex w-full flex-col gap-5" onSubmit={handleSubmit}>
                <div className="flex w-full flex-col gap-4">
                  <label className="flex w-full flex-col">
                    <p className="pb-2 text-sm font-medium text-zinc-200">Email</p>
                    <input 
                      className="form-input h-12 w-full flex-1 resize-none overflow-hidden rounded-lg border border-zinc-700 bg-zinc-800/50 p-3 text-base font-normal text-zinc-200 placeholder:text-zinc-500 focus:border-primary focus:outline-0 focus:ring-2 focus:ring-primary/50" 
                      placeholder="Enter your email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </label>
                  <label className="flex w-full flex-col">
                    <p className="pb-2 text-sm font-medium text-zinc-200">Password</p>
                    <div className="relative flex w-full items-stretch">
                      <input 
                        className="form-input h-12 w-full flex-1 resize-none overflow-hidden rounded-lg border border-zinc-700 bg-zinc-800/50 p-3 pr-10 text-base font-normal text-zinc-200 placeholder:text-zinc-500 focus:border-primary focus:outline-0 focus:ring-2 focus:ring-primary/50" 
                        placeholder="Enter your password" 
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                      />
                      <button
                        onClick={() => setShowPassword(!showPassword)}
                        className="text-zinc-400 absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer text-xl hover:text-zinc-300"
                        type="button"
                      >
                        {showPassword ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                      </button>
                    </div>
                  </label>
                </div>
                <div className="flex items-center justify-between">
                  <div></div>
                  <Link href="#" className="text-sm font-normal text-zinc-400 underline hover:text-primary">
                    Forgot Password?
                  </Link>
                </div>
                <div className="flex flex-col gap-2">
                  {error && (
                    <div className="flex items-center gap-2 rounded border border-red-500/50 bg-red-500/10 p-3">
                      <AlertCircle className="text-red-500 w-5 h-5" />
                      <p className="text-sm text-red-400">{error}</p>
                    </div>
                  )}
                  <button 
                    type="submit"
                    className="flex h-12 w-full items-center justify-center rounded-lg bg-primary px-4 py-2 text-base font-semibold text-white transition-all hover:bg-primary/90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={loading}
                  >
                    {loading ? "Signing In..." : "Sign In"}
                  </button>
                </div>
              </form>
              <p className="text-center text-sm text-zinc-400">
                Need an account?{" "}
                <Link href="/auth/register" className="font-medium text-primary underline hover:text-primary/90">
                  Sign Up
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
