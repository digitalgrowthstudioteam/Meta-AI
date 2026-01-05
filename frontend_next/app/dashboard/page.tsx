"use client";

import { useEffect, useState } from "react";

/**
 * FINAL Dashboard Contract (LOCKED)
 */
type DashboardSummary = {
  meta_connected?: boolean;

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
  // LOAD AD ACCOUNTS
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
      // silent
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
  const totalCampaigns =
    selectedAccountId ? data?.campaigns?.total ?? 0 : "—";
  const aiActive = data?.campaigns?.ai_active ?? 0;
  const aiLimit = data?.campaigns?.ai_limit ?? 0;

  if (loading) {
    return <div className="text-sm text-gray-500">Loading dashboard…</div>;
  }

  // --------------------------------------------------
  // FIRST TIME — META NOT CONNECTED
  // --------------------------------------------------
  if (!metaConnected) {
    return (
      <div className="space-y-6 max-w-2xl">
        <h1 className="text-xl font-semibold">
          Connect your Meta Ads account
        </h1>
        <p className="text-sm text-gray-600">
          We only read data. Your campaigns are never modified.
        </p>
        <button onClick={connectMeta} className="btn-primary">
          Connect Meta Ads
        </button>
      </div>
    );
  }

  // --------------------------------------------------
  // META CONNECTED BUT NO CAMPAIGNS
  // --------------------------------------------------
  if (metaConnected && adAccountsList.length === 0) {
    return (
      <div className="space-y-6 max-w-2xl">
        <h1 className="text-xl font-semibold">Sync Ad Accounts</h1>
        <p className="text-sm text-gray-600">
          Fetch ad accounts to load campaigns.
        </p>
        <button
          onClick={syncAdAccounts}
          disabled={syncing}
          className="btn-primary disabled:opacity-60"
        >
          {syncing ? "Syncing…" : "Sync Ad Accounts"}
        </button>
      </div>
    );
  }

  // --------------------------------------------------
  // NORMAL DASHBOARD
  // --------------------------------------------------
  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-gray-500">
            Overview of your Meta Ads and AI activity
          </p>
        </div>

        <div className="text-xs">
          Meta account:{" "}
          <span className="font-medium text-green-600">Connected</span>
        </div>
      </div>

      {/* AD ACCOUNT SELECT */}
      {adAccountsList.length > 0 && (
        <div className="surface p-4 flex flex-col sm:flex-row gap-3">
          <div className="text-sm text-gray-600">Ad Account:</div>
          <select
            className="border rounded px-2 py-1 text-sm max-w-xs"
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
          hint="Plan limit"
        />

        <KpiCard
          label="Account Status"
          value="Connected"
          hint="Meta Ads"
        />
      </div>

      <div className="text-xs text-gray-400">
        All data is read-only and synced from Meta Ads Manager.
      </div>
    </div>
  );
}

/* -------------------------------------------------- */

function KpiCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint: string;
}) {
  return (
    <div className="surface p-5 space-y-1">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400">{hint}</div>
    </div>
  );
}
