"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import toast from "react-hot-toast";
import { apiFetch } from "@/app/lib/fetcher";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type Campaign = {
  id: string;
  name: string;
  status: string;
  objective?: string;
  ai_active?: boolean;
};

type AudienceInsight = {
  age_group?: string;
  gender?: string;
  platform?: string;
  placement?: string;
  spend: number;
  conversions: number;
  revenue: number;
  cpa?: number | null;
  roas?: number | null;
  recommendation: "keep" | "expand" | "reduce";
  reason: string;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function CampaignDetailPage() {
  const params = useParams();
  const id = typeof params?.id === "string" ? params.id : "";

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [audienceInsights, setAudienceInsights] = useState<AudienceInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD CAMPAIGN
   * ---------------------------------- */
  const loadCampaign = async () => {
    if (!id) return;
    try {
      const res = await apiFetch(`/api/campaigns/${id}`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error();
      setCampaign(await res.json());
    } catch {
      setError("Unable to load campaign details.");
    }
  };

  /* ----------------------------------
   * LOAD AUDIENCE INSIGHTS
   * ---------------------------------- */
  const loadAudienceInsights = async () => {
    if (!id) return;
    try {
      const res = await apiFetch(`/api/ai/audience-insights/${id}`, {
        cache: "no-store",
      });
      if (!res.ok) return;
      const json = await res.json();
      setAudienceInsights(json?.insights ?? []);
    } catch (e) {
      console.error("Failed to load insights", e);
    }
  };

  useEffect(() => {
    if (id) {
      (async () => {
        setLoading(true);
        await Promise.all([loadCampaign(), loadAudienceInsights()]);
        setLoading(false);
      })();
    }
  }, [id]);

  /* ----------------------------------
   * TOGGLE AI
   * ---------------------------------- */
  const toggleAI = async () => {
    if (!campaign || toggling) return;

    const next = !campaign.ai_active;
    setToggling(true);
    
    // Optimistic Update
    setCampaign({ ...campaign, ai_active: next });

    try {
      const res = await apiFetch(`/api/campaigns/${id}/ai-toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: next }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail?.message || "Failed to toggle AI");
      }

      toast.success(next ? "AI Optimization Activated" : "AI Optimization Paused");
    } catch (err: any) {
      // Revert
      setCampaign({ ...campaign, ai_active: !next });
      toast.error(err.message || "Unable to update AI status");
    } finally {
      setToggling(false);
    }
  };

  /* ----------------------------------
   * FORMATTERS
   * ---------------------------------- */
  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);

  const getRecommendationBadge = (type: string) => {
    switch (type) {
      case "expand": return "bg-green-100 text-green-800 ring-green-600/20";
      case "reduce": return "bg-red-100 text-red-800 ring-red-600/20";
      default: return "bg-gray-100 text-gray-800 ring-gray-600/20";
    }
  };

  /* ----------------------------------
   * STATES
   * ---------------------------------- */
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-gray-500">
        Loading campaign data...
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        {error || "Campaign not found."}
      </div>
    );
  }

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* HEADER CARD */}
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-gray-900">{campaign.name}</h1>
            <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
              campaign.status === 'ACTIVE' 
                ? 'bg-green-50 text-green-700 ring-green-600/20' 
                : 'bg-yellow-50 text-yellow-800 ring-yellow-600/20'
            }`}>
              {campaign.status}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Objective: <span className="font-medium text-gray-700">{campaign.objective || "Unknown"}</span>
          </p>
        </div>

        {/* AI TOGGLE */}
        <div className="flex items-center gap-3 bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
          <span className="text-sm font-medium text-gray-700">AI Optimization</span>
          <button
            onClick={toggleAI}
            disabled={toggling}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
              campaign.ai_active ? "bg-indigo-600" : "bg-gray-200"
            } ${toggling ? "opacity-50 cursor-wait" : ""}`}
          >
            <span className="sr-only">Toggle AI</span>
            <span
              aria-hidden="true"
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                campaign.ai_active ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>
      </div>

      {/* AUDIENCE INSIGHTS */}
      <div className="space-y-4">
        <div>
          <h2 className="text-base font-semibold leading-6 text-gray-900">Audience & Placement Insights</h2>
          <p className="mt-1 text-sm text-gray-500">AI-driven analysis of your ad performance across different segments.</p>
        </div>

        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
          {audienceInsights.length === 0 ? (
            <div className="p-10 text-center">
              <p className="text-sm text-gray-500">
                Not enough data yet. Insights will appear here once the campaign generates traffic.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">Segment</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Spend</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">ROAS</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">AI Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {audienceInsights.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-gray-900 sm:pl-6">
                        <div className="font-medium">
                          {[row.age_group, row.gender].filter(Boolean).join(" · ") || "General Audience"}
                        </div>
                        <div className="text-xs text-gray-500">
                          {[row.platform, row.placement].filter(Boolean).join(" · ")}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                        {formatCurrency(row.spend)}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                        {row.roas ? (
                          <span className={row.roas > 2 ? "text-green-600 font-medium" : ""}>
                            {row.roas.toFixed(2)}x
                          </span>
                        ) : "—"}
                      </td>
                      <td className="px-3 py-4 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${getRecommendationBadge(row.recommendation)} uppercase`}>
                            {row.recommendation}
                          </span>
                          <span className="text-xs text-gray-500 truncate max-w-xs" title={row.reason}>
                            {row.reason}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
