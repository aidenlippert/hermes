"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import Link from "next/link"
import {
  Search,
  Sparkles,
  Code,
  FileText,
  BarChart3,
  Globe,
  Bot,
  Zap,
  Star,
  Filter,
  TrendingUp,
  Clock,
  Award,
  Shield,
  Briefcase,
  Database,
  Brain,
  Palette,
  MessageSquare,
  ChevronRight,
  ArrowUpRight,
  Users,
  Activity,
  CheckCircle2,
  Verified
} from "lucide-react"

// Mock data for stunning marketplace
const mockAgents = [
  {
    id: 1,
    name: "CodePilot Pro",
    description: "Advanced code generation and refactoring agent with support for 50+ languages",
    category: "Development",
    icon: Code,
    rating: 4.9,
    reviews: 2847,
    calls: 128400,
    verified: true,
    trending: true,
    skills: ["Code Generation", "Refactoring", "Testing", "Documentation"],
    author: "Google AI",
    price: "Free",
    gradient: "from-blue-500 to-cyan-500"
  },
  {
    id: 2,
    name: "DataSense Analytics",
    description: "Real-time data analysis and visualization with ML-powered insights",
    category: "Analytics",
    icon: BarChart3,
    rating: 4.8,
    reviews: 1923,
    calls: 89300,
    verified: true,
    trending: false,
    skills: ["Data Analysis", "Visualization", "ML Insights", "Reporting"],
    author: "OpenAI",
    price: "$0.01/call",
    gradient: "from-purple-500 to-pink-500"
  },
  {
    id: 3,
    name: "ContentCraft AI",
    description: "Professional content creation with SEO optimization and tone adjustment",
    category: "Content",
    icon: FileText,
    rating: 4.7,
    reviews: 3412,
    calls: 234000,
    verified: true,
    trending: true,
    skills: ["Writing", "SEO", "Translation", "Editing"],
    author: "Anthropic",
    price: "Free tier",
    gradient: "from-green-500 to-emerald-500"
  },
  {
    id: 4,
    name: "ResearchBot Ultra",
    description: "Deep web research and fact-checking with academic sources",
    category: "Research",
    icon: Globe,
    rating: 4.9,
    reviews: 892,
    calls: 45200,
    verified: false,
    trending: false,
    skills: ["Research", "Fact-checking", "Citations", "Summaries"],
    author: "MIT Labs",
    price: "$0.005/call",
    gradient: "from-orange-500 to-red-500"
  },
  {
    id: 5,
    name: "DesignGenius",
    description: "UI/UX design assistance with component generation and accessibility checks",
    category: "Design",
    icon: Palette,
    rating: 4.6,
    reviews: 1234,
    calls: 67800,
    verified: true,
    trending: true,
    skills: ["UI Design", "UX Research", "Prototyping", "A11y"],
    author: "Figma AI",
    price: "Premium",
    gradient: "from-pink-500 to-purple-500"
  },
  {
    id: 6,
    name: "SecurityShield",
    description: "Comprehensive security auditing and vulnerability detection",
    category: "Security",
    icon: Shield,
    rating: 5.0,
    reviews: 432,
    calls: 23400,
    verified: true,
    trending: false,
    skills: ["Auditing", "Penetration Testing", "Compliance", "Monitoring"],
    author: "CrowdStrike AI",
    price: "Enterprise",
    gradient: "from-red-500 to-orange-500"
  }
]

const categories = [
  { name: "All", icon: Sparkles, count: 2341 },
  { name: "Development", icon: Code, count: 523 },
  { name: "Analytics", icon: BarChart3, count: 234 },
  { name: "Content", icon: FileText, count: 456 },
  { name: "Research", icon: Globe, count: 189 },
  { name: "Design", icon: Palette, count: 267 },
  { name: "Security", icon: Shield, count: 123 },
  { name: "Business", icon: Briefcase, count: 345 },
  { name: "AI/ML", icon: Brain, count: 234 }
]

const sortOptions = [
  { label: "Most Popular", value: "popular" },
  { label: "Highest Rated", value: "rating" },
  { label: "Newest First", value: "newest" },
  { label: "Trending Now", value: "trending" },
  { label: "Most Reviewed", value: "reviews" }
]

