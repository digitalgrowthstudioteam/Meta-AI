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
};

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

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

  async function updateSetting(key: keyof SystemSettings, value: any) {
    const reason = prompt(`Reason for changing ${key}?`);
    if (!reason) return;

    setSaving(key);

    const res = await fetch("/api/admin/meta-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        [key]: value,
        reason,
      }),
    });

    setSaving(null);

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
        <p className="text-gray-500">
          System-wide AI behavior (all changes audited)
        </p>
      </div>

      {/* TOGGLES */}
      <div className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold">AI Control Toggles</h2>

        {[
          ["expansion_mode_enabled", "Expansion Mode"],
          ["fatigue_mode_enabled", "Fatigue Mode"],
          ["auto_pause_enabled", "Auto-Pause"],
          ["confidence_gating_enabled", "Confidence Gating"],
        ].map(([key, label]) => (
          <div
            key={key}
            className="flex items-center justify-between border-b pb-2"
          >
            <span>{label}</span>
            <button
              disabled={saving === key}
              onClick={() =>
                updateSetting(
                  key as keyof SystemSettings,
                  !settings[key as keyof SystemSettings]
                )
              }
              className={`px-3 py-1 text-xs rounded border ${
                settings[key as keyof SystemSettings]
                  ? "bg-green-100 border-green-400"
                  : "bg-red-100 border-red-400"
              }`}
            >
              {settings[key as keyof SystemSettings] ? "ACTIVE" : "DISABLED"}
            </button>
          </div>
        ))}
      </div>

      {/* THROTTLING */}
      <div className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold">AI Throttling Controls</h2>

        <div className="space-y-2">
          <label>Max Optimizations / Day</label>
          <input
            type="number"
            min={0}
            max={500}
            value={settings.max_optimizations_per_day}
            onChange={(e) =>
              setSettings({
                ...settings,
                max_optimizations_per_day: Number(e.target.value),
              })
            }
            onBlur={(e) =>
              updateSetting(
                "max_optimizations_per_day",
                Number(e.target.value)
              )
            }
            className="border p-2 w-full"
          />
        </div>

        <div className="space-y-2">
          <label>Max Expansions / Day</label>
          <input
            type="number"
            min={0}
            max={200}
            value={settings.max_expansions_per_day}
            onChange={(e) =>
              setSettings({
                ...settings,
                max_expansions_per_day: Number(e.target.value),
              })
            }
            onBlur={(e) =>
              updateSetting(
                "max_expansions_per_day",
                Number(e.target.value)
              )
            }
            className="border p-2 w-full"
          />
        </div>

        <div className="space-y-2">
          <label>AI Refresh Frequency (minutes)</label>
          <input
            type="number"
            min={5}
            max={1440}
            value={settings.ai_refresh_frequency_minutes}
            onChange={(e) =>
              setSettings({
                ...settings,
                ai_refresh_frequency_minutes: Number(e.target.value),
              })
            }
            onBlur={(e) =>
              updateSetting(
                "ai_refresh_frequency_minutes",
                Number(e.target.value)
              )
            }
            className="border p-2 w-full"
          />
        </div>
      </div>

      <div className="text-xs text-gray-500">
        All changes are logged with before/after snapshots.
      </div>
    </div>
  );
}
