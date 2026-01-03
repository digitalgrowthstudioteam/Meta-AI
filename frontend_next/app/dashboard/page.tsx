"use client";

import { useEffect, useState } from "react";

/**
 * FINAL Dashboard Contract (future-proof)
 * Backend may return partial data in Phase-1
 */
type DashboardSummary = {
  meta_connected: boolean;
  ad_accounts: number;

  campaigns?: {
    total: number;
    ai_active: number;
    ai_limit: number;
  };

  ai?: {
    engine_status: "on" | "off";
    last_action_at: string | null;
  };

  subscription?: {
    plan: string;
    expires_at: string;
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
  // LOAD DASHBOARD SUMMARY (READ-ONLY)
  // --------------------------------------------------
  const loadSummary = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/dashboard/summary", {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error("Dashboard API failed");
      }

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
      });

      if (!res.ok) {
        throw new Error();
      }

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
        <div className="text-sm text-red-600">
          {error ?? "Dashboard unavailable"}
        </div>
      </div>
    );
  }

  const campaignsTotal = data.campaigns?.total ?? 0;
  const aiActive = data.campaigns?.ai_active ?? 0;
  const aiLimit = data.campaigns?.ai_limit ?? 0;

  return (
    <div className="space-y-8">
      <DevBanner />

      {/* ================= HEADER ================= */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500">
            Command overview of Meta Ads & AI status
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

      {/* ================= META ACTION BAR ================= */}
      <div className="bg-white border border-gray-200 rounded p-4 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Meta connection is required to sync campaigns and enable AI.
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

      {message && <div className="text-sm text-green-600">{message}</div>}

      {/* ================= KPI GRID ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Ad Accounts"
          value={String(data.ad_accounts)}
          hint="Linked Meta ad accounts"
        />

        <KpiCard
          label="Total Campaigns"
          value={String(campaignsTotal)}
          hint="Fetched from Meta"
        />

        <KpiCard
          label="AI-Active Campaigns"
          value={`${aiActive} / ${aiLimit}`}
          hint="Plan enforced"
        />

        <KpiCard
          label="AI Engine"
          value={data.ai?.engine_status ?? "off"}
          hint="Global AI status"
          warning={data.ai?.engine_status !== "on"}
        />
      </div>

      <div className="text-xs text-gray-400">
        Dashboard is read-only. Performance analytics are available in Reports.
      </div>
    </div>
  );
}

/* -------------------------------------------------- */
/* COMPONENTS                                         */
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
