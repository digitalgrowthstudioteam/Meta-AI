"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type AdminUser = {
  id: string;
  email: string;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
};

type MetaAccount = {
  id: string;
  name: string;
  status: string;
  last_sync_at?: string;
};

type Campaign = {
  id: string;
  name: string;
  objective: string;
  ai_active: boolean;
  status: string;
  last_ai_action_at?: string;
};

type Invoice = {
  id: string;
  amount: number;
  status: string;
  created_at: string;
};

type AIAction = {
  id: string;
  decision: string;
  confidence: number;
  created_at: string;
};

type Tab =
  | "profile"
  | "meta"
  | "campaigns"
  | "billing"
  | "ai";

export default function AdminUserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params?.id as string;

  const [tab, setTab] = useState<Tab>("profile");
  const [loading, setLoading] = useState(true);

  const [user, setUser] = useState<AdminUser | null>(null);
  const [metaAccounts, setMetaAccounts] = useState<MetaAccount[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [aiActions, setAiActions] = useState<AIAction[]>([]);

  useEffect(() => {
    if (!userId) return;

    (async () => {
      try {
        const res = await fetch(`/api/admin/users/${userId}`, {
          credentials: "include",
          cache: "no-store",
        });
        const json = await res.json();

        setUser(json.user);
        setMetaAccounts(json.meta_accounts || []);
        setCampaigns(json.campaigns || []);
        setInvoices(json.invoices || []);
        setAiActions(json.ai_actions || []);
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

      <h1 className="text-lg font-semibold">{user.email}</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <TabButton tab="profile" current={tab} setTab={setTab} />
        <TabButton tab="meta" current={tab} setTab={setTab} />
        <TabButton tab="campaigns" current={tab} setTab={setTab} />
        <TabButton tab="billing" current={tab} setTab={setTab} />
        <TabButton tab="ai" current={tab} setTab={setTab} />
      </div>

      {/* PROFILE */}
      {tab === "profile" && (
        <Card>
          <Row label="Email" value={user.email} />
          <Row
            label="Status"
            value={user.is_active ? "Active" : "Inactive"}
          />
          <Row
            label="Created"
            value={user.created_at || "—"}
          />
          <Row
            label="Last Login"
            value={user.last_login_at || "—"}
          />
        </Card>
      )}

      {/* META */}
      {tab === "meta" && (
        <Card>
          {metaAccounts.length === 0 && <Empty />}
          {metaAccounts.map((a) => (
            <div key={a.id} className="border-b pb-2 mb-2 text-sm">
              <div className="font-medium">{a.name}</div>
              <div>Status: {a.status}</div>
              <div>Last Sync: {a.last_sync_at || "—"}</div>
            </div>
          ))}
        </Card>
      )}

      {/* CAMPAIGNS */}
      {tab === "campaigns" && (
        <Card>
          {campaigns.length === 0 && <Empty />}
          {campaigns.map((c) => (
            <div key={c.id} className="border-b pb-2 mb-2 text-sm">
              <div className="font-medium">{c.name}</div>
              <div>Objective: {c.objective}</div>
              <div>AI: {c.ai_active ? "ON" : "OFF"}</div>
              <div>Status: {c.status}</div>
              <div>Last AI Action: {c.last_ai_action_at || "—"}</div>
            </div>
          ))}
        </Card>
      )}

      {/* BILLING */}
      {tab === "billing" && (
        <Card>
          {invoices.length === 0 && <Empty />}
          {invoices.map((i) => (
            <div key={i.id} className="border-b pb-2 mb-2 text-sm">
              <div>Invoice #{i.id}</div>
              <div>Amount: ₹{i.amount}</div>
              <div>Status: {i.status}</div>
              <div>Date: {new Date(i.created_at).toLocaleDateString()}</div>
            </div>
          ))}
        </Card>
      )}

      {/* AI */}
      {tab === "ai" && (
        <Card>
          {aiActions.length === 0 && <Empty />}
          {aiActions.map((a) => (
            <div key={a.id} className="border-b pb-2 mb-2 text-sm">
              <div>
                Decision: <b>{a.decision}</b>
              </div>
              <div>Confidence: {a.confidence}%</div>
              <div>
                Time: {new Date(a.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

function TabButton({
  tab,
  current,
  setTab,
}: {
  tab: Tab;
  current: Tab;
  setTab: (t: Tab) => void;
}) {
  return (
    <button
      onClick={() => setTab(tab)}
      className={`px-3 py-2 text-sm border-b-2 ${
        current === tab
          ? "border-blue-600 text-blue-600"
          : "border-transparent text-gray-500"
      }`}
    >
      {tab.toUpperCase()}
    </button>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded border bg-white p-4 space-y-2 text-sm">
      {children}
    </div>
  );
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
  return (
    <div className="text-sm text-gray-500">No data available.</div>
  );
}
