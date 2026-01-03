"use client";

import { useEffect, useState } from "react";

type AIAction = {
  id: string;
  campaign_name: string;
  recommendation: string;
  confidence?: number;
};

export default function AIActionsPage() {
  const [actions, setActions] = useState<AIAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);

  // -----------------------------------
  // LOAD AI ACTIONS
  // -----------------------------------
  const loadActions = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch("/api/ai-actions", {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      // EMPTY ARRAY IS VALID
      setActions(Array.isArray(data) ? data : []);
      setMetaConnected(true);
    } catch (err) {
      console.error("AI actions fetch failed", err);
      setError("Unable to load AI actions.");
      setMetaConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActions();
  }, []);

  // -----------------------------------
  // CONNECT META
  // -----------------------------------
  const connectMeta = async () => {
    const res = await fetch("/api/meta/connect", {
      credentials: "include",
    });

    const data = await res.json();
    if (data?.redirect_url) {
      window.location.href = data.redirect_url;
    }
  };

  // -----------------------------------
  // RENDER
  // -----------------------------------
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">AI Actions</h1>
        <p className="text-sm text-gray-500">
          Explainable AI recommendations · Suggestions only
        </p>
      </div>

      {/* LOADING */}
      {loading && (
        <div className="text-gray-600">Loading AI actions…</div>
      )}

      {/* REAL ERROR ONLY */}
      {!loading && error && (
        <div className="text-red-600 font-medium">{error}</div>
      )}

      {/* META NOT CONNECTED */}
      {!loading && !error && metaConnected === false && (
        <div className="border rounded p-6 bg-white">
          <p className="font-medium mb-2">
            Connect Meta Ads to enable AI insights
          </p>
          <button
            onClick={connectMeta}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Connect Meta Ads
          </button>
        </div>
      )}

      {/* EMPTY STATE (NO AI ACTIONS YET) */}
      {!loading && !error && metaConnected && actions.length === 0 && (
        <div className="border rounded p-6 bg-white">
          <p className="font-medium mb-2">
            No AI actions available yet
          </p>
          <p className="text-sm text-gray-500">
            AI recommendations will appear once campaigns are synced
            and AI is enabled on eligible campaigns.
          </p>
        </div>
      )}

      {/* AI ACTION LIST */}
      {!loading && !error && actions.length > 0 && (
        <div className="space-y-3">
          {actions.map((a) => (
            <div
              key={a.id}
              className="border rounded p-4 bg-white"
            >
              <div className="flex justify-between">
                <div>
                  <p className="font-medium">{a.campaign_name}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {a.recommendation}
                  </p>
                </div>

                {a.confidence !== undefined && (
                  <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-700">
                    {Math.round(a.confidence * 100)}% confidence
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
