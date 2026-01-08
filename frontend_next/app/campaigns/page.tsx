"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";

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

type AdAccount = {
  id: string;
  name: string;
  meta_account_id: string;
};

type SessionContext = {
  user: {
    id: string;
    email: string;
    is_admin: boolean;
    is_impersonated: boolean;
  };
  ad_accounts?: AdAccount[];
};

/* -----------------------------------
 * COOKIE HELPERS
 * ----------------------------------- */
const COOKIE_KEY = "selected_ad_account";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? match[2] : null;
}

function setCookie(name: string, value: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${value}; path=/; max-age=31536000`;
}

/* -----------------------------------
 * PAGE
 * ----------------------------------- */
export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [session, setSession] = useState<SessionContext | null>(null);

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
    const res = await fetch("/api/session/context", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setSession(null);
      return;
    }

    const data = await res.json();
    setSession(data);
  };

  /* -----------------------------------
   * DETERMINE SELECTED ACCOUNT
   * ----------------------------------- */
  const getSelectedAccountId = () => {
    const cookieId = getCookie(COOKIE_KEY);
    if (cookieId) return cookieId;

    const first = session?.ad_accounts?.[0]?.id ?? null;
    if (first) setCookie(COOKIE_KEY, first);
    return first;
  };

  /* -----------------------------------
   * LOAD CAMPAIGNS
   * ----------------------------------- */
  const loadCampaigns = async () => {
    const selected = getSelectedAccountId();
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

      const res = await fetch(`/api/campaigns?${params.toString()}`, {
        credentials: "include",
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
    loadCampaigns();
  }, [session, statusFilter, aiFilter, objectiveFilter, page]);

  /* -----------------------------------
   * SWITCH ACCOUNT
   * ----------------------------------- */
  const switchAdAccount = (accountId: string) => {
    setCookie(COOKIE_KEY, accountId);
    setPage(1);
    loadCampaigns();
  };

  /* -----------------------------------
   * SYNC CAMPAIGNS
   * ----------------------------------- */
  const syncCampaigns = async () => {
    const selected = getSelectedAccountId();
    if (!selected) return;

    setSyncing(true);

    await fetch(`/api/campaigns/sync?account_id=${selected}`, {
      method: "POST",
      credentials: "include",
      cache: "no-store",
    });

    await loadCampaigns();
    setSyncing(false);
  };

  /* -----------------------------------
   * TOGGLE AI  (PLAN ENFORCED + UI REVERT)
   * ----------------------------------- */
  const toggleAI = async (campaign: Campaign) => {
    if (togglingId) return;

    const nextValue = !campaign.ai_active;
    setTogglingId(campaign.id);

    // Optimistic UI update
    setCampaigns((prev) =>
      prev.map((c) => (c.id === campaign.id ? { ...c, ai_active: nextValue } : c))
    );

    try {
      const res = await fetch(`/api/campaigns/${campaign.id}/ai-toggle`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: nextValue }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);

        // Revert UI
        setCampaigns((prev) =>
          prev.map((c) => (c.id === campaign.id ? { ...c, ai_active: !nextValue } : c))
        );

        if (res.status === 409 && err?.detail?.message) {
          toast.error(err.detail.message);
        } else {
          toast.error("Action failed");
        }

        return;
      }

      toast.success(nextValue ? "AI activated" : "AI deactivated");

    } catch {
      // Revert UI on unexpected failure
      setCampaigns((prev) =>
        prev.map((c) => (c.id === campaign.id ? { ...c, ai_active: !nextValue } : c))
      );

      toast.error("Action failed");
    } finally {
      setTogglingId(null);
    }
  };

  /* -----------------------------------
   * RENDER
   * ----------------------------------- */
  if (!session?.ad_accounts) return <div>Loading...</div>;

  const selectedId = getSelectedAccountId();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Campaigns</h1>
          <p className="text-sm text-gray-500">
            Active account:{" "}
            <strong>
              {session.ad_accounts.find((a) => a.id === selectedId)?.name}
            </strong>
          </p>
        </div>

        <select
          className="border rounded px-2 py-1 text-sm"
          value={selectedId || ""}
          onChange={(e) => switchAdAccount(e.target.value)}
        >
          {session.ad_accounts.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name}
            </option>
          ))}
        </select>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="PAUSED">Paused</option>
        </select>

        <select
          value={aiFilter}
          onChange={(e) => setAiFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">AI (All)</option>
          <option value="true">AI Active</option>
          <option value="false">AI Inactive</option>
        </select>

        <select
          value={objectiveFilter}
          onChange={(e) => setObjectiveFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Objectives</option>
          <option value="LEAD">Lead Gen</option>
          <option value="SALES">Sales</option>
        </select>

        <button onClick={syncCampaigns} disabled={syncing} className="btn-secondary">
          {syncing ? "Syncing…" : "Sync"}
        </button>
      </div>

      {loading && <div>Loading campaigns…</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && campaigns.length === 0 && <div>No campaigns found</div>}

      {!loading && campaigns.length > 0 && (
        <div className="surface overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="px-4 py-3 text-left">Campaign</th>
                <th className="px-4 py-3 text-left">Objective</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">AI</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3">{c.objective ?? "—"}</td>
                  <td className="px-4 py-3">{c.status}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleAI(c)}
                      disabled={togglingId === c.id}
                      className={`inline-flex h-6 w-11 items-center rounded-full transition ${
                        c.ai_active ? "bg-green-600" : "bg-gray-300"
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 rounded-full bg-white transition ${
                          c.ai_active ? "translate-x-6" : "translate-x-1"
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
