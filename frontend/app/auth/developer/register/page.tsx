"use client"

import Link from "next/link"
import { useState } from "react"
import { Eye, EyeOff } from "lucide-react"

export default function DeveloperRegisterPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col items-center justify-center p-4 font-display bg-background-light dark:bg-background-dark text-[#EAEAEA] dev-grid-background">
      <div className="absolute top-8 left-8">
        <h2 className="text-2xl font-bold tracking-wider uppercase text-white">HERMES</h2>
      </div>
      <div className="w-full max-w-md rounded-lg border border-[#333333] bg-background-dark/80 p-8 backdrop-blur-sm">
        <div className="flex flex-col gap-8">
          <h1 className="text-white tracking-light text-[32px] font-bold leading-tight text-left">Create Your Hermes Developer Account</h1>
          <form className="flex flex-col gap-6">
            <div className="flex flex-col">
              <label className="flex flex-col">
                <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Developer/Company Name</p>
                <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded bg-[#1A1A1A] text-white focus:outline-0 focus:ring-0 border border-[#333333] h-14 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal transition-colors focus:border-primary focus:ring-1 focus:ring-primary" placeholder="Enter your name or company name" type="text" />
              </label>
            </div>
            <div className="flex flex-col">
              <label className="flex flex-col">
                <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Email Address</p>
                <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded bg-[#1A1A1A] text-white focus:outline-0 focus:ring-0 border border-[#333333] h-14 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal transition-colors focus:border-primary focus:ring-1 focus:ring-primary" placeholder="Enter your email address" type="email" />
              </label>
            </div>
            <div className="flex flex-col">
              <label className="flex flex-col">
                <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Password</p>
                <div className="flex w-full flex-1 items-stretch rounded">
                  <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-r-none border-r-0 bg-[#1A1A1A] text-white focus:outline-0 focus:ring-0 border border-[#333333] h-14 placeholder:text-gray-500 p-[15px] pr-2 text-base font-normal leading-normal transition-colors focus:border-primary focus:ring-1 focus:ring-primary" placeholder="Create a password" type={showPassword ? "text" : "password"} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="text-gray-400 flex border border-[#333333] bg-[#1A1A1A] items-center justify-center px-[15px] rounded-r border-l-0 cursor-pointer">
                    {showPassword ? <EyeOff /> : <Eye />}
                  </button>
                </div>
              </label>
            </div>
            <div className="flex flex-col">
              <label className="flex flex-col">
                <p className="text-[#EAEAEA] text-base font-medium leading-normal pb-2">Confirm Password</p>
                <div className="flex w-full flex-1 items-stretch rounded">
                  <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-r-none border-r-0 bg-[#1A1A1A] text-white focus:outline-0 focus:ring-0 border border-[#333333] h-14 placeholder:text-gray-500 p-[15px] pr-2 text-base font-normal leading-normal transition-colors focus:border-primary focus:ring-1 focus:ring-primary" placeholder="Confirm your password" type={showConfirmPassword ? "text" : "password"} />
                  <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="text-gray-400 flex border border-[#333333] bg-[#1A1A1A] items-center justify-center px-[15px] rounded-r border-l-0 cursor-pointer">
                    {showConfirmPassword ? <EyeOff /> : <Eye />}
                  </button>
                </div>
              </label>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <input className="form-checkbox h-4 w-4 rounded-sm border-[#333333] bg-[#1A1A1A] text-primary focus:ring-primary focus:ring-offset-background-dark" id="terms" type="checkbox" />
              <label className="text-sm text-gray-300" htmlFor="terms">
                I agree to the <a className="underline text-gray-200 hover:text-primary transition-colors" href="#">Developer Terms and Conditions</a>.
              </label>
            </div>
            <button className="flex h-14 w-full items-center justify-center rounded bg-primary px-6 text-base font-bold text-white transition-transform hover:scale-[1.02] active:scale-[0.98]">
              Create Developer Account
            </button>
          </form>
          <div className="text-center">
            <p className="text-sm text-gray-400">
              Already have an account?{" "}
              <Link className="font-medium text-gray-200 hover:text-primary transition-colors" href="/auth/developer/login">Sign In</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
