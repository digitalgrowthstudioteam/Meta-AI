"use client";

import { useEffect, useState } from "react";

type Campaign = {
  id: string;
  name: string;
  status: string;
  objective?: string;
  ai_active?: boolean;

  // Phase 9.2 — category visibility
  category?: string | null;
  category_confidence?: number | null;
  category_source?: string | null;
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

      if (res.status === 409) {
        setCampaigns([]);
        setMetaConnected(false);
        return;
      }

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      setCampaigns(Array.isArray(data) ? data : []);
      setMetaConnected(true);
    } catch (err) {
      console.error("Campaign load failed", err);
      setError("Unable to load campaigns.");
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
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-500">
          Synced from Meta Ads Manager · Read-only
        </p>
      </div>

      {loading && <div className="text-gray-600">Loading campaigns…</div>}

      {!loading && error && (
        <div className="text-red-600 font-medium">{error}</div>
      )}

      {!loading && !error && metaConnected === false && (
        <div className="empty-state">
          <p className="empty-state-title mb-2">
            Connect your Meta Ads account
          </p>
          <p className="empty-state-sub mb-4">
            Meta connection is required to fetch campaigns.
          </p>
          <button onClick={connectMeta} className="btn-primary">
            Connect Meta Ads
          </button>
        </div>
      )}

      {!loading && !error && metaConnected && campaigns.length === 0 && (
        <div className="empty-state">
          <p className="empty-state-title mb-2">
            No campaigns synced yet
          </p>
          <p className="empty-state-sub mb-4">
            Fetch your campaigns from Meta Ads Manager.
          </p>
          <button onClick={syncCampaigns} className="btn-secondary">
            Sync Campaigns
          </button>
        </div>
      )}

      {!loading && !error && campaigns.length > 0 && (
        <div className="surface overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3 text-left">Objective</th>
                <th className="px-4 py-3 text-left">Category</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">AI</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3">{c.objective ?? "—"}</td>

                  {/* CATEGORY VISIBILITY */}
                  <td className="px-4 py-3">
                    {c.category ? (
                      <div className="space-y-1">
                        <div className="font-medium">{c.category}</div>
                        <div className="text-xs text-gray-500">
                          {c.category_source} ·{" "}
                          {c.category_confidence
                            ? `${Math.round(
                                c.category_confidence * 100
                              )}%`
                            : "—"}
                        </div>
                      </div>
                    ) : (
                      <span className="text-gray-400">Uncategorized</span>
                    )}
                  </td>

                  <td className="px-4 py-3">{c.status}</td>
                  <td className="px-4 py-3">
                    {c.ai_active ? (
                      <span className="text-green-700 font-medium">
                        AI Active
                      </span>
                    ) : (
                      <span className="text-gray-500">
                        AI Inactive
                      </span>
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
