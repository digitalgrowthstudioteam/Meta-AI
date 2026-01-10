"use client";

import { useEffect, useState } from "react";

type PricingConfig = {
  id: string;
  version: number;
  is_active: boolean;
  currency: string;
  tax_percentage: number;
  razorpay_mode: string;
  created_at: string;
  activated_at?: string | null;
};

export default function AdminSettingsPage() {
  const [configs, setConfigs] = useState<PricingConfig[]>([]);
  const [activeConfig, setActiveConfig] = useState<PricingConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);

  async function load() {
    const [activeRes, listRes] = await Promise.all([
      fetch("/api/admin/pricing-config/active"),
      fetch("/api/admin/pricing-config"),
    ]);

    if (activeRes.ok) {
      setActiveConfig(await activeRes.json());
    } else {
      setActiveConfig(null);
    }

    if (listRes.ok) {
      setConfigs(await listRes.json());
    }

    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function activateConfig(configId: string) {
    const reason = prompt("Reason for activating this pricing config?");
    if (!reason) return;

    setActivating(configId);

    const res = await fetch(
      `/api/admin/pricing-config/${configId}/activate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      }
    );

    setActivating(null);

    if (!res.ok) {
      alert("Activation failed");
      return;
    }

    await load();
  }

  if (loading) {
    return <div className="p-4 text-sm">Loading settings…</div>;
  }

  return (
    <div className="p-6 space-y-6 text-sm text-gray-800">
      <div>
        <h1 className="text-xl font-semibold">Admin Settings</h1>
        <p className="text-gray-500">
          System-wide configuration (audited & versioned)
        </p>
      </div>

      {/* ACTIVE PRICING CONFIG */}
      <div className="border rounded-lg p-4">
        <h2 className="font-semibold mb-2">Active Pricing Configuration</h2>
        {activeConfig ? (
          <div className="space-y-1">
            <div>Version: v{activeConfig.version}</div>
            <div>Currency: {activeConfig.currency}</div>
            <div>GST / Tax: {activeConfig.tax_percentage}%</div>
            <div>Razorpay Mode: {activeConfig.razorpay_mode}</div>
            <div>
              Activated At:{" "}
              {activeConfig.activated_at
                ? new Date(activeConfig.activated_at).toLocaleString()
                : "—"}
            </div>
          </div>
        ) : (
          <div className="text-gray-500">No active pricing config</div>
        )}
      </div>

      {/* PRICING CONFIG VERSIONS */}
      <div className="border rounded-lg p-4">
        <h2 className="font-semibold mb-3">Pricing Config Versions</h2>

        <table className="w-full border text-left">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 border">Version</th>
              <th className="p-2 border">Status</th>
              <th className="p-2 border">Currency</th>
              <th className="p-2 border">Tax %</th>
              <th className="p-2 border">Created At</th>
              <th className="p-2 border">Action</th>
            </tr>
          </thead>
          <tbody>
            {configs.map((c) => (
              <tr key={c.id}>
                <td className="p-2 border">v{c.version}</td>
                <td className="p-2 border">
                  {c.is_active ? "ACTIVE" : "INACTIVE"}
                </td>
                <td className="p-2 border">{c.currency}</td>
                <td className="p-2 border">{c.tax_percentage}%</td>
                <td className="p-2 border">
                  {new Date(c.created_at).toLocaleString()}
                </td>
                <td className="p-2 border">
                  {!c.is_active && (
                    <button
                      onClick={() => activateConfig(c.id)}
                      disabled={activating === c.id}
                      className="px-3 py-1 text-xs border rounded hover:bg-gray-100 disabled:opacity-50"
                    >
                      {activating === c.id ? "Activating…" : "Activate"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mt-3 text-xs text-gray-500">
          All activations are audited and reversible.
        </div>
      </div>
    </div>
  );
}
