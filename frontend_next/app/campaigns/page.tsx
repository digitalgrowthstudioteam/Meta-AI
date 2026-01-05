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
  created_at?: string;

  category?: string | null;
  category_confidence?: number | null;
  category_source?: string | null;
};

type AdAccount = {
  id: string;
  name: string;
  is_selected: boolean;
};

/* -----------------------------------
 * PAGE
 * ----------------------------------- */
export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metaConnected, setMetaConnected] = useState<boolean | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  /* Filters */
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);
  const [selectedAdAccount, setSelectedAdAccount] = useState<string>("");

  const [statusFilter, setStatusFilter] = useState("");
  const [aiFilter, setAiFilter] = useState("");
  const [objectiveFilter, setObjectiveFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

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
      });
      if (!res.ok) return;

      const data = await res.json();
      setAdAccounts(data ?? []);

      const selected = data?.find((a: AdAccount) => a.is_selected);
      if (selected) setSelectedAdAccount(selected.id);
    } catch {}
  };

  /* -----------------------------------
   * LOAD CAMPAIGNS
   * ----------------------------------- */
  const loadCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });

      if (selectedAdAccount) params.append("ad_account_id", selectedAdAccount);
      if (statusFilter) params.append("status", statusFilter);
      if (aiFilter) params.append("ai_active", aiFilter);
      if (objectiveFilter) params.append("objective", objectiveFilter);
      if (dateFrom) params.append("from", dateFrom);
      if (dateTo) params.append("to", dateTo);

      const res = await fetch(`/api/campaigns?${params.toString()}`, {
        credentials: "include",
      });

      if (res.status === 409) {
        setCampaigns([]);
        setMetaConnected(false);
        return;
      }

      if (!res.ok) throw new Error();

      const data = await res.json();
      setCampaigns(Array.isArray(data) ? data : []);
      setMetaConnected(true);
    } catch {
      setError("Unable to load campaigns.");
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
    dateFrom,
    dateTo,
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
    await fetch("/api/campaigns/sync", {
      method: "POST",
      credentials: "include",
    });
    loadCampaigns();
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
      alert("Unable to change AI state. Check plan limits.");
    } finally {
      setTogglingId(null);
    }
  };

  /* -----------------------------------
   * RENDER
   * ----------------------------------- */
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Campaigns</h1>
        <p className="text-sm text-gray-500">
          Synced from Meta Ads Manager · Read-only
        </p>
      </div>

      {/* FILTER BAR */}
      <div className="surface p-4 grid grid-cols-2 lg:grid-cols-6 gap-3 text-sm">
        <select
          value={selectedAdAccount}
          onChange={(e) => setSelectedAdAccount(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All Ad Accounts</option>
          {adAccounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
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

        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="border rounded px-2 py-1"
        />

        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="border rounded px-2 py-1"
        />
      </div>

      {/* PAGINATION */}
      <div className="flex justify-between items-center text-sm">
        <select
          value={pageSize}
          onChange={(e) => {
            setPageSize(Number(e.target.value));
            setPage(1);
          }}
          className="border rounded px-2 py-1"
        >
          {[10, 20, 50, 100].map((n) => (
            <option key={n} value={n}>
              {n} per page
            </option>
          ))}
        </select>

        <div className="flex gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="btn-secondary"
          >
            Prev
          </button>
          <button
            onClick={() => setPage((p) => p + 1)}
            className="btn-secondary"
          >
            Next
          </button>
        </div>
      </div>

      {/* STATES */}
      {loading && <div>Loading campaigns…</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && metaConnected === false && (
        <div className="empty-state">
          <p className="empty-state-title mb-2">
            Connect your Meta Ads account
          </p>
          <button onClick={connectMeta} className="btn-primary">
            Connect Meta Ads
          </button>
        </div>
      )}

      {!loading && campaigns.length === 0 && metaConnected && (
        <div className="empty-state">
          <p className="empty-state-title mb-2">No campaigns found</p>
          <button onClick={syncCampaigns} className="btn-secondary">
            Sync Campaigns
          </button>
        </div>
      )}

      {/* TABLE */}
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
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                        c.ai_active ? "bg-green-600" : "bg-gray-300"
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
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
