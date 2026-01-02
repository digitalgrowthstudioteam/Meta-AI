// frontend_next/app/campaigns/page.tsx

"use client";

import { useState } from "react";

type Campaign = {
  id: string;
  name: string;
  objective: "LEAD" | "SALES";
  status: "ACTIVE" | "PAUSED";
  aiActive: boolean;
};

const MOCK_CAMPAIGNS: Campaign[] = [
  {
    id: "cmp_001",
    name: "Lead Gen – Website Form",
    objective: "LEAD",
    status: "ACTIVE",
    aiActive: true,
  },
  {
    id: "cmp_002",
    name: "Sales – Retargeting",
    objective: "SALES",
    status: "ACTIVE",
    aiActive: false,
  },
  {
    id: "cmp_003",
    name: "Lead Gen – WhatsApp",
    objective: "LEAD",
    status: "PAUSED",
    aiActive: true,
  },
];

export default function CampaignsPage() {
  const [selectedCampaign, setSelectedCampaign] =
    useState<Campaign | null>(null);

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
          CAMPAIGNS TABLE
      =============================== */}
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
            {MOCK_CAMPAIGNS.map((campaign) => (
              <tr
                key={campaign.id}
                className="border-b last:border-b-0 hover:bg-gray-50"
              >
                <td className="px-4 py-3 font-medium">
                  {campaign.name}
                </td>
                <td className="px-4 py-3">
                  {campaign.objective === "LEAD" ? "Lead" : "Sales"}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={campaign.status} />
                </td>
                <td className="px-4 py-3">
                  <AIBadge active={campaign.aiActive} />
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
          </tbody>
        </table>
      </div>

      {/* ===============================
          AI DRAWER (RIGHT SIDE)
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
                {selectedCampaign.objective === "LEAD"
                  ? "Lead Generation"
                  : "Sales / Conversions"}
              </div>
            </div>

            <div>
              <div className="font-medium mb-1">AI Status</div>
              <div className="text-gray-600">
                {selectedCampaign.aiActive
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
   SMALL UI COMPONENTS
=============================== */

function StatusBadge({ status }: { status: "ACTIVE" | "PAUSED" }) {
  return (
    <span
      className={`inline-block rounded px-2 py-1 text-xs ${
        status === "ACTIVE"
          ? "bg-green-100 text-green-700"
          : "bg-gray-200 text-gray-700"
      }`}
    >
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
