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

type AuditLogDetail = {
  id: string;
  campaign_id: string;
  actor_type: string;
  action_type: string;
  reason: string | null;
  before_state: Record<string, any>;
  after_state: Record<string, any>;
  created_at: string;
};

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedLog, setSelectedLog] = useState<AuditLogDetail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);

  // -----------------------------------
  // LOAD AUDIT LIST
  // -----------------------------------
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

  // -----------------------------------
  // OPEN DRAWER
  // -----------------------------------
  const openDrawer = async (id: string) => {
    setDrawerOpen(true);
    setDrawerLoading(true);
    setSelectedLog(null);

    try {
      const res = await fetch(`/api/admin/audit/actions/${id}`, {
        credentials: "include",
      });
      const data = await res.json();
      setSelectedLog(data);
    } finally {
      setDrawerLoading(false);
    }
  };

  return (
    <>
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
                  onClick={() => openDrawer(log.id)}
                  className="border-b last:border-0 hover:bg-amber-50 cursor-pointer"
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

      {/* =========================
          DRAWER
         ========================= */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex">
          {/* OVERLAY */}
          <div
            className="flex-1 bg-black/30"
            onClick={() => setDrawerOpen(false)}
          />

          {/* PANEL */}
          <div className="w-full max-w-md bg-white border-l shadow-xl overflow-y-auto">
            <div className="px-4 py-3 border-b flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-gray-900">
                  Audit Detail
                </h3>
                <p className="text-xs text-gray-500">
                  Immutable snapshot
                </p>
              </div>
              <button
                className="text-sm text-gray-500 hover:text-gray-800"
                onClick={() => setDrawerOpen(false)}
              >
                Close
              </button>
            </div>

            {drawerLoading || !selectedLog ? (
              <div className="p-6 text-sm text-gray-500">
                Loading details…
              </div>
            ) : (
              <div className="p-4 space-y-4 text-sm">
                <DetailRow label="Time">
                  {new Date(selectedLog.created_at).toLocaleString()}
                </DetailRow>

                <DetailRow label="Actor">
                  {selectedLog.actor_type}
                </DetailRow>

                <DetailRow label="Action">
                  {selectedLog.action_type}
                </DetailRow>

                <DetailRow label="Reason">
                  {selectedLog.reason || "—"}
                </DetailRow>

                <div>
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    Before State
                  </div>
                  <pre className="bg-gray-50 border rounded p-2 text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.before_state, null, 2)}
                  </pre>
                </div>

                <div>
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    After State
                  </div>
                  <pre className="bg-gray-50 border rounded p-2 text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.after_state, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

/* -------------------------- */
/* SMALL UI HELPERS           */
/* -------------------------- */

function DetailRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500">
        {label}
      </div>
      <div className="text-sm text-gray-900">
        {children}
      </div>
    </div>
  );
}
