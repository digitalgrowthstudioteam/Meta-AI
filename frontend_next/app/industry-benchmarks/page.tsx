"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type InsightRow = {
  age_range?: string;
  gender?: string;
  city?: string;
  region?: string;
  placement?: string;
  device?: string;

  avg_roas?: number;
  median_roas?: number;
  avg_cpl?: number;

  sample_size: number;
  confidence: number;
};

type ChartRow = {
  label: string;
  roas?: number;
  cpl?: number;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function IndustryBenchmarksPage() {
  const [category, setCategory] = useState("");
  const [window, setWindow] = useState("90d");

  /* Filters */
  const [minConfidence, setMinConfidence] = useState(0.6);
  const [placementFilter, setPlacementFilter] = useState("");
  const [deviceFilter, setDeviceFilter] = useState("");
  const [genderFilter, setGenderFilter] = useState("");

  const [data, setData] = useState<InsightRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ----------------------------------
   * FETCH INSIGHTS
   * ---------------------------------- */
  const fetchInsights = async () => {
    if (!category) return;

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        category,
        window,
      });

      const res = await fetch(
        `/api/ai/category-insights?${params.toString()}`,
        { credentials: "include" }
      );

      if (!res.ok) {
        throw new Error("Unable to load industry benchmarks.");
      }

      const json = await res.json();
      const rows: InsightRow[] = Array.isArray(json.insights)
        ? json.insights
        : [];

      /* Client-side refinement (safe) */
      const filtered = rows.filter((r) => {
        if (r.confidence < minConfidence) return false;
        if (placementFilter && r.placement !== placementFilter) return false;
        if (deviceFilter && r.device !== deviceFilter) return false;
        if (genderFilter && r.gender !== genderFilter) return false;
        return true;
      });

      setData(filtered);
    } catch (err: any) {
      setData([]);
      setError(err.message || "Unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (category) fetchInsights();
  }, [window, minConfidence, placementFilter, deviceFilter, genderFilter]);

  /* ----------------------------------
   * CHART DATA
   * ---------------------------------- */
  const chartData: ChartRow[] = data.map((r) => ({
    label:
      [r.age_range, r.gender, r.placement, r.device]
        .filter(Boolean)
        .join(" · ") || "Segment",
    roas: r.median_roas ?? r.avg_roas,
    cpl: r.avg_cpl,
  }));

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Industry Benchmarks</h1>
        <p className="text-sm text-gray-500">
          Aggregated, anonymized performance benchmarks across similar businesses
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-6 gap-3 text-sm">
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Business category (e.g. Skin Care)"
          className="border rounded px-2 py-1"
        />

        <select
          value={window}
          onChange={(e) => setWindow(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="30d">30 Days</option>
          <option value="90d">90 Days</option>
          <option value="lifetime">Lifetime</option>
        </select>

        <select
          value={placementFilter}
          onChange={(e) => setPlacementFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Placements</option>
          <option value="feed">Feed</option>
          <option value="reels">Reels</option>
          <option value="stories">Stories</option>
        </select>

        <select
          value={deviceFilter}
          onChange={(e) => setDeviceFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Devices</option>
          <option value="mobile">Mobile</option>
          <option value="desktop">Desktop</option>
        </select>

        <select
          value={genderFilter}
          onChange={(e) => setGenderFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Genders</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>

        <select
          value={minConfidence}
          onChange={(e) => setMinConfidence(Number(e.target.value))}
          className="border rounded px-2 py-1"
        >
          <option value={0.5}>Confidence ≥ 50%</option>
          <option value={0.6}>Confidence ≥ 60%</option>
          <option value={0.7}>Confidence ≥ 70%</option>
          <option value={0.8}>Confidence ≥ 80%</option>
        </select>
      </div>

      <button
        onClick={fetchInsights}
        disabled={!category || loading}
        className="btn-primary"
      >
        {loading ? "Loading…" : "Load Benchmarks"}
      </button>

      {/* ERROR */}
      {error && (
        <div className="text-sm text-red-600 font-medium">{error}</div>
      )}

      {/* EMPTY */}
      {!loading && !error && category && data.length === 0 && (
        <div className="surface p-6 text-sm text-gray-600">
          No high-confidence benchmarks available for this category yet.
        </div>
      )}

      {/* CHART */}
      {data.length > 0 && (
        <div className="surface p-4">
          <h2 className="font-medium mb-3">Performance Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="label" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="roas" name="ROAS" />
                <Bar dataKey="cpl" name="CPL" />
              </BarChart>
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
                <th className="px-3 py-2 text-left">Audience</th>
                <th className="px-3 py-2">Placement</th>
                <th className="px-3 py-2">ROAS</th>
                <th className="px-3 py-2">CPL</th>
                <th className="px-3 py-2">Campaigns</th>
                <th className="px-3 py-2">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-3 py-2">
                    {[row.age_range, row.gender, row.city]
                      .filter(Boolean)
                      .join(", ") || "—"}
                  </td>
                  <td className="px-3 py-2">
                    {row.placement || row.device || "—"}
                  </td>
                  <td className="px-3 py-2">
                    {row.median_roas ?? row.avg_roas ?? "—"}
                  </td>
                  <td className="px-3 py-2">
                    {row.avg_cpl ?? "—"}
                  </td>
                  <td className="px-3 py-2">
                    {row.sample_size}
                  </td>
                  <td className="px-3 py-2">
                    {Math.round(row.confidence * 100)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="text-xs text-gray-400">
        Benchmarks are anonymized, aggregated, and confidence-weighted.
      </div>
    </div>
  );
}
