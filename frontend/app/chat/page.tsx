"use client"

"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Sparkles, Send, Search, Shield, Zap, Star, Check, Copy, Clock, Terminal, Verified, User2 } from "lucide-react"
import { api, createWebSocket } from "@/lib/api"
import { useAuthStore } from "@/lib/store"
import withAuth from "@/components/withAuth"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  agents: any[]
  error?: string
}

const initialMessage: Message = {
  id: "1",
  role: "assistant",
  content: "Hello! I'm Hermes. What would you like to accomplish today?",
  timestamp: new Date(),
  agents: []
}

function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([initialMessage])
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState("")
  const [discoveryPhase, setDiscoveryPhase] = useState<string | null>(null)
  const [currentAgents, setCurrentAgents] = useState<any[]>([])
  const [selectedAgents, setSelectedAgents] = useState<Record<string, boolean>>({})
  const [awaitingApproval, setAwaitingApproval] = useState(false)
  const [constraints, setConstraints] = useState<string[]>([])
  const [executionSteps, setExecutionSteps] = useState<any[]>([])
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const accessToken = useAuthStore((s) => s.accessToken)
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingText])

  useEffect(() => () => { wsConnection?.close() }, [wsConnection])

  const handleSend = useCallback(async () => {
    if (!input.trim() || isStreaming || !accessToken) return

    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input, timestamp: new Date(), agents: [] }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsStreaming(true)
    setDiscoveryPhase("Analyzing your request...")
    setCurrentAgents([])
    setExecutionSteps([])
    setAwaitingApproval(false)

    try {
      const response = await api.chat.send({ query: userMessage.content }, accessToken)
      setCurrentTaskId(response.task_id)
      setDiscoveryPhase("Orchestrating agents...")

      const ws = createWebSocket(response.task_id, accessToken)
      setWsConnection(ws)
      ws.onmessage = (ev) => {
        const data = JSON.parse(ev.data)
        if (data.type === "agents_discovered") {
          setDiscoveryPhase(`Found ${data.agents.length} specialized agents!`)
          setCurrentAgents(data.agents)
          const initial: Record<string, boolean> = {}
          data.agents.forEach((a: any) => { initial[a.name || a.id] = true })
          setSelectedAgents(initial)
        } else if (data.type === "awaiting_approval") {
          setAwaitingApproval(true)
          setCurrentAgents(data.agents || [])
        } else if (data.type === "execution_started") {
          setDiscoveryPhase("Executing agents...")
          setExecutionSteps(data.steps || [])
        } else if (data.type === "step_update") {
          setExecutionSteps((prev) => prev.map((s: any, i: number) => i === data.step_index ? { ...s, status: data.status } : s))
        } else if (data.type === "streaming_token") {
          setStreamingText((prev) => prev + (data.token || ""))
        } else if (data.type === "task_complete" || data.type === "execution_completed") {
          setDiscoveryPhase(null)
          const assistantMessage: Message = { id: Date.now().toString(), role: "assistant", content: data.result || data.message || "Task completed!", timestamp: new Date(), agents: currentAgents }
          setMessages((prev) => [...prev, assistantMessage])
          setStreamingText("")
          setIsStreaming(false)
          setCurrentAgents([])
          ws.close()
        } else if (data.type === "error") {
          setDiscoveryPhase(null)
          setExecutionSteps([])
          setMessages((prev) => [...prev, { id: Date.now().toString(), role: "assistant", content: "An error occurred.", timestamp: new Date(), agents: [], error: data.error }])
          setStreamingText("")
          setIsStreaming(false)
          setCurrentAgents([])
          ws.close()
        }
      }
    } catch (e) {
      setDiscoveryPhase(null)
      setIsStreaming(false)
      setMessages((prev) => [...prev, { id: Date.now().toString(), role: "assistant", content: "Sorry, I encountered an error.", timestamp: new Date(), agents: [] }])
    }
  }, [input, isStreaming, accessToken, currentAgents])

  const handleApprove = useCallback(async () => {
    if (!accessToken || !currentTaskId) return
    try {
      await api.chat.approve({ task_id: currentTaskId, conversation_id: "", approved: true, extracted_info: { approved_agents: Object.entries(selectedAgents).filter(([, v]) => v).map(([k]) => k), constraints } }, accessToken)
      setAwaitingApproval(false)
    } catch (e) { console.error(e) }
  }, [accessToken, currentTaskId, selectedAgents, constraints])

  return (
    <div className="flex h-screen bg-background-dark text-gray-100">
      <main className="flex-1 flex flex-col">
        <div className="flex-shrink-0 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-bold">Astraeus Orchestrator - Active</h3>
          <a href="/orchestration/history" className="text-sm text-gray-400 hover:text-white">View History →</a>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((m) => (
              <div key={m.id} className="flex gap-3">
                <div className={`w-8 h-8 rounded-full ${m.role === 'assistant' ? 'bg-red-600' : 'bg-gray-700'}`} />
                <div className="flex-1">
                  <div className={`rounded-xl px-4 py-3 border ${m.role === 'assistant' ? 'border-gray-700 bg-black/40' : 'border-gray-800 bg-gray-900'}`}>{m.content}</div>
                </div>
              </div>
            ))}

            {streamingText && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-red-600" />
                <div className="flex-1 rounded-xl px-4 py-3 border border-gray-700 bg-black/40">
                  {streamingText}
                </div>
              </div>
            )}

            {discoveryPhase && (
              <Card className="border-orange-800 bg-orange-950/20">
                <CardContent className="p-4 flex items-center gap-3">
                  <Loader2 className="w-5 h-5 text-orange-400 animate-spin" />
                  <p className="text-sm text-orange-200">{discoveryPhase}</p>
                </CardContent>
              </Card>
            )}

            {currentAgents.length > 0 && (
              <Card className="border-gray-700 bg-black/50">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2"><Search className="w-5 h-5"/> Discovered Agents ({currentAgents.length})</CardTitle>
                  <CardDescription>Review and select agents for this task</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {currentAgents.map((agent: any) => (
                    <div key={agent.id} className="p-4 bg-gray-900 rounded-xl border border-gray-700">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-red-600 to-red-500 flex items-center justify-center"><Sparkles className="w-6 h-6 text-white"/></div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-sm">{agent.name}</h4>
                            {agent.verified && <Verified className="w-4 h-4 text-blue-500"/>}
                          </div>
                          <p className="text-xs text-gray-300 mb-2">{agent.description}</p>
                          <div className="flex items-center gap-4 text-xs">
                            <div className="flex items-center gap-1"><Star className="w-3 h-3 text-yellow-500 fill-yellow-500"/><span>{agent.rating || agent.average_rating || 0}</span></div>
                            <div className="flex items-center gap-1"><Zap className="w-3 h-3 text-gray-400"/><span>{agent.total_calls || agent.calls || 0}</span></div>
                            <div className="ml-auto"><input type="checkbox" checked={!!selectedAgents[agent.name || agent.id]} onChange={() => setSelectedAgents((p) => ({...p, [agent.name || agent.id]: !p[agent.name || agent.id]}))}/></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {awaitingApproval && (
                    <div className="mt-4 rounded border border-red-500/40 bg-red-500/10 p-4">
                      <h4 className="text-base font-bold text-white">Approval Required</h4>
                      <p className="mt-1 text-sm text-gray-300">Confirm the selected agents. You can uncheck any before proceeding.</p>
                      <div className="mt-3 flex gap-3">
                        <Button onClick={handleApprove} className="bg-red-600 hover:bg-red-500"><Sparkles className="w-5 h-5 mr-2"/>Approve & Execute</Button>
                        <Button variant="outline" onClick={() => {
                          const c = prompt('Add a constraint (e.g., max cost $0.02)');
                          if (c) setConstraints((prev) => [...prev, c])
                        }} className="border-gray-600 text-gray-200">Add Constraint</Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {executionSteps.length > 0 && (
              <Card className="border-gray-700">
                <CardHeader><CardTitle className="text-lg flex items-center gap-2"><Terminal className="w-5 h-5"/>Execution Progress</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {executionSteps.map((step, idx) => (
                      <div key={idx} className={`p-3 rounded-lg border ${step.status === 'completed' ? 'bg-green-900/20 border-green-700' : step.status === 'executing' ? 'bg-blue-900/20 border-blue-700' : 'bg-gray-900 border-gray-700'}`}>
                        <div className="flex items-center gap-3">
                          {step.status === 'completed' ? <Check className="w-5 h-5 text-green-400"/> : step.status === 'executing' ? <Loader2 className="w-5 h-5 text-blue-400 animate-spin"/> : <Clock className="w-5 h-5 text-gray-400"/>}
                          <span className="text-sm font-medium">{step.agent || step.name || `Step ${idx+1}`}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="flex-shrink-0 border-t border-gray-800">
          <div className="max-w-4xl mx-auto px-6 py-4 flex items-end gap-4">
            <textarea ref={textareaRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }} placeholder=">_ Type a command or query..." disabled={isStreaming} rows={1} className="flex-1 px-5 py-3 bg-gray-900 border-2 border-gray-700 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent placeholder-gray-400 disabled:opacity-50 max-h-32 text-sm text-gray-100"/>
            <Button onClick={handleSend} disabled={isStreaming || !input.trim()} className="rounded-xl px-6 bg-red-600 hover:bg-red-500">{isStreaming ? <Loader2 className="w-5 h-5 animate-spin"/> : (<><Send className="w-5 h-5 mr-2"/>Send</>)}</Button>
          </div>
          <div className="max-w-4xl mx-auto px-6 pb-4 flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1"><Shield className="w-3 h-3"/>End-to-end encrypted</span>
            <span className="flex items-center gap-1"><Zap className="w-3 h-3"/>Powered by A2A Protocol</span>
          </div>
        </div>
      </main>
    </div>
  )
}

export default withAuth(ChatPage)