"use client";

import { useEffect, useState } from "react";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
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

type MetaAdAccount = {
  id: string;
  name: string;
  is_selected: boolean;
};

type SubscriptionInfo = {
  plan: string;
  expires_at: string | null;
  ai_campaign_limit: number;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function SettingsPage() {
  const [session, setSession] = useState<SessionContext | null>(null);
  const [adAccounts, setAdAccounts] = useState<MetaAdAccount[]>([]);
  const [subscription, setSubscription] =
    useState<SubscriptionInfo | null>(null);

  const [loading, setLoading] = useState(true);
  const [connectingMeta, setConnectingMeta] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD SESSION CONTEXT
   * ---------------------------------- */
  const loadSession = async () => {
    const res = await fetch("/api/session/context", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setSession(null);
      return;
    }

    setSession(await res.json());
  };

  /* ----------------------------------
   * LOAD META AD ACCOUNTS
   * ---------------------------------- */
  const loadAdAccounts = async () => {
    const res = await fetch("/api/meta/adaccounts", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setAdAccounts([]);
      return;
    }

    const json = await res.json();
    setAdAccounts(Array.isArray(json) ? json : []);
  };

  /* ----------------------------------
   * LOAD SUBSCRIPTION
   * ---------------------------------- */
  const loadSubscription = async () => {
    const res = await fetch("/api/billing/subscription", {
      credentials: "include",
      cache: "no-store",
    });

    if (!res.ok) {
      setSubscription(null);
      return;
    }

    setSubscription(await res.json());
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadSession();
      await loadAdAccounts();
      await loadSubscription();
      setLoading(false);
    })();
  }, []);

  /* ----------------------------------
   * CONNECT META
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
   * TOGGLE AD ACCOUNT (MULTI SELECT)
   * ---------------------------------- */
  const toggleAdAccount = async (id: string) => {
    try {
      setTogglingId(id);

      const res = await fetch(
        `/api/meta/adaccounts/${id}/toggle`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (!res.ok) throw new Error();

      await loadAdAccounts();
      await loadSession();
    } catch {
      alert("Failed to update ad account.");
    } finally {
      setTogglingId(null);
    }
  };

  /* ----------------------------------
   * STATES
   * ---------------------------------- */
  if (loading) {
    return <div className="text-sm text-gray-600">Loading settings…</div>;
  }

  if (!session) {
    return (
      <div className="text-sm text-red-600">
        Unable to load session.
      </div>
    );
  }

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-gray-500">
          Account configuration and connections
        </p>
      </div>

      {/* META ACCOUNTS */}
      <div className="bg-white border rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">
            Meta Ad Accounts
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
                <th className="px-3 py-2 text-center">Active</th>
              </tr>
            </thead>
            <tbody>
              {adAccounts.map((a) => (
                <tr key={a.id} className="border-b last:border-0">
                  <td className="px-3 py-2 font-medium">
                    {a.name}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button
                      onClick={() => toggleAdAccount(a.id)}
                      disabled={togglingId === a.id}
                      className={`px-3 py-1 rounded text-xs font-medium ${
                        a.is_selected
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {a.is_selected ? "ON" : "OFF"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* SUBSCRIPTION */}
      {subscription && (
        <div className="bg-white border rounded p-6 space-y-2">
          <h2 className="text-sm font-semibold text-gray-900">
            Subscription
          </h2>

          <div className="text-sm">
            Plan: <strong>{subscription.plan}</strong>
          </div>
          <div className="text-sm">
            AI Campaign Limit:{" "}
            <strong>{subscription.ai_campaign_limit}</strong>
          </div>
          <div className="text-sm">
            Expires At:{" "}
            {subscription.expires_at ?? "No expiry"}
          </div>
        </div>
      )}
    </div>
  );
}
