"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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
    const res = await fetch("/api/session/context", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setSession(null);
      return;
    }

    const json = await res.json();

    // 🔒 ADMIN → FORCE REDIRECT
    if (json?.user?.is_admin) {
      router.replace("/admin/dashboard");
      return;
    }

    setSession(json);
  };

  // -----------------------------
  // LOAD DASHBOARD SUMMARY
  // -----------------------------
  const loadSummary = async () => {
    if (!session?.ad_account) {
      setData(null);
      return;
    }

    const res = await fetch("/api/dashboard/summary", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setData(null);
      return;
    }

    const json = await res.json();
    setData(json);
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadSession();
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    loadSummary();
  }, [session?.ad_account?.id]);

  // -----------------------------
  // CONNECT META
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
  // SYNC CAMPAIGNS
  // -----------------------------
  const syncCampaigns = async () => {
    setSyncing(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/campaigns/sync", {
        method: "POST",
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) throw new Error();
      await loadSummary();
    } catch {
      setErrorMsg("Failed to sync campaigns");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-500">Loading dashboard…</div>;
  }

  if (!session?.ad_account) {
    return (
      <div className="space-y-4 max-w-xl">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-gray-600">
          Connect Meta Ads and select an ad account.
        </p>
        <button onClick={connectMeta} className="btn-primary">
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
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Active account: <strong>{session.ad_account.name}</strong>
        </p>
      </div>

      {errorMsg && <div className="text-sm text-red-600">{errorMsg}</div>}

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

      <div>
        <button
          onClick={syncCampaigns}
          disabled={syncing}
          className="btn-secondary disabled:opacity-60"
        >
          {syncing ? "Syncing…" : "Sync Campaigns"}
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
    <div className="bg-white border rounded-lg p-5 space-y-1">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
      <div className="text-xs text-gray-400">{hint}</div>
    </div>
  );
}
