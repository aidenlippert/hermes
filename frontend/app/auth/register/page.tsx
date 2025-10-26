"use client"

import Link from "next/link"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Shield, CheckCircle, AlertTriangle } from "lucide-react"

export default function RegisterPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          username: email, // Using email as username for now
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "An unknown error occurred.")
      }

      setSuccess(true)
      setError(null)
      
      // Redirect to login page after a short delay
      setTimeout(() => {
        router.push("/auth/login")
      }, 2000)

    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center bg-background-light dark:bg-background-dark dark:grid-background overflow-hidden p-4">
      <div className="w-full max-w-md rounded-lg border border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark p-8 shadow-2xl shadow-black/20">
        <div className="flex flex-col items-center">
          <Shield className="h-8 w-auto text-text-light dark:text-text-dark mb-2" />
          <h1 className="text-2xl font-bold tracking-tight text-text-light dark:text-text-dark">
            Create Your Hermes Account
          </h1>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="flex flex-col">
              <label className="pb-2 text-sm font-medium text-text-light dark:text-text-dark" htmlFor="full-name">
                Full Name
              </label>
              <input 
                className="form-input h-12 w-full min-w-0 flex-1 resize-none overflow-hidden rounded-md border border-border-light bg-background-light p-3 text-base font-normal leading-normal text-text-light placeholder:text-text-muted-light focus:border-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 dark:border-border-dark dark:bg-background-dark dark:text-text-dark dark:placeholder:text-text-muted-dark dark:focus:border-primary" 
                id="full-name" 
                name="full-name" 
                placeholder="Enter your full name" 
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col">
              <label className="pb-2 text-sm font-medium text-text-light dark:text-text-dark" htmlFor="work-email">
                Work Email
              </label>
              <input 
                className="form-input h-12 w-full min-w-0 flex-1 resize-none overflow-hidden rounded-md border border-border-light bg-background-light p-3 text-base font-normal leading-normal text-text-light placeholder:text-text-muted-light focus:border-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 dark:border-border-dark dark:bg-background-dark dark:text-text-dark dark:placeholder:text-text-muted-dark dark:focus:border-primary" 
                id="work-email" 
                name="work-email" 
                placeholder="Enter your work email address" 
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col">
              <label className="pb-2 text-sm font-medium text-text-light dark:text-text-dark" htmlFor="password">
                Password
              </label>
              <div className="relative flex w-full items-stretch">
                <input 
                  className="form-input h-12 w-full min-w-0 flex-1 resize-none overflow-hidden rounded-l-md border border-r-0 border-border-light bg-background-light p-3 pr-10 text-base font-normal leading-normal text-text-light placeholder:text-text-muted-light focus:border-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 dark:border-border-dark dark:bg-background-dark dark:text-text-dark dark:placeholder:text-text-muted-dark dark:focus:border-primary" 
                  id="password" 
                  name="password" 
                  placeholder="Create a password" 
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex cursor-pointer items-center justify-center rounded-r-md border border-l-0 border-border-light bg-background-light px-3 text-text-muted-light dark:border-border-dark dark:bg-background-dark dark:text-text-muted-dark"
                >
                  {showPassword ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                </button>
              </div>
            </div>
            <div className="flex flex-col">
              <label className="pb-2 text-sm font-medium text-text-light dark:text-text-dark" htmlFor="confirm-password">
                Confirm Password
              </label>
              <div className="relative flex w-full items-stretch">
                <input 
                  className="form-input h-12 w-full min-w-0 flex-1 resize-none overflow-hidden rounded-l-md border border-r-0 border-border-light bg-background-light p-3 pr-10 text-base font-normal leading-normal text-text-light placeholder:text-text-muted-light focus:border-primary focus:outline-0 focus:ring-2 focus:ring-primary/20 dark:border-border-dark dark:bg-background-dark dark:text-text-dark dark:placeholder:text-text-muted-dark dark:focus:border-primary" 
                  id="confirm-password" 
                  name="confirm-password" 
                  placeholder="Confirm your new password" 
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 flex cursor-pointer items-center justify-center rounded-r-md border border-l-0 border-border-light bg-background-light px-3 text-text-muted-light dark:border-border-dark dark:bg-background-dark dark:text-text-muted-dark"
                >
                  {showConfirmPassword ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-center space-x-2 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-500 dark:text-red-400">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {success && (
            <div className="flex items-center space-x-2 rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-500 dark:text-green-400">
              <CheckCircle className="h-5 w-5 flex-shrink-0" />
              <p>Account created successfully! Redirecting to login...</p>
            </div>
          )}

          <button 
            className="flex h-12 w-full items-center justify-center rounded-md bg-primary px-4 text-base font-semibold text-white transition-colors duration-200 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-surface-dark disabled:opacity-50 disabled:cursor-not-allowed" 
            type="submit"
            disabled={loading || success}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>
        <div className="mt-6 text-center">
          <p className="text-sm text-text-muted-light dark:text-text-muted-dark">
            Already have an account?{" "}
            <Link href="/auth/login" className="font-medium text-primary hover:underline">
              Sign In
            </Link>
          </p>
        </div>
        <div className="mt-8 text-center">
          <p className="text-xs text-text-muted-light dark:text-text-muted-dark">
            By creating an account, you agree to the Hermes{" "}
            <Link href="#" className="underline hover:text-primary">Terms of Service</Link> and{" "}
            <Link href="#" className="underline hover:text-primary">Privacy Policy</Link>.
          </p>
        </div>
      </div>
    </div>
  )
}
