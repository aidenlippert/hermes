"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Loader2, Sparkles, User2, LogOut, Menu } from "lucide-react";
import { useAuthStore, useChatStore } from "@/lib/store";
import { api, createWebSocket } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();
  const { messages, addMessage, addEvent, isStreaming, setStreaming } = useChatStore();

  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [currentAgents, setCurrentAgents] = useState<string[]>([]);
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

    try {
      const response = await api.chat.send({ query: input }, token);

      if (response.result) {
        simulateTokenStreaming(response.result);
        return;
      }

      const websocket = createWebSocket(response.task_id, token);

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addEvent(data);

        if (data.type === "agent_selected") {
          setCurrentAgents((prev) => [...prev, data.agent_name]);
        }

        if (data.type === "task_completed") {
          const result = data.final_output || response.result;
          if (result) {
            simulateTokenStreaming(result);
          }
          websocket.close();
        } else if (data.type === "task_failed") {
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
          <button className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium">
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

            {/* Agent Discovery */}
            {currentAgents.length > 0 && (
              <div className="flex gap-4 animate-in">
                <div className="w-8 h-8" />
                <div className="flex flex-wrap gap-2">
                  {currentAgents.map((agent, i) => (
                    <div
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-accent rounded-full text-xs font-medium text-accent-foreground"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                      {agent}
                    </div>
                  ))}
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
