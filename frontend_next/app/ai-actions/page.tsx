"use client";

import { useEffect, useState } from "react";

type CampaignAI = {
  id: string;
  name: string;
  status: string;
  objective?: string;
  ai_active: boolean;
};

export default function AIActionsPage() {
  const [campaigns, setCampaigns] = useState<CampaignAI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);

  // -----------------------------------
  // LOAD AI ACTION CAMPAIGNS
  // -----------------------------------
  const loadAICampaigns = async () => {
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
      console.error("AI Actions load failed:", err);
      setError("Unable to reach AI campaign service.");
      setMetaConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAICampaigns();
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
  // TOGGLE AI (SAFE)
  // -----------------------------------
  const toggleAI = async (campaignId: string, enable: boolean) => {
    await fetch(`/api/campaigns/${campaignId}/ai-toggle`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ enable }),
    });

    loadAICampaigns();
  };

  // -----------------------------------
  // RENDER
  // -----------------------------------
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">AI Actions</h1>
        <p className="text-sm text-gray-500">
          Control which campaigns AI can optimize
        </p>
      </div>

      {/* LOADING */}
      {loading && <div className="text-gray-600">Loading AI actions…</div>}

      {/* REAL ERROR ONLY */}
      {!loading && error && (
        <div className="text-red-600 font-medium">{error}</div>
      )}

      {/* META NOT CONNECTED */}
      {!loading && !error && metaConnected === false && (
        <div className="border rounded p-6 bg-white">
          <p className="font-medium mb-2">
            Connect your Meta Ads account to enable AI
          </p>
          <button
            onClick={connectMeta}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Connect Meta Ads
          </button>
        </div>
      )}

      {/* EMPTY STATE (CONNECTED, NO CAMPAIGNS) */}
      {!loading && !error && metaConnected && campaigns.length === 0 && (
        <div className="border rounded p-6 bg-white">
          <p className="font-medium mb-1">No campaigns available</p>
          <p className="text-sm text-gray-500">
            Sync campaigns from Meta Ads Manager first.
          </p>
        </div>
      )}

      {/* AI ACTION TABLE */}
      {!loading && !error && campaigns.length > 0 && (
        <div className="bg-white border rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3 text-left">Objective</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">AI Control</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3">{c.objective ?? "—"}</td>
                  <td className="px-4 py-3">{c.status}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleAI(c.id, !c.ai_active)}
                      className={`px-3 py-1 rounded text-xs font-medium ${
                        c.ai_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {c.ai_active ? "AI Active" : "AI Inactive"}
                    </button>
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
