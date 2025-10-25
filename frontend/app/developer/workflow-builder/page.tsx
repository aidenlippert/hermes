import Link from "next/link"
import { 
  Workflow, 
  CheckCircle, 
  Bell, 
  HelpCircle, 
  PlayCircle, 
  Database, 
  Share2, 
  ArrowRightCircle,
  PlusCircle,
  SlidersHorizontal,
  ChevronDown,
  Maximize,
  ZoomIn,
  ZoomOut,
  AlignEndHorizontal,
  AlignEndVertical,
  LayoutGrid,
  Bug,
  Play
} from "lucide-react"

const SidebarItem = ({ icon: Icon, label, active = false }: { icon: React.ElementType, label: string, active?: boolean }) => (
  <div className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${active ? 'bg-primary/20 text-accent-secondary' : 'hover:bg-white/5'}`}>
    <Icon className="w-5 h-5" />
    <p className="text-sm font-medium leading-normal">{label}</p>
  </div>
)

const InspectorPanel = () => (
  <aside className="flex h-full w-80 shrink-0 flex-col border-l border-solid border-border-color bg-background-dark p-4">
    <div className="flex items-center gap-3 mb-4">
      <SlidersHorizontal className="text-accent-secondary" />
      <h2 className="text-white text-base font-medium">Node Properties</h2>
    </div>
    <div className="flex flex-col gap-3">
      <details className="flex flex-col rounded-lg border border-border-color bg-white/5 px-[15px] py-[7px] group" open>
        <summary className="flex cursor-pointer items-center justify-between gap-6 py-2 list-none">
          <p className="text-white text-sm font-medium leading-normal">Configuration</p>
          <ChevronDown className="text-white group-open:rotate-180 transition-transform w-4 h-4" />
        </summary>
        <p className="text-gray-400 text-sm font-normal leading-normal pb-2">
          This section contains editable fields for the selected node, such as API endpoints, authentication keys, and other required settings.
        </p>
      </details>
      <details className="flex flex-col rounded-lg border border-border-color bg-white/5 px-[15px] py-[7px] group">
        <summary className="flex cursor-pointer items-center justify-between gap-6 py-2 list-none">
          <p className="text-white text-sm font-medium leading-normal">Parameters</p>
          <ChevronDown className="text-white group-open:rotate-180 transition-transform w-4 h-4" />
        </summary>
        <p className="text-gray-400 text-sm font-normal leading-normal pb-2">
          Define input and output parameters for this node to pass data between agents in the workflow.
        </p>
      </details>
      <details className="flex flex-col rounded-lg border border-border-color bg-white/5 px-[15px] py-[7px] group">
        <summary className="flex cursor-pointer items-center justify-between gap-6 py-2 list-none">
          <p className="text-white text-sm font-medium leading-normal">Documentation</p>
          <ChevronDown className="text-white group-open:rotate-180 transition-transform w-4 h-4" />
        </summary>
        <p className="text-gray-400 text-sm font-normal leading-normal pb-2">
          Access detailed documentation and examples for using this node effectively.
        </p>
      </details>
    </div>
  </aside>
)

export default function WorkflowBuilderPage() {
  return (
    <div className="flex flex-col h-screen font-display bg-background-dark text-white min-h-screen">
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-border-color px-6 py-3 shrink-0">
        <div className="flex items-center gap-4 text-white">
          <Workflow className="w-6 h-6 text-primary" />
          <h2 className="text-white text-lg font-bold leading-tight tracking-[-0.015em]">Hermes</h2>
        </div>
        <div className="flex items-center gap-6">
          <Link className="text-white text-sm font-medium leading-normal" href="#">Customer Onboarding v2.1</Link>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span>Saved</span>
          </div>
        </div>
        <div className="flex flex-1 justify-end items-center gap-4">
          <div className="flex gap-2">
            <button className="flex cursor-pointer items-center justify-center rounded-lg h-10 w-10 bg-white/5 text-white hover:bg-white/10 transition-colors">
              <Bell className="w-5 h-5" />
            </button>
            <button className="flex cursor-pointer items-center justify-center rounded-lg h-10 w-10 bg-white/5 text-white hover:bg-white/10 transition-colors">
              <HelpCircle className="w-5 h-5" />
            </button>
          </div>
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuDORxHKMzpZld38s60YiKsNTHAeFUkO2Ayc08VdG575P6qfWXrTlIpHQ12ewP3FhVU6dzIZlrtTfjEzZEr06pKtWSOxTeNZguTi50Fb2FdU0nHb11nM03MEZDwUT-go1wtYcdigNF4FHIjcjqtoV_LA_SzZLCF46QriM5YTh0o7enZoxqWnST4MIx3RK6aX_ltGG47jIMoI8UE2GzdMlQ2fPFOQEKYPpHi_fg-LQqp2Ldo4drhfBkUbhZXGZq70ocF_cY8DyJA6NQBf")'}}></div>
        </div>
      </header>
      
      <div className="flex flex-1 overflow-hidden">
        <aside className="flex h-full w-64 shrink-0 flex-col justify-between border-r border-solid border-border-color bg-background-dark p-4">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col">
              <h1 className="text-white text-base font-medium leading-normal">Component Library</h1>
              <p className="text-gray-400 text-sm font-normal leading-normal">Drag nodes to the canvas</p>
            </div>
            <div className="flex flex-col gap-2">
              <SidebarItem icon={PlayCircle} label="Triggers" active />
              <SidebarItem icon={Database} label="Data Processing" />
              <SidebarItem icon={Share2} label="Logic" />
              <SidebarItem icon={ArrowRightCircle} label="Outputs" />
            </div>
          </div>
        </aside>

        <main className="flex-1 relative canvas-bg">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-6 text-center p-4">
              <PlusCircle className="w-20 h-20 text-white/10" />
              <div className="flex max-w-[480px] flex-col items-center gap-2">
                <p className="text-white text-lg font-bold leading-tight tracking-[-0.015em]">Workflow Canvas is Empty</p>
                <p className="text-gray-400 text-sm font-normal leading-normal">Drag a node from the library to start building your orchestration.</p>
              </div>
              <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-white/10 text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-white/20 transition-colors">
                <span className="truncate">Add First Node</span>
              </button>
            </div>
          </div>
        </main>

        <InspectorPanel />
      </div>

      <footer className="flex items-center justify-between gap-2 px-4 py-2 border-t border-solid border-border-color shrink-0">
        <div className="flex items-center gap-2">
          <button className="p-2 text-white rounded-lg hover:bg-white/10 transition-colors"><ZoomIn className="w-5 h-5" /></button>
          <button className="p-2 text-white rounded-lg hover:bg-white/10 transition-colors"><ZoomOut className="w-5 h-5" /></button>
          <button className="p-2 text-white rounded-lg hover:bg-white/10 transition-colors"><Maximize className="w-5 h-5" /></button>
          <div className="w-px h-6 bg-border-color mx-2"></div>
          <button className="p-2 text-white rounded-lg hover:bg-white/10 transition-colors"><AlignEndHorizontal className="w-5 h-5" /></button>
          <button className="p-2 text-white rounded-lg hover:bg-white/10 transition-colors"><AlignEndVertical className="w-5 h-5" /></button>
          <button className="p-2 text-white rounded-lg hover:bg-white/10 transition-colors"><LayoutGrid className="w-5 h-5" /></button>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 bg-white/10 text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-4 hover:bg-white/20 transition-colors">
            <Bug className="w-4 h-4" />
            <span className="truncate">Debug</span>
          </button>
          <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 bg-primary text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-4 hover:bg-red-700 transition-colors">
            <Play className="w-4 h-4" />
            <span className="truncate">Run</span>
          </button>
        </div>
      </footer>
    </div>
  )
}
