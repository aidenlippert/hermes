"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles, User, Bot, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { useAuthStore, useChatStore } from "@/lib/store";
import { api, createWebSocket } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const { token, user } = useAuthStore();
  const { messages, addMessage, addEvent, isStreaming, setStreaming, currentEvents } = useChatStore();

  const [input, setInput] = useState("");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Redirect if not logged in
  useEffect(() => {
    if (!token) {
      router.push("/auth/login");
    }
  }, [token, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentEvents]);

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

    try {
      // Send chat request
      const response = await api.chat.send({ query: input }, token);

      // Connect to WebSocket for live updates
      const websocket = createWebSocket(response.task_id, token);

      websocket.onopen = () => {
        console.log("WebSocket connected");
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addEvent(data);

        // Add final result as assistant message
        if (data.type === "task_completed" && response.result) {
          addMessage({
            id: Date.now().toString(),
            role: "assistant",
            content: response.result,
            timestamp: new Date(),
            taskId: response.task_id,
          });
          setStreaming(false);
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

      websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStreaming(false);
      };

      setWs(websocket);
    } catch (error: any) {
      console.error("Chat error:", error);
      addMessage({
        id: Date.now().toString(),
        role: "assistant",
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
      });
      setStreaming(false);
    }
  };

  const getEventIcon = (type: string) => {
    if (type.includes("completed")) return <CheckCircle2 className="w-4 h-4 text-success-500" />;
    if (type.includes("failed") || type === "error") return <XCircle className="w-4 h-4 text-red-500" />;
    if (type.includes("started")) return <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />;
    return <AlertCircle className="w-4 h-4 text-primary-500" />;
  };

  if (!token) return null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="glass-effect border-b border-white/20 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-lg text-slate-800">Hermes Chat</h1>
              <p className="text-sm text-slate-600">Multi-agent orchestration</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-sm text-slate-600">
              {user?.email}
            </div>
            <button
              onClick={() => router.push("/marketplace")}
              className="button-secondary text-sm py-2"
            >
              Browse Agents
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-5xl mx-auto space-y-6">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`flex gap-4 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-500 to-accent-600 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                )}
                <div
                  className={`max-w-2xl px-6 py-4 rounded-2xl ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-primary-600 to-primary-700 text-white"
                      : "glass-effect text-slate-800"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
                {message.role === "user" && (
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center flex-shrink-0">
                    <User className="w-6 h-6 text-white" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Live Events */}
          {isStreaming && currentEvents.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card"
            >
              <div className="flex items-center gap-2 mb-4">
                <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
                <h3 className="font-semibold text-slate-800">Processing...</h3>
              </div>
              <div className="space-y-2">
                {currentEvents.slice(-5).map((event, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-3 text-sm"
                  >
                    {getEventIcon(event.type)}
                    <span className="text-slate-600">{event.message}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="glass-effect border-t border-white/20 px-6 py-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask Hermes anything..."
              disabled={isStreaming}
              className="input-field flex-1"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStreaming ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-2 text-center">
            Powered by multi-agent orchestration with real-time streaming
          </p>
        </div>
      </div>
    </div>
  );
}
