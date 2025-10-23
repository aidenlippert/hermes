"use client";

import { useRouter } from "next/navigation";
import { Circle, ArrowRight } from "lucide-react";

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl mx-auto text-center">
        {/* Logo */}
        <div className="mb-8 flex items-center justify-center gap-3">
          <Circle className="w-8 h-8 text-accent" fill="currentColor" />
          <h1 className="text-3xl font-semibold text-slate-900">Hermes</h1>
        </div>

        {/* Tagline */}
        <p className="text-lg text-slate-600 mb-12 leading-relaxed">
          Multi-agent orchestration platform powered by A2A protocol.
          <br />
          Natural language → intelligent coordination.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-16">
          <button
            onClick={() => router.push("/chat")}
            className="px-6 py-2.5 bg-accent text-white rounded-lg hover:bg-accent/90 minimal-transition flex items-center gap-2 group"
          >
            Start chatting
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 minimal-transition" />
          </button>
          <button
            onClick={() => router.push("/auth/login")}
            className="px-6 py-2.5 border border-slate-200 text-slate-700 rounded-lg hover:border-slate-300 minimal-transition"
          >
            Sign in
          </button>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-sm">
          <div>
            <div className="font-medium text-slate-900 mb-1">Real-time streaming</div>
            <div className="text-slate-500">Token-by-token responses with agent transparency</div>
          </div>
          <div>
            <div className="font-medium text-slate-900 mb-1">Agent discovery</div>
            <div className="text-slate-500">Automatic coordination of specialized agents</div>
          </div>
          <div>
            <div className="font-medium text-slate-900 mb-1">A2A protocol</div>
            <div className="text-slate-500">Fully compliant with Google's A2A v0.3.0</div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-20 pt-8 border-t border-slate-200">
          <p className="text-xs text-slate-500">
            4 travel agents ready: FlightBooker · HotelBooker · RestaurantFinder · EventsFinder
          </p>
        </div>
      </div>
    </div>
  );
}
