"use client";

import { useEffect, useState } from "react";
import {
  CreditCard,
  Clock,
  Loader2,
} from "lucide-react";
import { apiFetch } from "../lib/fetcher";

function formatDate(dateStr?: string | null) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

function StatusChip({ status }: { status: string }) {
  const map: any = {
    active: "bg-green-100 text-green-700",
    trial: "bg-blue-100 text-blue-700",
    grace: "bg-amber-100 text-amber-700",
    expired: "bg-gray-100 text-gray-700",
    cancelled: "bg-red-100 text-red-700",
  };

  const label = {
    active: "Active",
    trial: "Trial",
    grace: "Grace",
    expired: "Expired",
    cancelled: "Cancelled",
  }[status] || status;

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${map[status] || "bg-gray-100 text-gray-600"}`}
    >
      {label}
    </span>
  );
}

export default function BillingPage() {
  const [loading, setLoading] = useState(true);
  const [canceling, setCanceling] = useState(false);
  const [sub, setSub] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const sres = await apiFetch("/billing/status");
      const sinfo = await sres.json();

      const ires = await apiFetch("/billing/invoices");
      const iinfo = await ires.json();

      setSub(sinfo.subscription || null);
      setInvoices(Array.isArray(iinfo) ? iinfo : []);
    } catch (e) {
      setError("Failed to load billing data.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel() {
    if (!confirm("Cancel subscription at cycle end?")) return;

    try {
      setCanceling(true);
      setError(null);

      const res = await apiFetch("/billing/cancel", { method: "POST" });
      if (!res.ok) throw new Error("Cancel failed");

      await loadData();
    } catch (e) {
      setError("Cancellation failed.");
    } finally {
      setCanceling(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-600">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading billing info...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  const planName = sub?.plan_name || "Free";
  const expires = sub?.ends_at ? formatDate(sub.ends_at) : null;
  const status = sub?.status || "none";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          Billing & Subscription
        </h1>
        <p className="text-sm text-gray-500">
          Manage your plan and invoices.
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
                  {planName}
                </p>
                <div className="mt-2">
                  <StatusChip status={status} />
                </div>
              </div>
              <div className="p-2 bg-indigo-50 rounded-lg">
                <CreditCard className="h-6 w-6 text-indigo-600" />
              </div>
            </div>

            <p className="mt-4 text-sm text-gray-500">
              {expires ? `Renews on ${expires}` : "No renewal date"}
            </p>

            {sub?.in_grace && (
              <p className="mt-1 text-xs text-amber-600">
                In grace period (ends {formatDate(sub.grace_ends_at)})
              </p>
            )}

            {sub?.cancelled_at && (
              <p className="mt-1 text-xs text-red-600 font-medium">
                Will not renew after end of period
              </p>
            )}
          </div>

          {(status === "active" || status === "trial" || status === "grace") ? (
            <button
              onClick={handleCancel}
              disabled={canceling}
              className="mt-6 w-full rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 disabled:opacity-50"
            >
              {canceling ? "Processing..." : "Cancel Subscription"}
            </button>
          ) : (
            <p className="mt-6 text-sm text-gray-400 italic">
              No active subscription
            </p>
          )}
        </div>

        {/* INVOICES CARD */}
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 flex flex-col">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Invoices
          </h2>

          {invoices.length === 0 ? (
            <div className="flex-1 flex flex-col justify-center items-center text-sm text-gray-500 py-4">
              <Clock className="h-6 w-6 mb-2 text-gray-400" />
              No invoices yet.
            </div>
          ) : (
            <ul className="space-y-2 text-sm">
              {invoices.slice(0, 3).map((inv) => (
                <li key={inv.id} className="flex justify-between">
                  <span>{inv.invoice_number}</span>
                  <a
                    href={inv.download_url}
                    className="text-indigo-600 hover:text-indigo-500"
                  >
                    Download
                  </a>
                </li>
              ))}
            </ul>
          )}

          {invoices.length > 3 && (
            <a
              href="/billing/invoices"
              className="mt-4 text-sm text-indigo-600 hover:text-indigo-500"
            >
              View all invoices →
            </a>
          )}
        </div>
      </div>

      {/* RENEWAL HISTORY TIMELINE */}
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Renewal History
        </h2>

        {invoices.length === 0 ? (
          <p className="text-sm text-gray-500 italic">
            No renewal events recorded yet.
          </p>
        ) : (
          <div className="space-y-4">
            {[...invoices]
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
              .map((inv) => (
                <div key={inv.id} className="relative pl-6">
                  <div className="absolute left-0 top-1 h-2 w-2 rounded-full bg-indigo-600"></div>
                  <p className="text-sm font-medium text-gray-900">
                    {inv.currency} {inv.amount / 100}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDate(inv.created_at)} • {inv.invoice_number}
                  </p>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
