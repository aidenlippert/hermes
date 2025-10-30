"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Send,
  Loader2,
  Sparkles,
  User2,
  LogOut,
  Menu,
  Search,
  DollarSign,
  Star,
  Bot,
  Zap,
  Shield,
  ChevronRight,
  MessageSquare,
  Plus,
  Settings,
  History,
  Bookmark,
  Share2,
  Copy,
  Check,
  AlertCircle,
  Activity,
  Brain,
  Globe,
  Code,
  FileText,
  BarChart3,
  Briefcase,
  Palette,
  Database,
  Terminal,
  Verified,
  TrendingUp,
  Clock
} from "lucide-react"
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import withAuth from "@/components/withAuth";
import { api, createWebSocket } from "@/lib/api";

// Chat interfaces
interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  agents: any[]
  error?: string
}

interface ChatHistory {
  id: string
  title: string
  lastMessage: string
  timestamp: Date
  messages: Message[]
}

const initialMessage: Message = {
  id: "1",
  role: "assistant",
  content: "Hello! I'm Hermes, your AI agent orchestrator. I can help you find and coordinate specialized AI agents for any task. What would you like to accomplish today?",
  timestamp: new Date(),
  agents: []
}

const suggestedPrompts = [
  {
    icon: Globe,
    text: "Find me flights from NYC to Paris next month",
    category: "Travel"
  },
  {
    icon: Code,
    text: "Help me debug this React component",
    category: "Development"
  },
  {
    icon: BarChart3,
    text: "Analyze this dataset and create visualizations",
    category: "Analytics"
  },
  {
    icon: FileText,
    text: "Write a blog post about AI trends",
    category: "Content"
  }
]

