"use client";

import { useEffect, useState } from "react";

type Campaign = {
  id: string;
  name: string;
  objective: string;
  status: string;
  ai_active: boolean;
};

type AIAction = {
  id: string;
  action_type: string;
  reasoning?: string;
  confidence?: number;
  created_at: string;
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedCampaign, setSelectedCampaign] =
    useState<Campaign | null>(null);

  const [aiActions, setAiActions] = useState<AIAction[]>([]);
  const [aiLoading, setAiLoading] = useState(false);

  /* ===============================
     FETCH CAMPAIGNS
  =============================== */
  useEffect(() => {
    async function fetchCampaigns() {
      try {
        const res = await fetch("/campaigns/", {
          credentials: "include",
        });

        if (!res.ok) throw new Error();

        const data = await res.json();
        setCampaigns(data);
      } catch {
        setError("Unable to load campaigns from Meta.");
      } finally {
        setLoading(false);
      }
    }

    fetchCampaigns();
  }, []);

  /* ===============================
     FETCH AI ACTIONS
  =============================== */
  useEffect(() => {
    if (!selectedCampaign) return;

    async function fetchAiActions() {
      setAiLoading(true);
      try {
        const res = await fetch(
          `/ai/campaign/${selectedCampaign.id}/actions`,
          { credentials: "include" }
        );

        if (!res.ok) throw new Error();

        const data = await res.json();
        setAiActions(data);
      } catch {
        setAiActions([]);
      } finally {
        setAiLoading(false);
      }
    }

    fetchAiActions();
  }, [selectedCampaign]);

  return (
    <div className="space-y-6">
      {/* ================= HEADER ================= */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            Campaigns
          </h1>
          <p className="text-sm text-gray-500">
            Synced from Meta Ads Manager • Read-only
          </p>
        </div>

        <div className="text-xs text-gray-500">
          Managed in Meta
        </div>
      </div>

      {/* ================= STATES ================= */}
      {loading && (
        <div className="bg-white border border-gray-200 rounded p-6 text-sm text-gray-500">
          Loading campaigns from Meta…
        </div>
      )}

      {!loading && error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {/* ================= TABLE ================= */}
      {!loading && !error && (
        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr className="text-gray-600">
                <th className="px-4 py-3 text-left font-medium">
                  Campaign
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  Objective
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  Status
                </th>
                <th className="px-4 py-3 text-left font-medium">
                  AI Status
                </th>
                <th className="px-4 py-3 text-right font-medium">
                  Insights
                </th>
              </tr>
            </thead>

            <tbody>
              {campaigns.map((c) => (
                <tr
                  key={c.id}
                  className="border-b last:border-b-0 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {c.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      ID: {c.id.slice(0, 8)}…
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <ObjectiveBadge value={c.objective} />
                  </td>

                  <td className="px-4 py-3">
                    <StatusBadge value={c.status} />
                  </td>

                  <td className="px-4 py-3">
                    <AIBadge active={c.ai_active} />
                  </td>

                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setSelectedCampaign(c)}
                      className="text-blue-600 font-medium hover:text-blue-800"
                    >
                      View AI
                    </button>
                  </td>
                </tr>
              ))}

              {campaigns.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-10 text-center text-gray-500"
                  >
                    No campaigns found in this ad account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ================= AI DRAWER ================= */}
      {selectedCampaign && (
        <div className="fixed inset-y-0 right-0 w-[460px] bg-white border-l border-gray-200 shadow-2xl z-50">
          <div className="h-16 flex items-center justify-between px-5 border-b border-gray-200">
            <div>
              <div className="text-sm font-semibold text-gray-900">
                AI Insights
              </div>
              <div className="text-xs text-gray-500">
                {selectedCampaign.name}
              </div>
            </div>

            <button
              onClick={() => setSelectedCampaign(null)}
              className="text-gray-400 hover:text-gray-700 text-lg"
            >
              ×
            </button>
          </div>

          <div className="p-5 space-y-6 text-sm overflow-y-auto h-[calc(100%-64px)]">
            {aiLoading && (
              <div className="text-gray-500">
                Analyzing campaign performance…
              </div>
            )}

            {!aiLoading && aiActions.length === 0 && (
              <div className="text-gray-500">
                No AI suggestions generated yet.
              </div>
            )}

            {!aiLoading && aiActions.length > 0 && (
              <>
                <InfoBlock
                  title="Latest Recommendation"
                  value={aiActions[0].action_type}
                  highlight
                />
                <InfoBlock
                  title="Reasoning"
                  value={
                    aiActions[0].reasoning ??
                    "Not enough data available."
                  }
                />
                <InfoBlock
                  title="Confidence"
                  value={
                    aiActions[0].confidence !== undefined
                      ? `${Math.round(
                          aiActions[0].confidence * 100
                        )}%`
                      : "N/A"
                  }
                />
                <InfoBlock
                  title="Generated At"
                  value={new Date(
                    aiActions[0].created_at
                  ).toLocaleString()}
                />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ===============================
   UI COMPONENTS
=============================== */

function StatusBadge({ value }: { value: string }) {
  const active = value.toLowerCase() === "active";
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
        active
          ? "bg-green-100 text-green-700"
          : "bg-gray-200 text-gray-700"
      }`}
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

function AIBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
        active
          ? "bg-blue-100 text-blue-700"
          : "bg-gray-200 text-gray-600"
      }`}
    >
      {active ? "AI Active" : "AI Inactive"}
    </span>
  );
}

function InfoBlock({
  title,
  value,
  highlight,
}: {
  title: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500 mb-1">
        {title}
      </div>
      <div
        className={
          highlight
            ? "font-semibold text-gray-900"
            : "text-gray-800"
        }
      >
        {value}
      </div>
    </div>
  );
}
