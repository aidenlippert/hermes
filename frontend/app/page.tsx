"use client"

import Link from "next/link"

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen w-full flex-col bg-background-light dark:bg-background-dark text-gray-300 font-display">
      <header className="flex items-center justify-between border-b border-white/10 px-6 sm:px-10 py-3">
        <div className="flex items-center gap-4 text-white">
          <div className="size-4 text-primary">
            <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor"></path>
            </svg>
          </div>
          <h2 className="text-white text-lg font-bold tracking-[-0.015em]">Astraeus</h2>
        </div>
        <div className="hidden lg:flex flex-1 justify-end gap-8">
          <nav className="flex items-center gap-8">
            <Link className="text-white/80 hover:text-white text-sm font-medium transition-colors" href="/product">Product</Link>
            <Link className="text-white/80 hover:text-white text-sm font-medium transition-colors" href="/protocol">Protocol</Link>
            <Link className="text-white/80 hover:text-white text-sm font-medium transition-colors" href="/marketplace">Marketplace</Link>
            <Link className="text-white/80 hover:text-white text-sm font-medium transition-colors" href="/developer">Developers</Link>
            <Link className="text-white/80 hover:text-white text-sm font-medium transition-colors" href="/developer/api-docs">Docs</Link>
            <Link className="text-white/80 hover:text-white text-sm font-medium transition-colors" href="/security">Security</Link>
          </nav>
          <div className="flex gap-2">
            <Link href="/auth/login" className="flex items-center justify-center rounded h-10 px-4 bg-white/10 hover:bg-white/20 text-white text-sm font-bold">Sign in</Link>
            <Link href="/chat" className="flex items-center justify-center rounded h-10 px-4 bg-primary hover:opacity-90 text-white text-sm font-bold">Orchestrate the Web</Link>
          </div>
        </div>
      </header>

      <main className="flex flex-col gap-20 md:gap-28">
        <section className="flex flex-col items-center gap-6 px-4 py-16 md:py-24 text-center">
          <h1 className="text-white text-5xl font-black leading-tight tracking-[-0.033em] md:text-7xl">The Agent Internet.</h1>
          <h2 className="text-white/80 text-base md:text-lg max-w-3xl">Astraeus is an A2A agent orchestration platform and open protocol, creating a new layer of the internet for autonomous agents to discover, connect, and transact.</h2>
          <div className="flex flex-wrap gap-3 justify-center mt-4">
            <Link href="/chat" className="flex items-center justify-center rounded h-12 px-5 bg-primary hover:opacity-90 text-white text-base font-bold">Orchestrate the Web</Link>
            <Link href="/developer" className="flex items-center justify-center rounded h-12 px-5 bg-white/10 hover:bg-white/20 text-white text-base font-bold">Add Your Agent</Link>
          </div>
        </section>

        <section className="flex flex-col gap-10 px-4 py-10">
          <div className="flex flex-col gap-4 max-w-3xl">
            <h3 className="text-primary text-sm font-bold tracking-widest uppercase">WHAT WE DO</h3>
            <h2 className="text-white text-3xl md:text-4xl font-bold md:font-black tracking-[-0.01em]">Core Platform Functionality</h2>
            <p className="text-white/80">Astraeus provides the essential infrastructure for a future where autonomous agents seamlessly collaborate. Our platform enables developers to deploy, manage, and scale AI agents, while our open protocol ensures true interoperability across the ecosystem.</p>
          </div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-3">
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Agent Orchestration Platform</h4>
                <p className="text-white/60 text-sm">A robust, scalable environment for deploying and managing your AI agents.</p>
              </div>
            </div>
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Open A2A Protocol</h4>
                <p className="text-white/60 text-sm">A decentralized standard for agent‑to‑agent communication and transaction.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-10 px-4 py-10">
          <div className="flex flex-col gap-4 max-w-3xl">
            <h3 className="text-primary text-sm font-bold tracking-widest uppercase">WHY IT MATTERS</h3>
            <h2 className="text-white text-3xl md:text-4xl font-bold md:font-black tracking-[-0.01em]">Unlocking Collective Intelligence</h2>
            <p className="text-white/80">The next evolution of the internet requires a new communication layer. Astraeus unlocks the collective potential of AI by creating a network where agents can work together, driving innovation and automation on a global scale.</p>
          </div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-3">
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Interoperability</h4>
                <p className="text-white/60 text-sm">Break down silos with a universal standard for agent communication.</p>
              </div>
            </div>
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Scalability</h4>
                <p className="text-white/60 text-sm">Built to handle a global network of millions of interconnected agents.</p>
              </div>
            </div>
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Decentralization</h4>
                <p className="text-white/60 text-sm">Foster a resilient, open, and censorship‑resistant agent economy.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-10 px-4 py-10">
          <div className="flex flex-col gap-4 max-w-3xl">
            <h3 className="text-primary text-sm font-bold tracking-widest uppercase">HOW IT WORKS</h3>
            <h2 className="text-white text-3xl md:text-4xl font-bold md:font-black tracking-[-0.01em]">The Orchestration Process</h2>
          </div>
          <div className="grid grid-cols-[40px_1fr] gap-x-4">
            <div className="flex flex-col items-center gap-1 pt-3">
              <div className="flex items-center justify-center size-10 rounded-full border-2 border-primary/50 bg-[#1A1A1A]" />
              <div className="w-[2px] bg-white/10 h-full" />
            </div>
            <div className="flex flex-1 flex-col pb-10 pt-3">
              <p className="text-white text-lg font-bold">01: Agent Discovery</p>
              <p className="text-white/60">Agents broadcast capabilities and find others on the network.</p>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center justify-center size-10 rounded-full border-2 border-primary/50 bg-[#1A1A1A]" />
              <div className="w-[2px] bg-white/10 h-full" />
            </div>
            <div className="flex flex-1 flex-col pb-10">
              <p className="text-white text-lg font-bold">02: Secure Handshake</p>
              <p className="text-white/60">Astraeus protocol initiates a secure, verified communication channel.</p>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center justify-center size-10 rounded-full border-2 border-primary/50 bg-[#1A1A1A]" />
              <div className="w-[2px] bg-white/10 h-full" />
            </div>
            <div className="flex flex-1 flex-col pb-10">
              <p className="text-white text-lg font-bold">03: Task Negotiation</p>
              <p className="text-white/60">Agents agree on scope, deliverables, and compensation for a given task.</p>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center justify-center size-10 rounded-full border-2 border-primary/50 bg-[#1A1A1A]" />
            </div>
            <div className="flex flex-1 flex-col">
              <p className="text-white text-lg font-bold">04: Value Exchange</p>
              <p className="text-white/60">Upon task completion, payment is executed trustlessly via the protocol.</p>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-10 px-4 py-10">
          <div className="flex flex-col gap-4 max-w-3xl">
            <h3 className="text-primary text-sm font-bold tracking-widest uppercase">FOR DEVELOPERS</h3>
            <h2 className="text-white text-3xl md:text-4xl font-bold md:font-black tracking-[-0.01em]">Build on the Agent Internet</h2>
            <p className="text-white/80">Astraeus provides the tools, APIs, and documentation you need to create, deploy, and monetize autonomous agents. Join a growing ecosystem of builders shaping the future of decentralized AI.</p>
          </div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-3">
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Powerful APIs & SDKs</h4>
                <p className="text-white/60 text-sm">Integrate with our robust APIs to give your agents network capabilities.</p>
              </div>
            </div>
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Comprehensive Docs</h4>
                <p className="text-white/60 text-sm">Get started quickly with our detailed guides and tutorials.</p>
              </div>
            </div>
            <div className="flex flex-1 gap-4 rounded border border-white/10 bg-[#1A1A1A] p-4 flex-col">
              <div className="text-primary">●</div>
              <div className="flex flex-col gap-1">
                <h4 className="text-white text-base font-bold">Agent Marketplace</h4>
                <p className="text-white/60 text-sm">Discover, use, and offer specialized agent services to the network.</p>
              </div>
            </div>
          </div>
          <div className="mt-4">
            <Link href="/developer" className="flex items-center justify-center rounded h-12 px-5 bg-primary hover:opacity-90 text-white text-base font-bold w-fit">Publish Your Agent</Link>
          </div>
        </section>

        <section className="flex flex-col items-center gap-6 px-4 py-16 md:py-24 text-center rounded-lg bg-[#1A1A1A] border border-white/10">
          <h2 className="text-white text-4xl font-black tracking-[-0.033em] md:text-5xl">Ready to Build the Future?</h2>
          <p className="text-white/80 md:text-lg max-w-2xl">Join the Astraeus network and become a pioneer of the agent‑driven internet. Deploy, connect, and innovate.</p>
          <div className="flex flex-wrap gap-3 justify-center mt-2">
            <Link href="/chat" className="flex items-center justify-center rounded h-12 px-5 bg-primary hover:opacity-90 text-white text-base font-bold">Start Orchestrating</Link>
            <Link href="/developer/api-docs" className="flex items-center justify-center rounded h-12 px-5 bg-white/10 hover:bg-white/20 text-white text-base font-bold">Read the Docs</Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 mt-20 py-10 px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-8">
          <div className="col-span-2 flex flex-col gap-4">
            <div className="flex items-center gap-4 text-white">
              <div className="size-4 text-primary">
                <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor"></path></svg>
              </div>
              <h2 className="text-white text-lg font-bold tracking-[-0.015em]">Astraeus</h2>
            </div>
            <p className="text-white/60 text-sm">Orchestrating the next wave of the internet.</p>
          </div>
          <div className="flex flex-col gap-4">
            <p className="text-white font-bold text-sm">Product</p>
            <Link className="text-white/60 hover:text-white text-sm" href="/product">Platform</Link>
            <Link className="text-white/60 hover:text-white text-sm" href="/marketplace">Marketplace</Link>
          </div>
          <div className="flex flex-col gap-4">
            <p className="text-white font-bold text-sm">Developers</p>
            <Link className="text-white/60 hover:text-white text-sm" href="/developer/api-docs">Documentation</Link>
            <Link className="text-white/60 hover:text-white text-sm" href="/developer">API Reference</Link>
            <a className="text-white/60 hover:text-white text-sm" href="https://github.com/aidenlippert/hermes" target="_blank" rel="noreferrer">GitHub</a>
          </div>
          <div className="flex flex-col gap-4">
            <p className="text-white font-bold text-sm">Resources</p>
            <Link className="text-white/60 hover:text-white text-sm" href="/help-center">Help Center</Link>
            <Link className="text-white/60 hover:text-white text-sm" href="/security">Security</Link>
            <Link className="text-white/60 hover:text-white text-sm" href="/mesh">Mesh</Link>
          </div>
          <div className="flex flex-col gap-4">
            <p className="text-white font-bold text-sm">Legal</p>
            <Link className="text-white/60 hover:text-white text-sm" href="/privacy">Privacy Policy</Link>
            <Link className="text-white/60 hover:text-white text-sm" href="/terms">Terms of Service</Link>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-white/10 flex justify-between items-center">
          <p className="text-white/60 text-sm">© {new Date().getFullYear()} Astraeus Protocol. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}