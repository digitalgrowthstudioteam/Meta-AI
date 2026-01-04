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
  source?: "campaign" | "industry" | "category";
};

type BreakdownEvidence = {
  dimension: string;
  key: string;
  metrics: MetricEvidence[];
};

type ConfidenceScore = {
  score: number;
  reason?: string;
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
  const [aiActionSets, setAiActionSets] = useState<AIActionSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, boolean>>({});

  /* ----------------------------- */
  /* LOAD CAMPAIGNS */
  /* ----------------------------- */
  const loadCampaigns = async () => {
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
      setAiActionSets(Array.isArray(data) ? data : []);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await loadCampaigns();
        await loadAIActions();
      } catch {
        setError("Unable to load AI actions.");
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

    await loadCampaigns();
    await loadAIActions();
  };

  /* ----------------------------- */
  /* FEEDBACK */
  /* ----------------------------- */
  const submitFeedback = async (action: AIAction, isHelpful: boolean) => {
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
  /* RENDER */
  /* ----------------------------- */

  if (loading) {
    return <div className="text-gray-600">Loading AI actions…</div>;
  }

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  if (metaConnected === false) {
    return (
      <div className="surface p-6">
        <h2 className="font-medium mb-1">Meta account not connected</h2>
        <p className="text-sm text-gray-600">
          Connect your Meta Ads account to enable AI insights.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">AI Actions</h1>
        <p className="text-sm text-gray-500">
          Transparent AI recommendations with full reasoning
        </p>
      </div>

      {/* CAMPAIGN AI CONTROL */}
      {campaigns.length > 0 && (
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

      {/* EMPTY STATE */}
      {aiActionSets.length === 0 && (
        <div className="surface p-6 text-sm text-gray-600">
          No AI actions yet.
          <br />
          Enable AI and allow sufficient data accumulation.
        </div>
      )}

      {/* AI ACTIONS */}
      {aiActionSets.map((set) => {
        const campaign = campaigns.find(
          (c) => c.id === set.campaign_id
        );

        return (
          <div key={set.campaign_id} className="space-y-4">
            <h2 className="text-lg font-medium">
              {campaign?.name ?? "Campaign"}
            </h2>

            {set.actions.map((action, i) => {
              const key = `${action.campaign_id}_${action.action_type}_${action.summary}`;

              return (
                <div
                  key={i}
                  className="border-l-4 border-amber-400 bg-amber-50 p-4 rounded space-y-3"
                >
                  <div className="font-medium">{action.summary}</div>

                  <div className="text-xs text-gray-700">
                    Confidence:{" "}
                    <strong>
                      {Math.round(action.confidence.score * 100)}%
                    </strong>
                  </div>

                  {action.confidence.reason && (
                    <div className="text-xs text-gray-600 italic">
                      Why: {action.confidence.reason}
                    </div>
                  )}

                  {/* METRIC EVIDENCE */}
                  {action.metrics && action.metrics.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs font-medium text-gray-700 mb-1">
                        Evidence
                      </div>
                      <ul className="text-xs text-gray-700 space-y-1">
                        {action.metrics.map((m, idx) => (
                          <li key={idx}>
                            • <strong>{m.metric}</strong> ({m.window}):{" "}
                            {m.value}
                            {m.delta_pct !== undefined &&
                              ` (${m.delta_pct}% vs baseline)`}
                            {m.source && (
                              <span className="ml-1 text-gray-500">
                                [{m.source}]
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* BREAKDOWN EVIDENCE */}
                  {action.breakdowns && action.breakdowns.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs font-medium text-gray-700 mb-1">
                        Breakdown Insights
                      </div>
                      {action.breakdowns.map((b, idx) => (
                        <div key={idx} className="text-xs mb-2">
                          <div className="font-medium">
                            {b.dimension.replace("_", " ")}: {b.key}
                          </div>
                          <ul className="ml-3 list-disc">
                            {b.metrics.map((m, mi) => (
                              <li key={mi}>
                                {m.metric} ({m.window}): {m.value}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}

                  {!feedbackSent[key] && (
                    <div className="flex gap-2 text-xs pt-2">
                      <button
                        onClick={() => submitFeedback(action, true)}
                        className="px-2 py-1 bg-green-100 text-green-700 rounded"
                      >
                        👍 Helpful
                      </button>
                      <button
                        onClick={() => submitFeedback(action, false)}
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
        );
      })}
    </div>
  );
}
