"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type DashboardStats = {
  users: number;
  subscriptions: {
    active: number;
    expired: number;
  };
  campaigns: {
    total: number;
    ai_active: number;
    manual: number;
  };
  last_activity: string | null;
  system_status: string;
};

type UserLite = {
  id: string;
  email: string;
};

export default function AdminDashboardPage() {
  const router = useRouter();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<UserLite[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState(false);

  // ---------------------------------------
  // LOAD DASHBOARD + USER LIST (ADMIN ONLY)
  // ---------------------------------------
  useEffect(() => {
    const load = async () => {
      try {
        const statsRes = await fetch("/api/admin/dashboard", {
          credentials: "include",
        });

        // 🔒 HARD GUARD — NOT ADMIN
        if (statsRes.status === 403) {
          router.replace("/dashboard");
          return;
        }

        const usersRes = await fetch("/api/admin/users", {
          credentials: "include",
        });

        setStats(await statsRes.json());
        setUsers(await usersRes.json());
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [router]);

  // ---------------------------------------
  // IMPERSONATE USER
  // ---------------------------------------
  const impersonate = () => {
    if (!selectedUser) return;

    sessionStorage.setItem("impersonate_user", selectedUser);
    setImpersonating(true);
    router.push("/dashboard");
  };

  if (loading) {
    return (
      <div className="text-sm text-gray-500">
        Loading admin dashboard…
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-sm text-red-600">
        Failed to load admin stats.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">
          Admin Dashboard
        </h1>
        <p className="text-sm text-gray-500">
          System health, usage, and admin controls
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="text-sm font-medium text-amber-900">
          View as User (Read-only)
        </div>
        <p className="mt-1 text-xs text-amber-700">
          Temporarily view the system exactly as a user sees it.
          No mutations allowed.
        </p>

        <div className="mt-3 flex gap-2">
          <select
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            className="flex-1 border rounded-md px-3 py-2 text-sm"
          >
            <option value="">Select user…</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.email}
              </option>
            ))}
          </select>

          <button
            onClick={impersonate}
            disabled={!selectedUser || impersonating}
            className="px-4 py-2 rounded-md text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
          >
            View as User
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">
          System OK
        </span>
        {stats.last_activity && (
          <span className="text-xs text-gray-500">
            Last activity:{" "}
            {new Date(stats.last_activity).toLocaleString()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Metric label="Total Users" value={stats.users} />
        <Metric
          label="Active Subscriptions"
          value={stats.subscriptions.active}
        />
        <Metric
          label="Expired Subscriptions"
          value={stats.subscriptions.expired}
        />
        <Metric
          label="Total Campaigns"
          value={stats.campaigns.total}
        />
        <Metric
          label="AI Active Campaigns"
          value={stats.campaigns.ai_active}
        />
        <Metric
          label="Manual Campaigns"
          value={stats.campaigns.manual}
        />
      </div>

      <div className="text-xs text-gray-400">
        All admin actions are logged and auditable.
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="bg-white border rounded-lg px-4 py-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-gray-900">
        {value}
      </div>
    </div>
  );
}
