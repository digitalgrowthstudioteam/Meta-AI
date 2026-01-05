"use client";

import { useEffect, useState } from "react";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type MetaAdAccount = {
  id: string;
  name: string;
  meta_account_id: string;
  is_active: boolean;
  connected_at: string;
};

type SubscriptionInfo = {
  plan: string;
  expires_at: string | null;
  ai_campaign_limit: number;
};

type UserPreferences = {
  timezone: string;
  reporting_window: string;
};

export default function SettingsPage() {
  const [adAccounts, setAdAccounts] = useState<MetaAdAccount[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>({
    timezone: "Asia/Kolkata",
    reporting_window: "7d",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connectingMeta, setConnectingMeta] = useState(false);

  /* ----------------------------------
   * LOAD SETTINGS DATA
   * ---------------------------------- */
  const loadSettings = async () => {
    try {
      setLoading(true);

      const [accountsRes, subRes, prefRes] = await Promise.all([
        fetch("/api/meta/adaccounts", { credentials: "include", cache: "no-store" }),
        fetch("/api/billing/subscription", { credentials: "include", cache: "no-store" }),
        fetch("/api/user/preferences", { credentials: "include", cache: "no-store" }),
      ]);

      if (accountsRes.ok) {
        const json = await accountsRes.json();
        setAdAccounts(Array.isArray(json) ? json : []);
      }

      if (subRes.ok) {
        const json = await subRes.json();
        setSubscription(json ?? null);
      }

      if (prefRes.ok) {
        const json = await prefRes.json();
        setPreferences({
          timezone: json?.timezone ?? "Asia/Kolkata",
          reporting_window: json?.reporting_window ?? "7d",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  /* ----------------------------------
   * CONNECT META (REAL)
   * ---------------------------------- */
  const connectMeta = async () => {
    try {
      setConnectingMeta(true);

      const res = await fetch("/api/meta/connect", {
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) throw new Error();

      const json = await res.json();
      if (json?.redirect_url) {
        window.location.href = json.redirect_url;
      }
    } catch {
      alert("Failed to initiate Meta connection.");
    } finally {
      setConnectingMeta(false);
    }
  };

  /* ----------------------------------
   * SAVE PREFERENCES
   * ---------------------------------- */
  const savePreferences = async () => {
    try {
      setSaving(true);
      await fetch("/api/user/preferences", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-600">Loading settings…</div>;
  }

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-gray-500">
          Account configuration, connections, and preferences
        </p>
      </div>

      {/* ===============================
          META AD ACCOUNTS
      =============================== */}
      <div className="bg-white border rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">
            Connected Meta Ad Accounts
          </h2>

          <button
            onClick={connectMeta}
            disabled={connectingMeta}
            className="btn-primary text-sm"
          >
            {connectingMeta ? "Connecting…" : "Connect Meta Ads"}
          </button>
        </div>

        {adAccounts.length === 0 && (
          <div className="text-sm text-gray-600">
            No Meta ad accounts connected yet.
          </div>
        )}

        {adAccounts.length > 0 && (
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left">Account</th>
                <th className="px-3 py-2">Meta ID</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Connected At</th>
              </tr>
            </thead>
            <tbody>
              {adAccounts.map((a) => (
                <tr key={a.id} className="border-b last:border-0">
                  <td className="px-3 py-2 font-medium">{a.name}</td>
                  <td className="px-3 py-2 text-xs text-gray-600">
                    {a.meta_account_id}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        a.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {a.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {a.connected_at}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ===============================
          SUBSCRIPTION DETAILS
      =============================== */}
      <div className="bg-white border rounded p-6 space-y-3">
        <h2 className="text-sm font-semibold text-gray-900">
          Subscription Plan
        </h2>

        {subscription ? (
          <div className="text-sm space-y-1">
            <div><strong>Plan:</strong> {subscription.plan}</div>
            <div><strong>AI Campaign Limit:</strong> {subscription.ai_campaign_limit}</div>
            <div><strong>Expires At:</strong> {subscription.expires_at ?? "—"}</div>
          </div>
        ) : (
          <div className="text-sm text-gray-600">
            No active subscription.
          </div>
        )}
      </div>

      {/* ===============================
          USER PREFERENCES
      =============================== */}
      <div className="bg-white border rounded p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">
          Reporting Preferences
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <label className="text-xs text-gray-500">Timezone</label>
            <select
              value={preferences.timezone}
              onChange={(e) =>
                setPreferences((p) => ({ ...p, timezone: e.target.value }))
              }
              className="mt-1 w-full border rounded px-2 py-1"
            >
              <option value="Asia/Kolkata">Asia/Kolkata</option>
              <option value="UTC">UTC</option>
              <option value="America/New_York">America/New_York</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500">
              Default Reporting Window
            </label>
            <select
              value={preferences.reporting_window}
              onChange={(e) =>
                setPreferences((p) => ({ ...p, reporting_window: e.target.value }))
              }
              className="mt-1 w-full border rounded px-2 py-1"
            >
              <option value="7d">Last 7 Days</option>
              <option value="14d">Last 14 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>
        </div>

        <button
          onClick={savePreferences}
          disabled={saving}
          className="btn-primary"
        >
          {saving ? "Saving…" : "Save Preferences"}
        </button>
      </div>

      <div className="text-xs text-gray-400">
        All settings are applied safely without impacting live Meta campaigns.
      </div>
    </div>
  );
}
