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

  useEffect(() => {
    const loadCampaigns = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch("/api/campaigns/", {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          throw new Error(`API failed with status ${res.status}`);
        }

        const data = await res.json();

        if (Array.isArray(data)) {
          setCampaigns(data);
        } else {
          throw new Error("Invalid response format");
        }
      } catch (err) {
        console.error("Campaign fetch failed:", err);
        setError("Unable to load campaigns from Meta.");
      } finally {
        setLoading(false);
      }
    };

    loadCampaigns();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-1">Campaigns</h1>
      <p className="text-sm text-gray-500 mb-4">
        Synced from Meta Ads Manager · Read-only
      </p>

      {loading && <p className="text-gray-600">Loading campaigns…</p>}

      {!loading && error && (
        <p className="text-red-600 font-medium">{error}</p>
      )}

      {!loading && !error && campaigns.length === 0 && (
        <div className="rounded border border-dashed p-6 text-gray-600">
          <p className="font-medium">No campaigns found</p>
          <p className="text-sm mt-1">
            Connect a Meta Ad Account or sync campaigns to get started.
          </p>
        </div>
      )}

      {!loading && !error && campaigns.length > 0 && (
        <div className="space-y-2">
          {campaigns.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between rounded border p-3 bg-white"
            >
              <div>
                <p className="font-medium">{c.name}</p>
                <p className="text-xs text-gray-500">
                  {c.status} · {c.objective ?? "—"}
                </p>
              </div>

              <span
                className={`text-xs px-2 py-1 rounded ${
                  c.ai_active
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {c.ai_active ? "AI Active" : "AI Inactive"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
