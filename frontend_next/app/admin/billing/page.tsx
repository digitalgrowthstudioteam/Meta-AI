"use client";

import { useEffect, useState } from "react";

type Payment = {
  id: string;
  amount: number;
  currency: string;
  status: string;
  payment_for: string;
  created_at: string;
};

type Invoice = {
  id: string;
  invoice_number: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  download_url: string;
};

type SlotAddon = {
  id: string;
  user_id: string;
  extra_ai_campaigns: number;
  purchased_at: string;
  expires_at: string;
  payment_id: string | null;
};

export default function AdminBillingPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [slots, setSlots] = useState<SlotAddon[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [p, i, s] = await Promise.all([
        fetch("/api/admin/billing/payments"),
        fetch("/api/admin/billing/invoices"),
        fetch("/api/admin/billing/slots"),
      ]);

      if (p.ok) setPayments(await p.json());
      if (i.ok) setInvoices(await i.json());
      if (s.ok) setSlots(await s.json());

      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return <div className="p-4 text-sm">Loading billing data…</div>;
  }

  return (
    <div className="p-6 space-y-8 text-sm text-gray-800">
      <div>
        <h1 className="text-xl font-semibold">Billing Overview</h1>
        <p className="text-gray-500">
          Read-only visibility into subscriptions, payments, and slots
        </p>
      </div>

      {/* PAYMENTS */}
      <section className="border rounded-lg p-4">
        <h2 className="font-semibold mb-3">Payments</h2>
        <table className="w-full border">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 border">ID</th>
              <th className="p-2 border">Type</th>
              <th className="p-2 border">Amount</th>
              <th className="p-2 border">Status</th>
              <th className="p-2 border">Created</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id}>
                <td className="p-2 border">{p.id.slice(0, 8)}</td>
                <td className="p-2 border">{p.payment_for}</td>
                <td className="p-2 border">
                  {p.currency} {p.amount / 100}
                </td>
                <td className="p-2 border">{p.status}</td>
                <td className="p-2 border">
                  {new Date(p.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* INVOICES */}
      <section className="border rounded-lg p-4">
        <h2 className="font-semibold mb-3">Invoices</h2>
        <table className="w-full border">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 border">Invoice</th>
              <th className="p-2 border">Amount</th>
              <th className="p-2 border">Status</th>
              <th className="p-2 border">Created</th>
              <th className="p-2 border">Download</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((i) => (
              <tr key={i.id}>
                <td className="p-2 border">{i.invoice_number}</td>
                <td className="p-2 border">
                  {i.currency} {i.amount / 100}
                </td>
                <td className="p-2 border">{i.status}</td>
                <td className="p-2 border">
                  {new Date(i.created_at).toLocaleString()}
                </td>
                <td className="p-2 border">
                  <a
                    href={i.download_url}
                    className="text-blue-600 underline"
                  >
                    PDF
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* SLOT ADDONS */}
      <section className="border rounded-lg p-4">
        <h2 className="font-semibold mb-3">Campaign Slot Add-ons</h2>
        <table className="w-full border">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 border">User</th>
              <th className="p-2 border">Slots</th>
              <th className="p-2 border">Purchased</th>
              <th className="p-2 border">Expires</th>
              <th className="p-2 border">Payment</th>
            </tr>
          </thead>
          <tbody>
            {slots.map((s) => (
              <tr key={s.id}>
                <td className="p-2 border">{s.user_id.slice(0, 8)}</td>
                <td className="p-2 border">{s.extra_ai_campaigns}</td>
                <td className="p-2 border">
                  {new Date(s.purchased_at).toLocaleString()}
                </td>
                <td className="p-2 border">
                  {new Date(s.expires_at).toLocaleString()}
                </td>
                <td className="p-2 border">
                  {s.payment_id ? s.payment_id.slice(0, 8) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="text-xs text-gray-500">
        This view is read-only. All mutations require explicit audited actions.
      </div>
    </div>
  );
}
