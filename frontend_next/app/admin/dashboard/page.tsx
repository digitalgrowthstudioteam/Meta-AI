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
import { apiFetch } from "../../lib/fetcher";

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
        // ✅ FIX: correct backend admin route
        const res = await apiFetch("/admin/dashboard", {
          cache: "no-store",
        });

        if (!res.ok) {
          setData(null);
          return;
        }

        const json = await res.json();
        setData(json);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

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
      <div className="flex items-center justify-center h-64 text-sm text-gray-500">
        Loading system status...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 border border-red-200">
        Failed to load dashboard data. Please check the backend connection.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
          Admin Dashboard
        </h1>

        <select
          value={range}
          onChange={(e) => setRange(e.target.value as TimeRange)}
          className="block w-full sm:w-auto rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
        >
          <option value="7d">Last 7 days</option>
          <option value="14d">Last 14 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KPI title="Total Users" value={data.users} />
        <KPI title="Active Subs" value={data.subscriptions.active} color="text-green-600" />
        <KPI title="Expired Subs" value={data.subscriptions.expired} color="text-gray-500" />
        <KPI title="Total Campaigns" value={data.campaigns.total} />
        <KPI title="AI Active" value={data.campaigns.ai_active} color="text-indigo-600" />
        <KPI title="Manual Mode" value={data.campaigns.manual} color="text-orange-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="New Users / Day" data={series} />
        <ChartCard title="Revenue Trends" data={series} />
        <ChartCard title="AI Actions Executed" data={series} />
        <ChartCard title="API Error Rates" data={series} />
      </div>

      <div className="rounded-lg bg-white shadow-sm ring-1 ring-gray-900/5 p-4 flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="text-gray-500">System Status:</span>
          <span
            className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
              data.system_status === "ok"
                ? "bg-green-50 text-green-700 ring-green-600/20"
                : "bg-red-50 text-red-700 ring-red-600/20"
            } uppercase`}
          >
            {data.system_status}
          </span>
        </div>

        <div className="text-gray-500">
          Last Activity:{" "}
          <span className="font-medium text-gray-900">
            {data.last_activity
              ? new Date(data.last_activity).toLocaleString()
              : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value, color = "text-gray-900" }: { title: string; value: number; color?: string }) {
  return (
    <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm ring-1 ring-gray-900/5 sm:p-6">
      <dt className="truncate text-sm font-medium text-gray-500">{title}</dt>
      <dd className={`mt-1 text-3xl font-semibold tracking-tight ${color}`}>{value}</dd>
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
    <div className="rounded-lg bg-white shadow-sm ring-1 ring-gray-900/5 p-6">
      <h3 className="text-base font-semibold leading-6 text-gray-900 mb-4">
        {title}
      </h3>

      {isEmpty ? (
        <div className="h-64 flex items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50">
          <div className="text-center text-sm text-gray-500">
            No Data Available
          </div>
        </div>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#4F46E5" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
