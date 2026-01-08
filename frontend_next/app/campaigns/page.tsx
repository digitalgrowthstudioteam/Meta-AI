"use client";

import { useEffect, useState } from "react";

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
  is_selected?: boolean;
};

type SessionContext = {
  user: {
    id: string;
    email: string;
    is_admin: boolean;
    is_impersonated: boolean;
  };
  ad_account: AdAccount | null; // backward compat
  ad_accounts?: AdAccount[]; // new
  active_ad_account_id?: string; // new
};

/* -----------------------------------
 * PAGE
 * ----------------------------------- */
export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [session, setSession] = useState<SessionContext | null>(null);

  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  /* Filters */
  const [statusFilter, setStatusFilter] = useState("");
  const [aiFilter, setAiFilter] = useState("");
  const [objectiveFilter, setObjectiveFilter] = useState("");

  /* Pagination */
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  /* -----------------------------------
   * LOAD SESSION CONTEXT (SINGLE SOURCE)
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

    // backward compatibility fallback
    if (!data.ad_account && data.ad_accounts && data.active_ad_account_id) {
      const active = data.ad_accounts.find(
        (a: any) => a.id === data.active_ad_account_id
      );
      if (active) data.ad_account = active;
    }

    setSession(data);
  };

  /* -----------------------------------
   * LOAD CAMPAIGNS (STRICT CONTEXT)
   * ----------------------------------- */
  const loadCampaigns = async () => {
    if (!session?.ad_account) {
      setCampaigns([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });

      if (statusFilter) params.append("status", statusFilter);
      if (aiFilter) params.append("ai_active", aiFilter);
      if (objectiveFilter) params.append("objective", objectiveFilter);

      const res = await fetch(`/api/campaigns?${params}`, {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const data = await res.json();
      setCampaigns(Array.isArray(data) ? data : []);
    } catch {
      setError("Unable to load campaigns");
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
    loadCampaigns();
  }, [
    session?.ad_account?.id,
    statusFilter,
    aiFilter,
    objectiveFilter,
    page,
  ]);

  /* -----------------------------------
   * META CONNECT
   * ----------------------------------- */
  const connectMeta = async () => {
    const res = await fetch("/api/meta/connect", {
      credentials: "include",
      cache: "no-store",
    });

    const data = await res.json();
    if (data?.redirect_url) window.location.href = data.redirect_url;
  };

  /* -----------------------------------
   * SWITCH ACTIVE ACCOUNT (NEW)
   * ----------------------------------- */
  const switchAdAccount = async (accountId: string) => {
    await fetch("/api/session/set-active", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: accountId }),
    });

    await loadSession();
    await loadCampaigns();
  };

  /* -----------------------------------
   * SYNC CAMPAIGNS
   * ----------------------------------- */
  const syncCampaigns = async () => {
    setSyncing(true);
    await fetch("/api/campaigns/sync", {
      method: "POST",
      credentials: "include",
      cache: "no-store",
    });
    await loadCampaigns();
    setSyncing(false);
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
      const res = await fetch(
        `/api/campaigns/${campaign.id}/ai-toggle`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enable: nextValue }),
        }
      );

      if (!res.ok) throw new Error();
    } catch {
      setCampaigns((prev) =>
        prev.map((c) =>
          c.id === campaign.id
            ? { ...c, ai_active: campaign.ai_active }
            : c
        )
      );
      alert("Action failed");
    } finally {
      setTogglingId(null);
    }
  };

  /* -----------------------------------
   * RENDER
   * ----------------------------------- */
  if (!session?.ad_account) {
    return (
      <div className="space-y-4 max-w-xl">
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-600">
          Connect Meta Ads and select an ad account.
        </p>
        <button onClick={connectMeta} className="btn-primary">
          Connect Meta Ads
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Campaigns</h1>
          <p className="text-sm text-gray-500">
            Active account: <strong>{session.ad_account.name}</strong>
          </p>
        </div>

        {/* NEW ACCOUNT SWITCHER */}
        {session.ad_accounts && session.ad_accounts.length > 1 && (
          <select
            className="border rounded px-2 py-1 text-sm"
            value={session.ad_account.id}
            onChange={(e) => switchAdAccount(e.target.value)}
          >
            {session.ad_accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
          </select>
        )}
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
          <option value="LEAD">Leads</option>
          <option value="SALES">Sales</option>
        </select>

        <button
          onClick={syncCampaigns}
          disabled={syncing}
          className="btn-secondary"
        >
          {syncing ? "Syncing…" : "Sync"}
        </button>
      </div>

      {loading && <div>Loading campaigns…</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && campaigns.length === 0 && (
        <div className="empty-state">
          <p className="empty-state-title mb-2">No campaigns found</p>
        </div>
      )}

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
                          c.ai_active
                            ? "translate-x-6"
                            : "translate-x-1"
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
