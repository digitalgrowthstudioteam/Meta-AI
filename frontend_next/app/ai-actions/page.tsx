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
// FIXED: Changed from "@/lib/fetcher" to relative path
import { apiFetch } from "../lib/fetcher";

// ... (Keep the rest of the file exactly as it is, just change the import at the top) ...

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
      const endpoint = decision === "APPLY" 
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
      case "SCALE_BUDGET": return <TrendingUp className="h-5 w-5 text-green-600" />;
      case "REDUCE_BUDGET": return <TrendingDown className="h-5 w-5 text-orange-600" />;
      case "PAUSE_ADS": return <PauseCircle className="h-5 w-5 text-red-600" />;
      case "ENABLE_ADS": return <PlayCircle className="h-5 w-5 text-blue-600" />;
      default: return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">AI Recommendations</h1>
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : actions.length === 0 ? (
        <div className="text-center py-12 border rounded-lg">
          <CheckCircle className="mx-auto h-10 w-10 text-green-500 mb-2" />
          <h3>All caught up!</h3>
        </div>
      ) : (
        <div className="grid gap-4">
          {actions.map((action) => (
            <div key={action.id} className="bg-white border p-4 rounded-lg flex justify-between items-center">
              <div className="flex gap-4">
                <div className="p-2 bg-gray-50 rounded">{getActionIcon(action.action_type)}</div>
                <div>
                  <h3 className="font-medium">{action.action_type}</h3>
                  <p className="text-sm text-gray-500">{action.reason}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleAction(action.id, "DISMISS")} disabled={!!processingId} className="px-3 py-1 border rounded text-sm">Dismiss</button>
                <button onClick={() => handleAction(action.id, "APPLY")} disabled={!!processingId} className="px-3 py-1 bg-indigo-600 text-white rounded text-sm">Apply</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
