"use client";

import { useEffect, useState } from "react";

type Invoice = {
  id: string;
  user_email: string;
  amount: number;
  currency: string;
  status: "paid" | "unpaid" | "void";
  period_from: string;
  period_to: string;
  created_at: string;
};

export default function AdminInvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/admin/invoices")
      .then((res) => res.json())
      .then((data) => {
        setInvoices(data || []);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-6 text-sm text-gray-800">
      <div className="text-xl font-semibold mb-4">Invoices</div>

      {loading ? (
        <div className="text-gray-500">Loading invoices…</div>
      ) : invoices.length === 0 ? (
        <div className="text-gray-500">No invoices found.</div>
      ) : (
        <div className="overflow-x-auto border rounded-md">
          <table className="min-w-full text-left border-collapse">
            <thead className="bg-gray-100 text-xs uppercase text-gray-600">
              <tr>
                <th className="px-3 py-2">Invoice ID</th>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">Amount</th>
                <th className="px-3 py-2">Period</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Created</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs">{inv.id}</td>
                  <td className="px-3 py-2">{inv.user_email}</td>
                  <td className="px-3 py-2">
                    {inv.currency} {(inv.amount / 100).toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {inv.period_from} → {inv.period_to}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        inv.status === "paid"
                          ? "bg-green-100 text-green-700"
                          : inv.status === "unpaid"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-200 text-gray-600"
                      }`}
                    >
                      {inv.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs">{inv.created_at}</td>
                  <td className="px-3 py-2">
                    <button
                      className="text-blue-600 hover:underline text-xs"
                      onClick={() => {
                        fetch(`/api/admin/invoices/${inv.id}/resend`, {
                          method: "POST",
                        });
                      }}
                    >
                      Resend Invoice
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
