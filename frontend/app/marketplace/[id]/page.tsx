"use client"

import {
  LayoutGrid,
  Bot,
  GitFork,
  Key,
  Store,
  FileText,
  HelpCircle,
  Bell,
  Settings,
  Plus,
  Play,
  MessageSquare,
  Database,
  BarChart,
  Code,
  Link as LinkIcon,
  History,
} from "lucide-react"
import Link from "next/link"

const Sidebar = () => (
  <aside className="w-64 flex-shrink-0 bg-[#1C1C1C] border-r border-[#333333]">
    <div className="flex h-full flex-col justify-between p-4">
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3 px-2">
          <div className="size-8 text-primary">
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
          <h2 className="text-white text-lg font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
        </div>
        <div className="flex flex-col gap-2">
          <Link className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 rounded-lg transition-colors" href="#">
            <LayoutGrid className="text-2xl" />
            <p className="text-sm font-medium leading-normal">Dashboard</p>
          </Link>
          <Link className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/20 text-white" href="#">
            <Bot className="text-2xl" />
            <p className="text-sm font-medium leading-normal">Agents</p>
          </Link>
          <Link className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 rounded-lg transition-colors" href="#">
            <GitFork className="text-2xl" />
            <p className="text-sm font-medium leading-normal">Workflows</p>
          </Link>
          <Link className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 rounded-lg transition-colors" href="#">
            <Key className="text-2xl" />
            <p className="text-sm font-medium leading-normal">API Keys</p>
          </Link>
          <Link className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 rounded-lg transition-colors" href="#">
            <Store className="text-2xl" />
            <p className="text-sm font-medium leading-normal">Marketplace</p>
          </Link>
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <Link className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 rounded-lg transition-colors" href="#">
          <FileText className="text-2xl" />
          <p className="text-sm font-medium leading-normal">Documentation</p>
        </Link>
        <Link className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-white/5 rounded-lg transition-colors" href="#">
          <HelpCircle className="text-2xl" />
          <p className="text-sm font-medium leading-normal">Support</p>
        </Link>
      </div>
    </div>
  </aside>
)

