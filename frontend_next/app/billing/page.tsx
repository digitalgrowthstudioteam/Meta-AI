"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { CreditCard, Download, CheckCircle, AlertCircle, Clock } from "lucide-react";
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
};

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
  created_at: string;
  download_url?: string | null;
};

// Extend window for Razorpay
declare global {
  interface Window {
    Razorpay: any;
  }
}

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function BillingPage() {
  const [session, setSession] = useState<SessionContext | null>(null);
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);

  /* ----------------------------------
   * LOAD DATA
   * ---------------------------------- */
  const loadData = async () => {
    try {
      const [sessionRes, planRes, invoiceRes] = await Promise.all([
        apiFetch("/api/session/context", { cache: "no-store" }),
        apiFetch("/api/billing/plan", { cache: "no-store" }),
        apiFetch("/api/billing/invoices", { cache: "no-store" }),
      ]);

      if (sessionRes.ok) setSession(await sessionRes.json());
      if (planRes.ok) setPlan(await planRes.json());
      if (invoiceRes.ok) setInvoices(await invoiceRes.json());

    } catch (error) {
      console.error("Billing load error", error);
      toast.error("Failed to load billing details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load Razorpay Script dynamically
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    document.body.appendChild(script);

    loadData();

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  /* ----------------------------------
   * RAZORPAY CHECKOUT FLOW
   * ---------------------------------- */
  const startCheckout = async () => {
    if (!window.Razorpay) {
      toast.error("Payment gateway is still loading. Please wait...");
      return;
    }

    setPaying(true);

    try {
      // 1. Create Order on Server
      const orderRes = await apiFetch(
        "/api/billing/razorpay/order?amount=99900&payment_for=subscription",
        { method: "POST" }
      );

      if (!orderRes.ok) throw new Error("Failed to create order");
      const orderData = await orderRes.json();

      // 2. Initialize Razorpay
      const options = {
        key: orderData.key,
        amount: orderData.amount,
        currency: "INR",
        name: "Digital Growth Studio",
        description: "Premium Plan Subscription",
        order_id: orderData.razorpay_order_id,
        handler: async (response: any) => {
          // 3. Verify Payment on Server
          const verifyToast = toast.loading("Verifying payment...");
          
          try {
            const verifyRes = await apiFetch("/api/billing/razorpay/verify", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(response),
            });

            if (!verifyRes.ok) throw new Error("Verification failed");

            toast.success("Payment successful! Plan upgraded.", { id: verifyToast });
            await loadData(); // Refresh UI
          } catch (err) {
            toast.error("Payment verification failed. Contact support.", { id: verifyToast });
          }
        },
        theme: {
          color: "#4F46E5",
        },
        modal: {
          ondismiss: () => {
            setPaying(false);
            toast("Payment cancelled");
          }
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.on("payment.failed", function (response: any) {
        toast.error(`Payment Failed: ${response.error.description}`);
        setPaying(false);
      });
      
      rzp.open();

    } catch (e: any) {
      toast.error(e.message || "Could not initiate payment");
      setPaying(false);
    }
  };

  /* ----------------------------------
   * HELPERS
   * ---------------------------------- */
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "paid":
        return <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Paid</span>;
      case "pending":
        return <span className="inline-flex items-center rounded-md bg-yellow-50 px-2 py-1 text-xs font-medium text-yellow-800 ring-1 ring-inset ring-yellow-600/20">Pending</span>;
      default:
        return <span className="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">Failed</span>;
    }
  };

  const usagePct = plan && plan.ai_campaign_limit > 0
      ? Math.min((plan.ai_active_campaigns / plan.ai_campaign_limit) * 100, 100)
      : 0;

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-gray-500">
        Loading billing information...
      </div>
    );
  }

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
        <h1 className="text-xl font-semibold text-gray-900">Billing & Subscription</h1>
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
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Current Plan</h2>
                <p className="mt-2 text-3xl font-bold text-gray-900">{plan?.plan_name || "Free Tier"}</p>
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
            onClick={startCheckout}
            disabled={paying}
            className="mt-6 w-full rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-wait"
          >
            {paying ? "Processing..." : "Upgrade / Renew Plan"}
          </button>
        </div>

        {/* USAGE CARD */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 flex flex-col">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">AI Usage Limits</h2>
          
          <div className="flex-1 space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-900">Active AI Campaigns</span>
                <span className="text-gray-500">{plan?.ai_active_campaigns} / {plan?.ai_campaign_limit}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full ${usagePct > 90 ? 'bg-red-500' : 'bg-indigo-600'}`} 
                  style={{ width: `${usagePct}%` }}
                ></div>
              </div>
              {usagePct >= 100 && (
                <p className="mt-2 text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> Limit reached. Upgrade to add more.
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
          <h3 className="text-base font-semibold leading-6 text-gray-900 mb-4">Invoice History</h3>
          
          {invoices.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed">
              <Clock className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">No invoices found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">Invoice #</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Date</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Amount</th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">Download</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {invoices.map((inv) => (
                    <tr key={inv.id}>
                      <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                        {inv.invoice_number}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                        {new Date(inv.created_at).toLocaleDateString()}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                        {inv.currency.toUpperCase()} {(inv.amount / 100).toFixed(2)}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm">
                        {getStatusBadge(inv.status)}
                      </td>
                      <td className="whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                        {inv.download_url && (
                          <a href={inv.download_url} className="text-indigo-600 hover:text-indigo-900 flex items-center justify-end gap-1">
                            <Download className="h-4 w-4" /> Download
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
