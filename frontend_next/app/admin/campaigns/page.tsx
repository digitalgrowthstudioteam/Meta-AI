"use client";

import { useEffect, useState } from "react";

type Campaign = {
  id: string;
  user_id: string;
  name: string;
  objective: string;
  status: string;
  ai_active: boolean;
  ai_execution_locked: boolean;
  is_manual: boolean;
  created_at: string;
};

export default function AdminCampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiFilter, setAiFilter] = useState<string>("all");

  useEffect(() => {
    fetchCampaigns();
  }, [aiFilter]);

  async function fetchCampaigns() {
    setLoading(true);
    let url = "/api/admin/campaigns";
    if (aiFilter !== "all") {
      url += `?ai_active=${aiFilter}`;
    }

    const res = await fetch(url, { credentials: "include" });
    const data = await res.json();
    setCampaigns(data);
    setLoading(false);
  }

  async function forceToggleAI(
    campaignId: string,
    enable: boolean
  ) {
    const reason = prompt(
      `Reason for ${enable ? "ENABLING" : "DISABLING"} AI`
    );
    if (!reason) return;

    await fetch(`/api/admin/campaigns/${campaignId}/force-ai`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable, reason }),
    });

    fetchCampaigns();
  }

  return (
    <div className="p-6 text-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="text-lg font-semibold">Admin Campaign Explorer</div>

        <select
          className="border px-2 py-1 rounded text-sm"
          value={aiFilter}
          onChange={(e) => setAiFilter(e.target.value)}
        >
          <option value="all">All</option>
          <option value="true">AI Active</option>
          <option value="false">AI Disabled</option>
        </select>
      </div>

      {loading ? (
        <div className="text-gray-500">Loading campaigns…</div>
      ) : (
        <div className="overflow-x-auto border rounded">
          <table className="w-full border-collapse">
            <thead className="bg-gray-100 text-left">
              <tr>
                <th className="p-2 border">Campaign</th>
                <th className="p-2 border">Objective</th>
                <th className="p-2 border">Status</th>
                <th className="p-2 border">AI</th>
                <th className="p-2 border">Manual</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="p-2 border">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-gray-500">
                      {c.id}
                    </div>
                  </td>
                  <td className="p-2 border">{c.objective}</td>
                  <td className="p-2 border">{c.status}</td>
                  <td className="p-2 border">
                    {c.ai_active ? "ON" : "OFF"}
                  </td>
                  <td className="p-2 border">
                    {c.is_manual ? "YES" : "NO"}
                  </td>
                  <td className="p-2 border space-x-2">
                    {c.ai_active ? (
                      <button
                        className="px-2 py-1 bg-red-600 text-white rounded text-xs"
                        onClick={() =>
                          forceToggleAI(c.id, false)
                        }
                      >
                        Force OFF
                      </button>
                    ) : (
                      <button
                        className="px-2 py-1 bg-green-600 text-white rounded text-xs"
                        onClick={() =>
                          forceToggleAI(c.id, true)
                        }
                      >
                        Force ON
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
