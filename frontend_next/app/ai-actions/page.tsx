'use client';

import { useEffect, useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  PauseCircle,
  PlayCircle,
  AlertCircle,
  CheckCircle
} from "lucide-react";
import toast from "react-hot-toast";
import { apiFetch } from "../lib/fetcher";

type AIAction = {
  id: string;
  campaign_id: string;
  campaign_name: string;
  action_type: "SCALE_BUDGET" | "REDUCE_BUDGET" | "PAUSE_ADS" | "ENABLE_ADS";
  reason: string;
  confidence_score: number;
  suggested_value?: string;
  status: "PENDING" | "APPLIED" | "DISMISSED";
  created_at: string;
};

export default function AiActionsPage() {
  const [actions, setActions] = useState<AIAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const loadActions = async () => {
    try {
      setLoading(true);
      const res = await apiFetch("/api/ai/actions/pending", {
        cache: "no-store",
      });

      if (res.ok) {
        const json = await res.json();
        setActions(json || []);
      } else {
        setActions([]);
      }
    } catch (e) {
      console.error("Failed to load actions", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActions();
  }, []);

  const handleAction = async (actionId: string, decision: "APPLY" | "DISMISS") => {
    setProcessingId(actionId);
    try {
      const endpoint =
        decision === "APPLY"
          ? `/api/ai/actions/${actionId}/apply`
          : `/api/ai/actions/${actionId}/dismiss`;

      await apiFetch(endpoint, { method: "POST" });
      toast.success(decision === "APPLY" ? "Action applied" : "Action dismissed");
      setActions((prev) => prev.filter((a) => a.id !== actionId));
    } catch (error) {
      toast.error("Failed to process action");
    } finally {
      setProcessingId(null);
    }
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case "SCALE_BUDGET":
        return <TrendingUp className="h-5 w-5 text-green-600" />;
      case "REDUCE_BUDGET":
        return <TrendingDown className="h-5 w-5 text-orange-600" />;
      case "PAUSE_ADS":
        return <PauseCircle className="h-5 w-5 text-red-600" />;
      case "ENABLE_ADS":
        return <PlayCircle className="h-5 w-5 text-blue-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">AI Recommendations</h1>

      {loading ? (
        <div className="text-sm text-gray-500 text-center py-12">
          Loading...
        </div>
      ) : actions.length === 0 ? (
        <div className="bg-white border border-dashed rounded-lg shadow-sm p-10 text-center space-y-3">
          <CheckCircle className="mx-auto h-10 w-10 text-green-500" />
          <h3 className="text-base font-medium text-gray-900">All caught up!</h3>
          <p className="text-sm text-gray-500">
            There are no pending AI recommendations.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {actions.map((action) => (
            <div
              key={action.id}
              className="bg-white border rounded-lg shadow-sm p-4 flex items-center justify-between"
            >
              <div className="flex items-start gap-4">
                <div className="p-2 bg-gray-50 rounded">
                  {getActionIcon(action.action_type)}
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">
                    {action.action_type.replace(/_/g, " ")}
                  </h3>
                  <p className="text-sm text-gray-500">{action.reason}</p>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(action.id, "DISMISS")}
                  disabled={!!processingId}
                  className="px-3 py-1.5 border rounded-md text-sm shadow-sm hover:bg-gray-50 disabled:opacity-50"
                >
                  Dismiss
                </button>
                <button
                  onClick={() => handleAction(action.id, "APPLY")}
                  disabled={!!processingId}
                  className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm shadow-sm hover:bg-indigo-500 disabled:opacity-50"
                >
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
