"use client";

import { useEffect, useState } from "react";

type Campaign = {
  id: string;
  name: string;
  objective: string;
  status: string;
  ai_active: boolean;
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCampaign, setSelectedCampaign] =
    useState<Campaign | null>(null);

  useEffect(() => {
    async function fetchCampaigns() {
      try {
        const res = await fetch("/campaigns/", {
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Failed to fetch campaigns");
        }

        const data = await res.json();
        setCampaigns(data);
      } catch (err) {
        setError("Unable to load campaigns");
      } finally {
        setLoading(false);
      }
    }

    fetchCampaigns();
  }, []);

  return (
    <div className="relative space-y-6">
      {/* ===============================
          PAGE HEADER
      =============================== */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          Campaigns
        </h1>
        <p className="text-sm text-gray-500">
          Read-only Meta campaigns with AI insights
        </p>
      </div>

      {/* ===============================
          LOADING STATE (SKELETON)
      =============================== */}
      {loading && (
        <div className="bg-white border border-gray-200 rounded">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-center px-4 py-4 border-b last:border-b-0 animate-pulse"
            >
              <div className="flex-1 space-y-2">
                <div className="h-3 w-1/3 bg-gray-200 rounded" />
                <div className="h-2 w-1/4 bg-gray-100 rounded" />
              </div>
              <div className="h-6 w-16 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* ===============================
          ERROR STATE
      =============================== */}
      {!loading && error && (
        <div className="text-sm text-red-600">
          {error}
        </div>
      )}

      {/* ===============================
          CAMPAIGNS TABLE
      =============================== */}
      {!loading && !error && (
        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">
                  Campaign
                </th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">
                  Objective
                </th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">
                  Status
                </th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">
                  AI
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {campaigns.map((campaign) => (
                <tr
                  key={campaign.id}
                  className="border-b last:border-b-0 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {campaign.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      ID: {campaign.id.slice(0, 8)}…
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <ObjectiveBadge objective={campaign.objective} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={campaign.status} />
                  </td>
                  <td className="px-4 py-3">
                    <AIBadge active={campaign.ai_active} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() =>
                        setSelectedCampaign(campaign)
                      }
                      className="text-blue-600 hover:text-blue-800 font-medium text-sm"
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
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    No campaigns found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ===============================
          AI DRAWER
      =============================== */}
      {selectedCampaign && (
        <div className="fixed top-0 right-0 h-full w-[420px] bg-white border-l border-gray-200 shadow-xl z-50">
          <div className="h-16 flex items-center justify-between px-5 border-b border-gray-200">
            <div>
              <h2 className="text-sm font-semibold text-gray-900">
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

          <div className="p-5 space-y-6 text-sm">
            <Section
              title="Objective"
              value={selectedCampaign.objective}
            />
            <Section
              title="AI Status"
              value={
                selectedCampaign.ai_active
                  ? "AI Active"
                  : "AI Inactive"
              }
            />
            <Section
              title="AI Suggestions"
              value="Read-only insights available. No actions applied."
            />
          </div>
        </div>
      )}
    </div>
  );
}

/* ===============================
   SMALL UI COMPONENTS
=============================== */

function StatusBadge({ status }: { status: string }) {
  const isActive = status.toLowerCase() === "active";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${
        isActive
          ? "bg-green-100 text-green-700"
          : "bg-gray-200 text-gray-700"
      }`}
    >
      {status}
    </span>
  );
}

function ObjectiveBadge({
  objective,
}: {
  objective: string;
}) {
  const isLead = objective.toLowerCase().includes("lead");
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
        isLead
          ? "bg-purple-100 text-purple-700"
          : "bg-orange-100 text-orange-700"
      }`}
    >
      {objective}
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
}: {
  title: string;
  value: string;
}) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500 mb-1">
        {title}
      </div>
      <div className="text-gray-800">{value}</div>
    </div>
  );
}
