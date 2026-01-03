"use client";

import { useEffect, useState } from "react";

type Campaign = {
  id: string;
  name: string;
  status: string;
  objective?: string;
  ai_active?: boolean;
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);

  // -----------------------------------
  // LOAD CAMPAIGNS
  // -----------------------------------
  const loadCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch("/api/campaigns", {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      // EMPTY ARRAY IS VALID
      setCampaigns(Array.isArray(data) ? data : []);
      setMetaConnected(true);
    } catch (err) {
      console.error("Campaign load failed", err);
      setError("Unable to reach campaign service.");
      setMetaConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  // -----------------------------------
  // CONNECT META
  // -----------------------------------
  const connectMeta = async () => {
    const res = await fetch("/api/meta/connect", {
      credentials: "include",
    });

    const data = await res.json();
    if (data?.redirect_url) {
      window.location.href = data.redirect_url;
    }
  };

  // -----------------------------------
  // SYNC CAMPAIGNS
  // -----------------------------------
  const syncCampaigns = async () => {
    await fetch("/api/campaigns/sync", {
      method: "POST",
      credentials: "include",
    });

    loadCampaigns();
  };

  // -----------------------------------
  // RENDER
  // -----------------------------------
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-500">
          Synced from Meta Ads Manager · Read-only
        </p>
      </div>

      {/* LOADING */}
      {loading && (
        <div className="text-gray-600">Loading campaigns…</div>
      )}

      {/* REAL ERROR ONLY */}
      {!loading && error && (
        <div className="text-red-600 font-medium">{error}</div>
      )}

      {/* META NOT CONNECTED */}
      {!loading && !error && metaConnected === false && (
        <div className="border rounded p-6 bg-white">
          <p className="font-medium mb-2">
            Connect your Meta Ads account to get started
          </p>
          <button
            onClick={connectMeta}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Connect Meta Ads
          </button>
        </div>
      )}

      {/* EMPTY STATE (CONNECTED BUT NO CAMPAIGNS) */}
      {!loading && !error && metaConnected && campaigns.length === 0 && (
        <div className="border rounded p-6 bg-white">
          <p className="font-medium mb-2">No campaigns synced yet</p>
          <p className="text-sm text-gray-500 mb-4">
            Fetch your campaigns from Meta Ads Manager.
          </p>
          <button
            onClick={syncCampaigns}
            className="px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-800"
          >
            Sync Campaigns
          </button>
        </div>
      )}

      {/* CAMPAIGN LIST */}
      {!loading && !error && campaigns.length > 0 && (
        <div className="bg-white border rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3 text-left">Objective</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">AI</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-4 py-3">{c.name}</td>
                  <td className="px-4 py-3">{c.objective ?? "—"}</td>
                  <td className="px-4 py-3">{c.status}</td>
                  <td className="px-4 py-3">
                    {c.ai_active ? "AI Active" : "AI Inactive"}
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
