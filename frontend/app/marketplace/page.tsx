"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Search, Sparkles, Code, FileText, BarChart3, Globe } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { api, Agent } from "@/lib/api";

const iconMap: Record<string, any> = {
  code: Code,
  content: FileText,
  data: BarChart3,
  research: Globe,
};

export default function MarketplacePage() {
  const router = useRouter();
  const { token } = useAuthStore();

  const [agents, setAgents] = useState<Agent[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      router.push("/auth/login");
      return;
    }

    loadAgents();
  }, [token, router]);

  const loadAgents = async () => {
    if (!token) return;

    try {
      setIsLoading(true);
      const response = await api.agents.list(token);
      setAgents(response.agents);
    } catch (error) {
      console.error("Failed to load agents:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!token || !searchQuery.trim()) {
      loadAgents();
      return;
    }

    try {
      setIsLoading(true);
      const response = await api.agents.search(searchQuery, token);
      setAgents(response.agents);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredAgents = selectedCategory
    ? agents.filter((agent) => agent.category === selectedCategory)
    : agents;

  const categories = Array.from(new Set(agents.map((a) => a.category)));

  if (!token) return null;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="glass-effect border-b border-white/20 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-2xl text-slate-800">Agent Marketplace</h1>
                <p className="text-sm text-slate-600">
                  Browse {agents.length} AI agents
                </p>
              </div>
            </div>
            <button
              onClick={() => router.push("/chat")}
              className="button-primary"
            >
              Start Chat
            </button>
          </div>

          {/* Search */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search agents by capability..."
                className="input-field pl-12"
              />
            </div>
            <button onClick={handleSearch} className="button-primary px-8">
              Search
            </button>
          </div>

          {/* Categories */}
          <div className="flex gap-2 mt-4 flex-wrap">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedCategory === null
                  ? "bg-primary-600 text-white"
                  : "glass-effect text-slate-700 hover:shadow-md"
              }`}
            >
              All
            </button>
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all capitalize ${
                  selectedCategory === category
                    ? "bg-primary-600 text-white"
                    : "glass-effect text-slate-700 hover:shadow-md"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAgents.map((agent, index) => {
              const Icon = iconMap[agent.category] || Sparkles;
              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="card group cursor-pointer hover:border-primary-200"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-white group-hover:scale-110 transition-transform">
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg text-slate-800 mb-1">
                        {agent.name}
                      </h3>
                      <p className="text-xs text-slate-500 capitalize">
                        {agent.category}
                      </p>
                    </div>
                  </div>

                  <p className="text-sm text-slate-600 mb-4 line-clamp-3">
                    {agent.description}
                  </p>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {agent.capabilities.slice(0, 3).map((cap) => (
                      <span
                        key={cap}
                        className="px-2 py-1 bg-primary-50 text-primary-700 text-xs rounded-lg font-medium"
                      >
                        {cap}
                      </span>
                    ))}
                    {agent.capabilities.length > 3 && (
                      <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-lg">
                        +{agent.capabilities.length - 3} more
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                    <div className="text-sm text-slate-600">
                      {agent.total_calls} calls
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-sm font-medium text-slate-800">
                        {agent.average_rating.toFixed(1)}
                      </span>
                      <span className="text-yellow-500">★</span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}

        {!isLoading && filteredAgents.length === 0 && (
          <div className="text-center py-20">
            <p className="text-slate-600 mb-4">No agents found</p>
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory(null);
                loadAgents();
              }}
              className="button-secondary"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
