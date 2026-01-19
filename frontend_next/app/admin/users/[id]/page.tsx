"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "../../../../lib/fetcher";

type AdminUser = {
  id: string;
  email: string;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
};

type Subscription = {
  id: string;
  plan_name: string;
  status: string;
  starts_at: string;
  ends_at: string | null;
  pricing_mode: string;
  custom_price: number | null;
  never_expires: boolean;
};

type Tab = "profile" | "meta" | "campaigns" | "billing" | "ai" | "subscription";

export default function AdminUserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params?.id as string;

  const [tab, setTab] = useState<Tab>("profile");
  const [loading, setLoading] = useState(true);

  const [user, setUser] = useState<AdminUser | null>(null);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [assignOpen, setAssignOpen] = useState(false);

  useEffect(() => {
    if (!userId) return;
    (async () => {
      setLoading(true);
      const res = await apiFetch(`/admin/users/${userId}`, { cache: "no-store" });
      const json = await res.json();
      setUser(json.user || null);
      setLoading(false);
    })();
  }, [userId]);

  const loadSubscriptions = async () => {
    const res = await apiFetch(`/admin/users/${userId}/subscriptions`, { cache: "no-store" });
    const json = await res.json();
    setSubscriptions(json || []);
  };

  useEffect(() => {
    if (userId) loadSubscriptions();
  }, [userId]);

  if (loading) return <div className="text-sm text-gray-600">Loading user…</div>;

  if (!user)
    return (
      <div className="space-y-4">
        <BackButton />
        <div className="text-red-600 text-sm">User not found</div>
      </div>
    );

  return (
    <div className="space-y-6">
      <BackButton />
      <h1 className="text-lg font-semibold">{user.email}</h1>

      <TabBar tab={tab} setTab={setTab} />

      {tab === "profile" && (
        <Card>
          <Row label="Email" value={user.email} />
          <Row label="Status" value={user.is_active ? "Active" : "Inactive"} />
          <Row label="Created" value={user.created_at || "—"} />
          <Row label="Last Login" value={user.last_login_at || "—"} />
        </Card>
      )}

      {tab === "subscription" && (
        <Card>
          <div className="flex justify-between items-center mb-2">
            <div className="text-sm font-medium">Subscription History</div>
            <button
              className="px-2 py-1 text-xs bg-blue-600 text-white rounded"
              onClick={() => setAssignOpen(true)}
            >
              Assign Subscription
            </button>
          </div>

          {subscriptions.length === 0 ? (
            <Empty />
          ) : (
            subscriptions.map((s) => (
              <div key={s.id} className="border-b pb-2 mb-2 text-sm">
                <div className="font-medium">
                  {s.plan_name} — {s.status.toUpperCase()}
                </div>
                <div>
                  Starts: {new Date(s.starts_at).toLocaleDateString()} | Ends:{" "}
                  {s.never_expires
                    ? "Never"
                    : s.ends_at
                    ? new Date(s.ends_at).toLocaleDateString()
                    : "—"}
                </div>
                <div>Pricing: {s.pricing_mode}</div>
                {s.custom_price !== null && <div>Custom Price: ₹{s.custom_price}</div>}
              </div>
            ))
          )}
        </Card>
      )}

      {assignOpen && (
        <AssignModal
          userId={userId}
          onClose={() => setAssignOpen(false)}
          onAssigned={() => {
            setAssignOpen(false);
            loadSubscriptions();
          }}
        />
      )}
    </div>
  );
}

/* ------------------------- SUB COMPONENTS ------------------------- */

function BackButton() {
  const router = useRouter();
  return (
    <button onClick={() => router.back()} className="text-blue-600 hover:underline text-sm">
      ← Back
    </button>
  );
}

function TabBar({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const tabs: Tab[] = ["profile", "meta", "campaigns", "billing", "ai", "subscription"];
  return (
    <div className="flex gap-2 border-b">
      {tabs.map((t) => (
        <button
          key={t}
          onClick={() => setTab(t)}
          className={`px-3 py-2 text-sm border-b-2 ${
            tab === t ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500"
          }`}
        >
          {t.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded border bg-white p-4 space-y-2 text-sm">{children}</div>;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}</span>
      <span>{value}</span>
    </div>
  );
}

function Empty() {
  return <div className="text-sm text-gray-500">No data available.</div>;
}

/* ------------------------- ASSIGN MODAL ------------------------- */

function AssignModal({
  userId,
  onClose,
  onAssigned,
}: {
  userId: string;
  onClose: () => void;
  onAssigned: () => void;
}) {
  const [planId, setPlanId] = useState<string>("1");
  const [pricingMode, setPricingMode] = useState<"standard" | "custom">("standard");
  const [customPrice, setCustomPrice] = useState<string>("0");
  const [months, setMonths] = useState<string>("1");
  const [days, setDays] = useState<string>("0");
  const [neverExp, setNeverExp] = useState(false);
  const [saving, setSaving] = useState(false);

  const PLANS = [
    { id: "1", label: "FREE" },
    { id: "2", label: "STARTER" },
    { id: "3", label: "PRO" },
    { id: "4", label: "AGENCY" },
    { id: "5", label: "ENTERPRISE" },
  ];

  const handleSubmit = async () => {
    setSaving(true);
    await apiFetch("/admin/subscriptions/assign", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        plan_id: planId,
        pricing_mode: pricingMode,
        custom_price: pricingMode === "custom" ? Number(customPrice) : null,
        custom_duration_months: Number(months),
        custom_duration_days: Number(days),
        never_expires: neverExp,
      }),
    });
    setSaving(false);
    onAssigned();
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded p-4 w-96 space-y-3 text-sm shadow-lg">
        <div className="font-medium text-base">Assign Subscription</div>

        <div>
          <label className="block mb-1">Plan</label>
          <select
            className="border rounded px-2 py-1 w-full"
            value={planId}
            onChange={(e) => setPlanId(e.target.value)}
          >
            {PLANS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block mb-1">Pricing Mode</label>
          <select
            className="border rounded px-2 py-1 w-full"
            value={pricingMode}
            onChange={(e) => setPricingMode(e.target.value as any)}
          >
            <option value="standard">Standard</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        {pricingMode === "custom" && (
          <div>
            <label className="block mb-1">Custom Price (₹)</label>
            <input
              type="number"
              min="0"
              className="border rounded px-2 py-1 w-full"
              value={customPrice}
              onChange={(e) => setCustomPrice(e.target.value)}
            />
          </div>
        )}

        <div className="flex gap-2">
          <div className="flex-1">
            <label className="block mb-1">Months</label>
            <input
              type="number"
              min="0"
              className="border rounded px-2 py-1 w-full"
              value={months}
              onChange={(e) => setMonths(e.target.value)}
            />
          </div>
          <div className="flex-1">
            <label className="block mb-1">Days</label>
            <input
              type="number"
              min="0"
              className="border rounded px-2 py-1 w-full"
              value={days}
              onChange={(e) => setDays(e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input type="checkbox" checked={neverExp} onChange={(e) => setNeverExp(e.target.checked)} />
          <span>Never Expires</span>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button className="px-3 py-1 text-xs" onClick={onClose}>
            Cancel
          </button>
          <button
            disabled={saving}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded disabled:opacity-50"
            onClick={handleSubmit}
          >
            {saving ? "Saving…" : "Assign"}
          </button>
        </div>
      </div>
    </div>
  );
}
