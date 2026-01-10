"use client";

import { useEffect, useState } from "react";

type GlobalSettings = {
  meta_sync_enabled: boolean;
  ai_globally_enabled: boolean;
  maintenance_mode: boolean;
  site_name?: string;
  dashboard_title?: string;
  logo_url?: string;
};

type ThrottleConfig = {
  max_optimizations_per_day: number;
  max_expansions_per_day: number;
  ai_refresh_frequency_minutes: number;
};

export default function AdminAISystemControlsPage() {
  const [settings, setSettings] = useState<GlobalSettings | null>(null);
  const [throttles, setThrottles] = useState<ThrottleConfig>({
    max_optimizations_per_day: 50,
    max_expansions_per_day: 20,
    ai_refresh_frequency_minutes: 60,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    const res = await fetch("/api/admin/settings");
    if (res.ok) {
      const data = await res.json();
      setSettings(data);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function updateToggle(
    field: keyof GlobalSettings,
    value: boolean
  ) {
    const reason = prompt(
      `Reason for changing ${field} to ${value ? "ON" : "OFF"}?`
    );
    if (!reason) return;

    setSaving(true);

    const res = await fetch("/api/admin/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        [field]: value,
        reason,
      }),
    });

    setSaving(false);

    if (!res.ok) {
      alert("Update failed");
      return;
    }

    await load();
  }

  async function saveThrottles() {
    const reason = prompt("Reason for updating AI throttling limits?");
    if (!reason) return;

    setSaving(true);

    const res = await fetch("/api/admin/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...throttles,
        reason,
      }),
    });

    setSaving(false);

    if (!res.ok) {
      alert("Update failed");
      return;
    }

    await load();
  }

  if (loading || !settings) {
    return <div className="p-6 text-sm">Loading AI system controls…</div>;
  }

  return (
    <div className="p-6 space-y-8 text-sm text-gray-800">
      <div>
        <h1 className="text-xl font-semibold">
          Global AI System Controls
        </h1>
        <p className="text-gray-500">
          System-wide AI governance (audited & reversible)
        </p>
      </div>

      {/* GLOBAL AI TOGGLES */}
      <div className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold">AI Feature Toggles</h2>

        <ToggleRow
          label="AI Globally Enabled"
          value={settings.ai_globally_enabled}
          onChange={(v) =>
            updateToggle("ai_globally_enabled", v)
          }
          saving={saving}
        />

        <ToggleRow
          label="Meta Sync Enabled"
          value={settings.meta_sync_enabled}
          onChange={(v) =>
            updateToggle("meta_sync_enabled", v)
          }
          saving={saving}
        />

        <ToggleRow
          label="Maintenance Mode"
          value={settings.maintenance_mode}
          onChange={(v) =>
            updateToggle("maintenance_mode", v)
          }
          saving={saving}
        />

        <div className="text-xs text-gray-500">
          Each change is audited with before/after snapshots.
        </div>
      </div>

      {/* AI THROTTLING */}
      <div className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold">AI Throttling Limits</h2>

        <NumberField
          label="Max Optimizations / Day"
          value={throttles.max_optimizations_per_day}
          onChange={(v) =>
            setThrottles({
              ...throttles,
              max_optimizations_per_day: v,
            })
          }
        />

        <NumberField
          label="Max Expansions / Day"
          value={throttles.max_expansions_per_day}
          onChange={(v) =>
            setThrottles({
              ...throttles,
              max_expansions_per_day: v,
            })
          }
        />

        <NumberField
          label="AI Refresh Frequency (minutes)"
          value={throttles.ai_refresh_frequency_minutes}
          onChange={(v) =>
            setThrottles({
              ...throttles,
              ai_refresh_frequency_minutes: v,
            })
          }
        />

        <button
          onClick={saveThrottles}
          disabled={saving}
          className="px-4 py-2 border rounded text-xs hover:bg-gray-100 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save Throttling Limits"}
        </button>

        <div className="text-xs text-gray-500">
          Limits are enforced globally and logged.
        </div>
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  value,
  onChange,
  saving,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
  saving: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>{label}</div>
      <button
        onClick={() => onChange(!value)}
        disabled={saving}
        className={`px-3 py-1 text-xs border rounded ${
          value ? "bg-green-50" : "bg-gray-50"
        }`}
      >
        {value ? "ON" : "OFF"}
      </button>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>{label}</div>
      <input
        type="number"
        className="border p-1 w-24 text-right"
        value={value}
        min={0}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}
