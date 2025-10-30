"use client";

import React, { useEffect, useMemo, useState } from "react";

type Org = { id: string; name: string; domain?: string | null };
type Member = { id: string; user_id: string; role: string; joined_at?: string | null };
type Agent = { id: string; name: string; org_id?: string | null; creator_id?: string | null };

type FetcherOptions = {
  method?: string;
  body?: any;
};

export default function OrgsAdminPage() {
  const [token, setToken] = useState<string>("");
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [loadingOrgs, setLoadingOrgs] = useState(false);

  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgDomain, setNewOrgDomain] = useState("");

  const [selectedOrgId, setSelectedOrgId] = useState<string>("");
  const [members, setMembers] = useState<Member[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);

  const [addUserId, setAddUserId] = useState("");
  const [addRole, setAddRole] = useState("member");

  const [agents, setAgents] = useState<Agent[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);

  const [assignAgentId, setAssignAgentId] = useState("");
  const [assignDemoBusy, setAssignDemoBusy] = useState(false);
  const [assignDemoMsg, setAssignDemoMsg] = useState<string>("");

  // Federation contacts
  type FedContact = {
    id: string;
    remote_agent_at: string;
    remote_agent_name?: string | null;
    remote_domain?: string | null;
    remote_org_id?: string | null;
    local_agent_id?: string | null;
    local_org_id?: string | null;
    last_seen_at?: string | null;
  };
  const [contacts, setContacts] = useState<FedContact[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [contactsFilter, setContactsFilter] = useState("");

  const [orgAllowSource, setOrgAllowSource] = useState("");
  const [orgAllowTarget, setOrgAllowTarget] = useState("");
  const [orgAllowAllowed, setOrgAllowAllowed] = useState(true);

  const [agentAllowSource, setAgentAllowSource] = useState("");
  const [agentAllowTarget, setAgentAllowTarget] = useState("");
  const [agentAllowAllowed, setAgentAllowAllowed] = useState(true);

  const headers = useMemo(() => {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  }, [token]);

  const fetcher = async (path: string, opts: FetcherOptions = {}) => {
    const res = await fetch(path, {
      method: opts.method || "GET",
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${t}`);
    }
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return res.json();
    return res.text();
  };

  const loadOrgs = async () => {
    setLoadingOrgs(true);
    try {
      const data = await fetcher("/api/v1/orgs");
      setOrgs(data.orgs ?? []);
    } finally {
      setLoadingOrgs(false);
    }
  };

  const loadMembers = async (orgId: string) => {
    if (!orgId) return;
    setLoadingMembers(true);
    try {
      const data = await fetcher(`/api/v1/orgs/${orgId}/members`);
      setMembers(data.members ?? []);
    } finally {
      setLoadingMembers(false);
    }
  };

  const loadAgents = async () => {
    setLoadingAgents(true);
    try {
      const data = await fetcher(`/api/v1/agents`);
      setAgents(data.agents ?? []);
    } finally {
      setLoadingAgents(false);
    }
  };

  const loadContacts = async () => {
    setContactsLoading(true);
    try {
      const data = await fetcher(`/api/v1/a2a/federation/contacts`);
      setContacts(data.contacts ?? []);
    } finally {
      setContactsLoading(false);
    }
  };

  useEffect(() => {
    // no auto load until token provided
  }, []);

  const onCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetcher("/api/v1/orgs", {
      method: "POST",
      body: { name: newOrgName, domain: newOrgDomain || null },
    });
    setNewOrgName("");
    setNewOrgDomain("");
    await loadOrgs();
  };

  const onAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId) return;
    await fetcher(`/api/v1/orgs/${selectedOrgId}/members`, {
      method: "POST",
      body: { user_id: addUserId, role: addRole.toUpperCase() },
    });
    setAddUserId("");
    await loadMembers(selectedOrgId);
  };

  const onAssignAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId || !assignAgentId) return;
    await fetcher(`/api/v1/orgs/${selectedOrgId}/agents/${assignAgentId}/assign`, {
      method: "POST",
    });
    setAssignAgentId("");
    await loadAgents();
  };

  const onAssignDemoAgents = async () => {
    if (!selectedOrgId) return;
    setAssignDemoBusy(true);
    setAssignDemoMsg("");
    try {
      const data = await fetcher(`/api/v1/orgs/${selectedOrgId}/assign_demo_agents`, { method: "POST", body: {} });
      const assigned = (data?.assigned ?? []).join(", ");
      const skipped = (data?.skipped ?? []).join(", ");
      const missing = (data?.missing ?? []).join(", ");
      setAssignDemoMsg(`assigned: [${assigned}] | skipped: [${skipped}] | missing: [${missing}]`);
      await loadAgents();
    } catch (e: any) {
      setAssignDemoMsg(`error: ${e?.message || String(e)}`);
    } finally {
      setAssignDemoBusy(false);
    }
  };

  const onSetOrgAllow = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetcher(`/api/v1/a2a/allow/org`, {
      method: "POST",
      body: { source_org_id: orgAllowSource, target_org_id: orgAllowTarget, allowed: orgAllowAllowed },
    });
  };

  const onSetAgentAllow = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetcher(`/api/v1/a2a/allow/agent`, {
      method: "POST",
      body: { source_agent_id: agentAllowSource, target_agent_id: agentAllowTarget, allowed: agentAllowAllowed },
    });
  };

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold">Organization Admin</h1>

      <section className="space-y-2">
        <h2 className="text-xl font-medium">Auth</h2>
        <div className="flex gap-2 items-center">
          <input
            className="border rounded px-2 py-1 w-[600px]"
            placeholder="Paste Bearer token..."
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <button className="border rounded px-3 py-1" onClick={() => { loadOrgs(); loadAgents(); loadContacts(); }}>
            Load Orgs, Agents & Contacts
          </button>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">Create Organization</h2>
        <form className="flex gap-2 items-end" onSubmit={onCreateOrg}>
          <div className="flex flex-col">
            <label>Name</label>
            <input className="border rounded px-2 py-1" value={newOrgName} onChange={(e) => setNewOrgName(e.target.value)} required />
          </div>
          <div className="flex flex-col">
            <label>Domain (optional)</label>
            <input className="border rounded px-2 py-1" value={newOrgDomain} onChange={(e) => setNewOrgDomain(e.target.value)} />
          </div>
          <button className="border rounded px-3 py-1" disabled={!newOrgName}>Create</button>
        </form>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">Organizations</h2>
        <div className="flex items-center gap-2">
          <button className="border rounded px-3 py-1" onClick={loadOrgs} disabled={loadingOrgs}>Refresh</button>
          <span className="text-sm text-gray-500">{loadingOrgs ? "Loading..." : `${orgs.length} orgs`}</span>
        </div>
        <div className="flex gap-2 items-center">
          <label>Select</label>
          <select className="border rounded px-2 py-1" value={selectedOrgId} onChange={(e) => { setSelectedOrgId(e.target.value); loadMembers(e.target.value); }}>
            <option value="">--</option>
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>{o.name} ({o.domain || "no domain"})</option>
            ))}
          </select>
          <button className="border rounded px-3 py-1" onClick={() => selectedOrgId && loadMembers(selectedOrgId)} disabled={!selectedOrgId || loadingMembers}>Load Members</button>
        </div>
        {selectedOrgId && (
          <div className="border rounded p-3">
            <h3 className="font-medium mb-2">Members</h3>
            <ul className="list-disc pl-6 space-y-1">
              {members.map((m) => (
                <li key={m.id}>
                  <span className="font-mono">{m.user_id}</span> — {m.role} {m.joined_at ? `• joined ${new Date(m.joined_at).toLocaleString()}` : ""}
                </li>
              ))}
              {members.length === 0 && <li className="text-gray-500">No members</li>}
            </ul>
            <form className="mt-3 flex gap-2 items-end" onSubmit={onAddMember}>
              <div className="flex flex-col">
                <label>User ID</label>
                <input className="border rounded px-2 py-1" value={addUserId} onChange={(e) => setAddUserId(e.target.value)} required />
              </div>
              <div className="flex flex-col">
                <label>Role</label>
                <select className="border rounded px-2 py-1" value={addRole} onChange={(e) => setAddRole(e.target.value)}>
                  <option value="member">member</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <button className="border rounded px-3 py-1">Add Member</button>
            </form>
          </div>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">Agents</h2>
        <div className="flex items-center gap-2">
          <button className="border rounded px-3 py-1" onClick={loadAgents} disabled={loadingAgents}>Refresh</button>
          <span className="text-sm text-gray-500">{loadingAgents ? "Loading..." : `${agents.length} agents`}</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="border rounded p-3">
            <h3 className="font-medium mb-2">Assign Demo Agents to Org</h3>
            <div className="flex items-center gap-2">
              <label>Org</label>
              <select className="border rounded px-2 py-1" value={selectedOrgId} onChange={(e) => setSelectedOrgId(e.target.value)}>
                <option value="">--</option>
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>{o.name}</option>
                ))}
              </select>
              <button className="border rounded px-3 py-1" disabled={!selectedOrgId || assignDemoBusy} onClick={onAssignDemoAgents}>
                {assignDemoBusy ? "Assigning..." : "Assign Demo Agents"}
              </button>
            </div>
            {assignDemoMsg && (
              <p className="text-sm text-gray-600 mt-2 break-all">{assignDemoMsg}</p>
            )}
          </div>

          <div className="border rounded p-3">
            <h3 className="font-medium mb-2">Assign Agent to Org</h3>
            <form className="flex flex-col gap-2" onSubmit={onAssignAgent}>
              <div className="flex items-center gap-2">
                <label>Org</label>
                <select className="border rounded px-2 py-1" value={selectedOrgId} onChange={(e) => setSelectedOrgId(e.target.value)}>
                  <option value="">--</option>
                  {orgs.map((o) => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label>Agent</label>
                <select className="border rounded px-2 py-1" value={assignAgentId} onChange={(e) => setAssignAgentId(e.target.value)}>
                  <option value="">--</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name} ({a.id.slice(0, 6)}…)</option>
                  ))}
                </select>
              </div>
              <button className="border rounded px-3 py-1" disabled={!selectedOrgId || !assignAgentId}>Assign</button>
            </form>
          </div>

          <div className="border rounded p-3">
            <h3 className="font-medium mb-2">Federation Contacts</h3>
            <div className="flex items-center gap-2 mb-2">
              <button className="border rounded px-3 py-1" onClick={loadContacts} disabled={contactsLoading}>Refresh</button>
              <input className="border rounded px-2 py-1" placeholder="Filter by domain or name..." value={contactsFilter} onChange={(e) => setContactsFilter(e.target.value)} />
              <span className="text-sm text-gray-500">{contactsLoading ? "Loading..." : `${contacts.length} contacts`}</span>
            </div>
            <div className="max-h-64 overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="py-1 pr-2">Remote</th>
                    <th className="py-1 pr-2">Domain</th>
                    <th className="py-1 pr-2">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts
                    .filter((c) => {
                      const f = contactsFilter.toLowerCase();
                      if (!f) return true;
                      return (
                        (c.remote_domain || "").toLowerCase().includes(f) ||
                        (c.remote_agent_at || "").toLowerCase().includes(f) ||
                        (c.remote_agent_name || "").toLowerCase().includes(f)
                      );
                    })
                    .map((c) => (
                      <tr key={c.id} className="border-b">
                        <td className="py-1 pr-2">
                          <span className="font-mono">{c.remote_agent_at}</span>
                          {c.remote_agent_name ? <span className="text-gray-500 ml-1">({c.remote_agent_name})</span> : null}
                        </td>
                        <td className="py-1 pr-2">{c.remote_domain || ""}</td>
                        <td className="py-1 pr-2">{c.last_seen_at ? new Date(c.last_seen_at).toLocaleString() : ""}</td>
                      </tr>
                    ))}
                  {contacts.length === 0 && (
                    <tr><td className="py-2 text-gray-500" colSpan={3}>No contacts</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="border rounded p-3">
            <h3 className="font-medium mb-2">Org → Org Allow</h3>
            <form className="flex flex-col gap-2" onSubmit={onSetOrgAllow}>
              <div className="flex items-center gap-2">
                <label>Source Org</label>
                <select className="border rounded px-2 py-1" value={orgAllowSource} onChange={(e) => setOrgAllowSource(e.target.value)}>
                  <option value="">--</option>
                  {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label>Target Org</label>
                <select className="border rounded px-2 py-1" value={orgAllowTarget} onChange={(e) => setOrgAllowTarget(e.target.value)}>
                  <option value="">--</option>
                  {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label>Allowed</label>
                <input type="checkbox" checked={orgAllowAllowed} onChange={(e) => setOrgAllowAllowed(e.target.checked)} />
              </div>
              <button className="border rounded px-3 py-1" disabled={!orgAllowSource || !orgAllowTarget}>Save</button>
            </form>
          </div>

          <div className="border rounded p-3">
            <h3 className="font-medium mb-2">Agent → Agent Allow</h3>
            <form className="flex flex-col gap-2" onSubmit={onSetAgentAllow}>
              <div className="flex items-center gap-2">
                <label>Source Agent</label>
                <select className="border rounded px-2 py-1" value={agentAllowSource} onChange={(e) => setAgentAllowSource(e.target.value)}>
                  <option value="">--</option>
                  {agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label>Target Agent</label>
                <select className="border rounded px-2 py-1" value={agentAllowTarget} onChange={(e) => setAgentAllowTarget(e.target.value)}>
                  <option value="">--</option>
                  {agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label>Allowed</label>
                <input type="checkbox" checked={agentAllowAllowed} onChange={(e) => setAgentAllowAllowed(e.target.checked)} />
              </div>
              <button className="border rounded px-3 py-1" disabled={!agentAllowSource || !agentAllowTarget}>Save</button>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
}
