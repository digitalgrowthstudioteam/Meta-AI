"use client";

import { useEffect, useState } from "react";

type AuditLog = {
  id: string;
  campaign_id: string;
  actor_type: string;
  action_type: string;
  reason: string | null;
  created_at: string;
};

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/admin/audit/actions", {
          credentials: "include",
        });
        const data = await res.json();
        setLogs(data || []);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b">
        <h2 className="text-sm font-medium text-gray-900">
          Campaign Action Audit Log
        </h2>
        <p className="text-xs text-gray-500">
          Immutable, read-only system history
        </p>
      </div>

      {loading ? (
        <div className="p-6 text-sm text-gray-500">Loading…</div>
      ) : logs.length === 0 ? (
        <div className="p-6 text-sm text-gray-500">
          No audit records found.
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr className="text-left text-xs text-gray-500 uppercase">
              <th className="px-4 py-2">Time</th>
              <th className="px-4 py-2">Actor</th>
              <th className="px-4 py-2">Action</th>
              <th className="px-4 py-2">Reason</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr
                key={log.id}
                className="border-b last:border-0 hover:bg-gray-50"
              >
                <td className="px-4 py-2 text-gray-600">
                  {new Date(log.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-2 font-medium">
                  {log.actor_type}
                </td>
                <td className="px-4 py-2">
                  {log.action_type}
                </td>
                <td className="px-4 py-2 text-gray-600">
                  {log.reason || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
