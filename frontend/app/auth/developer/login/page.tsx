"use client"

import Link from "next/link"
import { useState } from "react"
import { Eye, EyeOff, Package } from "lucide-react"

export default function DeveloperLoginPage() {
  const [showPassword, setShowPassword] = useState(false)

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center bg-background-light dark:bg-background-dark text-white overflow-hidden p-4 font-display">
      <div className="absolute inset-0 z-0 opacity-10" style={{backgroundImage: "radial-gradient(circle at center, #333 1px, transparent 1px), radial-gradient(circle at center, #333 1px, transparent 1px)", backgroundSize: "20px 20px"}}></div>
      <div className="relative z-10 flex w-full max-w-md flex-col items-center justify-center rounded-lg border border-white/10 bg-background-dark/50 p-8 shadow-2xl shadow-primary/10 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <Package className="text-primary h-12 w-12" strokeWidth={1.5} />
          <h1 className="text-white tracking-light text-2xl font-bold leading-tight text-center font-display">Agent Developer Portal</h1>
        </div>
        <div className="w-full space-y-6">
          <div className="flex flex-col">
            <label className="flex flex-col min-w-40 flex-1">
              <p className="text-white/80 text-sm font-medium leading-normal pb-2 font-display">Email or Username</p>
              <input 
                className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-white/90 focus:outline-0 border border-white/20 bg-white/5 focus:border-primary h-12 placeholder:text-white/40 p-3 text-base font-normal leading-normal font-display transition-colors duration-300 focus:ring-1 focus:ring-primary" 
                placeholder="Enter your email or username" 
              />
            </label>
          </div>
          <div className="flex flex-col">
            <label className="flex flex-col min-w-40 flex-1">
              <p className="text-white/80 text-sm font-medium leading-normal pb-2 font-display">Password</p>
              <div className="flex w-full flex-1 items-stretch rounded-lg">
                <input 
                  className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-l-lg text-white/90 focus:outline-0 border border-white/20 bg-white/5 focus:border-primary h-12 placeholder:text-white/40 p-3 border-r-0 pr-2 text-base font-normal leading-normal font-display transition-colors duration-300 focus:ring-1 focus:ring-primary focus:z-10" 
                  placeholder="Enter your password" 
                  type={showPassword ? "text" : "password"}
                />
                <button 
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-white/40 flex border border-white/20 bg-white/5 items-center justify-center px-3 rounded-r-lg border-l-0"
                  type="button"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </label>
          </div>
        </div>
        <div className="flex w-full items-center justify-end mt-4">
          <Link href="#" className="text-white/60 text-sm font-normal leading-normal underline hover:text-primary transition-colors cursor-pointer font-display">
            Forgot Password?
          </Link>
        </div>
        <div className="flex w-full px-0 py-3 mt-4">
          <button className="flex min-w-[84px] w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-5 flex-1 bg-primary text-white text-base font-bold leading-normal tracking-[0.015em] font-display transition-all duration-300 hover:bg-red-700 hover:shadow-lg hover:shadow-primary/30 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background-dark">
            <span className="truncate">Sign In</span>
          </button>
        </div>
        <div className="mt-6 text-center">
          <p className="text-white/60 text-sm font-normal leading-normal font-display">
            Don't have an account?{" "}
            <Link href="/auth/developer/register" className="font-medium text-white/90 underline hover:text-primary transition-colors">
              Sign Up as a Developer
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
