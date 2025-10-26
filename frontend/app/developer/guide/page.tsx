"use client"

import Link from "next/link"
import { 
  Package, 
  LayoutGrid, 
  Download, 
  Code, 
  PlayCircle, 
  Copy, 
  Info,
  BrainCircuit,
  GitBranchPlus,
  Network
} from "lucide-react"

const CodeBlock = ({ code, language }: { code: string, language: string }) => (
  <div className="relative bg-background-dark rounded-lg border border-[#1C1C1E] font-mono text-sm">
    <div className="absolute top-2 right-2">
      <button className="flex items-center gap-2 px-2 py-1 bg-[#1C1C1E] rounded text-white/70 hover:text-white transition-colors text-xs">
        <Copy className="w-4 h-4" /> Copy
      </button>
    </div>
    <pre className="p-4 overflow-x-auto"><code className={`language-${language}`}>{code}</code></pre>
  </div>
)

export default function DeveloperOnboardingPage() {
  const pythonCode = `from hermes import Agent, on_message

agent = Agent("hello_agent")

@agent.on_message
def handle_message(payload):
    print(f"Received message: {payload}")
    return {"response": "Hello from agent!"}

if __name__ == "__main__":
    agent.run()`

  return (
    <div className="font-display bg-background-dark text-[#EAEAEA]">
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-solid border-[#1C1C1E] bg-background-dark/80 px-6 sm:px-10 py-3 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="size-8 text-primary">
            <Package className="w-full h-full" />
          </div>
          <h2 className="text-white text-xl font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
        </div>
        <div className="hidden md:flex flex-1 justify-end gap-8">
          <div className="flex items-center gap-9">
            <Link className="text-white text-sm font-medium leading-normal hover:text-primary transition-colors" href="/developer/guide">Docs</Link>
            <Link className="text-white text-sm font-medium leading-normal hover:text-primary transition-colors" href="/developer/api-docs">API Reference</Link>
            <Link className="text-white text-sm font-medium leading-normal hover:text-primary transition-colors" href="/chat">Console</Link>
          </div>
          <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary hover:brightness-110 transition-all text-white text-sm font-bold leading-normal tracking-[0.015em]">
            <span className="truncate">Download SDK</span>
          </button>
        </div>
      </header>

      <main className="pt-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-16">
            <div className="p-4">
              <div 
                className="flex min-h-[480px] flex-col gap-8 rounded-xl items-start justify-end p-10 border border-[#1C1C1E]" 
                style={{backgroundImage: 'linear-gradient(rgba(10, 10, 11, 0.4) 0%, rgba(10, 10, 11, 0.8) 100%), url("https://lh3.googleusercontent.com/aida-public/AB6AXuAqERvFVx-pr1V7cgrk2gDapIXvUHNDGedG42fmQ-naJpF01lcgJTm-8R1N-1SHv_W_sH_6515eK_tPJzCVnPrRic7gxg_vqMLo-uswQrHUD71was8-G6m-HhTeOLZiIWoWL0Sv3em3kgdwwS3Pkgy9w3woaegizlgMq3sqQLmwnchdfxBR_han7k829WnYc2Ai1FqYPUhkT6-CCf821Sk7h61nhVlpbZShrQU-yVn4__Z3XQpOBy9LoeLD-Ch-ZM_kzkd8PO3Zqkdr")'}}
              >
                <div className="flex flex-col gap-2 text-left">
                  <h1 className="text-white text-5xl font-black leading-tight tracking-[-0.033em]">Build Your First Hermes Agent</h1>
                  <h2 className="text-[#EAEAEA]/80 text-base font-normal leading-normal max-w-2xl">An introductory guide to creating, testing, and deploying agents on the Hermes orchestration platform.</h2>
                </div>
                <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-5 bg-primary/20 border border-primary text-primary hover:bg-primary hover:text-white transition-colors text-base font-bold leading-normal tracking-[0.015em]">
                  <span className="truncate">View Quickstart Video</span>
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-12 gap-8">
            <aside className="hidden lg:block col-span-3 sticky top-24 h-screen">
              <div className="flex flex-col gap-4 p-4 border border-[#1C1C1E] bg-[#1C1C1E]/20 rounded-lg">
                <div className="flex flex-col gap-2">
                  <Link className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/20 text-primary" href="#overview">
                    <LayoutGrid className="w-5 h-5" />
                    <p className="text-sm font-medium leading-normal">Overview</p>
                  </Link>
                  <Link className="flex items-center gap-3 px-3 py-2 rounded-lg text-white hover:bg-white/10 transition-colors" href="#setup">
                    <Download className="w-5 h-5" />
                    <p className="text-sm font-medium leading-normal">Setup</p>
                  </Link>
                  <Link className="flex items-center gap-3 px-3 py-2 rounded-lg text-white hover:bg-white/10 transition-colors" href="#develop">
                    <Code className="w-5 h-5" />
                    <p className="text-sm font-medium leading-normal">Develop</p>
                  </Link>
                  <Link className="flex items-center gap-3 px-3 py-2 rounded-lg text-white hover:bg-white/10 transition-colors" href="#test">
                    <PlayCircle className="w-5 h-5" />
                    <p className="text-sm font-medium leading-normal">Test & Deploy</p>
                  </Link>
                </div>
              </div>
            </aside>

            <div className="col-span-12 lg:col-span-9 space-y-12">
              <section className="flex flex-col gap-4 p-6 border border-[#1C1C1E] bg-[#1C1C1E]/20 rounded-lg" id="overview">
                <h2 className="text-white text-2xl font-bold leading-tight tracking-[-0.015em]">1. Introduction & Protocol Overview</h2>
                <p className="text-[#EAEAEA]/80 text-base font-normal leading-normal">Hermes is an advanced A2A (Agent-to-Agent) orchestration platform. It provides the infrastructure for creating, managing, and deploying autonomous agents that can communicate and collaborate securely. This guide will walk you through building your first agent, from initial setup to deployment.</p>
                <div className="mt-4 p-6 bg-background-dark border border-[#1C1C1E] rounded-lg">
                  <h3 className="text-lg font-bold mb-4">A2A Communication Flow</h3>
                  <div className="flex items-center justify-around text-center text-sm">
                    <div className="flex flex-col items-center gap-2">
                      <div className="p-3 rounded-full border-2 border-[#00B8D4] bg-[#00B8D4]/10"><BrainCircuit className="text-[#00B8D4] w-8 h-8" /></div>
                      <p>Agent A</p>
                    </div>
                    <div className="flex-1 border-t-2 border-dashed border-white/20 mx-4"></div>
                    <div className="flex flex-col items-center gap-2 text-primary">
                      <div className="p-3 rounded-full border-2 border-primary bg-primary/10"><Network className="w-8 h-8" /></div>
                      <p>Hermes<br/>Orchestrator</p>
                    </div>
                    <div className="flex-1 border-t-2 border-dashed border-white/20 mx-4"></div>
                    <div className="flex flex-col items-center gap-2">
                      <div className="p-3 rounded-full border-2 border-[#00B8D4] bg-[#00B8D4]/10"><GitBranchPlus className="text-[#00B8D4] w-8 h-8" /></div>
                      <p>Agent B</p>
                    </div>
                  </div>
                </div>
              </section>

              <section className="flex flex-col gap-4 p-6 border border-[#1C1C1E] bg-[#1C1C1E]/20 rounded-lg" id="setup">
                <h2 className="text-white text-2xl font-bold leading-tight tracking-[-0.015em]">2. Setup: SDK Installation</h2>
                <p className="text-[#EAEAEA]/80 text-base font-normal leading-normal">Before you begin, ensure you have the necessary prerequisites installed on your system. The Hermes SDK is available via pip.</p>
                <div className="my-4 space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer"><input className="w-5 h-5 rounded bg-transparent border-white/30 text-primary focus:ring-primary focus:ring-offset-background-dark" type="checkbox"/><span className="text-white">Python 3.9+</span></label>
                  <label className="flex items-center gap-3 cursor-pointer"><input className="w-5 h-5 rounded bg-transparent border-white/30 text-primary focus:ring-primary focus:ring-offset-background-dark" type="checkbox"/><span className="text-white">pip & venv</span></label>
                </div>
                <CodeBlock code="$ pip install hermes-sdk" language="bash" />
                <div className="mt-4 flex items-start gap-3 p-4 rounded-lg bg-primary/10 border border-primary/50 text-primary">
                  <Info className="mt-1 w-5 h-5" />
                  <p className="text-sm">It is highly recommended to install the SDK within a Python virtual environment to avoid dependency conflicts.</p>
                </div>
              </section>

              <section className="flex flex-col gap-4 p-6 border border-[#1C1C1E] bg-[#1C1C1E]/20 rounded-lg" id="develop">
                <h2 className="text-white text-2xl font-bold leading-tight tracking-[-0.015em]">3. Develop: Agent Workflow</h2>
                <p className="text-[#EAEAEA]/80 text-base font-normal leading-normal">Creating an agent involves defining its behavior, building its capabilities, and registering it with the platform. Here is a minimal "Hello, World" agent example.</p>
                <CodeBlock code={pythonCode} language="python" />
              </section>

              <section className="flex flex-col gap-4 p-6 border border-[#1C1C1E] bg-[#1C1C1E]/20 rounded-lg" id="test">
                <h2 className="text-white text-2xl font-bold leading-tight tracking-[-0.015em]">4. Test & Deploy</h2>
                <p className="text-[#EAEAEA]/80 text-base font-normal leading-normal">Use the Hermes CLI to test your agent locally before deploying it to the platform. Save your agent code as `agent.py` and run the following command.</p>
                <CodeBlock code={`$ hermes test agent.py --payload '{"message": "ping"}'`} language="bash" />
                <p className="text-[#EAEAEA]/80 text-base font-normal leading-normal pt-4">Once you are satisfied with its behavior, you can register and deploy your agent using the console or the CLI.</p>
              </section>

              <section className="flex flex-col gap-4 p-6 border border-[#1C1C1E] bg-[#1C1C1E]/20 rounded-lg" id="next-steps">
                <h2 className="text-white text-2xl font-bold leading-tight tracking-[-0.015em]">Next Steps</h2>
                <p className="text-[#EAEAEA]/80 text-base font-normal leading-normal">You've built your first agent! Now you're ready to explore more advanced topics and build more complex automations.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <Link className="group flex flex-col gap-1 p-4 rounded-lg border border-[#1C1C1E] hover:border-primary/50 hover:bg-primary/10 transition-all" href="#">
                    <h3 className="text-base font-bold text-white group-hover:text-primary">Full Documentation</h3>
                    <p className="text-sm text-white/70">Dive deep into the Hermes SDK and platform features.</p>
                  </Link>
                  <Link className="group flex flex-col gap-1 p-4 rounded-lg border border-[#1C1C1E] hover:border-primary/50 hover:bg-primary/10 transition-all" href="#">
                    <h3 className="text-base font-bold text-white group-hover:text-primary">API Reference</h3>
                    <p className="text-sm text-white/70">Explore all available classes, methods, and functions.</p>
                  </Link>
                  <Link className="group flex flex-col gap-1 p-4 rounded-lg border border-[#1C1C1E] hover:border-primary/50 hover:bg-primary/10 transition-all" href="#">
                    <h3 className="text-base font-bold text-white group-hover:text-primary">Agent Examples</h3>
                    <p className="text-sm text-white/70">Browse a library of pre-built agents for inspiration.</p>
                  </Link>
                  <Link className="group flex flex-col gap-1 p-4 rounded-lg border border-[#1C1C1E] hover:border-primary/50 hover:bg-primary/10 transition-all" href="#">
                    <h3 className="text-base font-bold text-white group-hover:text-primary">Community Forum</h3>
                    <p className="text-sm text-white/70">Join the discussion and get help from other developers.</p>
                  </Link>
                </div>
              </section>
            </div>
          </div>
        </div>
      </main>

      <footer className="mt-24 py-8 px-6 border-t border-[#1C1C1E]">
        <div className="max-w-7xl mx-auto text-center text-sm text-white/50">
          © 2024 Hermes Protocol. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
