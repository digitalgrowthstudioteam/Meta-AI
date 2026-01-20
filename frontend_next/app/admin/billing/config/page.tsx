"use client";

import { useState } from "react";
import toast from "react-hot-toast";

const mockInitial = {
  key_id: "",
  secret: "",
  mode: "test",
};

export default function AdminBillingConfigPage() {
  const [form, setForm] = useState(mockInitial);

  const onChange = (field: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const onSave = () => {
    if (!form.key_id || !form.secret) {
      toast.error("Key ID and Secret cannot be empty");
      return;
    }

    toast.success("Settings saved (Phase-2 mock only)");
  };

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Billing Configuration</h1>
        <p className="text-sm text-gray-500">
          Configure Razorpay API credentials for subscription billing.
        </p>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 space-y-6 max-w-xl">
        {/* Key ID */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Razorpay Key ID <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="rzp_test_xxxxxxxxx"
            value={form.key_id}
            onChange={(e) => onChange("key_id", e.target.value)}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        {/* Secret Key */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Razorpay Secret Key <span className="text-red-500">*</span>
          </label>
          <input
            type="password"
            placeholder="•••••••••••••••••"
            value={form.secret}
            onChange={(e) => onChange("secret", e.target.value)}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        {/* Mode */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Mode
          </label>
          <select
            value={form.mode}
            onChange={(e) => onChange("mode", e.target.value)}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="test">Test</option>
            <option value="live">Live</option>
          </select>
        </div>

        {/* Save Button */}
        <div>
          <button
            onClick={onSave}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            Save Settings
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-400">
        Phase-2 mock only — no backend submit yet.
      </p>
    </div>
  );
}
