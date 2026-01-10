"use client";

import { useEffect, useState } from "react";

type SystemSettings = {
  expansion_mode_enabled: boolean;
  fatigue_mode_enabled: boolean;
  auto_pause_enabled: boolean;
  confidence_gating_enabled: boolean;
  max_optimizations_per_day: number;
  max_expansions_per_day: number;
  ai_refresh_frequency_minutes: number;

  // audit metadata (already exists in backend)
  last_modified_by?: string;
  last_modified_at?: string;

  // usage counters (already enforced in backend)
  current_optimizations_today?: number;
  current_expansions_today?: number;
};

type PendingChange = {
  key: keyof SystemSettings;
  nextValue: any;
  label: string;
};

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [modal, setModal] = useState<PendingChange | null>(null);
  const [reason, setReason] = useState("");

  async function load() {
    const res = await fetch("/api/admin/meta-settings");
    if (res.ok) {
      setSettings(await res.json());
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function confirmChange() {
    if (!modal || !reason.trim()) return;

    setSaving(true);

    const res = await fetch("/api/admin/meta-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        [modal.key]: modal.nextValue,
        reason,
      }),
    });

    setSaving(false);
    setModal(null);
    setReason("");

    if (!res.ok) {
      alert("Update failed");
      return;
    }

    await load();
  }

  if (loading || !settings) {
    return <div className="p-6 text-sm">Loading system controls…</div>;
  }

  return (
    <div className="p-6 space-y-6 text-sm text-gray-800">
      <div>
        <h1 className="text-xl font-semibold">Global AI System Controls</h1>
        <p className="text-gray-500">System-wide AI behavior (audited)</p>
      </div>

      {/* TOGGLES */}
      <div className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold">AI Control Toggles</h2>

        {[
          ["expansion_mode_enabled", "Expansion Mode"],
          ["fatigue_mode_enabled", "Fatigue Mode"],
          ["auto_pause_enabled", "Auto-Pause"],
          ["confidence_gating_enabled", "Confidence Gating"],
        ].map(([key, label]) => {
          const k = key as keyof SystemSettings;
          const enabled = settings[k] as boolean;

          return (
            <div key={key} className="flex justify-between items-center border-b pb-2">
              <div>
                <div className="font-medium">{label}</div>
                <div className="text-xs text-gray-500">
                  Status:{" "}
                  <span
                    className={`px-2 py-0.5 rounded ${
                      enabled
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {enabled ? "ACTIVE" : "DISABLED"}
                  </span>
                </div>
              </div>

              <button
                onClick={() =>
                  setModal({
                    key: k,
                    nextValue: !enabled,
                    label,
                  })
                }
                className="px-3 py-1 text-xs border rounded hover:bg-gray-100"
              >
                Change
              </button>
            </div>
          );
        })}
      </div>

      {/* THROTTLING */}
      <div className="border rounded-lg p-4 space-y-6">
        <h2 className="font-semibold">AI Throttling Controls</h2>

        {/* Optimizations */}
        <div>
          <div className="flex justify-between">
            <label>Max Optimizations / Day</label>
            <span className="text-xs text-gray-500">
              {settings.current_optimizations_today ?? 0} /{" "}
              {settings.max_optimizations_per_day}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={500}
            value={settings.max_optimizations_per_day}
            onChange={(e) =>
              setModal({
                key: "max_optimizations_per_day",
                nextValue: Number(e.target.value),
                label: "Max Optimizations / Day",
              })
            }
          />
          <input
            type="number"
            className="border p-1 w-full mt-1"
            value={settings.max_optimizations_per_day}
            readOnly
          />
        </div>

        {/* Expansions */}
        <div>
          <div className="flex justify-between">
            <label>Max Expansions / Day</label>
            <span className="text-xs text-gray-500">
              {settings.current_expansions_today ?? 0} /{" "}
              {settings.max_expansions_per_day}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={200}
            value={settings.max_expansions_per_day}
            onChange={(e) =>
              setModal({
                key: "max_expansions_per_day",
                nextValue: Number(e.target.value),
                label: "Max Expansions / Day",
              })
            }
          />
          <input
            type="number"
            className="border p-1 w-full mt-1"
            value={settings.max_expansions_per_day}
            readOnly
          />
        </div>

        {/* Refresh */}
        <div>
          <label>AI Refresh Frequency (minutes)</label>
          <input
            type="range"
            min={5}
            max={1440}
            value={settings.ai_refresh_frequency_minutes}
            onChange={(e) =>
              setModal({
                key: "ai_refresh_frequency_minutes",
                nextValue: Number(e.target.value),
                label: "AI Refresh Frequency",
              })
            }
          />
          <input
            type="number"
            className="border p-1 w-full mt-1"
            value={settings.ai_refresh_frequency_minutes}
            readOnly
          />
        </div>
      </div>

      {/* AUDIT FOOTER */}
      <div className="text-xs text-gray-500">
        Last modified by {settings.last_modified_by ?? "—"} at{" "}
        {settings.last_modified_at
          ? new Date(settings.last_modified_at).toLocaleString()
          : "—"}
      </div>

      {/* CONFIRM MODAL */}
      {modal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center">
          <div className="bg-white p-4 rounded w-96 space-y-3">
            <h3 className="font-semibold">Confirm Change</h3>

            <div className="text-xs text-gray-600">
              <div>Setting: {modal.label}</div>
              <div>New value: {String(modal.nextValue)}</div>
            </div>

            <textarea
              className="border p-2 w-full text-sm"
              rows={3}
              placeholder="Reason (required)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setModal(null)}
                className="px-3 py-1 text-xs border rounded"
              >
                Cancel
              </button>
              <button
                onClick={confirmChange}
                disabled={saving || !reason.trim()}
                className="px-3 py-1 text-xs border rounded bg-black text-white disabled:opacity-50"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
