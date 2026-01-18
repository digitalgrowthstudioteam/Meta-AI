"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../lib/fetcher";

/* ============================
   TYPES
============================= */
type SessionContext = {
  user: {
    id: string;
    email: string;
    role: string;
    is_admin: boolean;
    is_impersonated: boolean;
  } | null;
  ad_account: {
    id: string;
    name: string;
    meta_account_id: string;
  } | null;
  has_backend_access?: boolean;
  needs_meta_connect?: boolean;
};

type DashboardSummary = {
  campaigns: {
    total: number;
    ai_active: number;
    ai_limit: number;
  };
};

/* ============================
   COMPONENTS
============================= */
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
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </div>
      <div className="text-2xl font-semibold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400">{hint}</div>
    </div>
  );
}

/* ============================
   MAIN PAGE
============================= */
export default function DashboardPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionContext | null>(null);
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  /* ============================
     LOADERS
  ============================= */
  const loadSession = async () => {
    try {
      const res = await apiFetch("/session/context", { cache: "no-store" });
      if (!res.ok) {
        setSession({ user: null, ad_account: null } as any);
        return;
      }
      setSession(await res.json());
    } catch {
      setSession({ user: null, ad_account: null } as any);
    }
  };

  const loadSummary = async () => {
    if (!session?.ad_account) return;

    try {
      const res = await apiFetch("/dashboard/summary", { cache: "no-store" });
      if (!res.ok) return;
      setData(await res.json());
    } catch {
      setData(null);
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
    if (!loading && session?.user === null) {
      router.replace("/login");
    }
  }, [loading, session, router]);

  useEffect(() => {
    if (session?.ad_account?.id) {
      loadSummary();
    }
  }, [session?.ad_account?.id]);

  /* ============================
     ACTIONS
  ============================= */
  const connectMeta = async () => {
    try {
      const res = await apiFetch("/meta/connect", { cache: "no-store" });
      if (!res.ok) return;
      const json = await res.json();
      if (json?.redirect_url) window.location.href = json.redirect_url;
    } catch {}
  };

  const syncCampaigns = async () => {
    setSyncing(true);
    setErrorMsg(null);

    try {
      const res = await apiFetch("/campaigns/sync", {
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

  /* ============================
     STATES
  ============================= */
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[70vh] text-sm text-gray-500">
        Loading dashboard...
      </div>
    );
  }

  // FALLBACK MODE
  if (session?.has_backend_access && session?.needs_meta_connect) {
    return (
      <div className="flex justify-center items-start pt-24 px-4">
        <div className="w-full max-w-xl p-6 bg-white border rounded-lg shadow-sm space-y-6">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Welcome to Digital Growth Studio</h1>
            <p className="mt-2 text-sm text-gray-600">
              Backend features are available. Connect Meta Ads to unlock AI capabilities.
            </p>
          </div>

          <div className="border-t pt-4 space-y-3">
            <button
              onClick={connectMeta}
              className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-500"
            >
              Connect Meta Ads
            </button>

            {session.user?.is_admin && (
              <button
                onClick={() => router.push("/admin/dashboard")}
                className="w-full rounded-md bg-white px-4 py-2.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50"
              >
                Go to Backend Dashboard
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!session?.ad_account) {
    return (
      <div className="flex justify-center items-start pt-24 px-4">
        <div className="w-full max-w-xl p-6 bg-white border rounded-lg shadow-sm space-y-6">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Connect Meta Ads</h1>
            <p className="mt-2 text-sm text-gray-600">
              To unlock AI optimization, please connect your Meta Ads account.
            </p>
          </div>
          <button
            onClick={connectMeta}
            className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-500"
          >
            Connect Meta Ads
          </button>
        </div>
      </div>
    );
  }

  /* ============================
     RENDER MAIN DASHBOARD
  ============================= */
  const totalCampaigns = data?.campaigns.total ?? 0;
  const aiActive = data?.campaigns.ai_active ?? 0;
  const aiLimit = data?.campaigns.ai_limit ?? 0;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">

      {/* HEADER */}
      <div>
        <h1 className="text-lg font-semibold text-gray-900">Dashboard Overview</h1>
        <p className="text-xs text-gray-500 mt-1">
          Active Ad Account: <span className="font-medium text-gray-900">{session.ad_account.name}</span>
        </p>
      </div>

      {/* ERROR */}
      {errorMsg && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">
          {errorMsg}
        </div>
      )}

      {/* KPI GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard label="Total Campaigns" value={totalCampaigns} hint="Across selected ad account" />
        <KpiCard label="AI Optimization" value={`${aiActive} / ${aiLimit}`} hint="Active / Limit" />
        <KpiCard label="Account Status" value="Connected" hint="Meta Ads Linked" />
      </div>

      {/* ACTIONS */}
      <div className="pt-4 border-t">
        <button
          onClick={syncCampaigns}
          disabled={syncing}
          className="rounded-md bg-white px-3.5 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {syncing ? "Syncing..." : "Sync Campaigns"}
        </button>
      </div>

    </div>
  );
}
