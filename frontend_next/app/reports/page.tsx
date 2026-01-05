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

type AdAccount = {
  id: string;
  name: string;
  is_selected: boolean;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function ReportsPage() {
  /* Filters */
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [objective, setObjective] = useState("");
  const [campaignId, setCampaignId] = useState("");
  const [selectedAdAccount, setSelectedAdAccount] = useState("");

  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [data, setData] = useState<ReportSummary[]>([]);

  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD AD ACCOUNTS
   * ---------------------------------- */
  const loadAdAccounts = async () => {
    try {
      const res = await fetch("/api/meta/adaccounts", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const json = await res.json();
      setAdAccounts(json ?? []);
      setMetaConnected(true);

      const selected = json?.find((a: AdAccount) => a.is_selected);
      if (selected) setSelectedAdAccount(selected.id);
    } catch {
      setMetaConnected(false);
    }
  };

  /* ----------------------------------
   * LOAD CAMPAIGNS
   * ---------------------------------- */
  const loadCampaigns = async () => {
    if (!selectedAdAccount) {
      setCampaigns([]);
      return;
    }

    const res = await fetch(
      `/api/campaigns?ad_account_id=${selectedAdAccount}`,
      { credentials: "include", cache: "no-store" }
    );

    if (!res.ok) return;

    const json = await res.json();
    setCampaigns(Array.isArray(json) ? json : []);
  };

  /* ----------------------------------
   * LOAD REPORT
   * ---------------------------------- */
  const loadReport = async () => {
    if (!fromDate || !toDate || !selectedAdAccount) return;

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        from: fromDate,
        to: toDate,
        ad_account_id: selectedAdAccount,
      });

      if (campaignId) params.append("campaign_id", campaignId);
      if (objective) params.append("objective", objective);

      const res = await fetch(
        `/api/reports/performance?${params.toString()}`,
        { credentials: "include", cache: "no-store" }
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
    loadAdAccounts();
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [selectedAdAccount]);

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
  if (metaConnected === false) {
    return (
      <div className="surface p-6">
        <h2 className="font-medium mb-1">Meta account not connected</h2>
        <p className="text-sm text-gray-600">
          Connect Meta Ads to generate performance reports.
        </p>
      </div>
    );
  }

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Reports</h1>
        <p className="text-sm text-gray-500">
          Performance summaries and trends (read-only)
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-7 gap-3 text-sm">
        <select
          value={selectedAdAccount}
          onChange={(e) => setSelectedAdAccount(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">Select Ad Account</option>
          {adAccounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>

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
          disabled={!fromDate || !toDate || !selectedAdAccount || loading}
          className="btn-primary col-span-2"
        >
          {loading ? "Loading…" : "Generate Report"}
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div className="text-sm text-red-600 font-medium">
          {error}
        </div>
      )}

      {/* SUMMARY */}
      {data.length > 0 && (
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
      )}

      {/* TREND CHART */}
      {data.length > 0 && (
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
      )}

      {/* TABLE */}
      {data.length > 0 && (
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
      )}

      <div className="text-xs text-gray-400">
        Reports are generated from immutable historical data.
      </div>
    </div>
  );
}
