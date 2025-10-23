"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Loader2, Circle, CheckCircle2, Clock, Users } from "lucide-react";
import { useAuthStore, useChatStore } from "@/lib/store";
import { api, createWebSocket } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();
  const { messages, addMessage, addEvent, isStreaming, setStreaming, currentEvents } = useChatStore();

  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [currentAgents, setCurrentAgents] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!token) {
      router.push("/auth/login");
    }
  }, [token, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

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

      setWs(websocket);
    } catch (error) {
      console.error("Chat error:", error);
      setStreaming(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <header className="border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Circle className="w-5 h-5 text-accent" fill="currentColor" />
          <span className="font-medium text-sm">Hermes</span>
        </div>
        <div className="flex items-center gap-4">
          {user && <span className="text-sm text-slate-600">{user.username}</span>}
          <button
            onClick={logout}
            className="text-sm text-slate-500 hover:text-slate-900 fast-transition"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`animate-fade-in ${
                message.role === "user" ? "ml-auto max-w-xl" : "mr-auto max-w-2xl"
              }`}
            >
              <div className="flex items-start gap-3">
                {message.role === "assistant" && (
                  <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Circle className="w-3 h-3 text-accent" fill="currentColor" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-500 font-medium">
                      {message.role === "user" ? "You" : "Hermes"}
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatTime(message.timestamp)}
                    </span>
                  </div>
                  <div
                    className={`text-sm leading-relaxed ${
                      message.role === "user"
                        ? "text-slate-900"
                        : "text-slate-700"
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Streaming Response */}
          {streamingText && (
            <div className="mr-auto max-w-2xl animate-fade-in">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Circle className="w-3 h-3 text-accent" fill="currentColor" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-500 font-medium">Hermes</span>
                    <span className="text-xs text-slate-400">now</span>
                  </div>
                  <div className="text-sm leading-relaxed text-slate-700 token-fade-in">
                    {streamingText}
                    <span className="inline-block w-1 h-4 bg-accent ml-0.5 animate-pulse" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Thinking State */}
          {isStreaming && !streamingText && (
            <div className="mr-auto max-w-2xl animate-fade-in">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Circle className="w-3 h-3 text-accent" fill="currentColor" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-500 font-medium">Hermes</span>
                    <span className="text-xs text-slate-400">now</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-400 thinking-dot"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-400 thinking-dot"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-400 thinking-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Agent Discovery UI */}
          {currentAgents.length > 0 && (
            <div className="mr-auto max-w-2xl">
              <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg animate-scale-in">
                <Users className="w-4 h-4 text-slate-500" />
                <span className="text-xs text-slate-600">Coordinating with:</span>
                <div className="flex gap-1.5">
                  {currentAgents.map((agent, i) => (
                    <span key={i} className="agent-badge">
                      {agent}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200 px-6 py-4 bg-slate-50/50">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask Hermes anything..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent minimal-transition disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              onClick={handleSend}
              disabled={isStreaming || !input.trim()}
              className="p-2.5 bg-accent text-white rounded-lg hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed minimal-transition"
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
            <span>
              Press <kbd className="kbd">⌘K</kbd> to focus
            </span>
            <span>
              <kbd className="kbd">Enter</kbd> to send
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
