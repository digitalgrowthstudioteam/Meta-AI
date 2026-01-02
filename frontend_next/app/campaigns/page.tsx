// frontend_next/app/campaigns/page.tsx

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
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    fetchCampaigns();
  }, []);

  return (
    <div className="relative">
      {/* ===============================
          PAGE HEADER
      =============================== */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-500">
          Read-only Meta campaigns with AI insights
        </p>
      </div>

      {/* ===============================
          LOADING STATE
      =============================== */}
      {loading && (
        <div className="text-sm text-gray-500">
          Loading campaigns…
        </div>
      )}

      {/* ===============================
          CAMPAIGNS TABLE
      =============================== */}
      {!loading && (
        <div className="bg-white border border-gray-200 rounded">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3">Campaign</th>
                <th className="text-left px-4 py-3">Objective</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">AI</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((campaign) => (
                <tr
                  key={campaign.id}
                  className="border-b last:border-b-0 hover:bg-gray-50"
                >
                  <td className="px-4 py-3 font-medium">
                    {campaign.name}
                  </td>
                  <td className="px-4 py-3">
                    {campaign.objective}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={campaign.status} />
                  </td>
                  <td className="px-4 py-3">
                    <AIBadge active={campaign.ai_active} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setSelectedCampaign(campaign)}
                      className="text-blue-600 hover:underline text-sm"
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
                    className="px-4 py-6 text-center text-gray-500"
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
        <div className="fixed top-0 right-0 h-full w-[420px] bg-white border-l border-gray-200 shadow-lg z-50">
          <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
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
              className="text-gray-500 hover:text-gray-800"
            >
              ✕
            </button>
          </div>

          <div className="p-4 text-sm space-y-4">
            <div>
              <div className="font-medium mb-1">Objective</div>
              <div className="text-gray-600">
                {selectedCampaign.objective}
              </div>
            </div>

            <div>
              <div className="font-medium mb-1">AI Status</div>
              <div className="text-gray-600">
                {selectedCampaign.ai_active
                  ? "AI Active"
                  : "AI Inactive"}
              </div>
            </div>

            <div>
              <div className="font-medium mb-1">
                AI Suggestions
              </div>
              <div className="text-gray-600">
                No actions applied. Read-only insights only.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ===============================
   UI COMPONENTS
=============================== */

function StatusBadge({ status }: { status: string }) {
  return (
    <span className="inline-block rounded px-2 py-1 text-xs bg-gray-100 text-gray-700">
      {status}
    </span>
  );
}

function AIBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block rounded px-2 py-1 text-xs ${
        active
          ? "bg-blue-100 text-blue-700"
          : "bg-gray-200 text-gray-600"
      }`}
    >
      {active ? "AI On" : "AI Off"}
    </span>
  );
}
