"use client"

import { useState, useEffect } from "react"
import {
  Search,
  Star,
  Plus,
  Globe,
  Code,
  BarChart,
  Palette,
  Mail,
  Database,
  LifeBuoy,
  Megaphone,
  StarHalf,
  Bot,
  Loader2,
  Shield,
  Zap,
  Brain,
} from "lucide-react"
import { api } from "@/lib/api"
import { useAuthStore } from "@/lib/store"
import Link from "next/link"

// Map category to icon
const categoryIcons: Record<string, any> = {
  travel: Globe,
  development: Code,
  coding: Code,
  finance: BarChart,
  creative: Palette,
  productivity: Mail,
  data: Database,
  support: LifeBuoy,
  marketing: Megaphone,
  ai: Brain,
  automation: Zap,
  security: Shield,
  default: Bot,
}

const getIconForCategory = (category: string) => {
  const lowerCategory = category?.toLowerCase() || ''
  return categoryIcons[lowerCategory] || categoryIcons.default
}

const defaultAgents = [
  {
    id: "trip-planner",
    name: "TripPlanner AI",
    description: "Automates travel itinerary creation based on user preferences and budget.",
    rating: 4,
    usage_count: 124,
    category: "travel",
    is_featured: true,
    price: 0,
  },
  {
    id: "code-helper",
    name: "CodeHelper",
    description: "Your personal AI pair programmer for debugging and code generation.",
    rating: 4.5,
    usage_count: 302,
    category: "development",
    is_featured: true,
    price: 0,
  },
  {
    id: "market-pulse",
    name: "MarketPulse",
    description: "Real-time stock market analysis and trend prediction agent.",
    rating: 5,
    usage_count: 98,
    category: "finance",
    is_featured: true,
    price: 0,
  },
  {
    id: "artisan-ai",
    name: "Artisan AI",
    description: "Generates unique visual concepts and creative assets from text prompts.",
    rating: 4.5,
    usage_count: 451,
    category: "creative",
    is_featured: true,
    price: 0,
  },
  {
    id: "inbox-zero",
    name: "InboxZero",
    description: "Intelligently sorts, summarizes, and prioritizes your emails.",
    rating: 5,
    usage_count: 512,
    category: "productivity",
    is_featured: false,
    price: 0,
  },
  {
    id: "data-miner",
    name: "DataMiner",
    description: "Extracts and analyzes data from unstructured documents and websites.",
    rating: 4,
    usage_count: 88,
    category: "data",
    is_featured: false,
    price: 0,
  },
  {
    id: "support-bot",
    name: "SupportBot",
    description: "Handles frontline customer queries and escalates when necessary.",
    rating: 3.5,
    usage_count: 156,
    category: "support",
    is_featured: false,
    price: 0,
  },
  {
    id: "ad-copy-pro",
    name: "AdCopy Pro",
    description: "Generates high-converting ad copy for various marketing platforms.",
    rating: 4.5,
    usage_count: 219,
    category: "marketing",
    is_featured: false,
    price: 0,
  },
]

interface Agent {
  id: string
  name: string
  description: string
  rating: number
  usage_count: number
  category: string
  is_featured?: boolean
  price?: number
  creator?: any
}

const StarRating = ({ rating, reviews }: { rating: number; reviews: number }) => {
  const fullStars = Math.floor(rating)
  const halfStar = rating % 1 !== 0
  const emptyStars = 5 - fullStars - (halfStar ? 1 : 0)

  return (
    <div className="flex items-center gap-1 text-sm text-primary">
      {[...Array(fullStars)].map((_, i) => (
        <Star key={`full-${i}`} className="!text-[16px] fill-current" />
      ))}
      {halfStar && <StarHalf className="!text-[16px] fill-current" />}
      {[...Array(emptyStars)].map((_, i) => (
        <Star key={`empty-${i}`} className="!text-[16px] text-white/30" />
      ))}
      <span className="ml-1 text-xs text-[#E0E0E0]/50">({reviews})</span>
    </div>
  )
}

