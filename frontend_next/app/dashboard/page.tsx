"use client";

import { useEffect, useState } from "react";

/**
 * FINAL Dashboard Contract (LOCKED)
 */
type DashboardSummary = {
  meta_connected: boolean;
  ad_accounts: number;

  campaigns: {
    total: number;
    ai_active: number;
    ai_limit: number;
  };

  ai: {
    engine_status: "on" | "off";
    last_action_at: string | null;
  };

  subscription: {
    plan: string;
    expires_at: string | null;
    manual_campaign_credits: number;
  };
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // --------------------------------------------------
  // LOAD DASHBOARD SUMMARY (NO CACHE — ALWAYS REAL)
  // --------------------------------------------------
  const loadSummary = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/dashboard/summary", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const json = await res.json();
      setData(json);
    } catch {
      setError("Unable to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

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
      setMessage("Failed to initiate Meta connection");
    }
  };

  // --------------------------------------------------
  // SYNC AD ACCOUNTS
  // --------------------------------------------------
  const syncAdAccounts = async () => {
    setSyncing(true);
    setMessage(null);

    try {
      const res = await fetch("/api/meta/adaccounts/sync", {
        method: "POST",
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const json = await res.json();
      setMessage(`Synced ${json.ad_accounts_processed} ad accounts`);
      await loadSummary();
    } catch {
      setMessage("Ad account sync failed");
    } finally {
      setSyncing(false);
    }
  };

  // --------------------------------------------------
  // UI STATES
  // --------------------------------------------------
  if (loading) {
    return (
      <div className="space-y-4">
        <DevBanner />
        <div className="text-sm text-gray-500">Loading dashboard…</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <DevBanner />
        <div className="empty-state">
          <p className="empty-state-title mb-1">
            Dashboard unavailable
          </p>
          <p className="empty-state-sub">
            {error ?? "Please try again shortly."}
          </p>
        </div>
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
          {data.meta_connected ? (
            <span className="text-green-600 font-medium">Connected</span>
          ) : (
            <span className="text-red-600 font-medium">Not connected</span>
          )}
        </div>
      </div>

      {/* META ACTION BAR */}
      {!data.meta_connected ? (
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
            Meta Ads is connected. You can sync ad accounts anytime.
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

      {message && (
        <div className="text-sm text-green-700">{message}</div>
      )}

      {/* KPI GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Ad Accounts"
          value={data.ad_accounts}
          hint="Connected Meta ad accounts"
        />

        <KpiCard
          label="Total Campaigns"
          value={data.campaigns.total}
          hint="Synced from Meta"
        />

        <KpiCard
          label="AI-Active Campaigns"
          value={`${data.campaigns.ai_active} / ${data.campaigns.ai_limit}`}
          hint="Current plan limit"
        />

        <KpiCard
          label="Account Status"
          value={data.meta_connected ? "Connected" : "Disconnected"}
          hint="Meta Ads"
          warning={!data.meta_connected}
        />
      </div>

      <div className="text-xs text-gray-400">
        All data is read-only and synced from Meta Ads Manager.
      </div>
    </div>
  );
}

/* -------------------------------------------------- */
/* COMPONENTS */
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
