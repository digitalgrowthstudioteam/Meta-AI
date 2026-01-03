"use client";

import { useEffect, useState } from "react";

type DashboardSummary = {
  meta_connected: boolean;
  ad_accounts: number;
  campaigns: number;
  ai_active: number;
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  // --------------------------------------------------
  // LOAD DASHBOARD SUMMARY (SOURCE OF TRUTH)
  // --------------------------------------------------
  useEffect(() => {
    fetch("/api/dashboard/summary", {
      credentials: "include",
    })
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  // --------------------------------------------------
  // CONNECT META
  // --------------------------------------------------
  const connectMeta = async () => {
    const res = await fetch("/meta/connect", {
      credentials: "include",
    });
    const json = await res.json();
    if (json?.redirect_url) {
      window.location.href = json.redirect_url;
    }
  };

  // --------------------------------------------------
  // SYNC AD ACCOUNTS
  // --------------------------------------------------
  const syncAdAccounts = async () => {
    setSyncing(true);
    setSyncResult(null);

    try {
      const res = await fetch("/meta/adaccounts/sync", {
        method: "POST",
        credentials: "include",
      });
      const json = await res.json();
      setSyncResult(
        `Synced ${json.ad_accounts_processed} ad accounts successfully`
      );

      // Refresh dashboard data after sync
      const refreshed = await fetch("/api/dashboard/summary", {
        credentials: "include",
      }).then((r) => r.json());

      setData(refreshed);
    } catch {
      setSyncResult("Sync failed. Please try again.");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="text-sm text-gray-500">
        Loading dashboard…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-sm text-red-600">
        Failed to load dashboard data
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* ================= HEADER ================= */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            Dashboard
          </h1>
          <p className="text-sm text-gray-500">
            Overview of your Meta Ads and AI activity
          </p>
        </div>

        <div className="text-xs">
          Meta account:{" "}
          {data.meta_connected ? (
            <span className="text-green-600 font-medium">
              Connected
            </span>
          ) : (
            <span className="text-red-600 font-medium">
              Not connected
            </span>
          )}
        </div>
      </div>

      {/* ================= META ACTION BAR ================= */}
      <div className="bg-white border border-gray-200 rounded p-4 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Meta Ads connection is required to sync campaigns and enable AI.
        </div>

        <div className="flex gap-3">
          {!data.meta_connected && (
            <button
              onClick={connectMeta}
              className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              Connect Meta
            </button>
          )}

          {data.meta_connected && (
            <button
              onClick={syncAdAccounts}
              disabled={syncing}
              className="px-4 py-2 text-sm rounded border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              {syncing ? "Syncing…" : "Sync Ad Accounts"}
            </button>
          )}
        </div>
      </div>

      {syncResult && (
        <div className="text-sm text-green-600">
          {syncResult}
        </div>
      )}

      {/* ================= KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Ad Accounts"
          value={String(data.ad_accounts)}
          hint="Connected Meta ad accounts"
        />
        <KpiCard
          label="Total Campaigns"
          value={String(data.campaigns)}
          hint="Synced from Meta"
        />
        <KpiCard
          label="AI-Active Campaigns"
          value={String(data.ai_active)}
          hint="Phase 1 = 0"
        />
        <KpiCard
          label="Account Status"
          value={data.meta_connected ? "Connected" : "Disconnected"}
          hint="Meta Ads"
          warning={!data.meta_connected}
        />
      </div>

      {/* ================= FOOTNOTE ================= */}
      <div className="text-xs text-gray-400">
        All data is read-only and synced from Meta Ads Manager.
        Changes are applied directly inside Meta.
      </div>
    </div>
  );
}

/* ===============================
   UI COMPONENTS
=============================== */

function KpiCard({
  label,
  value,
  hint,
  warning,
}: {
  label: string;
  value: string;
  hint: string;
  warning?: boolean;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded p-5 space-y-1">
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
