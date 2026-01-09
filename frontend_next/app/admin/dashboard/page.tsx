"use client";

import { useEffect, useState } from "react";

type DashboardData = {
  users: number;
  subscriptions: {
    active: number;
    expired: number;
  };
  campaigns: {
    total: number;
    ai_active: number;
    manual: number;
  };
  last_activity: string | null;
  system_status: string;
};

export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/admin/dashboard", {
          credentials: "include",
          cache: "no-store",
        });
        const json = await res.json();
        setData(json);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-600">Loading dashboard…</div>;
  }

  if (!data) {
    return <div className="text-red-600 text-sm">Failed to load dashboard.</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Admin Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Users" value={data.users} />
        <KPI title="Active Subs" value={data.subscriptions.active} />
        <KPI title="Expired Subs" value={data.subscriptions.expired} />
        <KPI title="Campaigns" value={data.campaigns.total} />
        <KPI title="AI Active" value={data.campaigns.ai_active} />
        <KPI title="Manual" value={data.campaigns.manual} />
      </div>

      <div className="p-4 rounded border bg-white text-sm space-y-1">
        <div>
          <span className="font-medium">System Status:</span>{" "}
          {data.system_status}
        </div>
        <div>
          <span className="font-medium">Last Activity:</span>{" "}
          {data.last_activity
            ? new Date(data.last_activity).toLocaleString()
            : "—"}
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value }: { title: string; value: number }) {
  return (
    <div className="p-4 rounded border bg-white">
      <div className="text-xs text-gray-500 uppercase">{title}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
    </div>
  );
}
