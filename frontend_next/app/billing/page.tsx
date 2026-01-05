"use client";

import { useEffect, useState } from "react";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type PlanInfo = {
  plan_name: string;
  plan_code: string;
  expires_at?: string | null;
  ai_campaign_limit: number;
  ai_active_campaigns: number;
};

type Invoice = {
  id: string;
  invoice_number: string;
  amount: number;
  currency: string;
  status: "paid" | "pending" | "failed";
  period_from: string;
  period_to: string;
  created_at: string;
  download_url?: string | null;
};

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function BillingPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ----------------------------------
   * LOAD BILLING DATA
   * ---------------------------------- */
  const loadBilling = async () => {
    try {
      setLoading(true);
      setError(null);

      const [planRes, invoiceRes] = await Promise.all([
        fetch("/api/billing/plan", { credentials: "include" }),
        fetch("/api/billing/invoices", { credentials: "include" }),
      ]);

      if (!planRes.ok) throw new Error("Unable to load plan details.");
      if (!invoiceRes.ok) throw new Error("Unable to load invoices.");

      const planJson = await planRes.json();
      const invoiceJson = await invoiceRes.json();

      setPlan(planJson ?? null);
      setInvoices(Array.isArray(invoiceJson) ? invoiceJson : []);
    } catch (err: any) {
      setError(err.message || "Unexpected billing error.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBilling();
  }, []);

  /* ----------------------------------
   * STATES
   * ---------------------------------- */
  if (loading) return <div>Loading billing information…</div>;
  if (error) return <div className="text-red-600">{error}</div>;

  const usagePct =
    plan && plan.ai_campaign_limit > 0
      ? Math.min(
          plan.ai_active_campaigns / plan.ai_campaign_limit,
          1
        )
      : 0;

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* ===============================
          PAGE HEADER
      =============================== */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          Billing & Plan
        </h1>
        <p className="text-sm text-gray-500">
          Subscription details, usage limits, and invoices
        </p>
      </div>

      {/* ===============================
          GRID LAYOUT
      =============================== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* CURRENT PLAN */}
        <div className="bg-white border border-blue-100 rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">
              Current Plan
            </h2>
            <span className="inline-flex rounded-full bg-blue-100 text-blue-700 px-2.5 py-1 text-xs font-medium">
              {plan?.plan_name ?? "—"}
            </span>
          </div>

          <div className="text-2xl font-semibold text-gray-900">
            {plan?.plan_name ?? "Unknown"}
          </div>

          <div className="mt-2 text-sm text-gray-500">
            {plan?.expires_at
              ? `Valid until ${plan.expires_at}`
              : "No expiry"}
          </div>

          <div className="mt-4 text-xs text-gray-400">
            Plan upgrades unlock higher AI limits and advanced features.
          </div>

          <a
            href="/buy-campaign"
            className="mt-6 block w-full text-center rounded-md bg-blue-600 text-white py-2 text-sm font-medium hover:bg-blue-700 transition"
          >
            Upgrade / Buy Campaigns
          </a>
        </div>

        {/* USAGE */}
        <div className="bg-white border border-indigo-100 rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            AI Usage
          </h2>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">
                  AI-Active Campaigns
                </span>
                <span className="font-medium text-gray-900">
                  {plan?.ai_active_campaigns ?? 0} /{" "}
                  {plan?.ai_campaign_limit ?? 0}
                </span>
              </div>

              <div className="h-2 rounded bg-gray-200 overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded"
                  style={{ width: `${usagePct * 100}%` }}
                />
              </div>
            </div>

            <div className="text-xs text-gray-400">
              Usage resets based on plan terms. No automatic overages.
            </div>
          </div>
        </div>

        {/* BILLING INFO */}
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Billing Policy
          </h2>

          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Explicit purchase only</li>
            <li>• No automatic renewals</li>
            <li>• Downloadable invoices</li>
            <li>• Audit-safe records</li>
          </ul>

          <div className="mt-4 text-xs text-gray-400">
            All charges are user-approved and fully transparent.
          </div>
        </div>
      </div>

      {/* ===============================
          INVOICES
      =============================== */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">Invoices</h2>

        {invoices.length === 0 && (
          <div className="surface p-6 text-sm text-gray-600">
            No invoices yet. Purchases will generate invoices automatically.
          </div>
        )}

        {invoices.length > 0 && (
          <div className="surface overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="px-3 py-2 text-left">
                    Invoice #
                  </th>
                  <th className="px-3 py-2">
                    Period
                  </th>
                  <th className="px-3 py-2">
                    Amount
                  </th>
                  <th className="px-3 py-2">
                    Status
                  </th>
                  <th className="px-3 py-2">
                    Date
                  </th>
                  <th className="px-3 py-2">
                    Download
                  </th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr
                    key={inv.id}
                    className="border-b last:border-0"
                  >
                    <td className="px-3 py-2 font-medium">
                      {inv.invoice_number}
                    </td>
                    <td className="px-3 py-2">
                      {inv.period_from} → {inv.period_to}
                    </td>
                    <td className="px-3 py-2">
                      {inv.currency} {inv.amount.toFixed(2)}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          inv.status === "paid"
                            ? "bg-green-100 text-green-700"
                            : inv.status === "pending"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {inv.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {inv.created_at}
                    </td>
                    <td className="px-3 py-2">
                      {inv.download_url ? (
                        <a
                          href={inv.download_url}
                          target="_blank"
                          className="text-blue-600 hover:underline"
                        >
                          Download
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* FOOTNOTE */}
      <div className="text-xs text-gray-400">
        Billing data is immutable and retained for compliance.
      </div>
    </div>
  );
}
