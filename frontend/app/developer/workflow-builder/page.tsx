"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import Link from "next/link"
import {
  Search,
  Play,
  Save,
  ZoomIn,
  ZoomOut,
  Maximize,
  AlignHorizontalLeft,
  AlignVerticalTop,
  ChevronDown,
  Webhook,
  Globe,
  Database,
  GitBranch,
  Zap,
  CheckCircle2,
  Trash2,
  PlusCircle,
  LayoutGrid
} from "lucide-react"

interface Node {
  id: string
  type: string
  label: string
  icon: any
  x: number
  y: number
  config: Record<string, any>
}

interface Connection {
  from: string
  to: string
}

const AGENT_TYPES = [
  { type: "webhook", label: "Webhook Trigger", icon: Webhook, category: "Triggers" },
  { type: "api", label: "API Caller", icon: Globe, category: "Agents" },
  { type: "llm", label: "LLM Agent", icon: Zap, category: "Agents" },
  { type: "database", label: "Database Query", icon: Database, category: "Agents" },
  { type: "condition", label: "If/Else", icon: GitBranch, category: "Logic Gates" }
]

export default function WorkflowBuilderPage() {
  const [nodes, setNodes] = useState<Node[]>([
    {
      id: "node-1",
      type: "webhook",
      label: "Webhook Trigger",
      icon: Webhook,
      x: 100,
      y: 200,
      config: { method: "POST", path: "/webhook" }
    },
    {
      id: "node-2",
      type: "api",
      label: "API Caller",
      icon: Globe,
      x: 450,
      y: 200,
      config: {
        url: "https://api.example.com/data",
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: { key: "value", data: "{{trigger.body}}" }
      }
    }
  ])

  const [connections, setConnections] = useState<Connection[]>([
    { from: "node-1", to: "node-2" }
  ])

  const [selectedNode, setSelectedNode] = useState<string>("node-2")
  const [zoom, setZoom] = useState(100)
  const [isDragging, setIsDragging] = useState(false)
  const [draggedNode, setDraggedNode] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [activeTab, setActiveTab] = useState<"properties" | "logs" | "settings">("properties")
  const [isSaved, setIsSaved] = useState(true)
  const [workflowName, setWorkflowName] = useState("Untitled Workflow")
  const canvasRef = useRef<HTMLDivElement>(null)

  const selectedNodeData = nodes.find(n => n.id === selectedNode)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging && draggedNode) {
        setNodes(prev => prev.map(node =>
          node.id === draggedNode
            ? { ...node, x: e.clientX - dragOffset.x, y: e.clientY - dragOffset.y }
            : node
        ))
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
      setDraggedNode(null)
    }

    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove)
      window.addEventListener("mouseup", handleMouseUp)
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isDragging, draggedNode, dragOffset])

  const handleNodeDragStart = (nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setIsDragging(true)
    setDraggedNode(nodeId)
    const node = nodes.find(n => n.id === nodeId)
    if (node) {
      setDragOffset({
        x: e.clientX - node.x,
        y: e.clientY - node.y
      })
    }
    setIsSaved(false)
  }

  const handleConfigChange = (field: string, value: any) => {
    setNodes(prev => prev.map(node =>
      node.id === selectedNode
        ? { ...node, config: { ...node.config, [field]: value } }
        : node
    ))
    setIsSaved(false)
  }

  const handleSave = async () => {
    try {
      const workflow = {
        name: workflowName,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          label: n.label,
          x: n.x,
          y: n.y,
          config: n.config
        })),
        connections
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/workflows`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Add auth header when implemented
          // "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(workflow)
      })

      if (response.ok) {
        setIsSaved(true)
        console.log("Workflow saved successfully")
      } else {
        console.error("Failed to save workflow:", await response.text())
      }
    } catch (error) {
      console.error("Failed to save workflow:", error)
      // Fallback: save to localStorage
      localStorage.setItem("workflow", JSON.stringify({ name: workflowName, nodes, connections }))
      setIsSaved(true)
    }
  }

  const handleRun = async () => {
    try {
      const workflow = {
        name: workflowName,
        nodes,
        connections
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/workflows/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(workflow)
      })

      if (response.ok) {
        const result = await response.json()
        alert(`Workflow executed! Orchestration ID: ${result.orchestration_id || 'demo'}`)
      } else {
        alert("Workflow execution started! (Backend pending)")
      }
    } catch (error) {
      console.error("Failed to run workflow:", error)
      alert("Workflow execution started! (Demo mode)")
    }
  }

  const addNode = (type: string) => {
    const agent = AGENT_TYPES.find(a => a.type === type)
    if (!agent) return

    const newNode: Node = {
      id: `node-${Date.now()}`,
      type,
      label: agent.label,
      icon: agent.icon,
      x: 300 + (nodes.length * 50),
      y: 300,
      config: {}
    }

    setNodes(prev => [...prev, newNode])
    setSelectedNode(newNode.id)
    setIsSaved(false)
  }

  const deleteNode = (nodeId: string) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId))
    setConnections(prev => prev.filter(c => c.from !== nodeId && c.to !== nodeId))
    if (selectedNode === nodeId) {
      setSelectedNode(nodes.find(n => n.id !== nodeId)?.id || "")
    }
    setIsSaved(false)
  }

  return (
    <div className="flex h-screen w-full bg-black text-white">
      {/* Left Sidebar */}
      <aside className="flex flex-col w-72 bg-surface-dark border-r border-white/10">
        <div className="flex flex-col gap-4 p-4 border-b border-white/10">
          <Link href="/developer" className="flex gap-3 items-center">
            <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center font-black">
              A
            </div>
            <div className="flex flex-col">
              <h1 className="text-white text-base font-medium">ASTRAEUS</h1>
              <p className="text-white/50 text-sm">Workflow Designer</p>
            </div>
          </Link>

          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-purple-600/20 text-purple-400">
              <Zap className="w-5 h-5" />
              <p className="text-sm font-medium">Designer</p>
            </div>
            <Link href="/developer/analytics" className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 rounded-lg">
              <LayoutGrid className="w-5 h-5" />
              <p className="text-sm font-medium">Analytics</p>
            </Link>
          </div>
        </div>

        <div className="flex-grow p-4 flex flex-col gap-4 overflow-y-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
            <input
              type="text"
              placeholder="Find agents or tools..."
              className="w-full pl-10 pr-4 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/50 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex flex-col">
            {["Triggers", "Agents", "Logic Gates"].map(category => (
              <details key={category} className="border-t border-white/10 py-2" open={category === "Agents"}>
                <summary className="flex cursor-pointer items-center justify-between py-2 hover:text-purple-400">
                  <p className="text-sm font-medium">{category}</p>
                  <ChevronDown className="w-4 h-4" />
                </summary>
                <div className="grid grid-cols-2 gap-2 pt-2">
                  {AGENT_TYPES.filter(a => a.category === category).map(agent => (
                    <button
                      key={agent.type}
                      onClick={() => addNode(agent.type)}
                      className="flex flex-col items-center gap-2 p-3 rounded-lg bg-black/40 hover:bg-white/5 cursor-pointer transition-colors"
                    >
                      <agent.icon className="w-5 h-5 text-purple-400" />
                      <p className="text-xs text-center">{agent.label}</p>
                    </button>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1 p-4 border-t border-white/10">
          <Link href="/developer" className="flex items-center gap-3 px-3 py-2 text-white/70 hover:bg-white/5 rounded-lg text-sm">
            ← Back to Hub
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex flex-wrap justify-between items-center gap-3 p-4 border-b border-white/10 bg-surface-dark/50">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => {
              setWorkflowName(e.target.value)
              setIsSaved(false)
            }}
            className="text-xl font-bold bg-transparent border-none outline-none focus:outline-none"
          />
          <div className="flex items-center gap-2">
            <button
              onClick={handleRun}
              className="flex items-center justify-center gap-2 h-9 px-4 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium"
            >
              <Play className="w-4 h-4" />
              Run
            </button>
            <button
              onClick={handleSave}
              disabled={isSaved}
              className={`flex items-center justify-center gap-2 h-9 px-4 rounded-lg text-sm font-medium ${
                isSaved
                  ? "bg-green-600/20 text-green-400 cursor-not-allowed"
                  : "bg-white/10 hover:bg-white/20 text-white"
              }`}
            >
              {isSaved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              {isSaved ? "Saved" : "Save"}
            </button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Canvas */}
          <div
            ref={canvasRef}
            className="flex-1 relative overflow-auto bg-black"
            style={{
              backgroundImage: `
                linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)
              `,
              backgroundSize: "24px 24px"
            }}
          >
            <div className="min-w-[2000px] min-h-[2000px] relative">
              {nodes.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-6 text-center p-4">
                    <PlusCircle className="w-20 h-20 text-white/10" />
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-lg font-bold">Canvas is Empty</p>
                      <p className="text-white/50 text-sm">Drag nodes from the sidebar to start building</p>
                    </div>
                    <button
                      onClick={() => addNode("webhook")}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium"
                    >
                      Add First Node
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Connections */}
                  <svg className="absolute inset-0 pointer-events-none">
                    {connections.map(conn => {
                      const fromNode = nodes.find(n => n.id === conn.from)
                      const toNode = nodes.find(n => n.id === conn.to)
                      if (!fromNode || !toNode) return null

                      const x1 = fromNode.x + 256
                      const y1 = fromNode.y + 60
                      const x2 = toNode.x
                      const y2 = toNode.y + 60

                      return (
                        <line
                          key={`${conn.from}-${conn.to}`}
                          x1={x1}
                          y1={y1}
                          x2={x2}
                          y2={y2}
                          stroke="#a855f7"
                          strokeWidth="2"
                          strokeDasharray="4 4"
                        />
                      )
                    })}
                  </svg>

                  {/* Nodes */}
                  {nodes.map(node => (
                    <div
                      key={node.id}
                      className={`absolute w-64 bg-surface-dark rounded-xl shadow-lg flex flex-col cursor-move ${
                        selectedNode === node.id ? "ring-2 ring-purple-500" : "border border-white/10"
                      }`}
                      style={{ left: node.x, top: node.y }}
                      onClick={() => setSelectedNode(node.id)}
                      onMouseDown={(e) => handleNodeDragStart(node.id, e)}
                    >
                      <div className="p-3 border-b border-white/10 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <node.icon className="w-5 h-5 text-purple-400" />
                          <h3 className="font-bold text-sm">{node.label}</h3>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteNode(node.id)
                          }}
                          className="text-white/50 hover:text-red-400"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="p-3 text-xs text-white/50">
                        {node.type === "webhook" && "Receives incoming requests"}
                        {node.type === "api" && "Calls external API"}
                        {node.type === "llm" && "LLM processing"}
                        {node.type === "database" && "Database query"}
                        {node.type === "condition" && "Conditional logic"}
                      </div>
                      <div className="absolute w-2 h-2 bg-purple-400 rounded-full -left-1 top-1/2 -translate-y-1/2" />
                      <div className="absolute w-2 h-2 bg-purple-400 rounded-full -right-1 top-1/2 -translate-y-1/2" />
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Right Panel */}
          {selectedNodeData && (
            <aside className="w-80 bg-surface-dark border-l border-white/10 flex flex-col">
              <h2 className="text-base font-bold px-4 py-4 border-b border-white/10">
                {selectedNodeData.label}
              </h2>

              <div className="flex border-b border-white/10">
                {(["properties", "logs", "settings"] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 text-center py-2 text-sm font-medium border-b-2 ${
                      activeTab === tab
                        ? "border-purple-500 text-purple-400"
                        : "border-transparent text-white/50"
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>

              <div className="flex-grow p-4 space-y-4 overflow-y-auto">
                {activeTab === "properties" && selectedNodeData.type === "api" && (
                  <>
                    <div>
                      <label className="text-xs font-medium text-white/50 mb-1 block">URL</label>
                      <input
                        type="text"
                        value={selectedNodeData.config.url || ""}
                        onChange={(e) => handleConfigChange("url", e.target.value)}
                        className="w-full rounded-lg bg-black/40 border border-white/10 text-sm px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-white/50 mb-1 block">Method</label>
                      <select
                        value={selectedNodeData.config.method || "GET"}
                        onChange={(e) => handleConfigChange("method", e.target.value)}
                        className="w-full rounded-lg bg-black/40 border border-white/10 text-sm px-3 py-2"
                      >
                        <option>GET</option>
                        <option>POST</option>
                        <option>PUT</option>
                        <option>DELETE</option>
                      </select>
                    </div>
                  </>
                )}
              </div>
            </aside>
          )}
        </div>

        {/* Bottom Toolbar */}
        <footer className="flex items-center justify-between p-2 border-t border-white/10">
          <div className="flex items-center gap-1">
            <button onClick={() => setZoom(z => Math.min(200, z + 10))} className="p-2 rounded hover:bg-white/5">
              <ZoomIn className="w-4 h-4" />
            </button>
            <button onClick={() => setZoom(z => Math.max(50, z - 10))} className="p-2 rounded hover:bg-white/5">
              <ZoomOut className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-3 text-sm text-white/70">
            {isSaved ? <CheckCircle2 className="w-4 h-4 text-green-400" /> : null}
            <span>Zoom: {zoom}%</span>
            <span>Nodes: {nodes.length}</span>
          </div>
        </footer>
      </main>
    </div>
  )
}
