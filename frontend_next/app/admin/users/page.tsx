"use client";

import { useEffect, useState } from "react";

type AdminUserRow = {
  id: string;
  email: string;
  is_active: boolean;
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/admin/users", {
          credentials: "include",
          cache: "no-store",
        });
        const json = await res.json();
        setUsers(json || []);
      } catch (e) {
        console.error("Failed to load users", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-600">Loading users…</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Users & Impersonation</h1>

      <div className="rounded border bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-2 text-left">Email</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-3 text-center text-gray-500">
                  No users found
                </td>
              </tr>
            )}

            {users.map((u) => (
              <tr key={u.id} className="border-t">
                <td className="px-4 py-2">{u.email}</td>
                <td className="px-4 py-2">
                  {u.is_active ? (
                    <span className="text-green-600">Active</span>
                  ) : (
                    <span className="text-red-600">Inactive</span>
                  )}
                </td>
                <td className="px-4 py-2 text-right">
                  <a
                    href={`/admin/users/${u.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    View →
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
