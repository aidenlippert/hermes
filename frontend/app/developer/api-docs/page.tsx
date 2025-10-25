"use client"

import Link from "next/link"
import { useState } from "react"
import { 
  Search, 
  PlayCircle, 
  Key, 
  Gauge, 
  Bot, 
  Share, 
  Waves, 
  FileCode, 
  FileJson, 
  AlertTriangle, 
  Copy,
  Book,
  GitCompare,
  Package
} from "lucide-react"

const CodeBlock = ({ code, language }: { code: string, language: string }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="mt-4 relative bg-surface-dark rounded-xl p-4">
      <button onClick={handleCopy} className="absolute top-3 right-3 text-text-muted-dark hover:text-white transition-colors">
        <Copy className="w-4 h-4" />
      </button>
      <pre className="text-sm code-highlight overflow-x-auto"><code className={`language-${language}`}>{code}</code></pre>
    </div>
  )
}

export default function ApiDocsPage() {
  const curlCode = `curl --request POST -L \\
  --url 'https://api.hermes.io/v1/agents' \\
  --header 'Authorization: Bearer <api_key>' \\
  --header 'Content-Type: application/json' \\
  --data '{
    "name": "data-processor-01",
    "type": "data_processor",
    "config": {
      "retries": 3,
      "timeout": 60
    }
  }'`

  const successResponse = `{
  "agent_id": "agt-1a2b3c4d5e6f",
  "name": "data-processor-01",
  "status": "registered",
  "created_at": "2023-10-27T10:00:00Z"
}`

  return (
    <div className="flex min-h-screen font-display bg-background-dark text-text-light">
      <aside className="w-72 flex-shrink-0 bg-black/30 border-r border-white/10 flex flex-col p-4 fixed h-full">
        <div className="flex items-center gap-3 mb-6 px-3">
          <div 
            className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" 
            style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAd0OsjIVn67sYrClEVWpvrcNLrXx2aMsNxcHaLiNvkFtyMi1fLPY7z2WhRKFpbEDTVWAjM3Fav9SZnGgIzUiqM0FSafICHVP_61Bh7ehst3CFKVRkQ_eUpJ9aWOw5KmweGaDsk-nU7mnSYhmFkGeqkveg1sq8Wd-HrYGCPQaK6xM7A7n250n6M2fzbimtzUVSS2JLrk3Pd4NjQ-ZwnFtqJLF2h6XYorIdLA_-MzuZuRcCdv6T-QQxrgxeCKab5ykFSYQyBkyjHGbyy")'}}
          ></div>
          <div className="flex flex-col">
            <h1 className="text-white text-base font-medium leading-normal">Hermes</h1>
            <p className="text-text-muted-dark text-sm font-normal leading-normal">A2A Orchestration</p>
          </div>
        </div>
        
        <div className="mb-4">
          <label className="flex flex-col min-w-40 h-11 w-full">
            <div className="flex w-full flex-1 items-stretch rounded-lg h-full">
              <div className="text-text-muted-dark flex border-none bg-surface-dark items-center justify-center pl-3 rounded-l-lg border-r-0">
                <Search className="w-5 h-5" />
              </div>
              <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-white focus:outline-0 focus:ring-0 border-none bg-surface-dark focus:border-none h-full placeholder:text-text-muted-dark px-4 rounded-l-none border-l-0 pl-2 text-sm font-normal leading-normal" placeholder="Search documentation..." />
            </div>
          </label>
        </div>

        <nav className="flex-grow overflow-y-auto pr-2">
          <div className="flex flex-col gap-1">
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <PlayCircle className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Getting Started</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <Key className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Authentication</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <Gauge className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Rate Limits</p>
            </Link>
            <p className="text-text-muted-dark text-xs font-bold uppercase tracking-wider px-3 pt-6 pb-2">API Endpoints</p>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/20 text-primary transition-colors duration-200">
              <Bot className="w-5 h-5" />
              <p className="text-primary text-sm font-bold leading-normal">Agent Management</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <Share className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Task Orchestration</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <Waves className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Data Streams</p>
            </Link>
            <p className="text-text-muted-dark text-xs font-bold uppercase tracking-wider px-3 pt-6 pb-2">SDK Modules</p>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <FileCode className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Python SDK</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <FileJson className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">JavaScript SDK</p>
            </Link>
            <p className="text-text-muted-dark text-xs font-bold uppercase tracking-wider px-3 pt-6 pb-2">Reference</p>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <Book className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Error Codes</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-dark transition-colors duration-200">
              <GitCompare className="w-5 h-5 text-text-muted-dark" />
              <p className="text-text-light text-sm font-medium leading-normal">Responses</p>
            </Link>
          </div>
        </nav>
      </aside>

      <main className="ml-72 flex-1 p-8 lg:p-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            <Link className="text-text-muted-dark text-sm font-medium leading-normal hover:text-text-light" href="#">API Endpoints</Link>
            <span className="text-text-muted-dark text-sm font-medium leading-normal">/</span>
            <Link className="text-text-muted-dark text-sm font-medium leading-normal hover:text-text-light" href="#">Agent Management</Link>
            <span className="text-text-muted-dark text-sm font-medium leading-normal">/</span>
            <span className="text-white text-sm font-medium leading-normal">Create Agent</span>
          </div>

          <header className="mb-10">
            <p className="text-primary font-mono text-lg font-medium mb-1">POST</p>
            <h1 className="text-white text-4xl font-black leading-tight tracking-[-0.033em] font-mono">/v1/agents</h1>
            <p className="text-text-muted-dark text-base font-normal leading-normal mt-3 max-w-2xl">
              Creates a new agent instance within the platform. This endpoint registers the agent and prepares it for task assignment.
            </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-12">
            <div className="lg:col-span-3 space-y-12">
              <section>
                <h2 className="text-2xl font-bold text-white border-b border-white/10 pb-3 mb-4">Request Body</h2>
                <div className="space-y-4">
                  <div className="font-mono">
                    <p className="text-text-light"><span className="font-bold">name</span> <span className="text-primary">string</span> <span className="text-text-muted-dark">required</span></p>
                    <p className="text-text-muted-dark pl-4">A unique identifier for the agent.</p>
                  </div>
                  <div className="font-mono">
                    <p className="text-text-light"><span className="font-bold">type</span> <span className="text-primary">string</span> <span className="text-text-muted-dark">required</span></p>
                    <p className="text-text-muted-dark pl-4">Specifies the agent's capability (e.g., "data_processor", "alert_monitor").</p>
                  </div>
                  <div className="font-mono">
                    <p className="text-text-light"><span className="font-bold">config</span> <span className="text-primary">object</span></p>
                    <p className="text-text-muted-dark pl-4">A JSON object containing agent-specific configuration.</p>
                  </div>
                </div>
              </section>

              <div className="flex items-start gap-4 p-4 rounded-lg bg-primary/10 border border-primary/30">
                <AlertTriangle className="text-primary mt-1 w-5 h-5" />
                <div>
                  <h3 className="font-bold text-white">Security Notice</h3>
                  <p className="text-text-muted-dark text-sm">Agent names must be unique across your organization. Duplicate names will result in a <code className="bg-surface-dark px-1.5 py-0.5 rounded text-primary">409 Conflict</code> error.</p>
                </div>
              </div>

              <section>
                <h2 className="text-2xl font-bold text-white border-b border-white/10 pb-3 mb-4">Responses</h2>
                <div className="space-y-4 font-mono">
                  <div>
                    <p><span className="bg-green-500/20 text-green-400 font-bold px-2 py-1 rounded-md text-sm">201 Created</span> - Agent successfully created.</p>
                  </div>
                  <div>
                    <p><span className="bg-yellow-500/20 text-yellow-400 font-bold px-2 py-1 rounded-md text-sm">400 Bad Request</span> - Invalid request body.</p>
                  </div>
                  <div>
                    <p><span className="bg-red-500/20 text-red-400 font-bold px-2 py-1 rounded-md text-sm">409 Conflict</span> - An agent with this name already exists.</p>
                  </div>
                </div>
              </section>
            </div>

            <div className="lg:col-span-2">
              <div className="sticky top-12">
                <div>
                  <div className="flex border-b border-white/10 gap-6">
                    <a className="flex flex-col items-center justify-center border-b-[3px] border-b-primary text-white pb-3 pt-2" href="#">
                      <p className="text-white text-sm font-bold leading-normal">cURL</p>
                    </a>
                    <a className="flex flex-col items-center justify-center border-b-[3px] border-b-transparent text-text-muted-dark pb-3 pt-2 hover:text-white" href="#">
                      <p className="text-sm font-bold leading-normal">Python</p>
                    </a>
                    <a className="flex flex-col items-center justify-center border-b-[3-px] border-b-transparent text-text-muted-dark pb-3 pt-2 hover:text-white" href="#">
                      <p className="text-sm font-bold leading-normal">Node.js</p>
                    </a>
                  </div>
                </div>
                
                <CodeBlock code={curlCode} language="bash" />

                <p className="text-text-muted-dark text-sm mt-6 font-semibold">SUCCESS RESPONSE</p>
                <CodeBlock code={successResponse} language="json" />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
