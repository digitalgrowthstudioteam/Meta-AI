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
  period_from: string | null;
  period_to: string | null;
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
  const [paying, setPaying] = useState(false);

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

      setPlan(await planRes.json());
      setInvoices(await invoiceRes.json());
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
   * RAZORPAY CHECKOUT
   * ---------------------------------- */
  const startCheckout = async () => {
    try {
      setPaying(true);

      const res = await fetch(
        "/api/billing/razorpay/order?amount=99900&payment_for=subscription",
        { method: "POST", credentials: "include" }
      );

      if (!res.ok) throw new Error("Unable to create payment order");

      const data = await res.json();

      const options = {
        key: data.key,
        order_id: data.razorpay_order_id,
        amount: data.amount,
        currency: "INR",
        name: "Digital Growth Studio",
        description: "Subscription Purchase",
        handler: async (response: any) => {
          await fetch("/api/billing/razorpay/verify", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(response),
          });
          await loadBilling();
        },
        theme: { color: "#2563eb" },
      };

      // @ts-ignore
      new window.Razorpay(options).open();
    } catch (e: any) {
      alert(e.message || "Payment failed");
    } finally {
      setPaying(false);
    }
  };

  /* ----------------------------------
   * STATES
   * ---------------------------------- */
  if (loading) return <div className="text-sm">Loading billing information…</div>;
  if (error) return <div className="text-red-600 text-sm">{error}</div>;

  const usagePct =
    plan && plan.ai_campaign_limit > 0
      ? Math.min(plan.ai_active_campaigns / plan.ai_campaign_limit, 1)
      : 0;

  /* ----------------------------------
   * HELPERS
   * ---------------------------------- */
  const statusBadge = (status: Invoice["status"]) => {
    if (status === "paid")
      return "bg-green-100 text-green-700";
    if (status === "pending")
      return "bg-yellow-100 text-yellow-700";
    return "bg-red-100 text-red-700";
  };

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Billing & Plan</h1>
        <p className="text-sm text-gray-500">
          Subscription details, usage limits, and invoices
        </p>
      </div>

      {/* TOP GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* CURRENT PLAN */}
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <div className="flex justify-between mb-4">
            <h2 className="text-sm font-semibold">Current Plan</h2>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
              {plan?.plan_name ?? "—"}
            </span>
          </div>

          <div className="text-2xl font-semibold">{plan?.plan_name}</div>
          <div className="mt-2 text-sm text-gray-500">
            {plan?.expires_at ? `Valid until ${plan.expires_at}` : "No expiry"}
          </div>

          <button
            onClick={startCheckout}
            disabled={paying}
            className="mt-6 w-full rounded-md bg-blue-600 text-white py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {paying ? "Processing…" : "Upgrade / Buy Plan"}
          </button>
        </div>

        {/* USAGE */}
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold mb-4">AI Usage</h2>

          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span>AI-Active Campaigns</span>
              <span>
                {plan?.ai_active_campaigns} / {plan?.ai_campaign_limit}
              </span>
            </div>

            <div className="h-2 bg-gray-200 rounded">
              <div
                className="h-full bg-indigo-500 rounded"
                style={{ width: `${usagePct * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* POLICY */}
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold mb-4">Billing Policy</h2>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Explicit purchase only</li>
            <li>• No auto-renewals</li>
            <li>• Audit-safe records</li>
          </ul>
        </div>
      </div>

      {/* INVOICES */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">Invoices</h2>

        {invoices.length === 0 && (
          <div className="text-sm text-gray-500 bg-white border rounded p-4">
            No invoices yet. Completed purchases will appear here.
          </div>
        )}

        {invoices.length > 0 && (
          <div className="overflow-x-auto bg-white border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="p-3 text-left">Invoice</th>
                  <th className="p-3 text-left">Amount</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-left">Date</th>
                  <th className="p-3 text-left">Download</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id} className="border-b last:border-0">
                    <td className="p-3 font-medium">
                      {inv.invoice_number}
                    </td>
                    <td className="p-3">
                      {inv.currency} {inv.amount.toFixed(2)}
                    </td>
                    <td className="p-3">
                      <span
                        className={`text-xs px-2 py-1 rounded ${statusBadge(
                          inv.status
                        )}`}
                      >
                        {inv.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3">{inv.created_at}</td>
                    <td className="p-3">
                      {inv.download_url ? (
                        <a
                          href={inv.download_url}
                          className="text-blue-600 hover:underline text-sm"
                        >
                          Download PDF
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

      <div className="text-xs text-gray-400">
        Billing data is immutable and retained for compliance.
      </div>
    </div>
  );
}
