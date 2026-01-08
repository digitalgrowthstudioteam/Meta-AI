"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/apiFetch";

type UserRow = {
  id: string;
  email: string;
  created_at: string;
  is_active: boolean;
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [detailsUser, setDetailsUser] = useState<UserRow | null>(null);

  const adminEmail = typeof window !== "undefined"
    ? JSON.parse(sessionStorage.getItem("session_context") || "{}")?.user?.email
    : null;

  const load = async () => {
    try {
      const res = await apiFetch("/api/admin/users");
      const data = await res.json();
      setUsers(data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggleActive = async (user: UserRow) => {
    if (user.email === adminEmail) {
      alert("You cannot disable your own admin account.");
      return;
    }

    if (!confirm(`Confirm to ${user.is_active ? "DISABLE" : "ENABLE"} ${user.email}?`)) {
      return;
    }

    setProcessing(user.id);

    const res = await apiFetch("/api/admin/user/toggle-active", {
      method: "POST",
      body: JSON.stringify({ user_id: user.id }),
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      alert("Failed to update user");
    }

    await load();
    setProcessing(null);
  };

  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b">
        <h2 className="text-sm font-medium text-gray-900">Users</h2>
        <p className="text-xs text-gray-500">Enable/Disable & View User Details</p>
      </div>

      {loading ? (
        <div className="p-6 text-sm text-gray-500">Loading users…</div>
      ) : users.length === 0 ? (
        <div className="p-6 text-sm text-gray-500">No users found.</div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr className="text-left text-xs text-gray-500 uppercase">
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Joined</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr
                key={u.id}
                className="border-b last:border-0 hover:bg-gray-50"
              >
                <td className="px-4 py-2 font-medium">{u.email}</td>
                <td className="px-4 py-2 text-gray-600">
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-2">
                  {u.is_active ? (
                    <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-700">
                      Active
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-1 rounded bg-red-100 text-red-700">
                      Disabled
                    </span>
                  )}
                </td>
                <td className="px-4 py-2 text-right space-x-2">
                  <button
                    onClick={() => setDetailsUser(u)}
                    className="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50"
                  >
                    Details
                  </button>
                  <button
                    onClick={() => toggleActive(u)}
                    disabled={processing === u.id}
                    className={`text-xs px-2 py-1 rounded border ${
                      u.is_active
                        ? "border-red-300 text-red-700 hover:bg-red-50"
                        : "border-green-300 text-green-700 hover:bg-green-50"
                    } disabled:opacity-50`}
                  >
                    {u.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* DETAILS MODAL */}
      {detailsUser && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center">
          <div className="bg-white rounded-lg p-5 w-80 space-y-3">
            <h3 className="text-sm font-medium text-gray-900">User Details</h3>
            <div className="text-xs text-gray-700 space-y-1">
              <div>Email: {detailsUser.email}</div>
              <div>
                Joined:{" "}
                {new Date(detailsUser.created_at).toLocaleString()}
              </div>
              <div>Status: {detailsUser.is_active ? "Active" : "Disabled"}</div>
            </div>
            <button
              onClick={() => setDetailsUser(null)}
              className="w-full text-xs px-3 py-2 rounded bg-gray-100 hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
