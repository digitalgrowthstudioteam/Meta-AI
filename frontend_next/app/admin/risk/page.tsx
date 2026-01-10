"use client";

import { useEffect, useState } from "react";

type RiskSummary = {
  users: {
    failed_payments_7d: number;
    expired_subscriptions: number;
  };
  campaigns: {
    ai_active_but_locked: number;
    ai_toggle_events_7d: number;
  };
  system: {
    stale_meta_sync_campaigns: number;
  };
  generated_at: string;
};

export default function AdminRiskPage() {
  const [data, setData] = useState<RiskSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/admin/risk", { cache: "no-store" })
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">Loading risk signals…</div>;
  }

  if (!data) {
    return <div className="text-sm text-red-600">Failed to load risk data</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Risk & Safety</h1>

      {/* USER RISK */}
      <div className="rounded border bg-white p-4 space-y-2">
        <div className="font-medium text-sm">User Risk</div>
        <div className="text-xs text-gray-600">
          Failed payments (7d):{" "}
          <span className="font-semibold">
            {data.users.failed_payments_7d}
          </span>
        </div>
        <div className="text-xs text-gray-600">
          Expired subscriptions:{" "}
          <span className="font-semibold">
            {data.users.expired_subscriptions}
          </span>
        </div>
      </div>

      {/* CAMPAIGN RISK */}
      <div className="rounded border bg-white p-4 space-y-2">
        <div className="font-medium text-sm">Campaign Risk</div>
        <div className="text-xs text-gray-600">
          AI active but execution locked:{" "}
          <span className="font-semibold">
            {data.campaigns.ai_active_but_locked}
          </span>
        </div>
        <div className="text-xs text-gray-600">
          AI toggle events (7d):{" "}
          <span className="font-semibold">
            {data.campaigns.ai_toggle_events_7d}
          </span>
        </div>
      </div>

      {/* SYSTEM RISK */}
      <div className="rounded border bg-white p-4 space-y-2">
        <div className="font-medium text-sm">System Risk</div>
        <div className="text-xs text-gray-600">
          Campaigns with stale Meta sync:{" "}
          <span className="font-semibold">
            {data.system.stale_meta_sync_campaigns}
          </span>
        </div>
      </div>

      <div className="text-[10px] text-gray-400">
        Generated at: {new Date(data.generated_at).toLocaleString()}
      </div>
    </div>
  );
}
