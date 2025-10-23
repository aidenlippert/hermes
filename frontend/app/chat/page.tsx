"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Loader2, Sparkles, User2, LogOut, Menu, Search, DollarSign, Star } from "lucide-react";
import { useAuthStore, useChatStore } from "@/lib/store";
import { api, createWebSocket } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();
  const { messages, addMessage, addEvent, isStreaming, setStreaming } = useChatStore();

  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [currentAgents, setCurrentAgents] = useState<any[]>([]);
  const [discoveryPhase, setDiscoveryPhase] = useState<string | null>(null);
  const [executionSteps, setExecutionSteps] = useState<any[]>([]);
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const [approvalData, setApprovalData] = useState<any>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!token) {
      router.push("/auth/login");
    }
  }, [token, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [input]);

  const simulateTokenStreaming = (text: string) => {
    setStreamingText("");
    const words = text.split(" ");
    let currentIndex = 0;

    const interval = setInterval(() => {
      if (currentIndex < words.length) {
        setStreamingText((prev) => prev + (prev ? " " : "") + words[currentIndex]);
        currentIndex++;
      } else {
        clearInterval(interval);
        addMessage({
          id: Date.now().toString(),
          role: "assistant",
          content: text,
          timestamp: new Date(),
        });
        setStreamingText("");
        setStreaming(false);
      }
    }, 50);
  };

  const handleApprove = async () => {
    if (!token || !approvalData) return;

    setAwaitingApproval(false);
    setStreaming(true);
    setDiscoveryPhase("Creating execution plan...");

    // Send approval message
    const approvalMessage = {
      id: Date.now().toString(),
      role: "user" as const,
      content: "Yes, proceed with these agents",
      timestamp: new Date(),
    };

    addMessage(approvalMessage);

    // This will trigger execution with approved agents
    // For now we just continue - the backend will need an approval endpoint
    // TODO: Create /api/v1/approve/{task_id} endpoint
  };

  const handleSend = async () => {
    if (!input.trim() || !token || isStreaming) return;

    const userMessage = {
      id: Date.now().toString(),
      role: "user" as const,
      content: input,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput("");
    setStreaming(true);
    setCurrentAgents([]);
    setDiscoveryPhase(null);
    setExecutionSteps([]);
    setAwaitingApproval(false);
    setApprovalData(null);

    try {
      const response = await api.chat.send({
        query: input,
        conversation_id: conversationId || undefined
      }, token);

      // Save conversation ID for next message
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Check if this is an awaiting_approval response
      if (response.status === "awaiting_approval") {
        // We need to connect to WebSocket to get the agent data
        const websocket = createWebSocket(response.task_id, token);

        websocket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          addEvent(data);

          if (data.type === "awaiting_approval") {
            setDiscoveryPhase(null);
            setAwaitingApproval(true);
            setApprovalData({
              agents: data.agents,
              extracted_info: data.extracted_info
            });
            setCurrentAgents(data.agents || []);
            if (data.message) {
              simulateTokenStreaming(data.message);
            }
            websocket.close();
          }
        };

        websocket.onerror = () => {
          setStreaming(false);
          websocket.close();
        };

        return;
      }

      if (response.result) {
        simulateTokenStreaming(response.result);
        return;
      }

      const websocket = createWebSocket(response.task_id, token);

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addEvent(data);

        // Intent parsed
        if (data.type === "intent_parsed") {
          setDiscoveryPhase("Analyzing request...");
        }

        // Agents discovered
        if (data.type === "agents_discovered") {
          setDiscoveryPhase("Agents discovered!");
          setCurrentAgents(data.agents || []);
        }

        // Follow-up questions
        if (data.type === "follow_up_required") {
          setDiscoveryPhase(null);
          setCurrentAgents([]);
          setAwaitingApproval(false);
          simulateTokenStreaming(data.message);
          websocket.close();
          return;
        }

        // Awaiting approval
        if (data.type === "awaiting_approval") {
          setDiscoveryPhase(null);
          setAwaitingApproval(true);
          setApprovalData({
            agents: data.agents,
            extracted_info: data.extracted_info
          });
          setCurrentAgents(data.agents || []);
          simulateTokenStreaming(data.message);
          websocket.close();
          return;
        }

        // Plan created
        if (data.type === "plan_created") {
          setDiscoveryPhase("Executing plan...");
          setExecutionSteps(data.steps || []);
        }

        // Agent execution events
        if (data.type === "agent_selected") {
          setExecutionSteps(prev =>
            prev.map(step =>
              step.agent === data.agent_name
                ? { ...step, status: "executing" }
                : step
            )
          );
        }

        if (data.type === "agent_result") {
          setExecutionSteps(prev =>
            prev.map(step =>
              step.agent === data.agent_name
                ? { ...step, status: "completed", result: data.result }
                : step
            )
          );
        }

        // Task completed
        if (data.type === "task_completed") {
          setDiscoveryPhase(null);
          setCurrentAgents([]);
          setExecutionSteps([]);
          const result = data.final_output || response.result;
          if (result) {
            simulateTokenStreaming(result);
          }
          websocket.close();
        } else if (data.type === "task_failed") {
          setDiscoveryPhase(null);
          setCurrentAgents([]);
          setExecutionSteps([]);
          addMessage({
            id: Date.now().toString(),
            role: "assistant",
            content: "Sorry, the task failed. Please try again.",
            timestamp: new Date(),
          });
          setStreaming(false);
          websocket.close();
        }
      };

      websocket.onerror = () => {
        setStreaming(false);
        websocket.close();
      };
    } catch (error) {
      console.error("Chat error:", error);
      setStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="hidden md:flex w-64 flex-col border-r border-border bg-muted/30">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="font-semibold text-lg">Hermes</span>
          </div>
        </div>

        <div className="flex-1 p-4">
          <button
            onClick={() => {
              setConversationId(null);
              useChatStore.setState({ messages: [] });
            }}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
          >
            New Chat
          </button>
        </div>

        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-secondary transition-colors cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <User2 className="w-4 h-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{user?.username || "User"}</div>
              <div className="text-xs text-muted-foreground">Free Plan</div>
            </div>
            <button
              onClick={logout}
              className="p-1 hover:bg-secondary rounded"
            >
              <LogOut className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="font-semibold">Hermes</span>
          </div>
          <button className="p-2 hover:bg-secondary rounded-lg transition-colors">
            <Menu className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 animate-in ${
                  message.role === "user" ? "justify-end" : ""
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`flex flex-col gap-2 max-w-2xl ${message.role === "user" ? "items-end" : ""}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground"
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                </div>
                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                    <User2 className="w-4 h-4 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}

            {/* Streaming Response */}
            {streamingText && (
              <div className="flex gap-4 animate-in">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="flex flex-col gap-2 max-w-2xl">
                  <div className="rounded-2xl px-4 py-3 bg-muted text-foreground">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {streamingText}
                      <span className="inline-block w-0.5 h-4 bg-primary ml-1 animate-pulse" />
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Thinking State */}
            {isStreaming && !streamingText && (
              <div className="flex gap-4 animate-in">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-muted">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-muted-foreground thinking-dot" />
                    <div className="w-2 h-2 rounded-full bg-muted-foreground thinking-dot" />
                    <div className="w-2 h-2 rounded-full bg-muted-foreground thinking-dot" />
                  </div>
                </div>
              </div>
            )}

            {/* Discovery Phase */}
            {discoveryPhase && (
              <div className="flex gap-4 animate-in">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center flex-shrink-0">
                  <Search className="w-4 h-4 text-white" />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-muted text-foreground">
                  <p className="text-sm font-medium">{discoveryPhase}</p>
                </div>
              </div>
            )}

            {/* Agent Discovery Cards */}
            {currentAgents.length > 0 && (
              <div className="flex gap-4 animate-in">
                <div className="w-8 h-8" />
                <div className="w-full max-w-2xl">
                  <p className="text-sm font-medium text-muted-foreground mb-3">
                    🔍 Found {currentAgents.length} specialized agents:
                  </p>
                  <div className="grid grid-cols-1 gap-3 mb-4">
                    {currentAgents.map((agent, i) => (
                      <div
                        key={i}
                        className="p-4 bg-background border border-border rounded-xl hover:border-primary/50 transition-all cursor-pointer group"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Sparkles className="w-4 h-4 text-primary" />
                              <h4 className="font-semibold text-sm">{agent.name}</h4>
                            </div>
                            <p className="text-xs text-muted-foreground mb-2">
                              {agent.description || agent.capabilities?.join(", ") || "No capabilities listed"}
                            </p>
                            {/* Coming soon - price and rating */}
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <DollarSign className="w-3 h-3" />
                                <span>Coming Soon</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <Star className="w-3 h-3" />
                                <span>Coming Soon</span>
                              </div>
                            </div>
                          </div>
                          <div className="text-xs text-primary group-hover:underline">
                            View Similar
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Approval Button */}
                  {awaitingApproval && (
                    <button
                      onClick={handleApprove}
                      className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                    >
                      <Sparkles className="w-5 h-5" />
                      Approve & Execute
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Execution Steps */}
            {executionSteps.length > 0 && (
              <div className="flex gap-4 animate-in">
                <div className="w-8 h-8" />
                <div className="w-full max-w-2xl">
                  <p className="text-sm font-medium text-muted-foreground mb-3">
                    ⚡ Execution Progress:
                  </p>
                  <div className="space-y-2">
                    {executionSteps.map((step, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-lg border ${
                          step.status === "completed"
                            ? "bg-primary/5 border-primary/30"
                            : step.status === "executing"
                            ? "bg-accent border-accent-foreground/30"
                            : "bg-muted border-border"
                        }`}
                      >
                        <div className="flex items-center gap-2 text-sm">
                          {step.status === "completed" ? (
                            <span className="text-primary">✓</span>
                          ) : step.status === "executing" ? (
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          ) : (
                            <span className="text-muted-foreground">○</span>
                          )}
                          <span className="font-medium">{step.agent || step.description}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-border bg-background">
          <div className="max-w-3xl mx-auto px-4 py-4">
            <div className="relative flex items-end gap-2 bg-muted rounded-2xl p-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Message Hermes..."
                disabled={isStreaming}
                rows={1}
                className="flex-1 bg-transparent border-none outline-none resize-none px-3 py-2 text-sm placeholder:text-muted-foreground disabled:opacity-50 max-h-32"
              />
              <button
                onClick={handleSend}
                disabled={isStreaming || !input.trim()}
                className="p-2 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all disabled:hover:bg-primary flex-shrink-0"
              >
                {isStreaming ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-3">
              Hermes can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