const TopNav = () => (
  <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-[#333333] px-8 py-4 bg-[#1C1C1C]">
    <div className="flex items-center gap-4 text-white">
      <h1 className="text-lg font-semibold">Agent Details</h1>
    </div>
    <div className="flex flex-1 justify-end gap-4 items-center">
      <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 w-10 bg-[#333333] text-gray-300 hover:bg-white/10 transition-colors">
        <Bell className="text-xl" />
      </button>
      <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 w-10 bg-[#333333] text-gray-300 hover:bg-white/10 transition-colors">
        <Settings className="text-xl" />
      </button>
      <div
        className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"
        style={{
          backgroundImage:
            'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAAEkbuCy5rymb85U8BBwF66D5sx89sX53A4OUa6RM1TFqIAUOjNw7fqILKOUfl2dvnNIQcAcJxg0eVBl2fvP_T-ZIyudgUjOqH-mPW2cPLna8leSmRTEbNeLDy5HmrjZaPnBnfleFvxaQp8l1hc9AN2T3ITh-Tcp63ZUtNE_vuaTsEO9ZpHWDS8wbns3a1LGhZ_38EjN5FFpRz-B0yKsZNZmE-BsZtxtodvVgP96WvspE0NfslxQ4YbhuvQQqxq2f4PHb5ELwiKEpZ")',
        }}
      ></div>
    </div>
  </header>
)

const StatCard = ({ title, value, change, isPositive }: { title: string; value: string; change: string; isPositive: boolean }) => (
    <div className="flex flex-col gap-2 rounded-lg p-6 bg-[#1C1C1C] border border-[#333333]">
        <p className="text-[#888888] text-sm font-medium leading-normal">{title}</p>
        <p className="text-white tracking-light text-3xl font-bold leading-tight">{value}</p>
        <p className={`text-sm font-medium leading-normal ${isPositive ? 'text-green-400' : 'text-red-400'}`}>{change}</p>
    </div>
)

const CapabilityCard = ({ title, description, icon }: { title: string; description: string; icon: React.ElementType }) => {
    const Icon = icon
    return (
        <div className="p-4 rounded-lg bg-background-dark border border-[#333333] flex items-center justify-between">
            <div>
                <p className="font-semibold text-white">{title}</p>
                <p className="text-sm text-[#888888]">{description}</p>
            </div>
            <Icon className="text-[#888888]" />
        </div>
    )
}

const MetadataSidebar = () => (
    <aside className="col-span-12 lg:col-span-3 bg-[#1C1C1C] border border-[#333333] rounded-lg p-6 h-fit">
        <div className="flex flex-col gap-6 divide-y divide-[#333333]">
            <div>
                <h4 className="text-sm font-semibold text-[#888888] mb-2 uppercase tracking-wider">Author</h4>
                <div className="flex items-center gap-3">
                    <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBXSmTal58sPPxe8H7O8AuRogi1c4Eaw7gsYY_hIlW92mp1h1zst2QGlNJ7lDwfXCf7MCgCk2cgWgCim8zWYNP6bUrRylyo_DaVYl0cv03hbsHnhDVjpm8S3sTZsy2Bd8CiWLfpXatWHAXOpoEp8i2o-aQ-iTbK6-7DoHbK7zH1-DVHGGGlDi3AiH5_YNvh4GHeNxwkeNsHCDfLaSoogtIMG9tWrVyQODxx8x9hX6WL73lYdIeg9K4mBrK98Oe7kh44aF1zZ6HmZfms")'}}></div>
                    <div>
                        <p className="font-medium text-white">Cyberdyne Systems</p>
                        <p className="text-sm text-[#888888]">Verified Creator</p>
                    </div>
                </div>
            </div>
            <div className="pt-6">
                <h4 className="text-sm font-semibold text-[#888888] mb-2 uppercase tracking-wider">Details</h4>
                <div className="text-sm space-y-3 text-white">
                    <div className="flex justify-between"><span className="text-[#888888]">Version:</span><span>2.1.3</span></div>
                    <div className="flex justify-between"><span className="text-[#888888]">Last Updated:</span><span>2 days ago</span></div>
                    <div className="flex justify-between"><span className="text-[#888888]">Created:</span><span>Jan 12, 2023</span></div>
                </div>
            </div>
            <div className="pt-6">
                <h4 className="text-sm font-semibold text-[#888888] mb-3 uppercase tracking-wider">Tags</h4>
                <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-mono py-1 px-2.5 bg-primary/20 text-primary rounded-full border border-primary/30">data-analysis</span>
                    <span className="text-xs font-mono py-1 px-2.5 bg-white/5 text-[#888888] rounded-full border border-white/10">nlp</span>
                    <span className="text-xs font-mono py-1 px-2.5 bg-white/5 text-[#888888] rounded-full border border-white/10">finance</span>
                    <span className="text-xs font-mono py-1 px-2.5 bg-white/5 text-[#888888] rounded-full border border-white/10">automation</span>
                </div>
            </div>
            <div className="pt-6">
                <h4 className="text-sm font-semibold text-[#888888] mb-3 uppercase tracking-wider">Resources</h4>
                <div className="flex flex-col gap-2">
                    <Link href="#" className="flex items-center gap-2 text-sm text-white hover:text-primary transition-colors"><LinkIcon className="text-base" /> API Documentation</Link>
                    <Link href="#" className="flex items-center gap-2 text-sm text-white hover:text-primary transition-colors"><History className="text-base" /> Version History</Link>
                </div>
            </div>
        </div>
    </aside>
)


export default function AgentDetailPage() {
  return (
    <div className="bg-background-dark font-display text-[#EAEAEA]">
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 flex flex-col">
          <TopNav />
          <div className="flex-1 p-8 grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-9 flex flex-col gap-8">
              <section>
                <div className="flex flex-wrap justify-between items-start gap-4">
                  <div className="flex flex-col gap-2">
                    <p className="text-white text-4xl font-black leading-tight tracking-tighter">DataAnalyzer v2.1</p>
                    <p className="text-[#888888] text-base font-mono leading-normal">Agent ID: H-AGENT-77B4</p>
                  </div>
                  <div className="flex gap-3">
                    <button className="flex items-center justify-center gap-2 rounded-lg h-12 px-6 text-sm font-bold bg-white/5 hover:bg-white/10 ring-1 ring-inset ring-white/10 transition-all hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]">
                      <Plus /> Add to Workflow
                    </button>
                    <button className="flex items-center justify-center gap-2 rounded-lg h-12 px-6 text-sm font-bold bg-primary text-white hover:bg-red-700 transition-all shadow-[0_0_15px_rgba(234,42,51,0.5)] hover:shadow-[0_0_25px_rgba(234,42,51,0.7)]">
                      <Play /> Try in Sandbox
                    </button>
                  </div>
                </div>
              </section>
              <section>
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex h-8 shrink-0 items-center justify-center gap-x-2 rounded-full bg-green-500/10 px-3 border border-green-500/20">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <p className="text-green-300 text-sm font-medium leading-normal">Online</p>
                  </div>
                  <div className="flex h-8 shrink-0 items-center justify-center gap-x-2 rounded-full bg-white/5 px-3 border border-white/10">
                    <p className="text-[#888888] text-sm font-medium leading-normal">Tasks Completed: 1,234,567</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    <StatCard title="Success Rate" value="98.7%" change="+0.2%" isPositive={true} />
                    <StatCard title="Avg. Response Time" value="1.2s" change="-0.1s" isPositive={false} />
                    <StatCard title="Total Runs (24h)" value="1.2M" change="+5.6%" isPositive={true} />
                </div>
              </section>
              <section className="flex flex-col gap-6">
                <div className="border-b border-[#333333]">
                  <nav className="flex gap-6 -mb-px">
                    <button className="py-3 px-1 border-b-2 border-primary text-white text-sm font-semibold">Capabilities</button>
                    <button className="py-3 px-1 border-b-2 border-transparent text-[#888888] hover:text-white transition-colors text-sm font-semibold">Pricing</button>
                    <button className="py-3 px-1 border-b-2 border-transparent text-[#888888] hover:text-white transition-colors text-sm font-semibold">Reviews</button>
                    <button className="py-3 px-1 border-b-2 border-transparent text-[#888888] hover:text-white transition-colors text-sm font-semibold">Sandbox</button>
                  </nav>
                </div>
                <div className="rounded-lg bg-[#1C1C1C] border border-[#333333] p-6">
                  <h3 className="text-lg font-bold text-white mb-4">Core Functions</h3>
                  <div className="space-y-4">
                    <CapabilityCard title="Natural Language Processing" description="Analyzes and understands human language from text and speech." icon={MessageSquare} />
                    <CapabilityCard title="Data Aggregation" description="Collects and combines data from multiple disparate sources." icon={Database} />
                    <CapabilityCard title="Predictive Modeling" description="Uses statistical models to forecast future outcomes." icon={BarChart} />
                    <CapabilityCard title="API Integration" description="Connects with third-party services via RESTful APIs." icon={Code} />
                  </div>
                </div>
              </section>
            </div>
            <MetadataSidebar />
          </div>
        </main>
      </div>
    </div>
  )
}