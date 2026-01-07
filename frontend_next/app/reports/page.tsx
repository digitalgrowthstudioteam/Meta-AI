"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type SessionContext = {
  user: {
    id: string;
    email: string;
    is_admin: boolean;
    is_impersonated: boolean;
  };
  ad_account: {
    id: string;
    name: string;
    meta_account_id: string;
  } | null;
};

type ReportSummary = {
  date: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  roas?: number;
  cpa?: number;
};

type Campaign = {
  id: string;
  name: string;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function ReportsPage() {
  const [session, setSession] = useState<SessionContext | null>(null);

  /* Filters */
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [objective, setObjective] = useState("");
  const [campaignId, setCampaignId] = useState("");

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [data, setData] = useState<ReportSummary[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD SESSION CONTEXT
   * ---------------------------------- */
  const loadSession = async () => {
    const res = await fetch("/api/session/context", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setSession(null);
      return;
    }

    const json = await res.json();
    setSession(json);
  };

  /* ----------------------------------
   * LOAD CAMPAIGNS (STRICT CONTEXT)
   * ---------------------------------- */
  const loadCampaigns = async () => {
    if (!session?.ad_account) {
      setCampaigns([]);
      return;
    }

    const res = await fetch("/api/campaigns", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setCampaigns([]);
      return;
    }

    const json = await res.json();
    setCampaigns(Array.isArray(json) ? json : []);
  };

  /* ----------------------------------
   * LOAD REPORT
   * ---------------------------------- */
  const loadReport = async () => {
    if (!fromDate || !toDate || !session?.ad_account) return;

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        from: fromDate,
        to: toDate,
      });

      if (campaignId) params.append("campaign_id", campaignId);
      if (objective) params.append("objective", objective);

      const res = await fetch(
        `/api/reports/performance?${params.toString()}`,
        {
          credentials: "include",
          cache: "no-store",
        }
      );

      if (!res.ok) throw new Error("Unable to load reports.");

      const json = await res.json();
      setData(Array.isArray(json.rows) ? json.rows : []);
    } catch (err: any) {
      setData([]);
      setError(err.message || "Unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [session?.ad_account?.id]);

  /* ----------------------------------
   * DERIVED METRICS
   * ---------------------------------- */
  const totals = data.reduce(
    (acc, r) => {
      acc.spend += r.spend;
      acc.conversions += r.conversions;
      acc.revenue += r.revenue;
      return acc;
    },
    { spend: 0, conversions: 0, revenue: 0 }
  );

  const avgRoas =
    totals.spend > 0 ? totals.revenue / totals.spend : null;

  /* ----------------------------------
   * STATES
   * ---------------------------------- */
  if (!session?.ad_account) {
    return (
      <div className="surface p-6">
        <h2 className="font-medium mb-1">No ad account selected</h2>
        <p className="text-sm text-gray-600">
          Connect Meta Ads and select an ad account.
        </p>
      </div>
    );
  }

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Reports</h1>
        <p className="text-sm text-gray-500">
          Active account: <strong>{session.ad_account.name}</strong>
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-6 gap-3 text-sm">
        <input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          className="border rounded px-2 py-1"
        />

        <input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          className="border rounded px-2 py-1"
        />

        <select
          value={campaignId}
          onChange={(e) => setCampaignId(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Campaigns</option>
          {campaigns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        <select
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Objectives</option>
          <option value="LEAD">Leads</option>
          <option value="SALES">Sales</option>
        </select>

        <button
          onClick={loadReport}
          disabled={!fromDate || !toDate || loading}
          className="btn-primary col-span-2"
        >
          {loading ? "Loading…" : "Generate Report"}
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-600 font-medium">
          {error}
        </div>
      )}

      {data.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="surface p-4">
              <div className="text-xs text-gray-500">Total Spend</div>
              <div className="text-lg font-semibold">
                ₹{totals.spend.toFixed(2)}
              </div>
            </div>

            <div className="surface p-4">
              <div className="text-xs text-gray-500">
                Total Conversions
              </div>
              <div className="text-lg font-semibold">
                {totals.conversions}
              </div>
            </div>

            <div className="surface p-4">
              <div className="text-xs text-gray-500">Avg ROAS</div>
              <div className="text-lg font-semibold">
                {avgRoas ? avgRoas.toFixed(2) : "—"}
              </div>
            </div>
          </div>

          <div className="surface p-4">
            <h2 className="font-medium mb-3">Performance Over Time</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line dataKey="spend" name="Spend" />
                  <Line dataKey="revenue" name="Revenue" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="surface overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Spend</th>
                  <th className="px-3 py-2">Conversions</th>
                  <th className="px-3 py-2">Revenue</th>
                  <th className="px-3 py-2">ROAS</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="px-3 py-2">{r.date}</td>
                    <td className="px-3 py-2">
                      ₹{r.spend.toFixed(2)}
                    </td>
                    <td className="px-3 py-2">
                      {r.conversions}
                    </td>
                    <td className="px-3 py-2">
                      ₹{r.revenue.toFixed(2)}
                    </td>
                    <td className="px-3 py-2">
                      {r.roas ? r.roas.toFixed(2) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div className="text-xs text-gray-400">
        Reports are generated from immutable historical data.
      </div>
    </div>
  );
}
