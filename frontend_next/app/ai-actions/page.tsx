"use client";

import { useEffect, useState } from "react";

/* ----------------------------- */
/* TYPES */
/* ----------------------------- */

type AIOverview = {
  queue_depth: number;
  actions: {
    total: number;
    success: number;
    failed: number;
  };
  confidence: {
    average: number | null;
  };
  signals: {
    expansion: number | null;
    fatigue: number | null;
  };
};

/* ----------------------------- */
/* COMPONENT */
/* ----------------------------- */

export default function AdminAIOverviewPage() {
  const [data, setData] = useState<AIOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/ai/admin/overview", {
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          throw new Error("Failed to load AI overview");
        }

        const json = await res.json();
        setData(json);
      } catch {
        setError("Unable to load AI intelligence panel.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-600">Loading AI intelligence…</div>;
  }

  if (error || !data) {
    return <div className="text-red-600 text-sm">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">AI Intelligence Panel</h1>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Queue Depth" value={data.queue_depth} />
        <KPI title="Total Actions" value={data.actions.total} />
        <KPI title="Successful Actions" value={data.actions.success} />
        <KPI title="Failed Actions" value={data.actions.failed} />
      </div>

      {/* CONFIDENCE */}
      <div className="p-4 rounded border bg-white text-sm space-y-1">
        <div>
          <span className="font-medium">Avg Confidence:</span>{" "}
          {data.confidence.average !== null
            ? `${Math.round(data.confidence.average * 100)}%`
            : "—"}
        </div>
        <div className="text-xs text-gray-500">
          Confidence gating health indicator
        </div>
      </div>

      {/* SIGNALS */}
      <div className="p-4 rounded border bg-white text-sm space-y-1">
        <div>
          <span className="font-medium">Expansion Signals:</span>{" "}
          {data.signals.expansion ?? "—"}
        </div>
        <div>
          <span className="font-medium">Fatigue Signals:</span>{" "}
          {data.signals.fatigue ?? "—"}
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value }: { title: string; value: number }) {
  return (
    <div className="p-4 rounded border bg-white">
      <div className="text-xs text-gray-500 uppercase">{title}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
    </div>
  );
}
