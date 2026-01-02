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
        setError("Unable to load AI actions");
      } finally {
        setLoading(false);
      }
    }

    fetchActions();
  }, []);

  return (
    <div className="space-y-6">
      {/* ===============================
          PAGE HEADER
      =============================== */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          AI Actions
        </h1>
        <p className="text-sm text-gray-500">
          Explainable AI recommendations across all campaigns
        </p>
      </div>

      {/* ===============================
          LOADING STATE
      =============================== */}
      {loading && (
        <div className="bg-white border rounded p-6 text-sm text-gray-500">
          Loading AI actions…
        </div>
      )}

      {/* ===============================
          ERROR STATE
      =============================== */}
      {!loading && error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {/* ===============================
          EMPTY STATE
      =============================== */}
      {!loading && !error && actions.length === 0 && (
        <div className="bg-white border rounded p-8 text-center text-sm text-gray-500">
          No AI actions generated yet.
        </div>
      )}

      {/* ===============================
          AI ACTIONS LIST
      =============================== */}
      {!loading && !error && actions.length > 0 && (
        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left">
                  Campaign
                </th>
                <th className="px-4 py-3 text-left">
                  Action
                </th>
                <th className="px-4 py-3 text-left">
                  Objective
                </th>
                <th className="px-4 py-3 text-left">
                  Confidence
                </th>
                <th className="px-4 py-3 text-left">
                  Generated
                </th>
              </tr>
            </thead>
            <tbody>
              {actions.map((action) => (
                <tr
                  key={action.id}
                  className="border-b last:border-b-0 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {action.campaign_name ??
                        action.campaign_id.slice(0, 8) + "…"}
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <ActionBadge value={action.action_type} />
                    {action.reasoning && (
                      <div className="text-xs text-gray-500 mt-1">
                        {action.reasoning.slice(0, 80)}
                        {action.reasoning.length > 80
                          ? "…"
                          : ""}
                      </div>
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <ObjectiveBadge
                      value={action.objective ?? "—"}
                    />
                  </td>

                  <td className="px-4 py-3">
                    {action.confidence !== undefined
                      ? `${Math.round(
                          action.confidence * 100
                        )}%`
                      : "N/A"}
                  </td>

                  <td className="px-4 py-3 text-gray-500">
                    {new Date(
                      action.created_at
                    ).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* FOOTNOTE */}
      <div className="text-xs text-gray-400">
        All AI actions are read-only. No changes are
        auto-applied.
      </div>
    </div>
  );
}

/* ===============================
   UI BADGES
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
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${styles}`}
    >
      {value}
    </span>
  );
}

function ObjectiveBadge({ value }: { value: string }) {
  const isLead = value.toLowerCase().includes("lead");
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
        isLead
          ? "bg-purple-100 text-purple-700"
          : "bg-orange-100 text-orange-700"
      }`}
    >
      {value}
    </span>
  );
}
