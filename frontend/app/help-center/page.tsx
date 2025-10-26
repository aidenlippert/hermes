"use client"

import Link from "next/link"
import { 
  LayoutDashboard, 
  Bot, 
  GitFork, 
  HelpCircle, 
  Settings, 
  LogOut,
  Search,
  ChevronDown,
  LifeBuoy
} from "lucide-react"

const faqs = [
  {
    question: "How do I create my first agent?",
    answer: "To create your first agent, navigate to the 'Agents' section from the sidebar, click on the 'New Agent' button, and follow the on-screen instructions. You'll need to provide a name, select a model, and define its initial prompt and capabilities. For a detailed walkthrough, check our 'Getting Started' guide.",
    open: true,
  },
  { question: "What is a workflow and how does it work?" },
  { question: "Can I integrate Hermes with my existing APIs?" },
  { question: "How is usage billed?" },
  { question: "Where can I find my API key?" },
];

const NavLink = ({ href, icon: Icon, label, active = false }: { href: string, icon: React.ElementType, label: string, active?: boolean }) => (
  <a className={`flex items-center gap-3 rounded-lg px-3 py-2 ${active ? 'bg-primary/20 text-primary' : 'text-gray-300 hover:bg-white/10'}`} href={href}>
    <Icon className={active ? "text-primary" : "text-white"} />
    <p className="text-sm font-medium leading-normal">{label}</p>
  </a>
);

const FaqItem = ({ faq }: { faq: typeof faqs[0] }) => (
  <div className="flex flex-col rounded-lg bg-[#2a1b1d]">
    <button className="flex w-full items-center justify-between p-5 text-left">
      <span className="text-lg font-medium text-white">{faq.question}</span>
      <ChevronDown className="text-gray-400" />
    </button>
    {faq.open && (
      <div className="px-5 pb-5 text-gray-300">
        <p>{faq.answer}</p>
      </div>
    )}
  </div>
);

export default function HelpCenterPage() {
  return (
    <div className="relative flex min-h-screen w-full flex-col bg-background-dark font-display">
      <div className="flex h-full grow">
        <aside className="flex w-64 flex-col bg-[#110A0B] p-4 text-white">
          <div className="flex h-full flex-col justify-between">
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBevkkEDogAUpm1Gn97V89nv5IfbJ-e3GAj4mfbx-l3Vk_53NH6L2jXS2H6EM5nZSv4FS0PQb3ozsSivPczzEVGXh49DIDZBNmhFUV-X08ZvmajaEs_2tH7ZK_QE0YB8c57rzFk58wd2DFd4nc5zfHMojSyPDTu5f09VBAtuouuybxF9OKM9fL79YjEREhShROKn_-f9hZdJnyu8h18Ni-JqT3iamyKxpedVaU517JqjeRQli2l83TAXWqrAA0yAC0Er9oK1c4k_wbE")' }}></div>
                <div className="flex flex-col">
                  <h1 className="text-white text-base font-medium leading-normal">Hermes</h1>
                  <p className="text-gray-400 text-sm font-normal leading-normal">A2A Agent Orchestration</p>
                </div>
              </div>
              <nav className="mt-4 flex flex-col gap-2">
                <NavLink href="/chat" icon={LayoutDashboard} label="Dashboard" />
                <NavLink href="/marketplace" icon={Bot} label="Agents" />
                <NavLink href="/developer/workflow-builder" icon={GitFork} label="Workflows" />
                <NavLink href="/help-center" icon={HelpCircle} label="Help Center" active />
              </nav>
            </div>
            <div className="flex flex-col gap-4">
              <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-wide hover:bg-primary/90">
                <span className="truncate">New Workflow</span>
              </button>
              <div className="flex flex-col gap-1 border-t border-white/10 pt-4">
                <NavLink href="/developer/api-docs" icon={Settings} label="Settings" />
                <NavLink href="/auth/login" icon={LogOut} label="Logout" />
              </div>
            </div>
          </div>
        </aside>
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
            <div className="flex flex-wrap gap-2 pb-4">
              <Link className="text-gray-400 text-sm font-medium leading-normal hover:text-white" href="/">Hermes</Link>
              <span className="text-gray-500 text-sm font-medium leading-normal">/</span>
              <span className="text-white text-sm font-medium leading-normal">Help Center</span>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 pb-6">
              <div className="flex min-w-72 flex-col gap-2">
                <p className="text-white text-4xl font-black leading-tight tracking-[-0.033em]">Hermes Help Center</p>
                <p className="text-gray-400 text-base font-normal leading-normal">Your knowledge base for mastering agent orchestration.</p>
              </div>
            </div>
            <div className="py-3">
              <div className="flex w-full flex-1 items-stretch rounded-lg h-14">
                <div className="text-gray-400 flex border-none bg-[#2a1b1d] items-center justify-center pl-4 rounded-l-lg border-r-0">
                  <Search />
                </div>
                <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border-none bg-[#2a1b1d] h-full placeholder:text-gray-400 px-4 rounded-l-none border-l-0 pl-2 text-base font-normal leading-normal" placeholder="Search topics and questions..." />
              </div>
            </div>
            <div className="flex flex-wrap gap-3 p-3">
              <button className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-primary px-4 text-sm font-medium text-white">Getting Started</button>
              <button className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-[#2a1b1d] px-4 text-sm font-medium text-gray-300 hover:bg-primary/30">Agent Configuration</button>
              <button className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-[#2a1b1d] px-4 text-sm font-medium text-gray-300 hover:bg-primary/30">API Integration</button>
              <button className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-[#2a1b1d] px-4 text-sm font-medium text-gray-300 hover:bg-primary/30">Billing</button>
              <button className="flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-[#2a1b1d] px-4 text-sm font-medium text-gray-300 hover:bg-primary/30">Troubleshooting</button>
            </div>
            <div className="mt-8 flex flex-col gap-3">
              {faqs.map((faq, i) => <FaqItem key={i} faq={faq} />)}
            </div>
            <div className="mt-12 rounded-lg border border-primary/50 bg-[#2a1b1d] p-8">
              <div className="flex flex-col items-center justify-center text-center">
                <div className="flex items-center justify-center rounded-full bg-primary/20 p-3 mb-4">
                  <LifeBuoy className="text-primary text-3xl" />
                </div>
                <h3 className="text-2xl font-bold text-white">Can't find an answer?</h3>
                <p className="mt-2 max-w-md text-gray-300">Our support team is here to help. Reach out to us for any questions you might have.</p>
                <button className="mt-6 flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-11 px-6 bg-primary text-white text-base font-bold leading-normal tracking-wide hover:bg-primary/90">Contact Support</button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
