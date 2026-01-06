"use client";

import { useEffect, useState } from "react";

type UserRow = {
  id: string;
  email: string;
  created_at: string;
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/admin/users", {
          credentials: "include",
        });
        const data = await res.json();
        setUsers(data || []);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const impersonate = async (user: UserRow) => {
    if (!confirm(`View dashboard as ${user.email}?`)) return;

    setImpersonating(user.id);

    try {
      const res = await fetch("/api/admin/impersonate", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: user.id,
        }),
      });

      if (!res.ok) {
        alert("Failed to impersonate user");
        return;
      }

      // 🔒 Store impersonation context (session-only)
      sessionStorage.setItem(
        "admin_impersonation",
        JSON.stringify({
          user_id: user.id,
          email: user.email,
          started_at: new Date().toISOString(),
        })
      );

      // Reload app as impersonated user
      window.location.href = "/dashboard";
    } finally {
      setImpersonating(null);
    }
  };

  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b">
        <h2 className="text-sm font-medium text-gray-900">
          Users
        </h2>
        <p className="text-xs text-gray-500">
          Read-only list • Admin impersonation enabled
        </p>
      </div>

      {loading ? (
        <div className="p-6 text-sm text-gray-500">
          Loading users…
        </div>
      ) : users.length === 0 ? (
        <div className="p-6 text-sm text-gray-500">
          No users found.
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr className="text-left text-xs text-gray-500 uppercase">
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Joined</th>
              <th className="px-4 py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr
                key={u.id}
                className="border-b last:border-0 hover:bg-gray-50"
              >
                <td className="px-4 py-2 font-medium">
                  {u.email}
                </td>
                <td className="px-4 py-2 text-gray-600">
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => impersonate(u)}
                    disabled={impersonating === u.id}
                    className="text-xs px-3 py-1 rounded border border-amber-300 text-amber-700 hover:bg-amber-50 disabled:opacity-50"
                  >
                    View as User
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
