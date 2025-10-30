"use client";

import React, { useMemo, useState } from "react";
import { useParams } from "next/navigation";

type Receipt = {
  message_id: string;
  conversation_id: string;
  from_agent_id: string;
  to_agent_id: string;
  message_type: string;
  requires_response?: boolean;
  receipt_id: string;
  delivered_at?: string | null;
  acked_at?: string | null;
};

export default function AgentInboxPage() {
  const params = useParams();
  const agentId = (params?.agentId as string) || "";
  const [token, setToken] = useState("");
  const [items, setItems] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(false);
  const [ackBusy, setAckBusy] = useState<string | null>(null);

  const headers = useMemo(() => {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  }, [token]);

  const load = async () => {
    if (!agentId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/a2a/receipts?agent_id=${agentId}&limit=50`, { headers });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setItems(data.receipts || []);
    } finally {
      setLoading(false);
    }
  };

  const ack = async (messageId: string) => {
    if (!agentId) return;
    setAckBusy(messageId);
    try {
      const url = new URL(`/api/v1/a2a/ack`, window.location.origin);
      url.searchParams.set("message_id", messageId);
      url.searchParams.set("agent_id", agentId);
      const res = await fetch(url.toString(), { method: "POST", headers });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      await load();
    } finally {
      setAckBusy(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Agent Inbox</h1>
      <div className="flex gap-2 items-center">
        <label className="text-sm text-gray-600">Agent</label>
        <input className="border rounded px-2 py-1 w-[340px]" value={agentId} readOnly />
      </div>
      <section className="space-y-3">
        <h2 className="text-xl font-medium">Auth</h2>
        <div className="flex gap-2 items-center">
          <input className="border rounded px-2 py-1 w-[600px]" placeholder="Paste Bearer token..." value={token} onChange={(e) => setToken(e.target.value)} />
          <button className="border rounded px-3 py-1" onClick={load} disabled={loading || !token}>{loading ? "Loading..." : "Load Receipts"}</button>
        </div>
      </section>

      <section>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="py-1 pr-2">Message</th>
              <th className="py-1 pr-2">Type</th>
              <th className="py-1 pr-2">Delivered</th>
              <th className="py-1 pr-2">Acked</th>
              <th className="py-1 pr-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.receipt_id} className="border-b">
                <td className="py-1 pr-2 font-mono text-xs">{r.message_id.slice(0, 8)}…</td>
                <td className="py-1 pr-2">{r.message_type}</td>
                <td className="py-1 pr-2">{r.delivered_at ? new Date(r.delivered_at).toLocaleString() : ""}</td>
                <td className="py-1 pr-2">{r.acked_at ? new Date(r.acked_at).toLocaleString() : ""}</td>
                <td className="py-1 pr-2">
                  <button className="border rounded px-2 py-0.5 text-sm" disabled={!!r.acked_at || ackBusy === r.message_id} onClick={() => ack(r.message_id)}>
                    {r.acked_at ? "Acked" : ackBusy === r.message_id ? "Acking..." : "Ack"}
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td className="py-2 text-gray-500" colSpan={5}>No receipts</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