function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([initialMessage])
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>([])
  const [availableAgents, setAvailableAgents] = useState<any[]>([])
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState("")
  const [currentAgents, setCurrentAgents] = useState<any[]>([])
  const [discoveryPhase, setDiscoveryPhase] = useState<string | null>(null)
  const [executionSteps, setExecutionSteps] = useState<any[]>([])
  const [awaitingApproval, setAwaitingApproval] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [mounted, setMounted] = useState(false)
  const logout = useAuthStore((state) => state.logout);
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Define callbacks before effects to avoid any TDZ issues on some bundlers
  const loadChatHistory = useCallback(async () => {
    if (!accessToken) return
    setLoadingHistory(true)
    try {
      const response = await api.chat.history(accessToken)
      if (response && response.conversations) {
        const histories: ChatHistory[] = response.conversations.map((conv: any) => ({
          id: conv.id,
          title: conv.title || "Untitled Chat",
          lastMessage: conv.last_message || "",
          timestamp: new Date(conv.created_at),
          messages: conv.messages || []
        }))
        setChatHistories(histories)
      }
    } catch (error) {
      console.error("Failed to load chat history:", error)
      setChatHistories([])
    } finally {
      setLoadingHistory(false)
    }
  }, [accessToken])

  const loadAvailableAgents = useCallback(async () => {
    setLoadingAgents(true)
    try {
      // Try authenticated request first
      const response = accessToken
        ? await api.agents.list(accessToken)
        : await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents`).then(res => res.json())

      if (response && response.agents) {
        setAvailableAgents(response.agents)
      }
    } catch (error) {
      console.error("Failed to load agents:", error)
      // Use default agents if API fails
      setAvailableAgents([
        {
          id: "flight-finder",
          name: "FlightFinder Pro",
          description: "Searches flights across airlines with real-time pricing",
          category: "travel",
          rating: 4.9,
          usage_count: 45200
        },
        {
          id: "code-assist",
          name: "CodeAssist Ultra",
          description: "Advanced code generation and debugging assistant",
          category: "development",
          rating: 4.9,
          usage_count: 128000
        }
      ])
    } finally {
      setLoadingAgents(false)
    }
  }, [accessToken])

  useEffect(() => {
    setMounted(true)
    // Load chat history and available agents when component mounts
    if (accessToken) {
      loadChatHistory()
      loadAvailableAgents()
    }
  }, [accessToken, loadChatHistory, loadAvailableAgents])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingText])

  useEffect(() => {
    // Cleanup WebSocket on unmount
    return () => {
      if (wsConnection) {
        wsConnection.close()
      }
    }
  }, [wsConnection])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px"
    }
  }, [input])

  if (!mounted) return null

  

  const simulateTokenStreaming = (text: string) => {
    setStreamingText("")
    const words = text.split(" ")
    let currentIndex = 0

    const interval = setInterval(() => {
      if (currentIndex < words.length) {
        setStreamingText((prev) => prev + (prev ? " " : "") + words[currentIndex])
        currentIndex++
      } else {
        clearInterval(interval)
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: "assistant",
          content: text,
          timestamp: new Date(),
          agents: currentAgents
        }])
        setStreamingText("")
        setIsStreaming(false)
        setCurrentAgents([])
      }
    }, 50)
  }

  const handleSend = async () => {
    if (!input.trim() || isStreaming || !accessToken) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
      agents: []
    }

    setMessages(prev => [...prev, userMessage])
    const query = input
    setInput("")
    setIsStreaming(true)
    setCurrentAgents([])
    setDiscoveryPhase("Analyzing your request...")
    setExecutionSteps([])
    setAwaitingApproval(false)

    try {
      // Call the real backend API
      const response = await api.chat.send({ query }, accessToken)
      
      setCurrentTaskId(response.task_id)
      setDiscoveryPhase("Orchestrating agents...")

      // Set up WebSocket connection for real-time updates
      const ws = createWebSocket(response.task_id, accessToken)
      setWsConnection(ws)

      ws.onopen = () => {
        console.log("WebSocket connected")
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === "agents_discovered") {
          setDiscoveryPhase(`Found ${data.agents.length} specialized agents!`)
          setCurrentAgents(data.agents)
        } else if (data.type === "execution_started") {
          setDiscoveryPhase("Executing agents...")
          setExecutionSteps(data.steps || [])
        } else if (data.type === "step_update") {
          setExecutionSteps(prev => 
            prev.map((s, i) => 
              i === data.step_index ? { ...s, status: data.status } : s
            )
          )
        } else if (data.type === "streaming_token") {
          setStreamingText(prev => prev + (data.token || ""))
        } else if (data.type === "task_complete") {
          setDiscoveryPhase(null)
          setExecutionSteps([])
          const assistantMessage: Message = {
            id: Date.now().toString(),
            role: "assistant",
            content: data.result || response.message || "Task completed successfully!",
            timestamp: new Date(),
            agents: currentAgents
          }
          setMessages(prev => [...prev, assistantMessage])
          setStreamingText("")
          setIsStreaming(false)
          setCurrentAgents([])
          ws.close()
        } else if (data.type === "error") {
          setDiscoveryPhase(null)
          setExecutionSteps([])
          const errorMessage: Message = {
            id: Date.now().toString(),
            role: "assistant",
            content: "An error occurred while processing your request.",
            timestamp: new Date(),
            agents: [],
            error: data.error
          }
          setMessages(prev => [...prev, errorMessage])
          setStreamingText("")
          setIsStreaming(false)
          setCurrentAgents([])
          ws.close()
        }
      }

      ws.onerror = (error) => {
        console.error("WebSocket error:", error)
        setDiscoveryPhase(null)
        setExecutionSteps([])
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: "assistant",
          content: response.message || "Task completed successfully!",
          timestamp: new Date(),
          agents: response.agents || []
        }
        setMessages(prev => [...prev, errorMessage])
        setStreamingText("")
        setIsStreaming(false)
        setCurrentAgents([])
      }

      ws.onclose = () => {
        console.log("WebSocket closed")
        setWsConnection(null)
      }

    } catch (error: any) {
      console.error("Chat error:", error)
      setDiscoveryPhase(null)
      setExecutionSteps([])
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your request.",
        timestamp: new Date(),
        agents: [],
        error: error.response?.data?.detail || error.message
      }
      setMessages(prev => [...prev, errorMessage])
      setStreamingText("")
      setIsStreaming(false)
      setCurrentAgents([])
    }
  }

  const handleApprove = () => {
    // With real backend, approval is automatic
    // This function is kept for UI compatibility but doesn't do anything
    // The WebSocket will handle execution updates
    setAwaitingApproval(false)
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handlePromptClick = (prompt: string) => {
    setInput(prompt)
    textareaRef.current?.focus()
  }

  return (
    <div className="flex h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-950 dark:to-gray-900">
      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {showSidebar && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="w-80 flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950"
          >
            {/* Sidebar Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="font-bold text-lg">Hermes AI</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Agent Orchestrator</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowSidebar(false)}
                >
                  <Menu className="w-5 h-5" />
                </Button>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={() => {
                  setMessages([initialMessage])
                  setActiveChat(null)
                }}
              >
                <Plus className="w-5 h-5 mr-2" />
                New Chat
              </Button>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-2 mb-3">
                  Recent Chats
                </h3>
                {loadingHistory ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                  </div>
                ) : chatHistories.length > 0 ? (
                  chatHistories.slice(0, 5).map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => {
                        // Load the selected chat history
                        setMessages([
                          ...chat.messages,
                          {
                            id: Date.now().toString(),
                            role: "assistant",
                            content: `Welcome back! I've loaded your previous conversation. How can I help you continue?`,
                            timestamp: new Date(),
                            agents: []
                          }
                        ])
                        setActiveChat(chat.id)
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors group ${
                        activeChat === chat.id
                          ? "bg-blue-100 dark:bg-blue-900/30 border-l-2 border-blue-500"
                          : "hover:bg-gray-100 dark:hover:bg-gray-800"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-gray-400" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {chat.title}
                          </span>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 ml-6 mt-1">
                        {new Date(chat.timestamp).toLocaleDateString()}
                      </p>
                    </button>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <MessageSquare className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      No chat history yet
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      Start a conversation below
                    </p>
                  </div>
                )}
              </div>

              <div className="mt-6 space-y-2">
                <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-2 mb-3">
                  Quick Actions
                </h3>
                <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <Bookmark className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Saved Prompts
                  </span>
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <History className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Chat History
                  </span>
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <Settings className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Settings
                  </span>
                </button>
              </div>
            </div>

            {/* User Profile */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-800">
              <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 border-0">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                      <User2 className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-sm">{user?.full_name || user?.email || "User"}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        {user?.subscription_tier === "PRO" ? "Pro" : user?.subscription_tier === "ENTERPRISE" ? "Enterprise" : "Free"} Plan
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => {
                      logout();
                      router.push('/auth/login');
                    }}>
                      <LogOut className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400">Usage today</span>
                      <span className="font-medium">24 / ∞</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-1.5">
                      <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full" style={{ width: "24%" }} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!showSidebar && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowSidebar(true)}
                >
                  <Menu className="w-5 h-5" />
                </Button>
              )}
              <div>
                <h1 className="text-lg font-semibold">Agent Chat</h1>
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <Activity className="w-3 h-3 text-green-500" />
                  <span>All systems operational</span>
                  <span className="text-gray-400">•</span>
                  <span>45ms avg response</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon">
                <Share2 className="w-5 h-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <Settings className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-6 py-8">
            {/* Welcome Message for Empty State */}
            {messages.length === 1 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
              >
                <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 border-blue-200 dark:border-blue-800">
                  <CardHeader>
                    <CardTitle className="text-2xl">Welcome to Hermes AI! 🚀</CardTitle>
                    <CardDescription className="text-base">
                      Your intelligent agent orchestrator that connects you with specialized AI agents
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                          <Bot className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">2,341 Agents</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">Ready to help</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                          <Zap className="w-5 h-5 text-green-600 dark:text-green-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">45ms Response</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">Lightning fast</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                          <Shield className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Enterprise Ready</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">SOC2 compliant</p>
                        </div>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Try these popular requests:
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {suggestedPrompts.map((prompt, index) => (
                          <button
                            key={index}
                            onClick={() => handlePromptClick(prompt.text)}
                            className="text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                          >
                            <div className="flex items-center gap-3">
                              <prompt.icon className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
                              <div className="flex-1">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                  {prompt.text}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  {prompt.category}
                                </p>
                              </div>
                              <ChevronRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Message Thread */}
            <div className="space-y-6">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    layout
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`flex gap-4 ${
                      message.role === "user" ? "justify-end" : ""
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                        <Sparkles className="w-5 h-5 text-white" />
                      </div>
                    )}
                    <div className={`flex-1 max-w-2xl ${message.role === "user" ? "flex flex-col items-end" : ""}`}>
                      <div
                        className={`rounded-2xl px-5 py-4 ${
                          message.role === "user"
                            ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white"
                            : "bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800"
                        }`}
                      >
                        <p className={`text-sm leading-relaxed whitespace-pre-wrap break-words ${
                          message.role === "user" ? "text-white" : "text-gray-900 dark:text-gray-100"
                        }`}>
                          {message.content}
                        </p>
                        {message.agents && message.agents.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                            <p className="text-xs font-medium mb-2 opacity-80">
                              Agents used:
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {message.agents.map((agent: any) => (
                                <span
                                  key={agent.id}
                                  className="px-2 py-1 bg-white/20 dark:bg-gray-800 rounded-full text-xs text-white/90"
                                >
                                  {agent.name}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-2 px-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                        {message.role === "assistant" && (
                          <>
                            <button
                              onClick={() => copyToClipboard(message.content, message.id)}
                              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                            >
                              {copiedId === message.id ? (
                                <Check className="w-3 h-3 text-green-500" />
                              ) : (
                                <Copy className="w-3 h-3 text-gray-400" />
                              )}
                            </button>
                            <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors">
                              <Share2 className="w-3 h-3 text-gray-400" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                    {message.role === "user" && (
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0">
                        <User2 className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Streaming Response */}
              {streamingText && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 max-w-2xl">
                    <div className="rounded-2xl px-5 py-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap break-words text-gray-900 dark:text-gray-100">
                        {streamingText}
                        <span className="inline-block w-1 h-4 bg-blue-500 ml-1 animate-pulse" />
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Discovery Phase */}
              {discoveryPhase && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex gap-4"
                >
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center flex-shrink-0 animate-pulse">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <Card className="flex-1 max-w-2xl border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-950/20">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <Loader2 className="w-5 h-5 text-orange-600 dark:text-orange-400 animate-spin" />
                        <p className="text-sm font-medium text-orange-900 dark:text-orange-100">
                          {discoveryPhase}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Agent Discovery Cards */}
              {currentAgents.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="w-10 h-10" />
                  <div className="flex-1 max-w-2xl">
                    <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/20">
                      <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                          <Search className="w-5 h-5" />
                          Found {currentAgents.length} Specialized Agents
                        </CardTitle>
                        <CardDescription>
                          Review the selected agents for your task
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {currentAgents.map((agent) => {
                          const Icon = agent.icon
                          return (
                            <motion.div
                              key={agent.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="p-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-500 transition-colors group cursor-pointer"
                            >
                              <div className="flex items-start gap-4">
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                  <Icon className="w-6 h-6 text-white" />
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <h4 className="font-semibold text-sm">{agent.name}</h4>
                                    {agent.verified && (
                                      <Verified className="w-4 h-4 text-blue-500" />
                                    )}
                                  </div>
                                  <p className="text-xs text-gray-700 dark:text-gray-300 mb-2">
                                    {agent.description}
                                  </p>
                                  <div className="flex items-center gap-4 text-xs">
                                    <div className="flex items-center gap-1">
                                      <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                                      <span className="font-medium">{agent.rating}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <Zap className="w-3 h-3 text-gray-400" />
                                      <span className="text-gray-700 dark:text-gray-300">{(agent.calls / 1000).toFixed(0)}K calls</span>
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {agent.skills.map((skill: string) => (
                                      <span
                                        key={skill}
                                        className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-xs rounded-full font-medium"
                                      >
                                        {skill}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </motion.div>
                          )
                        })}

                        {/* Approval Button */}
                        {awaitingApproval && (
                          <Button
                            onClick={handleApprove}
                            size="lg"
                            className="w-full"
                          >
                            <Sparkles className="w-5 h-5 mr-2" />
                            Approve & Execute
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </motion.div>
              )}

              {/* Execution Steps */}
              {executionSteps.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="w-10 h-10" />
                  <Card className="flex-1 max-w-2xl">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Terminal className="w-5 h-5" />
                        Execution Progress
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {executionSteps.map((step, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className={`p-3 rounded-lg border ${
                              step.status === "completed"
                                ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800"
                                : step.status === "executing"
                                ? "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800"
                                : "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800"
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              {step.status === "completed" ? (
                                <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
                              ) : step.status === "executing" ? (
                                <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                              ) : (
                                <Clock className="w-5 h-5 text-gray-400" />
                              )}
                              <span className="text-sm font-medium">{step.agent}</span>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Thinking Animation */}
              {isStreaming && !streamingText && !discoveryPhase && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 max-w-2xl">
                    <div className="rounded-2xl px-5 py-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-2 h-2 rounded-full bg-pink-500 animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="bg-white dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800">
          <div className="max-w-4xl mx-auto px-6 py-4">
            <div className="flex items-end gap-4">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                  placeholder="Ask Hermes to find agents for any task..."
                  disabled={isStreaming}
                  rows={1}
                  className="w-full px-5 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500 disabled:opacity-50 max-h-32 text-sm"
                />
              </div>
              <Button
                onClick={handleSend}
                disabled={isStreaming || !input.trim()}
                size="lg"
                className="rounded-2xl px-6"
              >
                {isStreaming ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Send className="w-5 h-5 mr-2" />
                    Send
                  </>
                )}
              </Button>
            </div>
            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Press Enter to send, Shift+Enter for new line
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  End-to-end encrypted
                </span>
                <span className="flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  Powered by A2A Protocol
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default withAuth(ChatPage);