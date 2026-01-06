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
  meta_account_id: string;
  account_name: string;
  is_selected: boolean;
};

/* -----------------------------------
 * PAGE
 * ----------------------------------- */
export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);
  const [selectedAdAccount, setSelectedAdAccount] = useState<string>("");

  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
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
  const [pageSize, setPageSize] = useState(10);

  /* -----------------------------------
   * LOAD AD ACCOUNTS
   * ----------------------------------- */
  const loadAdAccounts = async () => {
    try {
      const res = await fetch("/api/meta/adaccounts", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const data = await res.json();
      setAdAccounts(data ?? []);
      setMetaConnected(true);

      const selected = data?.find((a: AdAccount) => a.is_selected);
      if (selected) setSelectedAdAccount(selected.meta_account_id);
    } catch {
      setMetaConnected(false);
    }
  };

  /* -----------------------------------
   * SELECT AD ACCOUNT (SERVER TRUTH)
   * ----------------------------------- */
  const selectAdAccount = async (metaAccountId: string) => {
    setSelectedAdAccount(metaAccountId);

    await fetch(
      `/api/meta/adaccounts/select?meta_ad_account_id=${metaAccountId}`,
      {
        method: "POST",
        credentials: "include",
      }
    );

    await loadCampaigns();
  };

  /* -----------------------------------
   * LOAD CAMPAIGNS
   * ----------------------------------- */
  const loadCampaigns = async () => {
    if (!selectedAdAccount) {
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
        ad_account_id: selectedAdAccount,
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

  useEffect(() => {
    loadAdAccounts();
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [
    selectedAdAccount,
    statusFilter,
    aiFilter,
    objectiveFilter,
    page,
    pageSize,
  ]);

  /* -----------------------------------
   * META CONNECT
   * ----------------------------------- */
  const connectMeta = async () => {
    const res = await fetch("/api/meta/connect", {
      credentials: "include",
    });
    const data = await res.json();
    if (data?.redirect_url) window.location.href = data.redirect_url;
  };

  /* -----------------------------------
   * SYNC CAMPAIGNS
   * ----------------------------------- */
  const syncCampaigns = async () => {
    setSyncing(true);
    await fetch("/api/campaigns/sync", {
      method: "POST",
      credentials: "include",
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
      const res = await fetch(`/api/campaigns/${campaign.id}/ai-toggle`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable: nextValue }),
      });

      if (!res.ok) throw new Error();
    } catch {
      setCampaigns((prev) =>
        prev.map((c) =>
          c.id === campaign.id
            ? { ...c, ai_active: campaign.ai_active }
            : c
        )
      );
      alert("Plan limit reached or action failed");
    } finally {
      setTogglingId(null);
    }
  };

  /* -----------------------------------
   * RENDER
   * ----------------------------------- */
  if (metaConnected === false) {
    return (
      <div className="space-y-4 max-w-xl">
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-600">
          Connect Meta Ads to view campaigns.
        </p>
        <button onClick={connectMeta} className="btn-primary">
          Connect Meta Ads
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-500">
          Synced from Meta Ads Manager · One ad account at a time
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-5 gap-3 text-sm">
        <select
          value={selectedAdAccount}
          onChange={(e) => selectAdAccount(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">Select Ad Account</option>
          {adAccounts.map((a) => (
            <option key={a.id} value={a.meta_account_id}>
              {a.account_name}
            </option>
          ))}
        </select>

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
          disabled={syncing || !selectedAdAccount}
          className="btn-secondary"
        >
          {syncing ? "Syncing…" : "Sync"}
        </button>
      </div>

      {loading && <div>Loading campaigns…</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && campaigns.length === 0 && selectedAdAccount && (
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
