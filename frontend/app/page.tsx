"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { MessageSquare, Zap, Users, TrendingUp, ArrowRight, Sparkles } from "lucide-react";

export default function HomePage() {
  const router = useRouter();

  const features = [
    {
      icon: Zap,
      title: "Real-Time Streaming",
      description: "Watch AI agents work in real-time with WebSocket updates",
    },
    {
      icon: Users,
      title: "Multi-Agent Coordination",
      description: "Orchestrate multiple agents to solve complex tasks",
    },
    {
      icon: MessageSquare,
      title: "Natural Language",
      description: "Just describe what you need - Hermes handles the rest",
    },
    {
      icon: TrendingUp,
      title: "Smart Routing",
      description: "Intelligent agent selection using semantic search",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-100/20 via-accent-100/20 to-purple-100/20 animate-gradient-slow" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          {/* Logo/Brand */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-3 glass-effect px-6 py-3 rounded-full mb-6">
              <Sparkles className="w-5 h-5 text-primary-600" />
              <span className="text-sm font-medium text-slate-700">
                The Operating System for AI Agent Orchestration
              </span>
            </div>
            <h1 className="text-6xl md:text-7xl font-bold mb-6 gradient-text">
              Hermes
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 max-w-3xl mx-auto">
              Transform natural language into intelligent multi-agent workflows. Real-time coordination powered by A2A protocol.
            </p>
          </motion.div>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
          >
            <button
              onClick={() => router.push("/chat")}
              className="button-primary flex items-center gap-2 group"
            >
              Start Chatting
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => router.push("/marketplace")}
              className="button-secondary"
            >
              Browse Agents
            </button>
          </motion.div>

          {/* Features Grid */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.5 + index * 0.1 }}
                className="card group cursor-pointer hover:border-primary-200"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-white group-hover:scale-110 transition-transform">
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-800 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-slate-600">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto"
          >
            {[
              { number: "4+", label: "AI Agents" },
              { number: "100%", label: "A2A Compliant" },
              { number: "Real-time", label: "WebSocket Streaming" },
            ].map((stat, index) => (
              <div key={stat.label} className="text-center">
                <div className="text-4xl font-bold gradient-text mb-2">
                  {stat.number}
                </div>
                <div className="text-slate-600">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
