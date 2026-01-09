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
    return (
      <div className="text-sm text-gray-600 p-4 bg-gray-50 rounded border">
        Loading dashboard…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-red-600 text-sm p-4 bg-red-50 rounded border border-red-200">
        Failed to load dashboard.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Users" value={data.users} />
        <KPI title="Active Subs" value={data.subscriptions.active} />
        <KPI title="Expired Subs" value={data.subscriptions.expired} />
        <KPI title="Total Campaigns" value={data.campaigns.total} />
        <KPI title="AI Active Campaigns" value={data.campaigns.ai_active} />
        <KPI title="Manual Campaigns" value={data.campaigns.manual} />
      </div>

      {/* System Status */}
      <div className="p-4 rounded-lg border bg-white shadow-sm text-sm space-y-2">
        <div className="flex justify-between">
          <span className="font-medium text-gray-600">System Status:</span>
          <span
            className={`font-semibold ${
              data.system_status === "ok"
                ? "text-green-600"
                : "text-red-600"
            }`}
          >
            {data.system_status}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="font-medium text-gray-600">Last Activity:</span>
          <span>
            {data.last_activity
              ? new Date(data.last_activity).toLocaleString()
              : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value }: { title: string; value: number }) {
  return (
    <div className="p-4 rounded-lg border bg-white shadow-sm">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {title}
      </div>
      <div className="text-2xl font-semibold text-gray-900 mt-1">
        {value}
      </div>
    </div>
  );
}
