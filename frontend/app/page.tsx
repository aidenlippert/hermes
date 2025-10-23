"use client";

import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, Zap, Shield, Globe } from "lucide-react";

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      <div className="max-w-6xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="flex items-center justify-between mb-20">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary" />
            <span className="font-bold text-xl">Hermes</span>
          </div>
          <button
            onClick={() => router.push("/auth/login")}
            className="px-4 py-2 text-sm font-medium hover:bg-muted rounded-lg transition-colors"
          >
            Sign in
          </button>
        </div>

        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-blue-600 to-primary bg-clip-text text-transparent">
            The Operating System
            <br />
            for AI Agents
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Transform natural language into intelligent multi-agent workflows.
            Real-time coordination powered by the A2A protocol.
          </p>
          <button
            onClick={() => router.push("/chat")}
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-all hover:scale-105 active:scale-95"
          >
            Start chatting
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="p-6 rounded-2xl bg-background border border-border hover:border-primary/50 transition-all hover:shadow-lg">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-semibold mb-2">Real-time Streaming</h3>
            <p className="text-sm text-muted-foreground">
              Watch AI agents work together in real-time with token-by-token streaming responses.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-background border border-border hover:border-primary/50 transition-all hover:shadow-lg">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center mb-4">
              <Globe className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-semibold mb-2">Agent Discovery</h3>
            <p className="text-sm text-muted-foreground">
              Automatic coordination of specialized agents to solve complex tasks efficiently.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-background border border-border hover:border-primary/50 transition-all hover:shadow-lg">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-semibold mb-2">A2A Protocol</h3>
            <p className="text-sm text-muted-foreground">
              Fully compliant with Google's Agent-to-Agent protocol v0.3.0 standard.
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="text-center py-12 border-t border-border">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="text-3xl font-bold text-primary mb-1">4+</div>
              <div className="text-sm text-muted-foreground">Travel Agents</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary mb-1">100%</div>
              <div className="text-sm text-muted-foreground">A2A Compliant</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary mb-1">Real-time</div>
              <div className="text-sm text-muted-foreground">WebSocket Streaming</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
