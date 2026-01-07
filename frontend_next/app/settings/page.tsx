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

/* ----------------------------------
 * HELPERS
 * ---------------------------------- */
const getUserId = () => {
  const match = document.cookie.match(/meta_ai_session=([^;]+)/);
  return match?.[1] ?? null;
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

      const userId = getUserId();
      if (!userId) return;

      const headers = {
        "X-User-Id": userId,
      };

      const [accountsRes, subRes, prefRes] = await Promise.all([
        fetch("/api/meta/adaccounts", {
          credentials: "include",
          cache: "no-store",
          headers,
        }),
        fetch("/api/billing/subscription", {
          credentials: "include",
          cache: "no-store",
          headers,
        }),
        fetch("/api/user/preferences", {
          credentials: "include",
          cache: "no-store",
          headers,
        }),
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
   * CONNECT META
   * ---------------------------------- */
  const connectMeta = async () => {
    try {
      setConnectingMeta(true);

      const userId = getUserId();
      if (!userId) return;

      const res = await fetch("/api/meta/connect", {
        credentials: "include",
        cache: "no-store",
        headers: {
          "X-User-Id": userId,
        },
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

      const userId = getUserId();
      if (!userId) return;

      await fetch("/api/user/preferences", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": userId,
        },
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
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-gray-500">
          Account configuration, connections, and preferences
        </p>
      </div>

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
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
                      Inactive
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs">{a.connected_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
