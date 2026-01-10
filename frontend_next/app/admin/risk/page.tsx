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

type RiskEvent = {
  id: string;
  source: string;
  action: string;
  target_id: string | null;
  reason: string | null;
  timestamp: string;
};

export default function AdminRiskPage() {
  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/admin/risk", { cache: "no-store" }).then((r) => r.json()),
      fetch("/api/admin/risk/timeline", { cache: "no-store" }).then((r) =>
        r.json()
      ),
    ])
      .then(([summaryData, timelineData]) => {
        setSummary(summaryData);
        setEvents(timelineData || []);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">Loading risk data…</div>;
  }

  if (!summary) {
    return (
      <div className="text-sm text-red-600">
        Failed to load risk dashboard
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-lg font-semibold">Risk & Safety</h1>

      {/* =========================
          SUMMARY
         ========================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="User Risk">
          <Stat
            label="Failed payments (7d)"
            value={summary.users.failed_payments_7d}
          />
          <Stat
            label="Expired subscriptions"
            value={summary.users.expired_subscriptions}
          />
        </Card>

        <Card title="Campaign Risk">
          <Stat
            label="AI active but locked"
            value={summary.campaigns.ai_active_but_locked}
          />
          <Stat
            label="AI toggles (7d)"
            value={summary.campaigns.ai_toggle_events_7d}
          />
        </Card>

        <Card title="System Risk">
          <Stat
            label="Stale Meta sync campaigns"
            value={summary.system.stale_meta_sync_campaigns}
          />
        </Card>
      </div>

      {/* =========================
          TIMELINE
         ========================= */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b">
          <h2 className="text-sm font-medium text-gray-900">
            Risk Timeline
          </h2>
          <p className="text-xs text-gray-500">
            Correlated admin, AI, billing & system events
          </p>
        </div>

        {events.length === 0 ? (
          <div className="p-6 text-sm text-gray-500">
            No risk events detected.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr className="text-left text-xs text-gray-500 uppercase">
                <th className="px-4 py-2">Time</th>
                <th className="px-4 py-2">Source</th>
                <th className="px-4 py-2">Action</th>
                <th className="px-4 py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr
                  key={e.id}
                  className="border-b last:border-0 hover:bg-gray-50"
                >
                  <td className="px-4 py-2 text-gray-600">
                    {new Date(e.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    <Badge source={e.source} />
                  </td>
                  <td className="px-4 py-2">{e.action}</td>
                  <td className="px-4 py-2 text-gray-600">
                    {e.reason || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="text-[10px] text-gray-400">
        Generated at:{" "}
        {new Date(summary.generated_at).toLocaleString()}
      </div>
    </div>
  );
}

/* =========================
   SMALL UI HELPERS
   ========================= */

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded border bg-white p-4 space-y-2">
      <div className="font-medium text-sm">{title}</div>
      {children}
    </div>
  );
}

function Stat({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="text-xs text-gray-600">
      {label}: <span className="font-semibold">{value}</span>
    </div>
  );
}

function Badge({ source }: { source: string }) {
  const colors: Record<string, string> = {
    ADMIN: "bg-red-100 text-red-700",
    AI: "bg-indigo-100 text-indigo-700",
    SYSTEM: "bg-gray-100 text-gray-700",
    BILLING: "bg-amber-100 text-amber-700",
    USER: "bg-green-100 text-green-700",
  };

  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] font-medium ${
        colors[source] || "bg-gray-100 text-gray-700"
      }`}
    >
      {source}
    </span>
  );
}
