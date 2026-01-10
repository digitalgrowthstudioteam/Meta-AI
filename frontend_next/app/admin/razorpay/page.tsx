"use client";

import { useEffect, useState } from "react";

type RazorpayEvent = {
  id: string;
  entity_type: "order" | "payment" | "refund" | "webhook";
  entity_id: string;
  status: string;
  amount?: number;
  currency?: string;
  created_at: string;
  verified?: boolean;
};

export default function AdminRazorpayPage() {
  const [events, setEvents] = useState<RazorpayEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/admin/razorpay")
      .then((res) => res.json())
      .then((data) => {
        setEvents(data || []);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-6 text-sm text-gray-800">
      <div className="text-xl font-semibold mb-4">Razorpay Explorer</div>

      {loading ? (
        <div className="text-gray-500">Loading Razorpay events…</div>
      ) : events.length === 0 ? (
        <div className="text-gray-500">No Razorpay activity found.</div>
      ) : (
        <div className="overflow-x-auto border rounded-md">
          <table className="min-w-full border-collapse">
            <thead className="bg-gray-100 text-xs uppercase text-gray-600">
              <tr>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Entity ID</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Amount</th>
                <th className="px-3 py-2">Verification</th>
                <th className="px-3 py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id} className="border-t">
                  <td className="px-3 py-2 font-medium">
                    {e.entity_type.toUpperCase()}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{e.entity_id}</td>
                  <td className="px-3 py-2 text-xs">{e.status}</td>
                  <td className="px-3 py-2 text-xs">
                    {e.amount
                      ? `${e.currency} ${(e.amount / 100).toFixed(2)}`
                      : "—"}
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {e.verified === undefined ? (
                      "—"
                    ) : e.verified ? (
                      <span className="text-green-600 font-medium">
                        Verified
                      </span>
                    ) : (
                      <span className="text-red-600 font-medium">
                        Failed
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-xs">{e.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
