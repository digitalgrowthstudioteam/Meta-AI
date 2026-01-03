"use client";

import { useEffect, useState } from "react";

type MetaStatus = "unknown" | "connected" | "disconnected";

export default function DashboardPage() {
  const [metaStatus, setMetaStatus] = useState<MetaStatus>("unknown");
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  // --------------------------------------------------
  // CHECK META CONNECTION (DERIVED FROM TOKEN PRESENCE)
  // --------------------------------------------------
  useEffect(() => {
    fetch("/meta/connect", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.redirect_url) {
          setMetaStatus("disconnected");
        } else {
          setMetaStatus("connected");
        }
      })
      .catch(() => setMetaStatus("disconnected"));
  }, []);

  // --------------------------------------------------
  // CONNECT META
  // --------------------------------------------------
  const connectMeta = async () => {
    const res = await fetch("/meta/connect", {
      credentials: "include",
    });
    const data = await res.json();
    if (data?.redirect_url) {
      window.location.href = data.redirect_url;
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
      const data = await res.json();
      setSyncResult(
        `Synced ${data.ad_accounts_processed} ad accounts successfully`
      );
    } catch {
      setSyncResult("Sync failed. Please try again.");
    } finally {
      setSyncing(false);
    }
  };

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

        <div className="text-xs text-gray-500">
          Meta account:{" "}
          {metaStatus === "connected" ? (
            <span className="text-green-600 font-medium">
              Connected
            </span>
          ) : metaStatus === "disconnected" ? (
            <span className="text-red-600 font-medium">
              Not connected
            </span>
          ) : (
            "Checking…"
          )}
        </div>
      </div>

      {/* ================= META ACTION BAR ================= */}
      <div className="bg-white border border-gray-200 rounded p-4 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Meta Ads connection is required to sync campaigns and enable AI.
        </div>

        <div className="flex gap-3">
          {metaStatus === "disconnected" && (
            <button
              onClick={connectMeta}
              className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              Connect Meta
            </button>
          )}

          {metaStatus === "connected" && (
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
        <KpiCard label="Total Campaigns" value="—" hint="Synced from Meta" />
        <KpiCard
          label="AI-Active Campaigns"
          value="—"
          hint="Counts toward your plan"
        />
        <KpiCard
          label="Latest AI Action"
          value="—"
          hint="Most recent recommendation"
        />
        <KpiCard
          label="Account Status"
          value={metaStatus === "connected" ? "Connected" : "Disconnected"}
          hint="Meta Ads account"
          warning={metaStatus !== "connected"}
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
