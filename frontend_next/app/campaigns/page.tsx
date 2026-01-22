"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { apiFetch } from "../lib/fetcher";

/* -----------------------------------
 * TYPES
 * ----------------------------------- */
type Campaign = {
  id: string;
  name: string;
  status: string;
  objective?: string;
  ai_active?: boolean;
};

type Usage = {
  campaigns_used: number;
  campaigns_limit: number;
  ai_campaigns_used: number;
  ai_campaigns_limit: number;
};

type AdAccount = {
  id: string;
  name: string;
  meta_account_id: string;
};

type SessionContext = {
  user?: {
    id: string;
    email: string;
    is_admin: boolean;
    is_impersonated: boolean;
  } | null;
  ad_accounts?: AdAccount[];
  active_ad_account_id?: string | null;
};

/* -----------------------------------
 * PAGE
 * ----------------------------------- */
export default function CampaignsPage() {
  const [session, setSession] = useState<SessionContext | null>(null);

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);

  const [loadingUsage, setLoadingUsage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  /* Filters */
  const [statusFilter, setStatusFilter] = useState("");
  const [aiFilter, setAiFilter] = useState("");
  const [objectiveFilter, setObjectiveFilter] = useState("");

  /* Pagination */
  const [page, setPage] = useState(1);
  const pageSize = 10;

  /* -----------------------------------
   * LOAD SESSION CONTEXT
   * ----------------------------------- */
  const loadSession = async () => {
    try {
      const res = await apiFetch("/api/session/context", { cache: "no-store" });
      if (!res.ok) {
        setSession(null);
        return;
      }
      setSession(await res.json());
    } catch {
      setSession(null);
    }
  };

  /* -----------------------------------
   * LOAD USAGE
   * ----------------------------------- */
  const loadUsage = async () => {
    setLoadingUsage(true);
    try {
      const res = await apiFetch("/api/campaigns/usage", { cache: "no-store" });
      if (res.ok) setUsage(await res.json());
    } finally {
      setLoadingUsage(false);
    }
  };

  /* -----------------------------------
   * LOAD CAMPAIGNS
   * ----------------------------------- */
  const loadCampaigns = async () => {
    const selected = session?.active_ad_account_id;
    if (!selected) return;

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        account_id: selected,
        page: String(page),
        page_size: String(pageSize),
      });

      if (statusFilter) params.append("status", statusFilter);
      if (aiFilter) params.append("ai_active", aiFilter);
      if (objectiveFilter) params.append("objective", objectiveFilter);

      const res = await apiFetch(`/api/campaigns?${params.toString()}`, {
        cache: "no-store",
      });

      if (!res.ok) throw new Error();
      const data = await res.json();
      setCampaigns(Array.isArray(data) ? data : []);
    } catch {
      setError("Unable to load campaigns");
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  };

  /* -----------------------------------
   * EFFECTS
   * ----------------------------------- */
  useEffect(() => {
    loadSession();
  }, []);

  useEffect(() => {
    if (!session) return;
    loadUsage();
    loadCampaigns();
  }, [session, statusFilter, aiFilter, objectiveFilter, page]);

  /* -----------------------------------
   * SWITCH ACCOUNT (COOKIE-BASED)
   * ----------------------------------- */
  const switchAdAccount = async (accountId: string) => {
    try {
      await apiFetch(`/api/session/set-active`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_id: accountId }),
      });
      await loadSession();
      setPage(1);
    } catch {
      toast.error("Failed to switch account");
    }
  };

  /* -----------------------------------
   * SYNC CAMPAIGNS — COOKIE ONLY
   * ----------------------------------- */
  const syncCampaigns = async () => {
    setSyncing(true);
    try {
      await apiFetch(`/api/campaigns/sync`, {
        method: "POST",
        cache: "no-store",
      });
      await loadCampaigns();
      await loadUsage();
      toast.success("Campaigns synced successfully");
    } catch {
      toast.error("Failed to sync campaigns");
    } finally {
      setSyncing(false);
    }
  };

  /* -----------------------------------
   * TOGGLE AI
   * ----------------------------------- */
  const toggleAI = async (campaign: Campaign) => {
    if (togglingId) return;
    const nextValue = !campaign.ai_active;
    setTogglingId(campaign.id);

    setCampaigns((prev) =>
      prev.map((c) =>
        c.id === campaign.id ? { ...c, ai_active: nextValue } : c
      )
    );

    try {
      const res = await apiFetch(`/api/campaigns/${campaign.id}/ai-toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: nextValue }),
      });

      if (!res.ok) {
        setCampaigns((prev) =>
          prev.map((c) =>
            c.id === campaign.id ? { ...c, ai_active: !nextValue } : c
          )
        );

        let msg = "Action failed";
        try {
          const body = await res.json();
          if (body.detail?.message) msg = body.detail.message;
          else if (body.detail) msg = body.detail;
        } catch {}

        toast.error(msg);
        return;
      }

      await loadUsage();
      toast.success(nextValue ? "AI activated" : "AI deactivated");
    } catch {
      setCampaigns((prev) =>
        prev.map((c) =>
          c.id === campaign.id ? { ...c, ai_active: !nextValue } : c
        )
      );
      toast.error("Network error");
    } finally {
      setTogglingId(null);
    }
  };

  /* -----------------------------------
   * HELPERS
   * ----------------------------------- */
  const formatLimit = (used: number, limit: number) => {
    if (!limit || limit === 0) return `${used} / ∞`;
    return `${used} / ${limit}`;
  };

  const percent = (used: number, limit: number) => {
    if (!limit || limit === 0) return 0;
    return Math.min(Math.round((used / limit) * 100), 100);
  };

  /* -----------------------------------
   * RENDER
   * ----------------------------------- */
  if (!session?.ad_accounts) {
    return (
      <div className="p-6 text-sm text-gray-500">
        Loading context...
      </div>
    );
  }

  const selectedId = session.active_ad_account_id;

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-6 py-10">
      {/* HEADER */}
      <div>
        <h1 className="text-lg font-semibold text-gray-900">Campaigns</h1>
        <p className="text-xs text-gray-500 mt-1">
          Active Ad Account:{" "}
          <span className="font-medium text-gray-900">
            {session.ad_accounts.find((a) => a.id === selectedId)?.name || "None"}
          </span>
        </p>
      </div>

      {/* USAGE SECTION */}
      {usage && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <p className="text-xs text-gray-500">Campaigns</p>
            <p className="text-base font-medium text-gray-900">
              {formatLimit(usage.campaigns_used, usage.campaigns_limit)}
            </p>
            <div className="w-full h-2 rounded bg-gray-200 mt-2">
              <div
                className="h-2 rounded bg-blue-600"
                style={{
                  width: `${percent(
                    usage.campaigns_used,
                    usage.campaigns_limit
                  )}%`,
                }}
              />
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <p className="text-xs text-gray-500">AI Campaigns</p>
            <p className="text-base font-medium text-gray-900">
              {formatLimit(usage.ai_campaigns_used, usage.ai_campaigns_limit)}
            </p>
            <div className="w-full h-2 rounded bg-gray-200 mt-2">
              <div
                className="h-2 rounded bg-blue-600"
                style={{
                  width: `${percent(
                    usage.ai_campaigns_used,
                    usage.ai_campaigns_limit
                  )}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* FILTER PANEL */}
      <div className="bg-white p-4 rounded-lg border shadow-sm grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded border-gray-300 text-gray-900 shadow-sm focus:ring-blue-600 focus:border-blue-600"
        >
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="PAUSED">Paused</option>
        </select>

        <select
          value={aiFilter}
          onChange={(e) => setAiFilter(e.target.value)}
          className="rounded border-gray-300 text-gray-900 shadow-sm focus:ring-blue-600 focus:border-blue-600"
        >
          <option value="">AI (All)</option>
          <option value="true">AI Active</option>
          <option value="false">AI Inactive</option>
        </select>

        <select
          value={objectiveFilter}
          onChange={(e) => setObjectiveFilter(e.target.value)}
          className="rounded border-gray-300 text-gray-900 shadow-sm focus:ring-blue-600 focus:border-blue-600"
        >
          <option value="">All Objectives</option>
          <option value="LEAD">Lead Gen</option>
          <option value="SALES">Sales</option>
        </select>

        <select
          value={selectedId || ""}
          onChange={(e) => switchAdAccount(e.target.value)}
          className="rounded border-gray-300 text-gray-900 shadow-sm focus:ring-blue-600 focus:border-blue-600"
        >
          {session.ad_accounts.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name}
            </option>
          ))}
        </select>

        <button
          onClick={syncCampaigns}
          disabled={syncing}
          className="rounded bg-white px-3 py-2 font-semibold shadow-sm ring-1 ring-gray-300 hover:bg-gray-50 text-gray-900 disabled:opacity-50"
        >
          {syncing ? "Syncing…" : "Sync"}
        </button>
      </div>

      {/* STATUS MESSAGES */}
      {loading && <div className="text-sm text-gray-500">Loading campaigns…</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}

      {/* EMPTY STATE */}
      {!loading && campaigns.length === 0 && (
        <div className="text-center py-16 bg-white rounded-lg border border-dashed shadow-sm">
          <p className="text-sm text-gray-500">No campaigns found.</p>
        </div>
      )}

      {/* DATA TABLE */}
      {!loading && campaigns.length > 0 && (
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-300 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left font-semibold text-gray-900 sm:pl-6">
                  Campaign
                </th>
                <th className="px-3 py-3.5 text-left font-semibold text-gray-900">
                  Objective
                </th>
                <th className="px-3 py-3.5 text-left font-semibold text-gray-900">
                  Status
                </th>
                <th className="px-3 py-3.5 text-left font-semibold text-gray-900">
                  AI Optimization
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {campaigns.map((c) => (
                <tr key={c.id}>
                  <td className="whitespace-nowrap py-4 pl-4 pr-3 font-medium text-gray-900 sm:pl-6">
                    {c.name}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-gray-500">
                    {c.objective ?? "—"}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4">
                    <span
                      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                        c.status === "ACTIVE"
                          ? "bg-green-50 text-green-700 ring-green-600/20"
                          : "bg-yellow-50 text-yellow-800 ring-yellow-600/20"
                      }`}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-4">
                    <button
                      onClick={() => toggleAI(c)}
                      disabled={togglingId === c.id}
                      className={`relative inline-flex h-6 w-11 rounded-full transition-colors ring-1 ring-gray-300 focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 ${
                        c.ai_active ? "bg-blue-600" : "bg-gray-200"
                      } ${togglingId === c.id ? "opacity-50 cursor-wait" : ""}`}
                    >
                      <span className="sr-only">Toggle AI</span>
                      <span
                        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
                          c.ai_active ? "translate-x-5" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
