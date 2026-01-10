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
    buckets?: Record<string, number>;
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

  const confidenceBuckets =
    data.confidence.buckets ?? {
      "0–20": 0,
      "20–40": 0,
      "40–60": 0,
      "60–80": 0,
      "80–100": 0,
    };

  return (
    <div className="space-y-8">
      <h1 className="text-lg font-semibold">AI Intelligence Panel</h1>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Queue Depth" value={data.queue_depth} />
        <KPI title="Total Actions" value={data.actions.total} />
        <KPI title="Successful Actions" value={data.actions.success} />
        <KPI title="Failed Actions" value={data.actions.failed} />
      </div>

      {/* CONFIDENCE OVERVIEW */}
      <div className="rounded border bg-white p-4 space-y-3 text-sm">
        <div className="font-medium">Confidence Health</div>

        <div>
          <span className="text-gray-600">Average Confidence:</span>{" "}
          {data.confidence.average !== null
            ? `${Math.round(data.confidence.average * 100)}%`
            : "—"}
        </div>

        {/* HISTOGRAM */}
        <div className="space-y-2 pt-2">
          {Object.entries(confidenceBuckets).map(([range, count]) => (
            <div key={range} className="flex items-center gap-3">
              <div className="w-16 text-xs text-gray-500">{range}</div>
              <div className="flex-1 bg-gray-100 rounded h-3">
                <div
                  className="h-3 rounded bg-blue-500"
                  style={{
                    width: `${Math.min(count * 5, 100)}%`,
                  }}
                />
              </div>
              <div className="w-10 text-xs text-gray-600 text-right">
                {count}
              </div>
            </div>
          ))}
        </div>

        <div className="text-xs text-gray-500">
          Distribution of AI action confidence scores
        </div>
      </div>

      {/* SIGNAL BREAKDOWN */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SignalCard
          title="Expansion Signals"
          value={data.signals.expansion}
          description="Opportunities where AI suggested scaling"
        />
        <SignalCard
          title="Fatigue Signals"
          value={data.signals.fatigue}
          description="Detected performance decay patterns"
        />
      </div>

      {/* SUCCESS VS FAILURE */}
      <div className="rounded border bg-white p-4 space-y-3 text-sm">
        <div className="font-medium">Action Outcomes</div>

        <Bar
          label="Success"
          value={data.actions.success}
          color="bg-green-500"
        />
        <Bar
          label="Failure"
          value={data.actions.failed}
          color="bg-red-500"
        />

        <div className="text-xs text-gray-500">
          Operational health of AI executions
        </div>
      </div>
    </div>
  );
}

/* ----------------------------- */
/* UI ATOMS */
/* ----------------------------- */

function KPI({ title, value }: { title: string; value: number }) {
  return (
    <div className="p-4 rounded border bg-white">
      <div className="text-xs text-gray-500 uppercase">{title}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
    </div>
  );
}

function SignalCard({
  title,
  value,
  description,
}: {
  title: string;
  value: number | null;
  description: string;
}) {
  return (
    <div className="p-4 rounded border bg-white text-sm space-y-1">
      <div className="font-medium">{title}</div>
      <div className="text-2xl font-semibold">
        {value !== null ? value : "—"}
      </div>
      <div className="text-xs text-gray-500">{description}</div>
    </div>
  );
}

function Bar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-3 rounded bg-gray-100">
        <div
          className={`h-3 rounded ${color}`}
          style={{ width: `${Math.min(value * 5, 100)}%` }}
        />
      </div>
    </div>
  );
}
