import * as React from "react"
import { cn } from "@/lib/utils"

const buttonVariants = (
  variant?: string,
  size?: string
) => {
  const baseClasses = "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]"

  const variantClasses: Record<string, string> = {
    default: "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:from-blue-500 hover:to-blue-400",
    destructive: "bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/25",
    outline: "border border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-950 dark:hover:bg-gray-900",
    secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700",
    ghost: "hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-gray-100",
    link: "text-blue-500 underline-offset-4 hover:underline",
    gradient: "bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 text-white shadow-xl hover:shadow-2xl",
    success: "bg-green-500 text-white hover:bg-green-600 shadow-lg shadow-green-500/25",
  }

  const sizeClasses: Record<string, string> = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-lg px-3",
    lg: "h-12 rounded-xl px-6 text-base",
    xl: "h-14 rounded-2xl px-8 text-lg",
    icon: "h-10 w-10",
  }

  return cn(
    baseClasses,
    variantClasses[variant || "default"] || variantClasses.default,
    sizeClasses[size || "default"] || sizeClasses.default
  )
}

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "gradient" | "success"
  size?: "default" | "sm" | "lg" | "xl" | "icon"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? "button" : "button"
    return (
      <Comp
        className={cn(buttonVariants(variant, size), className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }