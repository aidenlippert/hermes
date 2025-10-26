"use client";

import { useEffect, useState } from "react";

interface Agent {
  agent_id: string;
  name: string;
  endpoint: string;
  capabilities: Array<{
    name: string;
    description: string;
    confidence: number;
    cost: number;
    latency: number;
  }>;
  owner: string;
  trust_score: number;
  registered_at: string;
}

interface Contract {
  id: string;
  task_type: string;
  description: string;
  status: string;
  created_at: string;
  awarded_to: string[];
}

interface Bid {
  agent_id: string;
  amount: number;
  confidence: number;
  estimated_time: number;
}

interface ContractWithBids {
  contract: Contract;
  bids: Bid[];
}

interface ActivityEvent {
  timestamp: string;
  type: string;
  message: string;
  severity: "info" | "success" | "warning" | "error";
}

export default function MeshDashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [contracts, setContracts] = useState<Map<string, ContractWithBids>>(new Map());
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    task_type: "flight_search",
    description: "",
    origin: "",
    destination: "",
    date: "",
  });

  // Fetch agents
  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  // Poll contracts every 2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      contracts.forEach((_, contractId) => {
        fetchContract(contractId);
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [contracts]);

  const fetchAgents = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/mesh/agents`);
      const data = await res.json();
      setAgents(data.agents || []);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch agents:", err);
      setLoading(false);
    }
  };

  const fetchContract = async (contractId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/mesh/contracts/${contractId}`);
      const data = await res.json();
      setContracts((prev) => new Map(prev).set(contractId, data));
      
      // Add activity event
      if (data.contract.status === "DELIVERED" && !activity.find(a => a.message.includes(contractId))) {
        addActivity({
          timestamp: new Date().toISOString(),
          type: "contract_completed",
          message: `Contract ${contractId.substring(0, 8)} completed successfully.`,
          severity: "success"
        });
      }
    } catch (err) {
      console.error(`Failed to fetch contract ${contractId}:`, err);
    }
  };

  const createContract = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/mesh/contracts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: createForm.task_type,
          description: createForm.description,
          requirements: {
            origin: createForm.origin,
            destination: createForm.destination,
            date: createForm.date,
          },
        }),
      });

      const data = await res.json();
      if (data.success) {
        // Start polling this contract
        fetchContract(data.contract_id);
        
        // Add activity
        addActivity({
          timestamp: new Date().toISOString(),
          type: "contract_announced",
          message: `Contract ${data.contract_id.substring(0, 8)} initiated bidding phase.`,
          severity: "info"
        });
        
        // Reset form
        setCreateForm({
          task_type: "flight_search",
          description: "",
          origin: "",
          destination: "",
          date: "",
        });
        setShowCreateModal(false);
      }
    } catch (err) {
      console.error("Failed to create contract:", err);
    }
  };

  const addActivity = (event: ActivityEvent) => {
    setActivity(prev => [event, ...prev].slice(0, 20)); // Keep last 20 events
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "OPEN":
      case "BIDDING":
        return "status-yellow";
      case "AWARDED":
      case "IN_PROGRESS":
        return "status-green";
      case "DELIVERED":
      case "SETTLED":
        return "text-dark";
      default:
        return "text-dark";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "BIDDING": return "Bidding";
      case "AWARDED": return "Awarded";
      case "IN_PROGRESS": return "Active";
      case "DELIVERED": return "Delivered";
      case "SETTLED": return "Completed";
      default: return status;
    }
  };

  const getActivityIcon = (severity: string) => {
    switch (severity) {
      case "success": return { icon: "check_circle", color: "text-status-green" };
      case "warning": return { icon: "group", color: "text-status-yellow" };
      case "error": return { icon: "error", color: "text-status-red" };
      default: return { icon: "play_circle", color: "text-status-green" };
    }
  };

  const activeContracts = Array.from(contracts.values()).filter(
    c => ["BIDDING", "AWARDED", "IN_PROGRESS"].includes(c.contract.status)
  );
  const completedContracts = Array.from(contracts.values()).filter(
    c => ["DELIVERED", "SETTLED"].includes(c.contract.status)
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="text-white text-2xl font-['Space_Grotesk']">Loading mesh network...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-[#121212] text-[#EAEAEA] font-['Space_Grotesk']">
      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="flex-shrink-0 bg-[#1A1A1A] border-b border-[#3a3a3a] px-6 py-4">
          <div className="flex justify-between items-center gap-4">
            <div className="flex gap-2">
              <button className="p-2 text-[#9e9e9e] hover:text-white rounded-lg hover:bg-white/10">
                <span className="material-symbols-outlined">search</span>
              </button>
              <button className="p-2 text-[#9e9e9e] hover:text-white rounded-lg hover:bg-white/10">
                <span className="material-symbols-outlined">filter_list</span>
              </button>
              <button className="p-2 text-[#9e9e9e] hover:text-white rounded-lg hover:bg-white/10 relative">
                <span className="material-symbols-outlined">notifications</span>
                {activity.length > 0 && (
                  <span className="absolute top-2 right-2 flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#f20d0d] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#f20d0d]"></span>
                  </span>
                )}
              </button>
            </div>
            
            <div className="flex-1 max-w-3xl">
              {/* Stats */}
              <div className="flex flex-wrap gap-4">
                <div className="flex flex-1 min-w-[158px] flex-col gap-1 rounded-lg p-3 bg-[#2C2C2C]/50 border border-[#3a3a3a]">
                  <p className="text-[#9e9e9e] text-xs font-medium">Active Agents</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-white tracking-tight text-lg font-bold">{agents.length}</p>
                    <p className="text-[#00FF41] text-xs font-medium">online</p>
                  </div>
                </div>
                <div className="flex flex-1 min-w-[158px] flex-col gap-1 rounded-lg p-3 bg-[#2C2C2C]/50 border border-[#3a3a3a]">
                  <p className="text-[#9e9e9e] text-xs font-medium">Contracts In-Progress</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-white tracking-tight text-lg font-bold">{activeContracts.length}</p>
                    <p className="text-[#FFD600] text-xs font-medium">active</p>
                  </div>
                </div>
                <div className="flex flex-1 min-w-[158px] flex-col gap-1 rounded-lg p-3 bg-[#2C2C2C]/50 border border-[#3a3a3a]">
                  <p className="text-[#9e9e9e] text-xs font-medium">Completed</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-white tracking-tight text-lg font-bold">{completedContracts.length}</p>
                    <p className="text-[#00FF41] text-xs font-medium">done</p>
                  </div>
                </div>
                <div className="flex flex-1 min-w-[158px] flex-col gap-1 rounded-lg p-3 bg-[#2C2C2C]/50 border border-[#3a3a3a]">
                  <p className="text-[#9e9e9e] text-xs font-medium">System Health</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-[#00FF41] tracking-tight text-lg font-bold">Online</p>
                  </div>
                </div>
              </div>
            </div>
            
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center justify-center rounded-lg h-10 bg-[#f20d0d] text-white gap-2 text-sm font-bold leading-normal tracking-wide px-4 hover:bg-[#f20d0d]/90 transition-colors"
            >
              <span className="material-symbols-outlined text-base">add</span>
              <span className="truncate">Create Contract</span>
            </button>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="flex-1 grid grid-cols-12 gap-6 p-6 overflow-hidden">
          {/* Center Panel */}
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-6 overflow-y-auto">
            {/* Live Contract Feed */}
            <div className="flex flex-col">
              <h3 className="text-white text-lg font-bold leading-tight tracking-tight px-4 pb-2 pt-0">
                Live Contract Feed
              </h3>
              <div className="px-4 py-3">
                <div className="flex overflow-hidden rounded-lg border border-[#3a3a3a] bg-[#1A1A1A]">
                  <table className="flex-1 table-fixed">
                    <thead className="bg-[#2C2C2C]/50">
                      <tr>
                        <th className="px-4 py-3 text-left text-[#9e9e9e] w-[15%] text-sm font-medium">Contract ID</th>
                        <th className="px-4 py-3 text-left text-[#9e9e9e] w-[30%] text-sm font-medium">Objective</th>
                        <th className="px-4 py-3 text-left text-[#9e9e9e] w-[20%] text-sm font-medium">Involved Agents</th>
                        <th className="px-4 py-3 text-left text-[#9e9e9e] w-[15%] text-sm font-medium">Status</th>
                        <th className="px-4 py-3 text-left text-[#9e9e9e] w-[20%] text-sm font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Array.from(contracts.values()).map((contractData) => (
                        <tr key={contractData.contract.id} className="border-t border-[#3a3a3a] hover:bg-white/5">
                          <td className="h-[72px] px-4 py-2 text-[#9e9e9e] text-sm font-mono leading-normal truncate">
                            {contractData.contract.id.substring(0, 10).toUpperCase()}
                          </td>
                          <td className="h-[72px] px-4 py-2 text-white text-sm font-normal leading-normal truncate">
                            {contractData.contract.task_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </td>
                          <td className="h-[72px] px-4 py-2 text-[#9e9e9e] text-sm font-normal leading-normal truncate">
                            {contractData.contract.awarded_to.length > 0 
                              ? contractData.contract.awarded_to[0]
                              : `Bidding (${contractData.bids.length} agents)`
                            }
                          </td>
                          <td className="h-[72px] px-4 py-2 text-sm font-normal leading-normal">
                            <div className="flex items-center gap-2">
                              <span className={`w-2.5 h-2.5 rounded-full bg-${getStatusColor(contractData.contract.status)} ${
                                ["BIDDING", "IN_PROGRESS"].includes(contractData.contract.status) ? 'animate-pulse' : ''
                              }`}></span>
                              <span className={`text-${getStatusColor(contractData.contract.status)}`}>
                                {getStatusText(contractData.contract.status)}
                              </span>
                            </div>
                          </td>
                          <td className="h-[72px] px-4 py-2 text-[#f20d0d] font-bold tracking-wide cursor-pointer hover:underline">
                            View Details
                          </td>
                        </tr>
                      ))}
                      {contracts.size === 0 && (
                        <tr>
                          <td colSpan={5} className="h-[200px] text-center text-[#9e9e9e]">
                            No contracts yet. Create one to get started!
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Real-Time Agent Grid */}
            <div className="flex flex-col">
              <h3 className="text-white text-lg font-bold leading-tight tracking-tight px-4 pb-2 pt-4">
                Real-Time Agent Grid
              </h3>
              <div className="px-4 py-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents.map((agent) => (
                  <div 
                    key={agent.agent_id}
                    className="bg-[#2C2C2C] rounded-lg p-4 border border-[#3a3a3a] flex flex-col gap-3 hover:border-[#f20d0d]/50 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <p className="text-white font-bold">{agent.name}</p>
                      <div className="flex items-center gap-2 text-sm">
                        <div className="w-2 h-2 rounded-full bg-[#00FF41] animate-pulse"></div>
                        <span className="text-[#00FF41]">Active</span>
                      </div>
                    </div>
                    <div className="text-sm text-[#9e9e9e]">
                      <p className="font-mono text-xs mb-2">{agent.agent_id}</p>
                      {agent.capabilities.map((cap, idx) => (
                        <div key={idx} className="mb-1">
                          <span className="text-white">{cap.name}</span>
                          <span className="ml-2 text-[#00FF41]">${cap.cost}</span>
                          <span className="ml-2">{(cap.confidence * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Sidebar - Activity Stream */}
          <aside className="col-span-12 lg:col-span-4 bg-[#1A1A1A] rounded-lg border border-[#3a3a3a] flex flex-col overflow-y-auto">
            <div className="p-4 border-b border-[#3a3a3a]">
              <h3 className="text-white text-lg font-bold">Live Activity Stream</h3>
            </div>
            <div className="p-4 flex-1 flex flex-col gap-4 text-sm">
              {activity.length === 0 && (
                <div className="text-[#9e9e9e] text-center py-8">
                  No activity yet. Create a contract to see events here.
                </div>
              )}
              {activity.map((event, idx) => {
                const { icon, color } = getActivityIcon(event.severity);
                return (
                  <div key={idx} className="flex gap-3">
                    <span className={`material-symbols-outlined ${color} text-lg`}>{icon}</span>
                    <div>
                      <p className="text-white">{event.message}</p>
                      <p className="text-[#9e9e9e] text-xs">
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </aside>
        </div>
      </main>

      {/* Create Contract Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowCreateModal(false)}>
          <div className="bg-[#1A1A1A] border border-[#3a3a3a] rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-white text-xl font-bold mb-4">Create New Contract</h2>
            <form onSubmit={createContract} className="space-y-4">
              <div>
                <label className="block text-white mb-2 text-sm">Task Type</label>
                <select
                  value={createForm.task_type}
                  onChange={(e) => setCreateForm({ ...createForm, task_type: e.target.value })}
                  className="w-full bg-[#2C2C2C] text-white rounded p-2 border border-[#3a3a3a] focus:border-[#f20d0d] outline-none"
                >
                  <option value="flight_search">Flight Search</option>
                  <option value="hotel_search">Hotel Search</option>
                </select>
              </div>
              <div>
                <label className="block text-white mb-2 text-sm">Description</label>
                <input
                  type="text"
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full bg-[#2C2C2C] text-white rounded p-2 border border-[#3a3a3a] focus:border-[#f20d0d] outline-none"
                  placeholder="What are you looking for?"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white mb-2 text-sm">Origin</label>
                  <input
                    type="text"
                    value={createForm.origin}
                    onChange={(e) => setCreateForm({ ...createForm, origin: e.target.value })}
                    className="w-full bg-[#2C2C2C] text-white rounded p-2 border border-[#3a3a3a] focus:border-[#f20d0d] outline-none"
                    placeholder="JFK"
                    required
                  />
                </div>
                <div>
                  <label className="block text-white mb-2 text-sm">Destination</label>
                  <input
                    type="text"
                    value={createForm.destination}
                    onChange={(e) => setCreateForm({ ...createForm, destination: e.target.value })}
                    className="w-full bg-[#2C2C2C] text-white rounded p-2 border border-[#3a3a3a] focus:border-[#f20d0d] outline-none"
                    placeholder="LAX"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-white mb-2 text-sm">Date</label>
                <input
                  type="date"
                  value={createForm.date}
                  onChange={(e) => setCreateForm({ ...createForm, date: e.target.value })}
                  className="w-full bg-[#2C2C2C] text-white rounded p-2 border border-[#3a3a3a] focus:border-[#f20d0d] outline-none"
                  required
                />
              </div>
              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-[#2C2C2C] hover:bg-[#3a3a3a] text-white font-bold py-2 px-6 rounded transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-[#f20d0d] hover:bg-[#f20d0d]/90 text-white font-bold py-2 px-6 rounded transition"
                >
                  🚀 Announce
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Material Icons Link */}
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
    </div>
  );
}
