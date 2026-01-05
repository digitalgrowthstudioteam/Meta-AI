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

type AdAccount = {
  id: string;
  name: string;
  is_selected: boolean;
};

/* ----------------------------- */
/* COMPONENT */
/* ----------------------------- */

export default function AIActionsPage() {
  const [campaigns, setCampaigns] = useState<CampaignAI[]>([]);
  const [aiActionSets, setAiActionSets] = useState<AIActionSet[]>([]);
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, boolean>>({});

  /* FILTERS */
  const [selectedAdAccount, setSelectedAdAccount] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [aiFilter, setAiFilter] = useState("");
  const [objectiveFilter, setObjectiveFilter] = useState("");

  /* PAGINATION */
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  /* ----------------------------- */
  /* LOAD AD ACCOUNTS */
  /* ----------------------------- */
  const loadAdAccounts = async () => {
    try {
      const res = await fetch("/api/meta/adaccounts", {
        credentials: "include",
      });
      if (!res.ok) return;
      const data = await res.json();
      setAdAccounts(data ?? []);
      const selected = data?.find((a: AdAccount) => a.is_selected);
      if (selected) setSelectedAdAccount(selected.id);
    } catch {}
  };

  /* ----------------------------- */
  /* LOAD CAMPAIGNS */
  /* ----------------------------- */
  const loadCampaigns = async () => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });

    if (selectedAdAccount) params.append("ad_account_id", selectedAdAccount);
    if (statusFilter) params.append("status", statusFilter);
    if (aiFilter) params.append("ai_active", aiFilter);
    if (objectiveFilter) params.append("objective", objectiveFilter);

    const res = await fetch(`/api/campaigns?${params}`, {
      credentials: "include",
    });

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
        await loadAdAccounts();
        await loadCampaigns();
        await loadAIActions();
      } catch {
        setError("Unable to load AI actions.");
      } finally {
        setLoading(false);
      }
    })();
  }, [
    selectedAdAccount,
    statusFilter,
    aiFilter,
    objectiveFilter,
    page,
    pageSize,
  ]);

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
  /* STATES */
  /* ----------------------------- */

  if (loading) return <div>Loading AI actions…</div>;
  if (error) return <div className="text-red-600">{error}</div>;

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

  /* ----------------------------- */
  /* RENDER */
  /* ----------------------------- */

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">AI Actions</h1>
        <p className="text-sm text-gray-500">
          Transparent AI recommendations with full reasoning
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-5 gap-3 text-sm">
        <select
          value={selectedAdAccount}
          onChange={(e) => setSelectedAdAccount(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Ad Accounts</option>
          {adAccounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="PAUSED">Paused</option>
        </select>

        <select
          value={aiFilter}
          onChange={(e) => setAiFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">AI (All)</option>
          <option value="true">AI Active</option>
          <option value="false">AI Inactive</option>
        </select>

        <select
          value={objectiveFilter}
          onChange={(e) => setObjectiveFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Objectives</option>
          <option value="LEAD">Leads</option>
          <option value="SALES">Sales</option>
        </select>

        <select
          value={pageSize}
          onChange={(e) => {
            setPageSize(Number(e.target.value));
            setPage(1);
          }}
          className="border rounded px-2 py-1"
        >
          {[10, 20, 50, 100].map((n) => (
            <option key={n} value={n}>
              {n} / page
            </option>
          ))}
        </select>
      </div>

      {/* AI ACTIONS */}
      {aiActionSets.length === 0 && (
        <div className="surface p-6 text-sm text-gray-600">
          No AI actions yet. Enable AI and allow data accumulation.
        </div>
      )}

      {aiActionSets.map((set) => {
        const campaign = campaigns.find(
          (c) => c.id === set.campaign_id
        );

        return (
          <div key={set.campaign_id} className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-medium">
                {campaign?.name ?? "Campaign"}
              </h2>

              {campaign && (
                <button
                  onClick={() => toggleAI(campaign.id, !campaign.ai_active)}
                  className={`px-3 py-1 rounded text-xs font-medium ${
                    campaign.ai_active
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {campaign.ai_active ? "AI Active" : "AI Inactive"}
                </button>
              )}
            </div>

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

      {/* PAGINATION */}
      <div className="flex justify-end gap-2">
        <button
          disabled={page === 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="btn-secondary"
        >
          Prev
        </button>
        <button
          onClick={() => setPage((p) => p + 1)}
          className="btn-secondary"
        >
          Next
        </button>
      </div>
    </div>
  );
}
