"use client";

import { useEffect, useState } from "react";

/**
 * FINAL Dashboard Contract (LOCKED)
 */
type DashboardSummary = {
  meta_connected?: boolean;
  ad_accounts?: number;

  campaigns?: {
    total?: number;
    ai_active?: number;
    ai_limit?: number;
  };
};

type AdAccount = {
  id: string;
  name: string;
  meta_account_id: string;
  is_selected: boolean;
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [adAccountsList, setAdAccountsList] = useState<AdAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // --------------------------------------------------
  // LOAD DASHBOARD SUMMARY
  // --------------------------------------------------
  const loadSummary = async () => {
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/dashboard/summary", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();
      const json = await res.json();
      setData(json ?? {});
    } catch {
      setErrorMsg("Unable to load dashboard data");
      setData({});
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // LOAD AD ACCOUNTS (FILTER)
  // --------------------------------------------------
  const loadAdAccounts = async () => {
    try {
      const res = await fetch("/api/meta/adaccounts", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) return;

      const json = await res.json();
      setAdAccountsList(json ?? []);

      const selected = json?.find((a: AdAccount) => a.is_selected);
      if (selected) setSelectedAccountId(selected.id);
    } catch {
      // Silent fail — dashboard still works
    }
  };

  useEffect(() => {
    loadSummary();
    loadAdAccounts();
  }, []);

  // --------------------------------------------------
  // SWITCH AD ACCOUNT
  // --------------------------------------------------
  const switchAdAccount = async (accountId: string) => {
    setSelectedAccountId(accountId);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/meta/adaccounts/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ ad_account_id: accountId }),
      });

      if (!res.ok) throw new Error();

      await loadSummary();
      setSuccessMsg("Ad account switched");
    } catch {
      setErrorMsg("Failed to switch ad account");
    }
  };

  // --------------------------------------------------
  // META CONNECT
  // --------------------------------------------------
  const connectMeta = async () => {
    try {
      const res = await fetch("/api/meta/connect", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) return;

      const json = await res.json();
      if (json?.redirect_url) {
        window.location.href = json.redirect_url;
      }
    } catch {
      setErrorMsg("Failed to initiate Meta connection");
    }
  };

  // --------------------------------------------------
  // SYNC AD ACCOUNTS
  // --------------------------------------------------
  const syncAdAccounts = async () => {
    setSyncing(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/meta/adaccounts/sync", {
        method: "POST",
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const json = await res.json();
      setSuccessMsg(
        `Synced ${json?.ad_accounts_processed ?? 0} ad accounts`
      );
      await loadAdAccounts();
      await loadSummary();
    } catch {
      setErrorMsg("Ad account sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const metaConnected = Boolean(data?.meta_connected);
  const totalCampaigns = data?.campaigns?.total ?? 0;
  const aiActive = data?.campaigns?.ai_active ?? 0;
  const aiLimit = data?.campaigns?.ai_limit ?? 0;

  if (loading) {
    return (
      <div className="space-y-4">
        <DevBanner />
        <div className="text-sm text-gray-500">Loading dashboard…</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <DevBanner />

      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-gray-500">
            Overview of your Meta Ads and AI activity
          </p>
        </div>

        <div className="text-xs">
          Meta account:{" "}
          {metaConnected ? (
            <span className="text-green-600 font-medium">Connected</span>
          ) : (
            <span className="text-red-600 font-medium">Not connected</span>
          )}
        </div>
      </div>

      {/* FILTER BAR */}
      {metaConnected && adAccountsList.length > 0 && (
        <div className="surface p-4 flex items-center gap-4">
          <div className="text-sm text-gray-600">Ad Account:</div>
          <select
            className="border rounded px-2 py-1 text-sm"
            value={selectedAccountId ?? ""}
            onChange={(e) => switchAdAccount(e.target.value)}
          >
            {adAccountsList.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* META ACTION BAR */}
      {!metaConnected ? (
        <div className="empty-state">
          <p className="empty-state-title mb-2">
            Connect your Meta Ads account
          </p>
          <p className="empty-state-sub mb-4">
            Meta connection is required to sync campaigns and enable AI features.
          </p>
          <button onClick={connectMeta} className="btn-primary">
            Connect Meta Ads
          </button>
        </div>
      ) : (
        <div className="surface flex items-center justify-between p-4">
          <div className="text-sm text-gray-600">
            Meta Ads is connected. Sync ad accounts anytime.
          </div>
          <button
            onClick={syncAdAccounts}
            disabled={syncing}
            className="btn-secondary disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync Ad Accounts"}
          </button>
        </div>
      )}

      {successMsg && (
        <div className="text-sm text-green-700">{successMsg}</div>
      )}
      {errorMsg && (
        <div className="text-sm text-red-600">{errorMsg}</div>
      )}

      {/* KPI GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Campaigns"
          value={totalCampaigns}
          hint="Selected ad account"
        />

        <KpiCard
          label="AI-Active Campaigns"
          value={`${aiActive} / ${aiLimit}`}
          hint="Current plan limit"
        />

        <KpiCard
          label="Account Status"
          value={metaConnected ? "Connected" : "Disconnected"}
          hint="Meta Ads"
          warning={!metaConnected}
        />
      </div>

      <div className="text-xs text-gray-400">
        All data is read-only and synced from Meta Ads Manager.
      </div>
    </div>
  );
}

/* -------------------------------------------------- */

function DevBanner() {
  return (
    <div className="text-xs bg-yellow-50 border border-yellow-200 rounded px-3 py-2 text-yellow-800">
      Meta Ads AI • Development Mode | Auth: Disabled
    </div>
  );
}

function KpiCard({
  label,
  value,
  hint,
  warning,
}: {
  label: string;
  value: string | number;
  hint: string;
  warning?: boolean;
}) {
  return (
    <div className="surface p-5 space-y-1">
      <div className="text-xs text-gray-500">{label}</div>
      <div
        className={`text-xl font-semibold ${
          warning ? "text-red-600" : "text-gray-900"
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-gray-400">{hint}</div>
    </div>
  );
}
