"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";

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
    try {
      setLoading(true);
      const r = await fetch("/api/admin/billing/providers/config");
      const data = await r.json();
      setRows(data);
    } catch (err) {
      toast.error("Failed to load provider configs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const existing = rows.find((r) => r.mode === mode);

  const handleSave = async () => {
    if (!form.key_id || !form.key_secret) {
      toast.error("Key ID and Secret are required");
      return;
    }

    const payload = {
      provider: "razorpay",
      mode,
      key_id: form.key_id,
      key_secret: form.key_secret,
      webhook_secret: form.webhook_secret || undefined,
    };

    try {
      await fetch("/api/admin/billing/providers/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      toast.success(`Saved ${mode} config`);
      setForm({ key_id: "", key_secret: "", webhook_secret: "" });
      load();
    } catch (err) {
      toast.error("Failed to save config");
    }
  };

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Billing Provider Configuration</h1>
        <p className="text-sm text-gray-500">Manage billing provider credentials for Razorpay.</p>
      </div>

      <div className="flex gap-2">
        {["TEST", "LIVE"].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m as any)}
            className={`px-4 py-2 text-sm rounded-md ${
              mode === m ? "bg-indigo-600 text-white" : "bg-gray-200 text-gray-700"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 space-y-6 max-w-xl">
          <div className="space-y-1 text-sm">
            <div className="text-gray-700">Provider: Razorpay</div>
            <div className="text-gray-500">Mode: {mode}</div>
          </div>

          {/* Key ID */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Key ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder={existing?.key_id || "rzp_test_xxx"}
              value={form.key_id}
              onChange={(e) => setForm({ ...form, key_id: e.target.value })}
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          {/* Secret */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Key Secret <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              placeholder={existing?.has_secret ? "********" : "enter secret"}
              value={form.key_secret}
              onChange={(e) => setForm({ ...form, key_secret: e.target.value })}
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          {/* Webhook Secret */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Webhook Secret (optional)</label>
            <input
              type="password"
              placeholder="optional"
              value={form.webhook_secret}
              onChange={(e) => setForm({ ...form, webhook_secret: e.target.value })}
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            Save
          </button>

          <p className="text-xs text-gray-400">
            {existing ? "Configuration loaded." : "No configuration for this mode yet."}
          </p>
        </div>
      )}
    </div>
  );
}
