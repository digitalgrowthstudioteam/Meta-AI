"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../lib/fetcher";

/**
 * SINGLE SOURCE OF TRUTH
 */
type SessionContext = {
  user: {
    id: string;
    email: string;
    is_admin: boolean;
    is_impersonated: boolean;
  };
  ad_account: {
    id: string;
    name: string;
    meta_account_id: string;
  } | null;
};

type DashboardSummary = {
  campaigns: {
    total: number;
    ai_active: number;
    ai_limit: number;
  };
};

export default function DashboardPage() {
  const router = useRouter();

  const [session, setSession] = useState<SessionContext | null>(null);
  const [data, setData] = useState<DashboardSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // -----------------------------
  // LOAD SESSION CONTEXT
  // -----------------------------
  const loadSession = async () => {
    try {
      const res = await apiFetch("/api/session/context", {
        cache: "no-store",
      });

      if (!res.ok) {
        setSession(null);
        return;
      }

      const json = await res.json();

      // ❌ REMOVED AUTO-REDIRECT FOR ADMIN (INFINITE LOOP FIX)
      setSession(json);
    } catch (error) {
      console.error("Session load error:", error);
      setSession(null);
    }
  };

  // -----------------------------
  // LOAD DASHBOARD SUMMARY
  // -----------------------------
  const loadSummary = async () => {
    if (!session?.ad_account) {
      setData(null);
      return;
    }

    try {
      const res = await apiFetch("/api/dashboard/summary", {
        cache: "no-store",
      });

      if (!res.ok) {
        setData(null);
        return;
      }

      const json = await res.json();
      setData(json);
    } catch (error) {
      console.error("Dashboard summary error:", error);
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadSession();
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    if (session?.ad_account?.id) {
      loadSummary();
    }
  }, [session?.ad_account?.id]);

  // -----------------------------
  // CONNECT META
  // -----------------------------
  const connectMeta = async () => {
    try {
      const res = await apiFetch("/api/meta/connect", {
        cache: "no-store",
      });
      if (!res.ok) return;

      const json = await res.json();
      if (json?.redirect_url) {
        window.location.href = json.redirect_url;
      }
    } catch (error) {
      console.error("Meta connect error:", error);
    }
  };

  // -----------------------------
  // SYNC CAMPAIGNS
  // -----------------------------
  const syncCampaigns = async () => {
    setSyncing(true);
    setErrorMsg(null);

    try {
      const res = await apiFetch("/api/campaigns/sync", {
        method: "POST",
        cache: "no-store",
      });
      if (!res.ok) throw new Error();
      await loadSummary();
    } catch {
      setErrorMsg("Failed to sync campaigns. Please try again.");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-gray-500">
        Loading dashboard...
      </div>
    );
  }

  if (!session?.ad_account) {
    return (
      <div className="space-y-6 max-w-xl mx-auto mt-10 p-6 bg-white rounded-lg border shadow-sm">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Welcome to Digital Growth Studio</h1>
          <p className="mt-2 text-sm text-gray-600">
            To get started with AI optimization, please connect your Meta Ads account and select an ad account to manage.
          </p>
        </div>
        <button
          onClick={connectMeta}
          className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          Connect Meta Ads
        </button>
      </div>
    );
  }

  const totalCampaigns = data?.campaigns.total ?? 0;
  const aiActive = data?.campaigns.ai_active ?? 0;
  const aiLimit = data?.campaigns.ai_limit ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Active account: <strong className="text-gray-900">{session.ad_account.name}</strong>
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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

      <div className="pt-4 border-t">
        <button
          onClick={syncCampaigns}
          disabled={syncing}
          className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {syncing ? "Syncing..." : "Sync Campaigns Now"}
        </button>
      </div>
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
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-1 shadow-sm">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-semibold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400">{hint}</div>
    </div>
  );
}
