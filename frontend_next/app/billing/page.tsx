"use client";

import { useState } from "react";
import { CreditCard, CheckCircle, AlertCircle, Clock } from "lucide-react";

/* ----------------------------------
 * MOCK DATA (Phase 2 only)
 * ---------------------------------- */
const mockSession = {
  user: {
    id: "user_123",
    email: "demo@example.com",
    is_admin: false,
    is_impersonated: false,
  },
};

const mockPlan = {
  plan_name: "Starter",
  plan_code: "starter",
  expires_at: "2025-12-31",
  ai_campaign_limit: 10,
  ai_active_campaigns: 3,
};

/* In Phase-2, invoices must be empty */
const mockInvoices: any[] = [];

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function BillingPage() {
  const [session] = useState(mockSession);
  const [plan] = useState(mockPlan);
  const [invoices] = useState(mockInvoices);

  const usagePct =
    plan && plan.ai_campaign_limit > 0
      ? Math.min(
          (plan.ai_active_campaigns / plan.ai_campaign_limit) * 100,
          100
        )
      : 0;

  if (!session) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        Session expired. Please login again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          Billing & Subscription
        </h1>
        <p className="text-sm text-gray-500">
          Manage your plan, track usage, and view payment history.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* CURRENT PLAN CARD */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                  Current Plan
                </h2>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {plan?.plan_name || "Free Tier"}
                </p>
              </div>
              <div className="p-2 bg-indigo-50 rounded-lg">
                <CreditCard className="h-6 w-6 text-indigo-600" />
              </div>
            </div>

            <p className="mt-4 text-sm text-gray-500">
              {plan?.expires_at
                ? `Valid until ${new Date(plan.expires_at).toLocaleDateString()}`
                : "No active expiration"}
            </p>
          </div>

          <button
            disabled
            className="mt-6 w-full rounded-md bg-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 shadow-sm cursor-not-allowed"
          >
            Checkout Disabled (Phase 2)
          </button>
        </div>

        {/* USAGE CARD */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 flex flex-col">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            AI Usage Limits
          </h2>

          <div className="flex-1 space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-900">
                  Active AI Campaigns
                </span>
                <span className="text-gray-500">
                  {plan?.ai_active_campaigns} / {plan?.ai_campaign_limit}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full ${
                    usagePct > 90 ? "bg-red-500" : "bg-indigo-600"
                  }`}
                  style={{ width: `${usagePct}%` }}
                ></div>
              </div>
              {usagePct >= 100 && (
                <p className="mt-2 text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> Limit reached. Upgrade to add
                  more.
                </p>
              )}
            </div>

            <div className="pt-4 border-t border-gray-100">
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Priority Support
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Advanced Analytics
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* INVOICE HISTORY */}
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-base font-semibold leading-6 text-gray-900 mb-4">
            Invoice History
          </h3>

          {invoices.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed">
              <Clock className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">No invoices found.</p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
