"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

/* ---------------------------------
 * TYPES
 * --------------------------------- */
type AudienceRow = {
  campaign_id: string;
  campaign_name: string;
  age_group?: string;
  gender?: string;
  platform?: string;
  placement?: string;
  region?: string;
  impressions: number;
  clicks: number;
  spend: number;
  conversions: number;
  conversion_value: number;
  roas?: number | null;
  cpa?: number | null;
  suggestion?: "keep" | "expand" | "reduce";
  reason?: string;
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

/* ---------------------------------
 * PAGE
 * --------------------------------- */
export default function AudienceInsightsPage() {
  const [rows, setRows] = useState<AudienceRow[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);

  const [selectedAdAccount, setSelectedAdAccount] = useState("");
  const [campaignId, setCampaignId] = useState("");
  const [dimension, setDimension] = useState("age_gender");
  const [objective, setObjective] = useState("");

  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ---------------------------------
   * LOAD AD ACCOUNTS
   * --------------------------------- */
  const loadAdAccounts = async () => {
    try {
      const res = await fetch("/api/meta/adaccounts", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const data = await res.json();
      setAdAccounts(data ?? []);
      setMetaConnected(true);

      const selected = data?.find((a: AdAccount) => a.is_selected);
      if (selected) setSelectedAdAccount(selected.id);
    } catch {
      setMetaConnected(false);
    }
  };

  /* ---------------------------------
   * LOAD CAMPAIGNS
   * --------------------------------- */
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

    const data = await res.json();
    setCampaigns(Array.isArray(data) ? data : []);
  };

  /* ---------------------------------
   * LOAD AUDIENCE INSIGHTS
   * --------------------------------- */
  const loadInsights = async () => {
    if (!selectedAdAccount) {
      setRows([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        ad_account_id: selectedAdAccount,
      });

      if (campaignId) params.append("campaign_id", campaignId);
      if (dimension) params.append("dimension", dimension);
      if (objective) params.append("objective", objective);

      const res = await fetch(
        `/api/ai/audience-insights?${params.toString()}`,
        { credentials: "include", cache: "no-store" }
      );

      if (!res.ok) throw new Error();

      const json = await res.json();
      setRows(Array.isArray(json) ? json : []);
    } catch {
      setError("Unable to load audience insights.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadAdAccounts();
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    loadCampaigns();
    loadInsights();
  }, [selectedAdAccount, campaignId, dimension, objective]);

  /* ---------------------------------
   * STATES
   * --------------------------------- */
  if (loading) return <div>Loading audience insights…</div>;

  if (metaConnected === false) {
    return (
      <div className="surface p-6">
        <h2 className="font-medium mb-1">Meta account not connected</h2>
        <p className="text-sm text-gray-600">
          Connect Meta Ads to unlock audience insights.
        </p>
      </div>
    );
  }

  if (error) return <div className="text-red-600">{error}</div>;

  /* ---------------------------------
   * CHART DATA
   * --------------------------------- */
  const chartData = rows.map((r) => ({
    name:
      [r.age_group, r.gender, r.platform, r.placement, r.region]
        .filter(Boolean)
        .join(" · ") || "Unknown",
    spend: Number(r.spend),
    conversions: Number(r.conversions),
  }));

  /* ---------------------------------
   * RENDER
   * --------------------------------- */
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Audience Insights</h1>
        <p className="text-sm text-gray-500">
          AI-driven audience analysis (read-only)
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
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
          value={dimension}
          onChange={(e) => setDimension(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="age_gender">Age & Gender</option>
          <option value="placement">Placement</option>
          <option value="platform">Platform</option>
          <option value="region">Region</option>
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
      </div>

      {/* CHART */}
      {chartData.length > 0 && (
        <div className="surface p-4">
          <h2 className="font-medium mb-3">Performance Overview</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="spend" />
                <Bar dataKey="conversions" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* TABLE */}
      {rows.length === 0 && (
        <div className="surface p-6 text-sm text-gray-600">
          No audience insights available yet.
        </div>
      )}

      {rows.length > 0 && (
        <div className="surface overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="px-3 py-2 text-left">Segment</th>
                <th className="px-3 py-2 text-right">Spend</th>
                <th className="px-3 py-2 text-right">Conversions</th>
                <th className="px-3 py-2 text-right">ROAS</th>
                <th className="px-3 py-2 text-left">AI Suggestion</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-3 py-2">
                    {[r.age_group, r.gender, r.platform, r.placement, r.region]
                      .filter(Boolean)
                      .join(" · ")}
                  </td>
                  <td className="px-3 py-2 text-right">
                    ₹{Number(r.spend).toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {r.conversions}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {r.roas ? r.roas.toFixed(2) : "—"}
                  </td>
                  <td className="px-3 py-2">
                    {r.suggestion ? (
                      <span className="font-medium">
                        {r.suggestion.toUpperCase()} — {r.reason}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="text-xs text-gray-400">
        Audience suggestions are advisory only and never auto-applied.
      </div>
    </div>
  );
}
