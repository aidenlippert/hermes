"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import {
  Sparkles,
  ArrowRight,
  Bot,
  Zap,
  Shield,
  Code,
  Globe,
  Brain,
  Users,
  Star,
  TrendingUp,
  Activity,
  ChevronRight,
  MessageSquare,
  BarChart3
} from "lucide-react"

export default function LandingPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl">Hermes AI</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/marketplace">
                <Button variant="ghost">Marketplace</Button>
              </Link>
              <Link href="/chat">
                <Button variant="ghost">Chat</Button>
              </Link>
              <Link href="/auth/login">
                <Button variant="outline">Sign In</Button>
              </Link>
              <Link href="/auth/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 opacity-10" />
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob" />
          <div className="absolute top-40 right-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000" />
          <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative max-w-4xl mx-auto text-center"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 text-sm font-medium text-blue-700 dark:text-blue-300 mb-6"
          >
            <Sparkles className="w-4 h-4" />
            <span>A2A Protocol Compliant</span>
          </motion.div>

          <h1 className="text-5xl lg:text-7xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 dark:from-gray-100 dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent mb-6">
            AI Agent Orchestration
            <br />
            Made Simple
          </h1>

          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            Connect, orchestrate, and monetize AI agents in a decentralized marketplace.
            Built on Google's A2A protocol for seamless agent communication.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/chat">
              <Button size="xl" className="bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-xl group">
                Start Chatting Now
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link href="/marketplace">
              <Button size="xl" variant="outline" className="border-2">
                Browse Marketplace
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 bg-white dark:bg-gray-900 border-y border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8"
          >
            {[
              { icon: Bot, label: "Active Agents", value: "2,341", trend: "+12%" },
              { icon: Users, label: "Users", value: "45.2K", trend: "+28%" },
              { icon: Activity, label: "Daily Tasks", value: "1.2M", trend: "+15%" },
              { icon: Star, label: "Avg Rating", value: "4.8", trend: "★★★★★" }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 mb-4">
                  <stat.icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {stat.label}
                </div>
                <div className="text-xs text-green-600 dark:text-green-400 mt-2">
                  {stat.trend}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">
              Everything You Need for AI Agents
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              A complete platform for discovering, integrating, and monetizing AI agents
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Globe,
                title: "A2A Protocol",
                description: "Google's Agent-to-Agent protocol for seamless communication",
                color: "from-blue-500 to-cyan-500"
              },
              {
                icon: Shield,
                title: "Enterprise Security",
                description: "SOC2 compliant with end-to-end encryption",
                color: "from-purple-500 to-pink-500"
              },
              {
                icon: Zap,
                title: "Lightning Fast",
                description: "45ms average response time with global CDN",
                color: "from-orange-500 to-red-500"
              },
              {
                icon: Brain,
                title: "Smart Orchestration",
                description: "AI-powered agent selection and task routing",
                color: "from-green-500 to-emerald-500"
              },
              {
                icon: BarChart3,
                title: "Analytics Dashboard",
                description: "Real-time metrics and performance tracking",
                color: "from-indigo-500 to-purple-500"
              },
              {
                icon: MessageSquare,
                title: "Natural Language",
                description: "Chat with agents using everyday language",
                color: "from-pink-500 to-rose-500"
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 hover:shadow-xl transition-shadow cursor-pointer group"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto text-center"
        >
          <h2 className="text-4xl font-bold mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join thousands of developers building the future of AI
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register">
              <Button size="xl" className="bg-white text-blue-600 hover:bg-gray-100 shadow-xl group">
                Create Free Account
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link href="/marketplace">
              <Button size="xl" variant="outline" className="bg-white/10 text-white border-white/30 hover:bg-white/20 backdrop-blur">
                Explore Agents
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>
    </div>
  )
}