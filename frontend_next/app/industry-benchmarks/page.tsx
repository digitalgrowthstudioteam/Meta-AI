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

/* ---------------------------------------
   MOCK FALLBACK (CRASH-PROOF)
--------------------------------------- */
const MOCK_DATA: InsightRow[] = [
  {
    age_range: "20–32",
    gender: "Female",
    city: "Mumbai",
    placement: "Instagram Feed",
    median_roas: 3.4,
    avg_cpl: 180,
    sample_size: 42,
    confidence: 0.82,
  },
  {
    age_range: "25–40",
    gender: "Male",
    city: "Delhi",
    placement: "Facebook Feed",
    median_roas: 2.8,
    avg_cpl: 220,
    sample_size: 31,
    confidence: 0.74,
  },
];

export default function IndustryBenchmarksPage() {
  const [category, setCategory] = useState("");
  const [window, setWindow] = useState("90d");
  const [data, setData] = useState<InsightRow[]>(MOCK_DATA);
  const [loading, setLoading] = useState(false);
  const [usingMock, setUsingMock] = useState(true);

  const fetchInsights = async () => {
    if (!category) return;

    try {
      setLoading(true);

      const res = await fetch(
        `/api/ai/category-insights?category=${encodeURIComponent(
          category
        )}&window=${window}`,
        { credentials: "include" }
      );

      if (!res.ok) throw new Error("API not ready");

      const json = await res.json();

      if (Array.isArray(json.insights) && json.insights.length > 0) {
        setData(json.insights);
        setUsingMock(false);
      } else {
        setData(MOCK_DATA);
        setUsingMock(true);
      }
    } catch {
      setData(MOCK_DATA);
      setUsingMock(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
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

      {/* INFO */}
      {usingMock && (
        <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
          Showing sample benchmarks. Real data will appear automatically once
          enough high-confidence data is available.
        </div>
      )}

      {/* TABLE */}
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
                    .join(", ")}
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
    </div>
  );
}
