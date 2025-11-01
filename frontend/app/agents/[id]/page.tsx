"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  Search,
  Bell,
  Plus,
  Star,
  StarHalf,
  Briefcase
} from "lucide-react"

interface Capability {
  name: string
  costPerCall: number
  confidenceScore: number
}

interface Review {
  author: string
  rating: number
  comment: string
  date: string
}

interface AgentData {
  id: string
  name: string
  description: string
  trustGrade: string
  publisher: {
    name: string
    description: string
    profileUrl: string
  }
  imageUrl: string
  capabilities: Capability[]
  stats: {
    totalRuns: string
    successRate: string
    avgLatency: string
  }
  tags: string[]
  reviews: {
    average: number
    count: number
    items: Review[]
  }
}

export default function AgentProfilePage() {
  const params = useParams()
  const router = useRouter()
  const [agent, setAgent] = useState<AgentData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAgentData()
  }, [params.id])

  const fetchAgentData = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/agents/${params.id}`,
        {
          headers: {
            "Content-Type": "application/json",
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAgent(data)
      } else {
        setAgent(getMockData())
      }
    } catch (error) {
      console.error("Failed to fetch agent data:", error)
      setAgent(getMockData())
    } finally {
      setLoading(false)
    }
  }

  const getMockData = (): AgentData => ({
    id: params.id as string,
    name: "QuantumLeap Analyzer",
    description: "A high-performance agent designed for complex data analysis and predictive modeling. Ideal for financial forecasting, market trend analysis, and scientific research. Utilizes proprietary quantum-inspired algorithms to deliver results with unparalleled speed and accuracy.",
    trustGrade: "A+",
    publisher: {
      name: "Cyberdyne Systems",
      description: "Pioneering advancements in artificial intelligence and automation since 1984.",
      profileUrl: "/publishers/cyberdyne-systems"
    },
    imageUrl: "https://images.unsplash.com/photo-1639322537228-f710d846310a?w=800&auto=format&fit=crop",
    capabilities: [
      { name: "Predictive Financial Modeling", costPerCall: 0.025, confidenceScore: 99.2 },
      { name: "Market Trend Analysis", costPerCall: 0.018, confidenceScore: 98.5 },
      { name: "Scientific Data Simulation", costPerCall: 0.040, confidenceScore: 97.9 },
      { name: "Anomaly Detection", costPerCall: 0.010, confidenceScore: 92.1 }
    ],
    stats: {
      totalRuns: "1.2M",
      successRate: "98.7%",
      avgLatency: "120ms"
    },
    tags: ["data-analysis", "finance", "predictive-modeling", "research"],
    reviews: {
      average: 4.9,
      count: 1283,
      items: [
        { author: "Alex R.", rating: 5, comment: "Game-changer for our fintech startup. The accuracy of financial predictions is insane.", date: "2024-01-15" },
        { author: "Dr. Lena Soren", rating: 5, comment: "Accelerated our research by months. The simulation capability is robust and reliable.", date: "2024-01-10" },
        { author: "Market Maven", rating: 4, comment: "Very powerful, but has a slight learning curve. Once you get it, it's indispensable.", date: "2024-01-05" }
      ]
    }
  })

  const handleAddToWorkflow = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://web-production-3df46.up.railway.app'}/api/v1/workflows/add-agent`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ agentId: params.id })
        }
      )

      if (response.ok) {
        router.push("/developer/workflow-builder")
      }
    } catch (error) {
      console.error("Failed to add agent to workflow:", error)
    }
  }

  const renderStars = (rating: number) => {
    const stars = []
    const fullStars = Math.floor(rating)
    const hasHalfStar = rating % 1 !== 0

    for (let i = 0; i < fullStars; i++) {
      stars.push(<Star key={i} className="w-4 h-4 fill-red-500 text-red-500" />)
    }

    if (hasHalfStar) {
      stars.push(<StarHalf key="half" className="w-4 h-4 fill-red-500 text-red-500" />)
    }

    while (stars.length < 5) {
      stars.push(<Star key={`empty-${stars.length}`} className="w-4 h-4 text-white/30" />)
    }

    return stars
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-white text-xl">Loading agent profile...</div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-xl mb-4">Agent not found</p>
          <Link href="/marketplace" className="text-purple-400 hover:text-purple-300 transition-colors">
            Return to Marketplace
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <header className="sticky top-0 bg-[#0a0a0a]/80 backdrop-blur-sm z-50 border-b border-white/10 px-6 sm:px-10 lg:px-20 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 text-white">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 48 48">
                  <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" />
                </svg>
              </div>
              <h2 className="text-lg font-bold">Astraeus</h2>
            </div>
            <label className="hidden md:flex items-center h-10 max-w-64">
              <div className="flex w-full items-stretch rounded-lg overflow-hidden">
                <div className="flex items-center justify-center pl-4 bg-white/5 text-white/50">
                  <Search className="w-5 h-5" />
                </div>
                <input
                  type="text"
                  placeholder="Search"
                  className="flex-1 bg-white/5 text-white placeholder:text-white/50 px-4 border-none focus:outline-none focus:ring-0"
                />
              </div>
            </label>
          </div>
          <div className="flex items-center gap-8">
            <div className="hidden lg:flex items-center gap-9">
              <Link href="/marketplace" className="text-white/90 hover:text-white text-sm font-medium transition-colors">
                Marketplace
              </Link>
              <Link href="/my-workflows" className="text-white/90 hover:text-white text-sm font-medium transition-colors">
                My Workflows
              </Link>
              <Link href="/developer/api-docs" className="text-white/90 hover:text-white text-sm font-medium transition-colors">
                API Keys
              </Link>
              <Link href="/developer/guide" className="text-white/90 hover:text-white text-sm font-medium transition-colors">
                Docs
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <button className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 text-white transition-colors">
                <Bell className="w-5 h-5" />
              </button>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500"></div>
            </div>
          </div>
        </div>
      </header>

      <main className="px-6 sm:px-10 lg:px-20 py-5">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-2 py-4 text-sm">
            <Link href="/marketplace" className="text-white/60 hover:text-white transition-colors">
              Marketplace
            </Link>
            <span className="text-white/60">/</span>
            <Link href="/marketplace?category=data-analysis" className="text-white/60 hover:text-white transition-colors">
              Data Analysis Agents
            </Link>
            <span className="text-white/60">/</span>
            <span className="text-white font-medium">{agent.name}</span>
          </div>

          <div className="flex flex-wrap items-start justify-between gap-4 py-6 border-b border-white/10">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-4">
                <h1 className="text-white text-4xl font-black">{agent.name}</h1>
                <div className="flex items-center gap-2 bg-green-500/10 text-green-400 px-3 py-1 rounded-full">
                  <span className="font-bold text-sm">{agent.trustGrade}</span>
                  <span className="text-xs">Trust Grade</span>
                </div>
              </div>
              <p className="text-white/60 text-base">
                Published by{" "}
                <Link href={agent.publisher.profileUrl} className="text-red-400/80 hover:text-red-400 underline transition-colors">
                  {agent.publisher.name}
                </Link>
              </p>
            </div>
            <button
              onClick={handleAddToWorkflow}
              className="flex items-center gap-2 rounded-lg h-10 px-6 bg-purple-600 hover:bg-purple-700 text-white font-bold transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add to Workflow
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
            <div className="lg:col-span-2 flex flex-col gap-8">
              <div className="flex flex-col bg-white/5 border border-white/10 rounded-lg overflow-hidden">
                <div
                  className="w-full aspect-[21/9] bg-cover bg-center"
                  style={{ backgroundImage: `url(${agent.imageUrl})` }}
                />
                <div className="p-6">
                  <p className="text-white text-lg font-bold mb-2">Description</p>
                  <p className="text-white/60">{agent.description}</p>
                </div>
              </div>

              <div className="flex flex-col bg-white/5 rounded-lg border border-white/10">
                <h2 className="text-white text-lg font-bold px-6 pt-5 pb-3">Capabilities</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-t border-white/10">
                      <tr>
                        <th className="p-4 px-6 text-xs font-medium uppercase text-white/60 text-left">Capability Name</th>
                        <th className="p-4 px-6 text-xs font-medium uppercase text-white/60 text-right">Cost/API Call</th>
                        <th className="p-4 px-6 text-xs font-medium uppercase text-white/60 text-right">Confidence Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {agent.capabilities.map((cap, i) => (
                        <tr key={i}>
                          <td className="p-4 px-6 text-white/90 text-sm">{cap.name}</td>
                          <td className="p-4 px-6 text-white/90 text-sm text-right">${cap.costPerCall.toFixed(3)}</td>
                          <td className={`p-4 px-6 text-sm font-semibold text-right ${
                            cap.confidenceScore >= 95 ? 'text-green-400' : 'text-orange-400'
                          }`}>
                            {cap.confidenceScore}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex flex-col bg-white/5 rounded-lg border border-white/10 p-6 gap-4">
                <h2 className="text-white text-lg font-bold">Usage Statistics</h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="border border-white/10 rounded-lg p-4">
                    <span className="text-white/60 text-sm block mb-1">Total Runs</span>
                    <span className="text-white text-2xl font-bold">{agent.stats.totalRuns}</span>
                  </div>
                  <div className="border border-white/10 rounded-lg p-4">
                    <span className="text-white/60 text-sm block mb-1">Success Rate</span>
                    <span className="text-red-500 text-2xl font-bold">{agent.stats.successRate}</span>
                  </div>
                  <div className="border border-white/10 rounded-lg p-4">
                    <span className="text-white/60 text-sm block mb-1">Average Latency</span>
                    <span className="text-white text-2xl font-bold">{agent.stats.avgLatency}</span>
                  </div>
                </div>
              </div>
            </div>

            <aside className="flex flex-col gap-8">
              <div className="flex flex-col gap-4 bg-white/5 rounded-lg border border-white/10 p-6">
                <h3 className="text-white text-lg font-bold">Publisher</h3>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center">
                    <Briefcase className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-white font-semibold">{agent.publisher.name}</p>
                    <Link href={agent.publisher.profileUrl} className="text-red-400/80 hover:text-red-400 text-sm transition-colors">
                      View Profile
                    </Link>
                  </div>
                </div>
                <p className="text-white/60 text-sm">{agent.publisher.description}</p>
              </div>

              <div className="flex flex-col gap-4 bg-white/5 rounded-lg border border-white/10 p-6">
                <h3 className="text-white text-lg font-bold">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.tags.map((tag, i) => (
                    <span key={i} className="bg-red-500/20 text-red-400/90 px-3 py-1 text-sm rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex flex-col gap-4 bg-white/5 rounded-lg border border-white/10 p-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-white text-lg font-bold">User Reviews</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-bold">{agent.reviews.average}</span>
                    <div className="flex">{renderStars(agent.reviews.average)}</div>
                    <span className="text-white/60 text-sm">({agent.reviews.count})</span>
                  </div>
                </div>
                <div className="flex flex-col gap-6 max-h-96 overflow-y-auto pr-2">
                  {agent.reviews.items.map((review, i) => (
                    <div key={i} className={`flex flex-col gap-2 ${i < agent.reviews.items.length - 1 ? 'border-b border-white/10 pb-4' : ''}`}>
                      <div className="flex justify-between items-center">
                        <p className="text-white font-semibold">{review.author}</p>
                        <div className="flex">{renderStars(review.rating)}</div>
                      </div>
                      <p className="text-white/60 text-sm">{review.comment}</p>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  )
}
