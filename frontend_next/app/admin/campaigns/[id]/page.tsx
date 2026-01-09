"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

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

type AuditLog = {
  id: string;
  action_type: string;
  actor_type: string;
  reason: string | null;
  created_at: string;
};

export default function AdminCampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params.id as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCampaign();
    loadAuditLogs();
  }, [campaignId]);

  async function loadCampaign() {
    const res = await fetch(`/api/admin/campaigns?id=${campaignId}`, {
      credentials: "include",
    });
    const data = await res.json();
    setCampaign(data[0] || null);
    setLoading(false);
  }

  async function loadAuditLogs() {
    const res = await fetch(
      `/api/admin/audit?campaign_id=${campaignId}`,
      { credentials: "include" }
    );
    const data = await res.json();
    setLogs(data || []);
  }

  async function forceToggleAI(enable: boolean) {
    const reason = prompt(
      `Reason for ${enable ? "FORCE ENABLE" : "FORCE DISABLE"} AI`
    );
    if (!reason) return;

    await fetch(`/api/admin/campaigns/${campaignId}/force-ai`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable, reason }),
    });

    loadCampaign();
    loadAuditLogs();
  }

  async function resetAI() {
    const reason = prompt("Reason for resetting campaign AI state");
    if (!reason) return;

    await fetch(`/api/admin/campaigns/${campaignId}/reset`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });

    loadCampaign();
    loadAuditLogs();
  }

  if (loading) {
    return <div className="p-6 text-sm text-gray-500">Loading…</div>;
  }

  if (!campaign) {
    return (
      <div className="p-6 text-sm text-red-600">
        Campaign not found
      </div>
    );
  }

  return (
    <div className="p-6 text-sm space-y-6">
      <div>
        <button
          onClick={() => router.back()}
          className="text-xs text-blue-600 underline"
        >
          ← Back
        </button>
      </div>

      <div className="border rounded p-4">
        <div className="text-lg font-semibold mb-2">
          {campaign.name}
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div><b>ID:</b> {campaign.id}</div>
          <div><b>User:</b> {campaign.user_id}</div>
          <div><b>Objective:</b> {campaign.objective}</div>
          <div><b>Status:</b> {campaign.status}</div>
          <div><b>AI Active:</b> {campaign.ai_active ? "YES" : "NO"}</div>
          <div><b>Manual:</b> {campaign.is_manual ? "YES" : "NO"}</div>
        </div>

        <div className="mt-4 flex gap-2">
          {campaign.ai_active ? (
            <button
              className="px-3 py-1 bg-red-600 text-white rounded text-xs"
              onClick={() => forceToggleAI(false)}
            >
              Force AI OFF
            </button>
          ) : (
            <button
              className="px-3 py-1 bg-green-600 text-white rounded text-xs"
              onClick={() => forceToggleAI(true)}
            >
              Force AI ON
            </button>
          )}

          <button
            className="px-3 py-1 bg-yellow-600 text-white rounded text-xs"
            onClick={resetAI}
          >
            Reset AI State
          </button>
        </div>
      </div>

      <div className="border rounded p-4">
        <div className="font-semibold mb-2">Audit Log</div>

        {logs.length === 0 ? (
          <div className="text-xs text-gray-500">
            No audit entries
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((l) => (
              <div
                key={l.id}
                className="border rounded p-2 text-xs"
              >
                <div>
                  <b>{l.action_type}</b> ({l.actor_type})
                </div>
                <div className="text-gray-500">
                  {new Date(l.created_at).toLocaleString()}
                </div>
                {l.reason && (
                  <div className="mt-1">
                    <b>Reason:</b> {l.reason}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
