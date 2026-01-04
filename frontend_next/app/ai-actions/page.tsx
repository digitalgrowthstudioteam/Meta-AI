"use client";

import { useEffect, useState } from "react";

/* ----------------------------- */
/* TYPES */
/* ----------------------------- */

type CampaignAI = {
  id: string;
  name: string;
  status: string;
  objective?: string;
  ai_active: boolean;
};

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
};

type AIActionSet = {
  campaign_id: string;
  actions: AIAction[];
};

/* ----------------------------- */
/* COMPONENT */
/* ----------------------------- */

export default function AIActionsPage() {
  const [campaigns, setCampaigns] = useState<CampaignAI[]>([]);
  const [aiActions, setAiActions] = useState<AIActionSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, boolean>>({});

  /* ----------------------------- */
  /* LOAD CAMPAIGNS */
  /* ----------------------------- */
  const loadAICampaigns = async () => {
    const res = await fetch("/api/campaigns", { credentials: "include" });

    if (res.status === 409) {
      setCampaigns([]);
      setMetaConnected(false);
      return;
    }

    const data = await res.json();
    setCampaigns(Array.isArray(data) ? data : []);
    setMetaConnected(true);
  };

  /* ----------------------------- */
  /* LOAD AI ACTIONS */
  /* ----------------------------- */
  const loadAIActions = async () => {
    const res = await fetch("/api/ai/actions", {
      credentials: "include",
    });

    if (res.ok) {
      const data = await res.json();
      setAiActions(Array.isArray(data) ? data : []);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await loadAICampaigns();
        await loadAIActions();
      } catch {
        setError("Unable to load AI data.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  /* ----------------------------- */
  /* TOGGLE AI */
  /* ----------------------------- */
  const toggleAI = async (campaignId: string, enable: boolean) => {
    await fetch(`/api/campaigns/${campaignId}/ai-toggle`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable }),
    });

    await loadAICampaigns();
    await loadAIActions();
  };

  /* ----------------------------- */
  /* FEEDBACK */
  /* ----------------------------- */
  const submitFeedback = async (
    action: AIAction,
    isHelpful: boolean
  ) => {
    const key = `${action.campaign_id}_${action.action_type}_${action.summary}`;
    if (feedbackSent[key]) return;

    await fetch("/api/ai/actions/feedback", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        campaign_id: action.campaign_id,
        rule_name: action.action_type,
        action_type: action.action_type,
        is_helpful: isHelpful,
        confidence_at_time: action.confidence.score,
      }),
    });

    setFeedbackSent((prev) => ({ ...prev, [key]: true }));
  };

  /* ----------------------------- */
  /* DERIVED */
  /* ----------------------------- */
  const strategyActions = aiActions.flatMap((s) =>
    s.actions.filter((a) => a.action_type === "NO_ACTION")
  );

  const operationalActions = aiActions.flatMap((s) =>
    s.actions.filter((a) => a.action_type !== "NO_ACTION")
  );

  /* ----------------------------- */
  /* RENDER */
  /* ----------------------------- */
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">AI Actions</h1>
        <p className="text-sm text-gray-500">
          Control AI and review recommendations
        </p>
      </div>

      {loading && <div className="text-gray-600">Loading…</div>}
      {!loading && error && <div className="text-red-600">{error}</div>}

      {/* CAMPAIGN CONTROL */}
      {!loading && metaConnected && campaigns.length > 0 && (
        <div className="surface overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3">Objective</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">AI</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3">{c.objective ?? "—"}</td>
                  <td className="px-4 py-3">{c.status}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleAI(c.id, !c.ai_active)}
                      className={`px-3 py-1 rounded text-xs font-medium ${
                        c.ai_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {c.ai_active ? "AI Active" : "AI Inactive"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* STRATEGY INSIGHTS */}
      {strategyActions.length > 0 && (
        <div>
          <h2 className="text-lg font-medium mb-2">🧠 Strategy Insights</h2>
          <div className="space-y-3">
            {strategyActions.map((a, i) => {
              const key = `${a.campaign_id}_${a.action_type}_${a.summary}`;
              return (
                <div
                  key={i}
                  className="border-l-4 border-blue-400 bg-blue-50 p-4 rounded"
                >
                  <div className="font-medium">{a.summary}</div>
                  <div className="text-xs text-gray-600 mt-1">
                    Confidence: {Math.round(a.confidence.score * 100)}%
                  </div>

                  {!feedbackSent[key] && (
                    <div className="mt-2 flex gap-2 text-xs">
                      <button
                        onClick={() => submitFeedback(a, true)}
                        className="px-2 py-1 bg-green-100 text-green-700 rounded"
                      >
                        👍 Helpful
                      </button>
                      <button
                        onClick={() => submitFeedback(a, false)}
                        className="px-2 py-1 bg-red-100 text-red-700 rounded"
                      >
                        👎 Not Helpful
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ACTION RECOMMENDATIONS */}
      {operationalActions.length > 0 && (
        <div>
          <h2 className="text-lg font-medium mb-2">
            ⚠️ Action Recommendations
          </h2>
          <div className="space-y-3">
            {operationalActions.map((a, i) => {
              const key = `${a.campaign_id}_${a.action_type}_${a.summary}`;
              return (
                <div
                  key={i}
                  className="border-l-4 border-amber-400 bg-amber-50 p-4 rounded"
                >
                  <div className="font-medium">
                    {a.action_type.replace("_", " ")}
                  </div>
                  <div className="text-sm text-gray-700">{a.summary}</div>
                  <div className="text-xs text-gray-600 mt-1">
                    Confidence: {Math.round(a.confidence.score * 100)}%
                  </div>

                  {!feedbackSent[key] && (
                    <div className="mt-2 flex gap-2 text-xs">
                      <button
                        onClick={() => submitFeedback(a, true)}
                        className="px-2 py-1 bg-green-100 text-green-700 rounded"
                      >
                        👍 Helpful
                      </button>
                      <button
                        onClick={() => submitFeedback(a, false)}
                        className="px-2 py-1 bg-red-100 text-red-700 rounded"
                      >
                        👎 Not Helpful
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
