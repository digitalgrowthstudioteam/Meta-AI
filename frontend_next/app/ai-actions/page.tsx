"use client";

import { useEffect, useState } from "react";

type AIAction = {
  id: string;
  action_type: string;
  reasoning?: string;
  confidence?: number;
  created_at: string;
  campaign_id: string;
  campaign_name?: string;
  objective?: string;
};

export default function AIActionsPage() {
  const [actions, setActions] = useState<AIAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchActions() {
      try {
        const res = await fetch("/ai/actions", {
          credentials: "include",
        });

        if (!res.ok) throw new Error();

        const data = await res.json();
        setActions(data);
      } catch {
        setError("Unable to load AI actions.");
      } finally {
        setLoading(false);
      }
    }

    fetchActions();
  }, []);

  return (
    <div className="space-y-6">
      {/* ================= HEADER ================= */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            AI Actions
          </h1>
          <p className="text-sm text-gray-500">
            Explainable AI recommendations across your Meta campaigns
          </p>
        </div>

        <div className="text-xs text-gray-500">
          Suggestions only • No auto-apply
        </div>
      </div>

      {/* ================= STATES ================= */}
      {loading && (
        <div className="bg-white border border-gray-200 rounded p-6 text-sm text-gray-500">
          Loading AI recommendations…
        </div>
      )}

      {!loading && error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {!loading && !error && actions.length === 0 && (
        <div className="bg-white border border-gray-200 rounded p-10 text-center text-sm text-gray-500">
          No AI actions have been generated yet.
        </div>
      )}

      {/* ================= ACTION CARDS ================= */}
      {!loading && !error && actions.length > 0 && (
        <div className="space-y-4">
          {actions.map((action) => (
            <div
              key={action.id}
              className="bg-white border border-gray-200 rounded p-5 hover:shadow-sm transition"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-gray-900">
                    {action.campaign_name ??
                      `Campaign ${action.campaign_id.slice(0, 8)}…`}
                  </div>

                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <ObjectiveBadge
                      value={action.objective ?? "—"}
                    />
                    <span>•</span>
                    <span>
                      {new Date(
                        action.created_at
                      ).toLocaleString()}
                    </span>
                  </div>
                </div>

                <ConfidenceBadge
                  confidence={action.confidence}
                />
              </div>

              <div className="mt-4 flex items-start gap-4">
                <ActionBadge value={action.action_type} />

                <div className="text-sm text-gray-700 leading-relaxed">
                  {action.reasoning ??
                    "No detailed reasoning available for this recommendation yet."}
                </div>
              </div>

              <div className="mt-4 text-xs text-gray-400">
                This is a recommendation only. Apply changes in
                Meta Ads Manager.
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ===============================
   UI COMPONENTS
=============================== */

function ActionBadge({ value }: { value: string }) {
  const v = value.toLowerCase();

  const styles =
    v === "pause"
      ? "bg-red-100 text-red-700"
      : v === "scale"
      ? "bg-green-100 text-green-700"
      : v === "optimize"
      ? "bg-blue-100 text-blue-700"
      : "bg-gray-200 text-gray-700";

  return (
    <span
      className={`inline-flex shrink-0 rounded-full px-3 py-1 text-xs font-medium ${styles}`}
    >
      {value}
    </span>
  );
}

function ObjectiveBadge({ value }: { value: string }) {
  const isLead = value.toLowerCase().includes("lead");
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        isLead
          ? "bg-purple-100 text-purple-700"
          : "bg-orange-100 text-orange-700"
      }`}
    >
      {value}
    </span>
  );
}

function ConfidenceBadge({
  confidence,
}: {
  confidence?: number;
}) {
  if (confidence === undefined) {
    return (
      <span className="text-xs text-gray-400">
        Confidence N/A
      </span>
    );
  }

  const pct = Math.round(confidence * 100);

  let styles = "bg-gray-200 text-gray-700";
  if (pct >= 80) styles = "bg-green-100 text-green-700";
  else if (pct >= 50)
    styles = "bg-yellow-100 text-yellow-800";

  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${styles}`}
    >
      {pct}% confidence
    </span>
  );
}
