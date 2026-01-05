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
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // -----------------------------
  // LOAD SUMMARY
  // -----------------------------
  const loadSummary = async () => {
    try {
      const res = await fetch("/api/dashboard/summary", {
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) throw new Error();
      const json = await res.json();
      setData(json ?? {});
    } catch {
      setData({});
    }
  };

  // -----------------------------
  // LOAD AD ACCOUNTS
  // -----------------------------
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
    } catch {}
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadSummary();
      await loadAdAccounts();
      setLoading(false);
    })();
  }, []);

  // -----------------------------
  // CONNECT META (REAL)
  // -----------------------------
  const connectMeta = async () => {
    const res = await fetch("/api/meta/connect", {
      credentials: "include",
      cache: "no-store",
    });
    if (!res.ok) return;

    const json = await res.json();
    if (json?.redirect_url) {
      window.location.href = json.redirect_url;
    }
  };

  // -----------------------------
  // SYNC AD ACCOUNTS
  // -----------------------------
  const syncAdAccounts = async () => {
    setSyncing(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/meta/adaccounts/sync", {
        method: "POST",
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) throw new Error();

      await loadAdAccounts();
      await loadSummary();
    } catch {
      setErrorMsg("Failed to sync ad accounts");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-500">Loading dashboard…</div>;
  }

  const metaConnected = Boolean(data?.meta_connected);
  const totalCampaigns = data?.campaigns?.total ?? 0;
  const aiActive = data?.campaigns?.ai_active ?? 0;
  const aiLimit = data?.campaigns?.ai_limit ?? 0;

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Overview of your Meta Ads and AI activity
        </p>
      </div>

      {/* META CONNECTION BLOCK */}
      {!metaConnected ? (
        <div className="bg-white border rounded-lg p-6 max-w-xl">
          <h2 className="font-medium mb-2">
            Connect your Meta Ads account
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Required to fetch ad accounts, campaigns, and AI insights.
            Read-only. Safe.
          </p>
          <button onClick={connectMeta} className="btn-primary">
            Connect Meta Ads Account
          </button>
        </div>
      ) : (
        <div className="bg-white border rounded-lg p-6 max-w-xl">
          <h2 className="font-medium mb-2">Sync Ad Accounts</h2>
          <p className="text-sm text-gray-600 mb-4">
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
      )}

      {errorMsg && <div className="text-sm text-red-600">{errorMsg}</div>}

      {/* KPI GRID (ONLY IF META CONNECTED) */}
      {metaConnected && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
            value="Connected"
            hint="Meta Ads"
          />
        </div>
      )}
    </div>
  );
}

/* ----------------------------- */

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
    <div className="bg-white border rounded-lg p-5 space-y-1">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
      <div className="text-xs text-gray-400">{hint}</div>
    </div>
  );
}