export default function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("All")
  const [sortBy, setSortBy] = useState("popular")
  const [showFilters, setShowFilters] = useState(false)
  const [agents, setAgents] = useState(mockAgents)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  // Filter and sort agents
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = searchQuery === "" ||
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.skills.some(skill => skill.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesCategory = selectedCategory === "All" || agent.category === selectedCategory

    return matchesSearch && matchesCategory
  })

  // Sort agents
  const sortedAgents = [...filteredAgents].sort((a, b) => {
    switch (sortBy) {
      case "rating":
        return b.rating - a.rating
      case "reviews":
        return b.reviews - a.reviews
      case "trending":
        return (b.trending ? 1 : 0) - (a.trending ? 1 : 0)
      case "popular":
      default:
        return b.calls - a.calls
    }
  })

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-gray-200 dark:border-gray-800">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-blue-950/20 dark:via-purple-950/20 dark:to-pink-950/20" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 text-sm font-medium text-blue-700 dark:text-blue-300 mb-6"
            >
              <Sparkles className="w-4 h-4" />
              <span>2,341 AI Agents Available</span>
            </motion.div>

            <h1 className="text-5xl lg:text-6xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 dark:from-gray-100 dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent mb-4">
              Agent Marketplace
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Discover, integrate, and orchestrate AI agents from leading providers
            </p>
          </motion.div>

          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-3xl mx-auto mb-8"
          >
            <div className="relative">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agents by name, skill, or description..."
                className="w-full pl-14 pr-5 py-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-lg"
              />
              <Button
                size="lg"
                className="absolute right-2 top-1/2 -translate-y-1/2"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto"
          >
            {[
              { icon: Bot, label: "Total Agents", value: "2,341" },
              { icon: Users, label: "Active Users", value: "45.2K" },
              { icon: Activity, label: "Daily Calls", value: "1.2M" },
              { icon: TrendingUp, label: "Success Rate", value: "99.7%" }
            ].map((stat, index) => (
              <div key={stat.label} className="text-center">
                <div className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <stat.icon className="w-4 h-4" />
                  <span className="text-sm">{stat.label}</span>
                </div>
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                  {stat.value}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="hidden lg:block w-64 space-y-6"
          >
            {/* Categories */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4 uppercase tracking-wider">
                Categories
              </h3>
              <div className="space-y-1">
                {categories.map((category) => {
                  const Icon = category.icon
                  return (
                    <button
                      key={category.name}
                      onClick={() => setSelectedCategory(category.name)}
                      className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                        selectedCategory === category.name
                          ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg"
                          : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="w-5 h-5" />
                        <span className="font-medium">{category.name}</span>
                      </div>
                      <span className={`text-sm ${
                        selectedCategory === category.name ? "text-white/80" : "text-gray-500"
                      }`}>
                        {category.count}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Sort Options */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4 uppercase tracking-wider">
                Sort By
              </h3>
              <div className="space-y-1">
                {sortOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSortBy(option.value)}
                    className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                      sortBy === option.value
                        ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                        : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Platform Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Avg Response</span>
                  <span className="text-sm font-medium">45ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Uptime</span>
                  <span className="text-sm font-medium">99.99%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Active Now</span>
                  <span className="text-sm font-medium text-green-600">2,128</span>
                </div>
              </CardContent>
            </Card>
          </motion.aside>

          {/* Agent Grid */}
          <div className="flex-1">
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {selectedCategory === "All" ? "All Agents" : selectedCategory}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {sortedAgents.length} agents found
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link href="/chat">
                  <Button>
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Start Chat
                  </Button>
                </Link>
                <Link href="/agents/submit">
                  <Button variant="outline">
                    Submit Agent
                  </Button>
                </Link>
              </div>
            </div>

            {/* Agent Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <AnimatePresence mode="popLayout">
                {sortedAgents.map((agent, index) => {
                  const Icon = agent.icon
                  return (
                    <motion.div
                      key={agent.id}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.2, delay: index * 0.02 }}
                      whileHover={{ y: -5 }}
                    >
                      <Card className="h-full hover:shadow-2xl transition-all cursor-pointer border-2 hover:border-blue-500/50 group">
                        <CardHeader>
                          {/* Agent Header */}
                          <div className="flex items-start justify-between mb-4">
                            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-r ${agent.gradient} flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
                              <Icon className="w-7 h-7" />
                            </div>
                            <div className="flex items-center gap-2">
                              {agent.trending && (
                                <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-xs font-medium rounded-full">
                                  <TrendingUp className="w-3 h-3 inline mr-1" />
                                  Trending
                                </span>
                              )}
                              {agent.verified && (
                                <Verified className="w-5 h-5 text-blue-500" />
                              )}
                            </div>
                          </div>

                          {/* Agent Info */}
                          <div>
                            <CardTitle className="text-xl mb-2 flex items-center gap-2">
                              {agent.name}
                              <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </CardTitle>
                            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                              <span className="flex items-center gap-1">
                                <Users className="w-4 h-4" />
                                {agent.author}
                              </span>
                              <span className="text-gray-400">•</span>
                              <span className={`font-medium ${
                                agent.price === "Free" ? "text-green-600" : "text-gray-900 dark:text-gray-100"
                              }`}>
                                {agent.price}
                              </span>
                            </div>
                          </div>
                        </CardHeader>

                        <CardContent>
                          {/* Description */}
                          <CardDescription className="text-base mb-4 line-clamp-2">
                            {agent.description}
                          </CardDescription>

                          {/* Skills */}
                          <div className="flex flex-wrap gap-2 mb-4">
                            {agent.skills.slice(0, 3).map((skill) => (
                              <span
                                key={skill}
                                className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium rounded-full"
                              >
                                {skill}
                              </span>
                            ))}
                            {agent.skills.length > 3 && (
                              <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded-full">
                                +{agent.skills.length - 3}
                              </span>
                            )}
                          </div>

                          {/* Stats */}
                          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                            <div className="flex items-center gap-4">
                              <div className="flex items-center gap-1">
                                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                                <span className="font-medium">{agent.rating}</span>
                                <span className="text-sm text-gray-500">({agent.reviews})</span>
                              </div>
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              <Zap className="w-4 h-4 inline mr-1" />
                              {(agent.calls / 1000).toFixed(0)}K calls
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </div>

            {/* Empty State */}
            {sortedAgents.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-20"
              >
                <Bot className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  No agents found
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Try adjusting your search or filters
                </p>
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchQuery("")
                    setSelectedCategory("All")
                  }}
                >
                  Clear Filters
                </Button>
              </motion.div>
            )}

            {/* Load More */}
            {sortedAgents.length > 0 && (
              <div className="mt-12 text-center">
                <Button variant="outline" size="lg">
                  Load More Agents
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
