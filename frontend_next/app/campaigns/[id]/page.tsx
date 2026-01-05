"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

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
  const { id } = useParams<{ id: string }>();

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [audienceInsights, setAudienceInsights] = useState<AudienceInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD CAMPAIGN
   * ---------------------------------- */
  const loadCampaign = async () => {
    try {
      const res = await fetch(`/api/campaigns/${id}`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error();
      setCampaign(await res.json());
    } catch {
      setError("Unable to load campaign");
    }
  };

  /* ----------------------------------
   * LOAD AUDIENCE INSIGHTS
   * ---------------------------------- */
  const loadAudienceInsights = async () => {
    try {
      const res = await fetch(`/api/ai/audience-insights/${id}`, {
        credentials: "include",
      });
      if (!res.ok) return;
      const json = await res.json();
      setAudienceInsights(json?.insights ?? []);
    } catch {}
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadCampaign();
      await loadAudienceInsights();
      setLoading(false);
    })();
  }, [id]);

  /* ----------------------------------
   * TOGGLE AI
   * ---------------------------------- */
  const toggleAI = async () => {
    if (!campaign || toggling) return;

    const next = !campaign.ai_active;
    setToggling(true);
    setCampaign({ ...campaign, ai_active: next });

    try {
      const res = await fetch(`/api/campaigns/${id}/ai-toggle`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: next }),
      });

      if (!res.ok) throw new Error();
    } catch {
      setCampaign({ ...campaign, ai_active: !next });
      alert("Unable to toggle AI. Check plan limits.");
    } finally {
      setToggling(false);
    }
  };

  /* ----------------------------------
   * STATES
   * ---------------------------------- */
  if (loading) return <div>Loading campaign…</div>;
  if (error || !campaign)
    return <div className="text-red-600">{error}</div>;

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-xl font-semibold">{campaign.name}</h1>
          <p className="text-sm text-gray-500">
            {campaign.objective ?? "—"} · {campaign.status}
          </p>
        </div>

        {/* AI TOGGLE */}
        <button
          onClick={toggleAI}
          disabled={toggling}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
            campaign.ai_active ? "bg-green-600" : "bg-gray-300"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
              campaign.ai_active ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
      </div>

      {/* AUDIENCE INSIGHTS */}
      <div className="surface p-4">
        <h2 className="font-medium mb-3">Audience Insights</h2>

        {audienceInsights.length === 0 && (
          <div className="text-sm text-gray-500">
            No audience insights yet. Metrics are still accumulating.
          </div>
        )}

        {audienceInsights.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="px-3 py-2 text-left">Segment</th>
                  <th className="px-3 py-2 text-left">Spend</th>
                  <th className="px-3 py-2 text-left">ROAS</th>
                  <th className="px-3 py-2 text-left">AI Suggestion</th>
                </tr>
              </thead>
              <tbody>
                {audienceInsights.map((row, idx) => (
                  <tr key={idx} className="border-b last:border-0">
                    <td className="px-3 py-2">
                      {[row.age_group, row.gender, row.platform, row.placement]
                        .filter(Boolean)
                        .join(" · ")}
                    </td>
                    <td className="px-3 py-2">₹{row.spend.toFixed(2)}</td>
                    <td className="px-3 py-2">
                      {row.roas ? row.roas.toFixed(2) : "—"}
                    </td>
                    <td className="px-3 py-2 font-medium">
                      {row.recommendation.toUpperCase()} — {row.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
