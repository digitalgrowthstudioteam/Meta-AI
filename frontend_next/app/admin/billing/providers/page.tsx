"use client";

import { useEffect, useState } from "react";

type ProviderRow = {
  id: string;
  provider: string;
  mode: "TEST" | "LIVE";
  key_id: string;
  has_secret: boolean;
  active: boolean;
};

export default function BillingProvidersPage() {
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<ProviderRow[]>([]);
  const [mode, setMode] = useState<"TEST" | "LIVE">("TEST");

  const [form, setForm] = useState({
    key_id: "",
    key_secret: "",
    webhook_secret: "",
  });

  const load = async () => {
    setLoading(true);
    const r = await fetch("/api/admin/billing/providers/config");
    const data = await r.json();
    setRows(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const existing = rows.find(r => r.mode === mode);

  const handleSave = async () => {
    if (!form.key_id || !form.key_secret) {
      alert("key_id and key_secret required");
      return;
    }

    await fetch("/api/admin/billing/providers/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: "razorpay",
        mode,
        key_id: form.key_id,
        key_secret: form.key_secret,
        webhook_secret: form.webhook_secret || undefined,
      }),
    });

    alert("Saved");
    setForm({ key_id: "", key_secret: "", webhook_secret: "" });
    load();
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-semibold">Billing Provider Configuration</h1>

      <div className="flex gap-2">
        <button
          onClick={() => setMode("TEST")}
          className={`px-3 py-1 rounded ${mode === "TEST" ? "bg-blue-600 text-white" : "bg-gray-200"}`}
        >
          TEST
        </button>
        <button
          onClick={() => setMode("LIVE")}
          className={`px-3 py-1 rounded ${mode === "LIVE" ? "bg-blue-600 text-white" : "bg-gray-200"}`}
        >
          LIVE
        </button>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="space-y-3">
          <div className="border rounded p-4 bg-white space-y-2">
            <div className="text-sm text-gray-600">Provider: Razorpay</div>
            <div className="text-sm text-gray-600">Mode: {mode}</div>

            <div>
              <label className="block text-sm font-medium">Key ID</label>
              <input
                className="border rounded px-3 py-1 w-full"
                value={form.key_id}
                onChange={e => setForm({ ...form, key_id: e.target.value })}
                placeholder={existing?.key_id || "rzp_test_xxx"}
              />
            </div>

            <div>
              <label className="block text-sm font-medium">Key Secret</label>
              <input
                className="border rounded px-3 py-1 w-full"
                type="password"
                value={form.key_secret}
                onChange={e => setForm({ ...form, key_secret: e.target.value })}
                placeholder={existing?.has_secret ? "********" : "enter secret"}
              />
            </div>

            <div>
              <label className="block text-sm font-medium">Webhook Secret (optional)</label>
              <input
                className="border rounded px-3 py-1 w-full"
                type="password"
                value={form.webhook_secret}
                onChange={e => setForm({ ...form, webhook_secret: e.target.value })}
                placeholder="optional"
              />
            </div>

            <button
              onClick={handleSave}
              className="mt-3 px-4 py-2 rounded bg-blue-600 text-white"
            >
              Save
            </button>
          </div>

          <div className="text-sm text-gray-500">
            {existing ? "Existing config loaded." : "No config for this mode yet."}
          </div>
        </div>
      )}
    </div>
  );
}
