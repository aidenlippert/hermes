"use client"

import Link from "next/link"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { EyeOff, Eye, AlertCircle } from "lucide-react"
import { useAuthStore } from "@/lib/store"
import { api } from "@/lib/api"

export default function LoginPage() {
  const router = useRouter()
  const setTokens = useAuthStore((state) => state.setTokens)
  const setAuth = useAuthStore((state) => state.setAuth as (token: string, user: any) => void)

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

      // Store tokens immediately
      setTokens(data.access_token, data.refresh_token)
      
      // Prefer user from response; otherwise fetch /auth/me
      try {
        if (data.user) {
          setAuth(data.access_token, data.user)
        } else {
          const me = await api.auth.getMe(data.access_token)
          setAuth(data.access_token, me)
        }
      } catch (e) {
        // Non-fatal: proceed without user prefetch
        console.warn("Login succeeded but fetching user profile failed:", e)
      }
      
      router.push("/chat")

    } catch (err: any) {
      console.error("Login error:", err)
      setError(err.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col bg-background-light dark:bg-background-dark overflow-x-hidden font-display">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-4">
        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity w-fit">
          <div className="w-8 h-8 text-[#FF1744]">
            <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z"
                fill="currentColor"
              ></path>
              <path
                clipRule="evenodd"
                d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z"
                fill="currentColor"
                fillRule="evenodd"
              ></path>
            </svg>
          </div>
          <h2 className="text-zinc-200 text-lg font-bold">HERMES</h2>
        </Link>
      </header>

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
