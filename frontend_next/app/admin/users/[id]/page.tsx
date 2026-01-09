"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type AdminUserRow = {
  id: string;
  email: string;
  is_active: boolean;
};

type SupportAction =
  | "force_meta_resync"
  | "refresh_billing"
  | "clear_ai_queue"
  | "reprocess_webhooks"
  | "regenerate_invoices"
  | "rebuild_ml";

export default function AdminUserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params?.id as string;

  const [user, setUser] = useState<AdminUserRow | null>(null);
  const [loading, setLoading] = useState(true);

  const [reason, setReason] = useState("");
  const [action, setAction] = useState<SupportAction | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!userId) return;

    (async () => {
      try {
        const res = await fetch("/api/admin/users", {
          credentials: "include",
          cache: "no-store",
        });
        const json: AdminUserRow[] = await res.json();
        const found = json.find((u) => u.id === userId) || null;
        setUser(found);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [userId]);

  const startImpersonation = async () => {
    await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/impersonate?user_id=${userId}`,
      {
        method: "POST",
        credentials: "include",
      }
    );
    router.refresh();
  };

  const runSupportAction = async () => {
    if (!action || !reason.trim()) return;

    setSubmitting(true);
    await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/admin/support/${action}`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          reason,
        }),
      }
    );

    setSubmitting(false);
    setReason("");
    setAction(null);
    alert("Action executed and logged");
  };

  if (loading) {
    return <div className="text-sm text-gray-600">Loading user…</div>;
  }

  if (!user) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:underline text-sm"
        >
          ← Back
        </button>
        <div className="text-red-600 text-sm">User not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => router.back()}
        className="text-blue-600 hover:underline text-sm"
      >
        ← Back
      </button>

      <h1 className="text-lg font-semibold">User Details</h1>

      {/* USER INFO */}
      <div className="rounded border bg-white p-4 space-y-3 text-sm">
        <div>
          <span className="font-medium">Email:</span> {user.email}
        </div>

        <div>
          <span className="font-medium">Status:</span>{" "}
          {user.is_active ? (
            <span className="text-green-600">Active</span>
          ) : (
            <span className="text-red-600">Inactive</span>
          )}
        </div>
      </div>

      {/* IMPERSONATION */}
      <div className="rounded border bg-white p-4 space-y-3 text-sm">
        <div className="font-medium">Impersonation</div>
        <button
          onClick={startImpersonation}
          className="px-3 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
        >
          View as User (Read-only)
        </button>
      </div>

      {/* SUPPORT TOOLS */}
      <div className="rounded border bg-white p-4 space-y-4 text-sm">
        <div className="font-medium">Support Tools (Audited)</div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <ActionButton label="Force Meta Resync" onClick={() => setAction("force_meta_resync")} />
          <ActionButton label="Refresh Billing from Razorpay" onClick={() => setAction("refresh_billing")} />
          <ActionButton label="Clear AI Queue" onClick={() => setAction("clear_ai_queue")} />
          <ActionButton label="Reprocess Razorpay Webhooks" onClick={() => setAction("reprocess_webhooks")} />
          <ActionButton label="Regenerate Invoice PDFs" onClick={() => setAction("regenerate_invoices")} />
          <ActionButton label="Rebuild ML Aggregations" onClick={() => setAction("rebuild_ml")} />
        </div>

        {action && (
          <div className="border-t pt-4 space-y-3">
            <div className="text-xs text-gray-600">
              Reason is mandatory. Action will be logged.
            </div>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full border rounded p-2 text-sm"
              placeholder="Enter reason for this action"
            />
            <div className="flex gap-2">
              <button
                disabled={submitting}
                onClick={runSupportAction}
                className="px-3 py-2 rounded bg-red-600 text-white text-sm"
              >
                Confirm & Execute
              </button>
              <button
                onClick={() => {
                  setAction(null);
                  setReason("");
                }}
                className="px-3 py-2 rounded bg-gray-200 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-2 rounded border text-left hover:bg-gray-50"
    >
      {label}
    </button>
  );
}
