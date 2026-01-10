"use client";

import { useEffect, useState } from "react";
import axios from "axios";

type MetaSettings = {
  meta_sync_enabled: boolean;
  ai_globally_enabled: boolean;
  maintenance_mode: boolean;
  updated_at: string;
};

export default function AdminMetaSettingsPage() {
  const [settings, setSettings] = useState<MetaSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/admin/global-settings");
      setSettings(res.data);
    } catch (err) {
      console.error("Failed to fetch meta settings", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSetting = async (key: keyof MetaSettings) => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = { ...settings, [key]: !settings[key] };
      const res = await axios.put("/admin/global-settings", {
        updates: { [key]: updated[key] },
        reason: "Admin updated via Meta Settings page",
      });
      setSettings(res.data);
    } catch (err) {
      console.error("Failed to update setting", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading || !settings) {
    return <div className="p-8 text-center">Loading Meta Settings...</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Meta Admin Settings</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Meta Sync Enabled */}
        <div className="p-6 border rounded shadow flex flex-col items-center">
          <h2 className="font-semibold mb-2">Meta Sync Enabled</h2>
          <button
            className={`px-4 py-2 rounded ${
              settings.meta_sync_enabled
                ? "bg-green-500 text-white"
                : "bg-gray-300 text-gray-700"
            }`}
            onClick={() => toggleSetting("meta_sync_enabled")}
            disabled={saving}
          >
            {settings.meta_sync_enabled ? "ON" : "OFF"}
          </button>
        </div>

        {/* AI Globally Enabled */}
        <div className="p-6 border rounded shadow flex flex-col items-center">
          <h2 className="font-semibold mb-2">AI Globally Enabled</h2>
          <button
            className={`px-4 py-2 rounded ${
              settings.ai_globally_enabled
                ? "bg-green-500 text-white"
                : "bg-gray-300 text-gray-700"
            }`}
            onClick={() => toggleSetting("ai_globally_enabled")}
            disabled={saving}
          >
            {settings.ai_globally_enabled ? "ON" : "OFF"}
          </button>
        </div>

        {/* Maintenance Mode */}
        <div className="p-6 border rounded shadow flex flex-col items-center">
          <h2 className="font-semibold mb-2">Maintenance Mode</h2>
          <button
            className={`px-4 py-2 rounded ${
              settings.maintenance_mode
                ? "bg-red-500 text-white"
                : "bg-gray-300 text-gray-700"
            }`}
            onClick={() => toggleSetting("maintenance_mode")}
            disabled={saving}
          >
            {settings.maintenance_mode ? "ON" : "OFF"}
          </button>
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-4 text-gray-500">
        Last Updated:{" "}
        {new Date(settings.updated_at).toLocaleString("en-IN", {
          dateStyle: "short",
          timeStyle: "short",
        })}
      </div>
    </div>
  );
}
