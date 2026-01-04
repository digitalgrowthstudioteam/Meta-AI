"use client";

import { useEffect, useState } from "react";

type MetricEvidence = {
  metric: string;
  window: string;
  value: number;
  baseline?: number;
  delta_pct?: number;
};

type BreakdownEvidence = {
  dimension: string;
  key: string;
  metrics: MetricEvidence[];
};

type ConfidenceScore = {
  score: number;
  reason: string;
};

type AIAction = {
  campaign_id: string;
  action_type: string;
  summary: string;
  metrics?: MetricEvidence[];
  breakdowns?: BreakdownEvidence[];
  confidence: ConfidenceScore;
  generated_at: string;
};

type AIActionSet = {
  campaign_id: string;
  actions: AIAction[];
  evaluated_at: string;
};

export default function AISuggestionsPage() {
  const [data, setData] = useState<AIActionSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch("/ai/actions", {
        credentials: "include",
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const json = await res.json();
      setData(Array.isArray(json) ? json : []);
    } catch (err) {
      console.error("AI Suggestions fetch failed:", err);
      setError("Unable to load AI suggestions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuggestions();
  }, []);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">AI Suggestions</h1>
        <p className="text-sm text-gray-500">
          Live, explainable AI recommendations (read-only)
        </p>
      </div>

      {/* LOADING */}
      {loading && <div className="text-gray-600">Analyzing campaigns…</div>}

      {/* ERROR */}
      {!loading && error && (
        <div className="text-red-600 font-medium">{error}</div>
      )}

      {/* EMPTY */}
      {!loading && !error && data.length === 0 && (
        <div className="empty-state">
          <p className="empty-state-title mb-1">No AI suggestions yet</p>
          <p className="empty-state-sub">
            AI will suggest actions once patterns are detected.
          </p>
        </div>
      )}

      {/* RESULTS */}
      {!loading &&
        !error &&
        data.map((set) => (
          <div
            key={set.campaign_id}
            className="surface p-4 space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Campaign ID: {set.campaign_id}
              </div>
              <div className="text-xs text-gray-400">
                Evaluated:{" "}
                {new Date(set.evaluated_at).toLocaleString()}
              </div>
            </div>

            {set.actions.map((action, idx) => (
              <div
                key={idx}
                className="border rounded-lg p-4 space-y-3 bg-white"
              >
                {/* ACTION HEADER */}
                <div className="flex items-center justify-between">
                  <div className="font-medium">
                    {action.action_type.replaceAll("_", " ")}
                  </div>
                  <div className="text-xs font-medium px-2 py-1 rounded bg-gray-100">
                    Confidence:{" "}
                    {Math.round(action.confidence.score * 100)}%
                  </div>
                </div>

                {/* SUMMARY */}
                <p className="text-sm text-gray-700">
                  {action.summary}
                </p>

                {/* METRIC EVIDENCE */}
                {action.metrics && action.metrics.length > 0 && (
                  <div>
                    <div className="text-xs font-medium mb-1 text-gray-700">
                      Metric Evidence
                    </div>
                    <table className="w-full text-xs border">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="border px-2 py-1 text-left">
                            Metric
                          </th>
                          <th className="border px-2 py-1">Window</th>
                          <th className="border px-2 py-1">Value</th>
                          <th className="border px-2 py-1">Baseline</th>
                          <th className="border px-2 py-1">Δ%</th>
                        </tr>
                      </thead>
                      <tbody>
                        {action.metrics.map((m, i) => (
                          <tr key={i}>
                            <td className="border px-2 py-1">
                              {m.metric.toUpperCase()}
                            </td>
                            <td className="border px-2 py-1">
                              {m.window}
                            </td>
                            <td className="border px-2 py-1">
                              {m.value}
                            </td>
                            <td className="border px-2 py-1">
                              {m.baseline ?? "—"}
                            </td>
                            <td className="border px-2 py-1">
                              {m.delta_pct !== undefined
                                ? `${m.delta_pct}%`
                                : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* BREAKDOWN EVIDENCE */}
                {action.breakdowns && action.breakdowns.length > 0 && (
                  <div>
                    <div className="text-xs font-medium mb-1 text-gray-700">
                      Breakdown Evidence
                    </div>
                    <div className="space-y-2">
                      {action.breakdowns.map((b, i) => (
                        <div
                          key={i}
                          className="border rounded p-2 text-xs bg-gray-50"
                        >
                          <div className="font-medium mb-1">
                            {b.dimension}: {b.key}
                          </div>
                          <ul className="list-disc pl-4">
                            {b.metrics.map((m, j) => (
                              <li key={j}>
                                {m.metric.toUpperCase()} ({m.window}):{" "}
                                {m.value}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* CONFIDENCE REASON */}
                <div className="text-xs text-gray-500">
                  {action.confidence.reason}
                </div>
              </div>
            ))}
          </div>
        ))}
    </div>
  );
}
