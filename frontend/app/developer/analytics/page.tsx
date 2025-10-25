"use client"

import Link from "next/link"
import { 
  LayoutDashboard, 
  Bot, 
  BarChart, 
  History, 
  Settings, 
  FileText, 
  HelpCircle 
} from "lucide-react"

const StatCard = ({ title, value, change, isError = false }: { title: string, value: string, change: string, isError?: boolean }) => (
  <div className={`flex flex-col gap-2 rounded-lg p-6 border ${isError ? 'border-primary/50' : 'border-[#533c3d]'} bg-[#181111]`}>
    <p className="text-white text-base font-medium leading-normal">{title}</p>
    <p className={`tracking-light text-3xl font-bold leading-tight ${isError ? 'text-primary' : 'text-white'}`}>{value}</p>
    <p className={`text-base font-medium leading-normal ${isError ? 'text-primary' : change.startsWith('+') ? 'text-[#0bda95]' : 'text-[#fa7f38]'}`}>{change}</p>
  </div>
)

const Chart = () => (
  <div className="flex min-h-[250px] flex-1 flex-col gap-8 py-4">
    <svg fill="none" height="100%" preserveAspectRatio="none" viewBox="-3 0 478 150" width="100%" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient gradientUnits="userSpaceOnUse" id="paint0_linear_1131_5935" x1="236" x2="236" y1="1" y2="149">
          <stop stopColor="#382929"></stop>
          <stop offset="1" stopColor="#382929" stopOpacity="0"></stop>
        </linearGradient>
      </defs>
      <path d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25V149H0V109Z" fill="url(#paint0_linear_1131_5935)"></path>
      <path d="M0 109C18.1538 109 18.1538 21 36.3077 21C54.4615 21 54.4615 41 72.6154 41C90.7692 41 90.7692 93 108.923 93C127.077 93 127.077 33 145.231 33C163.385 33 163.385 101 181.538 101C199.692 101 199.692 61 217.846 61C236 61 236 45 254.154 45C272.308 45 272.308 121 290.462 121C308.615 121 308.615 149 326.769 149C344.923 149 344.923 1 363.077 1C381.231 1 381.231 81 399.385 81C417.538 81 417.538 129 435.692 129C453.846 129 453.846 25 472 25" stroke="#b89d9f" strokeLinecap="round" strokeWidth="3"></path>
      <path d="M0 140C18.1538 140 18.1538 130 36.3077 130C54.4615 130 54.4615 135 72.6154 135C90.7692 135 90.7692 142 108.923 142C127.077 142 127.077 138 145.231 138C163.385 138 163.385 145 181.538 145C199.692 145 199.692 141 217.846 141C236 141 236 143 254.154 143C272.308 143 272.308 148 290.462 148C308.615 148 308.615 146 326.769 146C344.923 146 344.923 125 363.077 125C381.231 125 381.231 140 399.385 140C417.538 140 417.538 138 435.692 138C453.846 138 453.846 132 472 132" stroke="#ea2a33" strokeLinecap="round" strokeWidth="2"></path>
    </svg>
    <div className="flex justify-around -mt-4">
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">12 AM</p>
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">4 AM</p>
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">8 AM</p>
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">12 PM</p>
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">4 PM</p>
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">8 PM</p>
      <p className="text-[#b89d9f] text-[13px] font-bold leading-normal tracking-[0.015em]">Now</p>
    </div>
  </div>
)

const queries = [
  { timestamp: "2024-07-21 14:35:12.189", id: "q_ab12cd34ef56", status: "Success", latency: "112ms" },
  { timestamp: "2024-07-21 14:35:10.543", id: "q_bc23de45fg67", status: "Success", latency: "98ms" },
  { timestamp: "2024-07-21 14:35:08.912", id: "q_cd34ef56gh78", status: "System Error", latency: "1540ms" },
  { timestamp: "2024-07-21 14:35:07.331", id: "q_de45fg67hi89", status: "Validation Error", latency: "45ms" },
  { timestamp: "2024-07-21 14:35:05.102", id: "q_ef56gh78ij90", status: "Success", latency: "130ms" },
]

export default function AnalyticsPage() {
  return (
    <div className="flex min-h-screen bg-background-dark font-display text-[#E0E0E0]">
      <aside className="flex w-64 flex-col bg-[#181111] p-4 border-r border-[#382929]">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBV4qqVD5MG4j40aIvWlr9rBeDSDzVU3hzzkSBJ6qrz7rNfZ6tWt5NVIMziKmZWTk6aQcfOrBdjGR1vy0NGLSVbaS2YYZSdJpKw0UiXenESFU2BAKJX3captbSxqjjwdf-z9zeZeRFi2mj93uSGzb5NgodGtJeyXcweABcwl3x8qInxIoDW-5hq9rGXq29FxnRkCse9Lt06QCAD0slu-3seI-saZlxdkXW9SmQeObnad5YPmoYzAUfv74K-Ttbab_1axuC8f29kFxSy")'}}></div>
            <div className="flex flex-col">
              <h1 className="text-white text-base font-medium leading-normal">Hermes</h1>
              <p className="text-[#b89d9f] text-sm font-normal leading-normal">Agent Orchestration</p>
            </div>
          </div>
          <div className="flex flex-col gap-2 mt-4">
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#382929] transition-colors">
              <LayoutDashboard className="text-white" />
              <p className="text-white text-sm font-medium leading-normal">Dashboard</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#382929] transition-colors">
              <Bot className="text-white" />
              <p className="text-white text-sm font-medium leading-normal">Agents</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[#382929]">
              <BarChart className="text-white" />
              <p className="text-white text-sm font-medium leading-normal">Analytics</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#382929] transition-colors">
              <History className="text-white" />
              <p className="text-white text-sm font-medium leading-normal">Logs</p>
            </Link>
            <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#382929] transition-colors">
              <Settings className="text-white" />
              <p className="text-white text-sm font-medium leading-normal">Settings</p>
            </Link>
          </div>
        </div>
        <div className="mt-auto flex flex-col gap-1">
          <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#382929] transition-colors">
            <FileText className="text-white" />
            <p className="text-white text-sm font-medium leading-normal">Documentation</p>
          </Link>
          <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#382929] transition-colors">
            <HelpCircle className="text-white" />
            <p className="text-white text-sm font-medium leading-normal">Support</p>
          </Link>
        </div>
      </aside>

      <main className="flex-1 p-8">
        <div className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-col gap-2">
              <p className="text-white text-4xl font-black leading-tight tracking-[-0.033em]">Agent Performance: QueryProcessor-v3</p>
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <p className="text-[#0BDA95] text-base font-normal leading-normal">Status: Online</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#382929] text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-[#4a3a3a] transition-colors">
                <span className="truncate">Refresh Data</span>
              </button>
              <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-red-700 transition-colors">
                <span className="truncate">Export Report</span>
              </button>
              <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-transparent border border-[#533c3d] text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-[#382929] transition-colors">
                <span className="truncate">Configure Agent</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Total Queries" value="1,230,456" change="+5.2%" />
            <StatCard title="Success Rate" value="99.8%" change="-0.1%" />
            <StatCard title="Avg. Latency" value="128ms" change="+2.4%" />
            <StatCard title="Error Count" value="42" change="+12.0%" isError />
          </div>

          <div className="flex flex-col gap-2 rounded-lg border border-[#533c3d] p-6 bg-[#181111]">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-white text-lg font-medium leading-normal">Core Metrics Over Time</p>
                <p className="text-[#b89d9f] text-base font-normal leading-normal">Last 24 Hours</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#b89d9f]"></div>
                  <span className="text-sm text-[#b89d9f]">Queries</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-primary"></div>
                  <span className="text-sm text-[#b89d9f]">Errors</span>
                </div>
              </div>
            </div>
            <Chart />
          </div>

          <div className="flex flex-col gap-4 rounded-lg border border-[#533c3d] p-6 bg-[#181111]">
            <h3 className="text-lg font-medium text-white">Recent Agent Queries</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-[#b89d9f]">
                <thead className="border-b border-[#533c3d] text-xs uppercase text-white">
                  <tr>
                    <th className="px-4 py-3" scope="col">Timestamp</th>
                    <th className="px-4 py-3" scope="col">Query ID</th>
                    <th className="px-4 py-3" scope="col">Status</th>
                    <th className="px-4 py-3 text-right" scope="col">Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {queries.map((query, index) => (
                    <tr key={index} className="border-b border-[#382929] hover:bg-[#2a1f1f]">
                      <td className="px-4 py-3">{query.timestamp}</td>
                      <td className="px-4 py-3 font-mono">{query.id}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                          query.status === 'Success' ? 'bg-green-500/20 text-green-400' :
                          query.status === 'System Error' ? 'bg-red-500/20 text-primary' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {query.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">{query.latency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
