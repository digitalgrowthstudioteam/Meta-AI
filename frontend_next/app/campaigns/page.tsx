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

        if (!res.ok) {
          throw new Error();
        }

        const data = await res.json();
        setCampaigns(data);
      } catch {
        setError("Unable to load campaigns");
      } finally {
        setLoading(false);
      }
    }

    fetchCampaigns();
  }, []);

  /* ===============================
     FETCH AI ACTIONS (PER CAMPAIGN)
  =============================== */
  useEffect(() => {
    if (!selectedCampaign) return;

    const campaignId = selectedCampaign.id;

    async function fetchAiActions() {
      setAiLoading(true);
      try {
        const res = await fetch(
          `/ai/campaign/${campaignId}/actions`,
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
    <div className="relative space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          Campaigns
        </h1>
        <p className="text-sm text-gray-500">
          Read-only Meta campaigns with AI intelligence
        </p>
      </div>

      {loading && (
        <div className="bg-white border rounded p-6 text-sm text-gray-500">
          Loading campaigns…
        </div>
      )}

      {!loading && error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {!loading && !error && (
        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3 text-left">Objective</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">AI</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr
                  key={c.id}
                  className="border-b last:border-b-0 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-gray-500">
                      {c.id.slice(0, 8)}…
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
                    className="px-6 py-8 text-center text-gray-500"
                  >
                    No campaigns found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {selectedCampaign && (
        <div className="fixed top-0 right-0 h-full w-[440px] bg-white border-l shadow-xl z-50">
          <div className="h-16 flex items-center justify-between px-5 border-b">
            <div>
              <h2 className="text-sm font-semibold">
                AI Insights
              </h2>
              <p className="text-xs text-gray-500">
                {selectedCampaign.name}
              </p>
            </div>
            <button
              onClick={() => setSelectedCampaign(null)}
              className="text-gray-400 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="p-5 space-y-6 text-sm overflow-y-auto h-[calc(100%-64px)]">
            {aiLoading && (
              <div className="text-gray-500">
                Loading AI insights…
              </div>
            )}

            {!aiLoading && aiActions.length === 0 && (
              <div className="text-gray-500">
                No AI suggestions generated yet.
              </div>
            )}

            {!aiLoading && aiActions.length > 0 && (
              <>
                <Section
                  title="Latest AI Suggestion"
                  value={aiActions[0].action_type}
                  highlight
                />
                <Section
                  title="Why AI suggests this"
                  value={
                    aiActions[0].reasoning ??
                    "Insufficient reasoning data available."
                  }
                />
                <Section
                  title="Confidence"
                  value={
                    aiActions[0].confidence !== undefined
                      ? `${Math.round(
                          aiActions[0].confidence * 100
                        )}%`
                      : "N/A"
                  }
                />
                <Section
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

function Section({
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
