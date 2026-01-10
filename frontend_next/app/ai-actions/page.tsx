"use client";

import { useEffect, useState } from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  PauseCircle, 
  PlayCircle, 
  AlertCircle, 
  CheckCircle, 
  XCircle 
} from "lucide-react";
import toast from "react-hot-toast";
import { apiFetch } from "../lib/fetcher";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type AIAction = {
  id: string;
  campaign_id: string;
  campaign_name: string;
  action_type: "SCALE_BUDGET" | "REDUCE_BUDGET" | "PAUSE_ADS" | "ENABLE_ADS";
  reason: string;
  confidence_score: number;
  suggested_value?: string; // e.g. "₹500 -> ₹1000"
  status: "PENDING" | "APPLIED" | "DISMISSED";
  created_at: string;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function AiActionsPage() {
  const [actions, setActions] = useState<AIAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD ACTIONS
   * ---------------------------------- */
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
        // Fallback for demo/initial phase if endpoint returns 404
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

  /* ----------------------------------
   * HANDLERS
   * ---------------------------------- */
  const handleAction = async (actionId: string, decision: "APPLY" | "DISMISS") => {
    setProcessingId(actionId);
    
    try {
      const endpoint = decision === "APPLY" 
        ? `/api/ai/actions/${actionId}/apply` 
        : `/api/ai/actions/${actionId}/dismiss`;

      const res = await apiFetch(endpoint, {
        method: "POST",
      });

      if (!res.ok) throw new Error("Operation failed");

      toast.success(decision === "APPLY" ? "Action applied successfully" : "Action dismissed");
      
      // Remove from list locally
      setActions((prev) => prev.filter((a) => a.id !== actionId));

    } catch (error) {
      toast.error("Failed to process action");
    } finally {
      setProcessingId(null);
    }
  };

  /* ----------------------------------
   * UI HELPERS
   * ---------------------------------- */
  const getActionIcon = (type: string) => {
    switch (type) {
      case "SCALE_BUDGET": return <TrendingUp className="h-5 w-5 text-green-600" />;
      case "REDUCE_BUDGET": return <TrendingDown className="h-5 w-5 text-orange-600" />;
      case "PAUSE_ADS": return <PauseCircle className="h-5 w-5 text-red-600" />;
      case "ENABLE_ADS": return <PlayCircle className="h-5 w-5 text-blue-600" />;
      default: return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getConfidenceBadge = (score: number) => {
    let colorClass = "bg-gray-100 text-gray-800";
    if (score >= 80) colorClass = "bg-green-100 text-green-800";
    else if (score >= 50) colorClass = "bg-yellow-100 text-yellow-800";
    
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}>
        {score}% Confidence
      </span>
    );
  };

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">AI Recommendations</h1>
        <p className="text-sm text-gray-500">
          Review and apply optimization actions suggested by our AI Engine.
        </p>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-64 text-sm text-gray-500">
          Analyzing campaigns...
        </div>
      )}

      {!loading && actions.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed">
          <CheckCircle className="mx-auto h-10 w-10 text-green-500 mb-3" />
          <h3 className="text-sm font-semibold text-gray-900">All caught up!</h3>
          <p className="mt-1 text-sm text-gray-500">
            No pending actions. Your campaigns are running optimally.
          </p>
        </div>
      )}

      <div className="grid gap-4">
        {actions.map((action) => (
          <div 
            key={action.id} 
            className="bg-white border rounded-lg p-5 shadow-sm transition hover:shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div className="flex items-start gap-4">
              <div className="p-2 bg-gray-50 rounded-lg shrink-0">
                {getActionIcon(action.action_type)}
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-gray-900">
                    {action.action_type.replace(/_/g, " ")}
                  </h3>
                  {getConfidenceBadge(action.confidence_score)}
                </div>
                
                <p className="text-sm text-gray-600">
                  Campaign: <span className="font-medium">{action.campaign_name}</span>
                </p>
                
                <p className="text-sm text-gray-500 max-w-2xl">
                  {action.reason}
                  {action.suggested_value && (
                    <span className="block mt-1 font-medium text-gray-700">
                      Suggestion: {action.suggested_value}
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-100">
              <button
                onClick={() => handleAction(action.id, "DISMISS")}
                disabled={processingId === action.id}
                className="flex-1 sm:flex-none px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Dismiss
              </button>
              
              <button
                onClick={() => handleAction(action.id, "APPLY")}
                disabled={processingId === action.id}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {processingId === action.id ? "Processing..." : "Apply Action"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
