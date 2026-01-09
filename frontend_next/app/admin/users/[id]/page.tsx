"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type AdminUserRow = {
  id: string;
  email: string;
  is_active: boolean;
};

export default function AdminUserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params?.id as string;

  const [user, setUser] = useState<AdminUserRow | null>(null);
  const [loading, setLoading] = useState(true);

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

      <div className="rounded border bg-white p-4 text-sm">
        <div className="font-medium mb-3">Actions</div>
        <button
          className="px-3 py-2 text-sm rounded bg-gray-200 text-gray-700 cursor-not-allowed"
          disabled
        >
          Impersonate (coming soon)
        </button>
      </div>
    </div>
  );
}
