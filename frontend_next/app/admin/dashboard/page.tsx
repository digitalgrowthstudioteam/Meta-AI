"use client";

import { useEffect, useState } from "react";

type DashboardStats = {
  users_total: number;
  subscriptions_active: number;
  subscriptions_expired: number;
  campaigns_total: number;
  campaigns_ai_active: number;
  campaigns_manual: number;
  last_cron_run: string | null;
  system_status: "ok" | "warning";
};

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/admin/dashboard", {
          credentials: "include",
        });
        const data = await res.json();
        setStats(data);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="text-sm text-gray-500">
        Loading admin dashboard…
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-sm text-red-600">
        Failed to load admin stats.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-lg font-semibold text-gray-900">
          Admin Dashboard
        </h1>
        <p className="text-sm text-gray-500">
          System health, usage, and safety overview (read-only)
        </p>
      </div>

      {/* STATUS */}
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
            stats.system_status === "ok"
              ? "bg-green-100 text-green-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          System {stats.system_status === "ok" ? "OK" : "Attention"}
        </span>
        {stats.last_cron_run && (
          <span className="text-xs text-gray-500">
            Last cron: {new Date(stats.last_cron_run).toLocaleString()}
          </span>
        )}
      </div>

      {/* METRICS GRID */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Metric label="Total Users" value={stats.users_total} />
        <Metric
          label="Active Subscriptions"
          value={stats.subscriptions_active}
        />
        <Metric
          label="Expired Subscriptions"
          value={stats.subscriptions_expired}
        />
        <Metric label="Total Campaigns" value={stats.campaigns_total} />
        <Metric
          label="AI Active Campaigns"
          value={stats.campaigns_ai_active}
        />
        <Metric
          label="Manual Campaigns"
          value={stats.campaigns_manual}
        />
      </div>

      {/* FOOTER NOTE */}
      <div className="text-xs text-gray-400">
        All values are read-only. Every admin mutation is audited.
      </div>
    </div>
  );
}

/* ---------------------------------- */
/* COMPONENTS */
/* ---------------------------------- */

function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="bg-white border rounded-lg px-4 py-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-gray-900">
        {value}
      </div>
    </div>
  );
}