const AgentCard = ({ agent }: { agent: Agent }) => {
  const Icon = getIconForCategory(agent.category)
  return (
    <div className="group relative flex flex-col overflow-hidden rounded-xl border border-white/10 bg-white/5 p-5 transition-all duration-300 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10">
      <div className="absolute -right-12 -top-12 size-48 rounded-full bg-primary/20 opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100"></div>
      <div className="relative z-10">
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-lg border border-white/10 bg-black/20">
            <Icon className="text-3xl text-primary" />
          </div>
          <h3 className="font-mono text-lg font-bold text-[#E0E0E0]">{agent.name}</h3>
        </div>
        <p className="mt-4 text-sm text-[#E0E0E0]/70">{agent.description}</p>
        <div className="mt-4 flex items-center justify-between">
          <StarRating rating={agent.rating} reviews={agent.usage_count} />
          <div className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-[#E0E0E0]/80">
            {agent.category?.charAt(0).toUpperCase() + agent.category?.slice(1)}
          </div>
        </div>
        <button className="absolute bottom-5 right-5 z-20 flex size-8 items-center justify-center rounded-full bg-primary/80 text-white opacity-0 transition-all group-hover:opacity-100">
          <Plus className="!text-lg" />
        </button>
      </div>
    </div>
  )
}

const Header = () => (
  <header className="sticky top-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-solid border-white/10 px-10 py-3 bg-background-dark/80 backdrop-blur-sm">
    <div className="flex items-center gap-4">
      <div className="size-6 text-primary">
        <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z"
            fill="currentColor"
          ></path>
          <path
            clipRule="evenodd"
            d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z"
            fill="currentColor"
            fillRule="evenodd"
          ></path>
        </svg>
      </div>
      <h2 className="text-[#E0E0E0] text-lg font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
    </div>
    <div className="flex flex-1 justify-end gap-8">
      <div className="flex items-center gap-9">
        <Link className="text-[#E0E0E0] text-sm font-medium leading-normal transition-colors hover:text-primary" href="#">
          Marketplace
        </Link>
        <Link className="text-[#E0E0E0] text-sm font-medium leading-normal transition-colors hover:text-primary" href="#">
          My Agents
        </Link>
        <Link className="text-[#E0E0E0] text-sm font-medium leading-normal transition-colors hover:text-primary" href="#">
          API Docs
        </Link>
      </div>
      <div
        className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"
        style={{
          backgroundImage:
            'url("https://lh3.googleusercontent.com/aida-public/AB6AXuC9LvZL3s4bPE_hog2SqFKuxC-Gm0pyPC3mCle4P60BHoR6kclL-0210lhNfmwXkZk4bvbaft9lzJU--Gisw4OI5-NcHa0X1Zi8usZVCMeDX0TPiZ9OUSJ_2DugAn7rxVsJOuBwKfEqeS1kTDTkt4QyZaJ2Pz5Lh7hnhi-4PZq9csRteLQOkq5A6qcsg84zCknpikA6NbZ1z1x2xNIdpvC0ZoBazPERgkk0eUXgKnvnYMwtDf2VaWYhVOJW45Eoc_c8rsblKnjE4cVk")',
        }}
      ></div>
    </div>
  </header>
)

export default function MarketplacePage() {
  const [agents, setAgents] = useState<Agent[]>(defaultAgents)
  const [featuredAgents, setFeaturedAgents] = useState<Agent[]>([])
  const [allAgents, setAllAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")
  const accessToken = useAuthStore((state) => state.accessToken)
  const [categories, setCategories] = useState([
    { name: "All", value: "all", active: true },
    { name: "Productivity", value: "productivity", active: false },
    { name: "Finance", value: "finance", active: false },
    { name: "Development", value: "development", active: false },
    { name: "Marketing", value: "marketing", active: false },
    { name: "Support", value: "support", active: false },
  ])

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    setLoading(true)
    try {
      // Try to fetch agents from backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/agents`)

      if (response.ok) {
        const data = await response.json()
        if (data.agents && data.agents.length > 0) {
          setAgents(data.agents)
          // Split into featured and regular agents
          const featured = data.agents.filter((a: Agent) => a.is_featured).slice(0, 4)
          const regular = data.agents.filter((a: Agent) => !a.is_featured).slice(0, 8)

          setFeaturedAgents(featured.length > 0 ? featured : data.agents.slice(0, 4))
          setAllAgents(regular.length > 0 ? regular : data.agents.slice(4, 12))

          // Extract unique categories from agents
          const uniqueCategories = Array.from(new Set(data.agents.map((a: Agent) => a.category)))
            .filter((cat): cat is string => Boolean(cat))
            .map(cat => ({
              name: cat.charAt(0).toUpperCase() + cat.slice(1),
              value: cat,
              active: false
            }))

          setCategories([
            { name: "All", value: "all", active: true },
            ...uniqueCategories
          ])
        } else {
          // Use default agents if backend returns empty
          const featured = defaultAgents.filter(a => a.is_featured)
          const regular = defaultAgents.filter(a => !a.is_featured)
          setFeaturedAgents(featured)
          setAllAgents(regular)
        }
      } else {
        // Use default agents if backend fails
        const featured = defaultAgents.filter(a => a.is_featured)
        const regular = defaultAgents.filter(a => !a.is_featured)
        setFeaturedAgents(featured)
        setAllAgents(regular)
      }
    } catch (error) {
      console.error("Failed to load agents:", error)
      // Use default agents on error
      const featured = defaultAgents.filter(a => a.is_featured)
      const regular = defaultAgents.filter(a => !a.is_featured)
      setFeaturedAgents(featured)
      setAllAgents(regular)
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryClick = (category: string) => {
    setSelectedCategory(category)
    setCategories(prev => prev.map(cat => ({
      ...cat,
      active: cat.value === category
    })))
  }

  const filteredFeaturedAgents = featuredAgents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          agent.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === "all" || agent.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const filteredAllAgents = allAgents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          agent.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === "all" || agent.category === selectedCategory
    return matchesSearch && matchesCategory
  })
  return (
    <div className="bg-background-dark font-display text-[#E0E0E0]">
      <div className="relative flex min-h-screen w-full flex-col">
        <Header />
        <main className="flex-grow px-10 py-16">
          <div className="mx-auto max-w-7xl">
            <section className="flex flex-col items-center justify-center text-center">
              <h1 className="text-[#E0E0E0] tracking-[-0.02em] text-5xl font-bold leading-tight font-mono">
                Hermes Agent Marketplace
              </h1>
              <p className="text-[#E0E0E0]/70 text-lg font-normal leading-normal pt-4 max-w-2xl">
                Discover, Integrate, and Deploy AI Agents for Any Task.
              </p>
              <div className="mt-8 w-full max-w-2xl">
                <div className="relative">
                  <div className="pointer-events-none text-[#E0E0E0]/50 absolute inset-y-0 left-0 flex items-center pl-4">
                    <Search />
                  </div>
                  <input
                    className="form-input block w-full rounded-lg border-2 border-white/10 bg-white/5 py-3.5 pl-12 pr-4 text-[#E0E0E0] placeholder:text-[#E0E0E0]/50 focus:border-primary focus:outline-none focus:ring-0 transition-colors"
                    placeholder="Search for agents by name, function, or tag..."
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                {categories.map((cat) => (
                  <button
                    key={cat.value}
                    onClick={() => handleCategoryClick(cat.value)}
                    className={`flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-full border px-4 text-sm font-medium transition-colors ${
                      cat.active
                        ? "border-primary bg-primary/20 text-primary hover:bg-primary/30"
                        : "border-white/10 bg-white/5 text-[#E0E0E0] hover:border-primary hover:bg-primary/20 hover:text-primary"
                    }`}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </section>

            <section className="mt-20">
              <h2 className="text-2xl font-bold font-mono tracking-tight text-[#E0E0E0]">Featured Agents</h2>
              {loading ? (
                <div className="mt-6 flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : filteredFeaturedAgents.length > 0 ? (
                <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                  {filteredFeaturedAgents.map((agent) => (
                    <AgentCard key={agent.id} agent={agent} />
                  ))}
                </div>
              ) : (
                <div className="mt-6 text-center py-12">
                  <Bot className="w-12 h-12 text-white/30 mx-auto mb-4" />
                  <p className="text-[#E0E0E0]/50">No featured agents found matching your criteria</p>
                </div>
              )}
            </section>

            <section className="mt-20">
              <h2 className="text-2xl font-bold font-mono tracking-tight text-[#E0E0E0]">All Agents</h2>
              {loading ? (
                <div className="mt-6 flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : filteredAllAgents.length > 0 ? (
                <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                  {filteredAllAgents.map((agent) => (
                    <AgentCard key={agent.id} agent={agent} />
                  ))}
                </div>
              ) : (
                <div className="mt-6 text-center py-12">
                  <Bot className="w-12 h-12 text-white/30 mx-auto mb-4" />
                  <p className="text-[#E0E0E0]/50">No agents found matching your criteria</p>
                </div>
              )}
            </section>
          </div>
        </main>
      </div>
    </div>
  )
}