"use client";

import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

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

type TimeRange = "7d" | "14d" | "30d" | "90d";

type TrendPoint = {
  date: string;
  value: number;
};

export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<TimeRange>("7d");

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

  // Empty-safe mock series until backend series is wired (UI COMPLETE)
  const series = useMemo<TrendPoint[]>(() => {
    const days =
      range === "7d" ? 7 : range === "14d" ? 14 : range === "30d" ? 30 : 90;

    return Array.from({ length: days }).map((_, i) => ({
      date: `D-${days - i}`,
      value: 0,
    }));
  }, [range]);

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
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">
          Admin Dashboard
        </h1>

        <select
          value={range}
          onChange={(e) => setRange(e.target.value as TimeRange)}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="7d">Last 7 days</option>
          <option value="14d">Last 14 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Users" value={data.users} />
        <KPI title="Active Subs" value={data.subscriptions.active} />
        <KPI title="Expired Subs" value={data.subscriptions.expired} />
        <KPI title="Total Campaigns" value={data.campaigns.total} />
        <KPI title="AI Active Campaigns" value={data.campaigns.ai_active} />
        <KPI title="Manual Campaigns" value={data.campaigns.manual} />
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="New Users / Day" data={series} />
        <ChartCard title="Revenue / Day" data={series} />
        <ChartCard title="AI Actions / Day" data={series} />
        <ChartCard title="Meta API Errors / Day" data={series} />
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

function ChartCard({
  title,
  data,
}: {
  title: string;
  data: { date: string; value: number }[];
}) {
  const isEmpty = data.every((d) => d.value === 0);

  return (
    <div className="p-4 rounded-lg border bg-white shadow-sm">
      <div className="text-sm font-medium text-gray-700 mb-2">{title}</div>

      {isEmpty ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-400 border rounded bg-gray-50">
          No data yet
        </div>
      ) : (
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
