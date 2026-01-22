"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/fetcher";

type UsageSummary = {
  ad_accounts: { used: number; limit: number };
  campaigns: { used: number; limit: number };
  ai_campaigns: { used: number; limit: number };
};

export default function UsageDashboard() {
  const [data, setData] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const loadUsage = async () => {
    try {
      setLoading(true);
      const res = await apiFetch("/api/usage/summary", { cache: "no-store" });
      if (res.ok) {
        setData(await res.json());
      } else {
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsage();
  }, []);

  const format = (used: number, limit: number) => {
    if (!limit || limit === 0) return `${used} / ∞`;
    return `${used} / ${limit}`;
  };

  const pct = (used: number, limit: number) => {
    if (!limit || limit === 0) return 0;
    return Math.min(Math.round((used / limit) * 100), 100);
  };

  if (loading || !data) {
    return (
      <div className="p-6 text-sm text-gray-500">
        Loading usage…
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-10">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">Usage & Limits</h1>
        <p className="text-xs text-gray-500 mt-1">
          View current quota and remaining limits.
        </p>
      </div>

      {/* GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Ad Accounts */}
        <UsageCard
          title="Ad Accounts"
          used={data.ad_accounts.used}
          limit={data.ad_accounts.limit}
          percent={pct(data.ad_accounts.used, data.ad_accounts.limit)}
          format={format}
        />

        {/* Total Campaigns */}
        <UsageCard
          title="Campaigns"
          used={data.campaigns.used}
          limit={data.campaigns.limit}
          percent={pct(data.campaigns.used, data.campaigns.limit)}
          format={format}
        />

        {/* AI Campaigns */}
        <UsageCard
          title="AI Campaigns"
          used={data.ai_campaigns.used}
          limit={data.ai_campaigns.limit}
          percent={pct(data.ai_campaigns.used, data.ai_campaigns.limit)}
          format={format}
        />
      </div>
    </div>
  );
}

/* --------------------------------------------
 * Usage Card Component
 * -------------------------------------------- */
function UsageCard({
  title,
  used,
  limit,
  percent,
  format,
}: {
  title: string;
  used: number;
  limit: number;
  percent: number;
  format: (used: number, limit: number) => string;
}) {
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm space-y-2">
      <p className="text-xs text-gray-500">{title}</p>
      <p className="text-base font-medium text-gray-900">
        {format(used, limit)}
      </p>

      <div className="w-full h-2 rounded bg-gray-200 mt-1">
        <div
          className="h-2 rounded bg-blue-600"
          style={{ width: `${percent}%` }}
        />
      </div>

      <div className="flex justify-between text-xs text-gray-400">
        <span>Used: {used}</span>
        <span>{percent}%</span>
      </div>
    </div>
  );
}
