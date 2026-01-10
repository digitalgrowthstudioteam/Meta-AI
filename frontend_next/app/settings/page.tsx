"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { CheckCircle, XCircle, RefreshCw, Facebook } from "lucide-react";
import { apiFetch } from "../lib/fetcher";

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
  id: number;
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
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);

  const [loading, setLoading] = useState(true);
  const [connectingMeta, setConnectingMeta] = useState(false);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  /* ----------------------------------
   * LOAD DATA
   * ---------------------------------- */
  const loadData = async () => {
    try {
      const [sessionRes, accountsRes, subRes] = await Promise.all([
        apiFetch("/api/session/context", { cache: "no-store" }),
        apiFetch("/api/meta/adaccounts", { cache: "no-store" }),
        apiFetch("/api/billing/subscription", { cache: "no-store" }),
      ]);

      if (sessionRes.ok) setSession(await sessionRes.json());
      
      if (accountsRes.ok) {
        const json = await accountsRes.json();
        setAdAccounts(Array.isArray(json) ? json : []);
      }

      if (subRes.ok) setSubscription(await subRes.json());

    } catch (error) {
      console.error("Failed to load settings data", error);
      toast.error("Some settings could not be loaded");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  /* ----------------------------------
   * CONNECT META
   * ---------------------------------- */
  const connectMeta = async () => {
    try {
      setConnectingMeta(true);
      const res = await apiFetch("/api/meta/connect", { cache: "no-store" });

      if (!res.ok) throw new Error("Connection initialization failed");

      const json = await res.json();
      if (json?.redirect_url) {
        window.location.href = json.redirect_url;
      }
    } catch {
      toast.error("Failed to connect to Meta. Please try again.");
    } finally {
      setConnectingMeta(false);
    }
  };

  /* ----------------------------------
   * TOGGLE AD ACCOUNT
   * ---------------------------------- */
  const toggleAdAccount = async (id: number) => {
    try {
      setTogglingId(id);

      const res = await apiFetch(`/api/meta/adaccounts/${id}/toggle`, {
        method: "POST",
      });

      if (!res.ok) throw new Error("Failed to toggle account");

      await loadData(); // Reload to refresh session context
      toast.success("Ad account selection updated");
    } catch {
      toast.error("Failed to update ad account selection");
    } finally {
      setTogglingId(null);
    }
  };

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-gray-500">
        Loading settings...
      </div>
    );
  }

  if (!session) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        Unable to verify session. Please login again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">
          Manage your account connections and preferences.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* META ACCOUNTS CARD */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold leading-6 text-gray-900">
                Meta Ad Accounts
              </h2>
              <button
                onClick={connectMeta}
                disabled={connectingMeta}
                className="inline-flex items-center gap-2 rounded-md bg-[#1877F2] px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#166fe5] disabled:opacity-50"
              >
                {connectingMeta ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Facebook className="h-4 w-4" />
                )}
                {connectingMeta ? "Connecting..." : "Connect New"}
              </button>
            </div>

            {adAccounts.length === 0 ? (
              <div className="text-center py-6 bg-gray-50 rounded-lg border border-dashed">
                <p className="text-sm text-gray-500">No ad accounts connected.</p>
              </div>
            ) : (
              <div className="flow-root">
                <ul role="list" className="-my-5 divide-y divide-gray-200">
                  {adAccounts.map((account) => (
                    <li key={account.id} className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-gray-900">
                            {account.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            ID: {account.id}
                          </p>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <button
                            onClick={() => toggleAdAccount(account.id)}
                            disabled={togglingId === account.id}
                            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
                              account.is_selected ? "bg-indigo-600" : "bg-gray-200"
                            } ${togglingId === account.id ? "opacity-50" : ""}`}
                          >
                            <span
                              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                                account.is_selected ? "translate-x-5" : "translate-x-0"
                              }`}
                            />
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* SUBSCRIPTION CARD */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden h-fit">
          <div className="px-4 py-5 sm:p-6">
            <h2 className="text-base font-semibold leading-6 text-gray-900 mb-4">
              Subscription Status
            </h2>

            {subscription ? (
              <dl className="divide-y divide-gray-100">
                <div className="px-0 py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">Current Plan</dt>
                  <dd className="mt-1 text-sm font-semibold text-gray-900 sm:col-span-2 sm:mt-0 uppercase">
                    {subscription.plan}
                  </dd>
                </div>
                <div className="px-0 py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">Campaign Limit</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
                    {subscription.ai_campaign_limit} AI Campaigns
                  </dd>
                </div>
                <div className="px-0 py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                  <dt className="text-sm font-medium text-gray-500">Expires At</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
                    {subscription.expires_at ? new Date(subscription.expires_at).toLocaleDateString() : "Never (Lifetime)"}
                  </dd>
                </div>
              </dl>
            ) : (
              <div className="text-sm text-gray-500">
                Subscription details unavailable.
              </div>
            )}
          </div>
          <div className="bg-gray-50 px-4 py-4 sm:px-6">
            <div className="text-sm">
              <a href="/billing" className="font-medium text-indigo-600 hover:text-indigo-500">
                Manage billing details <span aria-hidden="true">&rarr;</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
