"use client";

import { useEffect, useState } from "react";

type Campaign = {
  id: string;
  name: string;
  objective: string;
  status: string;
  ai_active: boolean;
  last_meta_sync_at?: string;
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ===============================
  // LOAD CAMPAIGNS (READ-ONLY)
  // ===============================
  const loadCampaigns = async () => {
    setLoading(true);
    setError(null);

    try {
      const url = new URL("/api/campaigns/", window.location.href);

      const res = await fetch(url.toString(), {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      // IMPORTANT: empty array is a VALID state
      setCampaigns(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setCampaigns([]);
      setError("Unable to load campaigns from Meta.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  // ===============================
  // SYNC CAMPAIGNS
  // ===============================
  const syncCampaigns = async () => {
    setSyncing(true);

    try {
      const url = new URL("/api/campaigns/sync", window.location.href);

      const res = await fetch(url.toString(), {
        method: "POST",
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      await loadCampaigns();
    } catch {
      alert("Failed to sync campaigns. Please try again.");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            Campaigns
          </h1>
          <p className="text-sm text-gray-500">
            Synced from Meta Ads Manager • Read-only
          </p>
        </div>

        <button
          onClick={syncCampaigns}
          disabled={syncing}
          className="px-4 py-2 text-sm rounded border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50"
        >
          {syncing ? "Syncing…" : "Sync Campaigns"}
        </button>
      </div>

      {/* INFO */}
      <div className="bg-blue-50 border border-blue-100 rounded p-4 text-sm text-blue-700">
        Campaigns are managed in Meta Ads Manager. You cannot create or edit
        campaigns here.
      </div>

      {/* LOADING */}
      {loading && (
        <div className="bg-white border border-gray-200 rounded p-6 text-sm text-gray-500">
          Loading campaigns from Meta…
        </div>
      )}

      {/* ERROR */}
      {!loading && error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {/* EMPTY STATE */}
      {!loading && !error && campaigns.length === 0 && (
        <div className="bg-white border border-gray-200 rounded p-10 text-center">
          <div className="text-sm text-gray-600 mb-3">
            No campaigns synced yet.
          </div>
          <button
            onClick={syncCampaigns}
            disabled={syncing}
            className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync Campaigns"}
          </button>
        </div>
      )}

      {/* TABLE */}
      {!loading && !error && campaigns.length > 0 && (
        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr className="text-gray-600">
                <th className="px-4 py-3 text-left font-medium">
                  Campaign
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  Objective
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  Status
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  AI Status
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  Last Synced
                </th>
              </tr>
            </thead>

            <tbody>
              {campaigns.map((c) => (
                <tr
                  key={c.id}
                  className="border-b last:border-b-0 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {c.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      ID: {c.id.slice(0, 8)}…
                    </div>
                  </td>

                  <td className="px-4 py-3">{c.objective}</td>
                  <td className="px-4 py-3">{c.status}</td>
                  <td className="px-4 py-3">
                    {c.ai_active ? "AI Active" : "AI Inactive"}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {c.last_meta_sync_at
                      ? new Date(c.last_meta_sync_at).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="text-xs text-gray-400">
        All data is read-only and synced directly from Meta Ads Manager.
      </div>
    </div>
  );
}
