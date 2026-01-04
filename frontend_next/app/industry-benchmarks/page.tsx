"use client";

import { useEffect, useState } from "react";

type InsightRow = {
  age_range?: string;
  gender?: string;
  city?: string;
  placement?: string;
  device?: string;
  avg_roas?: number;
  median_roas?: number;
  avg_cpl?: number;
  sample_size: number;
  confidence: number;
};

export default function IndustryBenchmarksPage() {
  const [category, setCategory] = useState("");
  const [window, setWindow] = useState("90d");
  const [data, setData] = useState<InsightRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = async () => {
    if (!category) return;

    try {
      setLoading(true);
      setError(null);

      const res = await fetch(
        `/api/ai/category-insights?category=${encodeURIComponent(
          category
        )}&window=${window}`,
        { credentials: "include" }
      );

      if (res.status === 401) {
        throw new Error("Please log in to view benchmarks.");
      }

      if (!res.ok) {
        throw new Error("Unable to load industry benchmarks.");
      }

      const json = await res.json();
      setData(Array.isArray(json.insights) ? json.insights : []);
    } catch (err: any) {
      setData([]);
      setError(err.message || "Unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (category) {
      fetchInsights();
    }
  }, [window]);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Industry Benchmarks</h1>
        <p className="text-sm text-gray-500">
          Aggregated, anonymized performance insights across the platform
        </p>
      </div>

      {/* CONTROLS */}
      <div className="flex gap-4 items-end">
        <div>
          <label className="text-xs text-gray-500">Business Category</label>
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g. Skin Care"
            className="input mt-1"
          />
        </div>

        <div>
          <label className="text-xs text-gray-500">Time Window</label>
          <select
            value={window}
            onChange={(e) => setWindow(e.target.value)}
            className="input mt-1"
          >
            <option value="30d">30 Days</option>
            <option value="90d">90 Days</option>
            <option value="lifetime">Lifetime</option>
          </select>
        </div>

        <button
          onClick={fetchInsights}
          className="btn-primary"
          disabled={!category || loading}
        >
          {loading ? "Loading…" : "Load Insights"}
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div className="text-sm text-red-600 font-medium">
          {error}
        </div>
      )}

      {/* LOADING */}
      {loading && (
        <div className="text-sm text-gray-600">
          Loading industry benchmarks…
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && !error && category && data.length === 0 && (
        <div className="surface text-sm text-gray-600">
          <div className="font-medium mb-1">
            No benchmarks available
          </div>
          <div>
            There is not enough high-confidence data for this category yet.
            As more campaigns run, benchmarks will appear automatically.
          </div>
        </div>
      )}

      {/* TABLE */}
      {!loading && !error && data.length > 0 && (
        <div className="surface overflow-x-auto">
          <table className="w-full text-sm border">
            <thead className="bg-gray-50">
              <tr>
                <th className="border px-2 py-1">Audience</th>
                <th className="border px-2 py-1">Placement</th>
                <th className="border px-2 py-1">ROAS</th>
                <th className="border px-2 py-1">CPL</th>
                <th className="border px-2 py-1">Campaigns</th>
                <th className="border px-2 py-1">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i}>
                  <td className="border px-2 py-1">
                    {[row.age_range, row.gender, row.city]
                      .filter(Boolean)
                      .join(", ") || "—"}
                  </td>
                  <td className="border px-2 py-1">
                    {row.placement || row.device || "—"}
                  </td>
                  <td className="border px-2 py-1">
                    {row.median_roas ?? row.avg_roas ?? "—"}
                  </td>
                  <td className="border px-2 py-1">
                    {row.avg_cpl ?? "—"}
                  </td>
                  <td className="border px-2 py-1">
                    {row.sample_size}
                  </td>
                  <td className="border px-2 py-1">
                    {Math.round(row.confidence * 100)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
