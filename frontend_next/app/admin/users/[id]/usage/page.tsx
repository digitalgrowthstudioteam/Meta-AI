"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import toast from "react-hot-toast";

export default function UserUsageOverridePage({ params }: { params: { id: string } }) {
  const userId = params.id;
  const router = useRouter();

  // Mock initial values
  const [campaignLimit, setCampaignLimit] = useState<number | null>(null);
  const [adLimit, setAdLimit] = useState<number | null>(null);
  const [expiry, setExpiry] = useState<string>("");

  const onSave = () => {
    toast.success("Override saved (mock)");
    router.back();
  };

  return (
    <div className="space-y-6 p-4 max-w-lg">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Usage Override</h1>
        <p className="text-sm text-gray-500">
          Manually override usage limits for this user
        </p>
        <div className="text-xs text-gray-400 mt-1">
          User ID: {userId}
        </div>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm mb-1 font-medium text-gray-700">
            Campaign Limit Override
          </label>
          <input
            type="number"
            value={campaignLimit ?? ""}
            onChange={(e) => setCampaignLimit(e.target.value ? Number(e.target.value) : null)}
            placeholder="Leave blank to remove override"
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm mb-1 font-medium text-gray-700">
            Ad Account Limit Override
          </label>
          <input
            type="number"
            value={adLimit ?? ""}
            onChange={(e) => setAdLimit(e.target.value ? Number(e.target.value) : null)}
            placeholder="Leave blank to remove override"
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm mb-1 font-medium text-gray-700">
            Override Expiry (optional)
          </label>
          <input
            type="date"
            value={expiry}
            onChange={(e) => setExpiry(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>
      </div>

      <button
        onClick={onSave}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500"
      >
        Save Override
      </button>

      <p className="text-xs text-gray-400">
        Phase-2 mock only — backend will apply overrides later
      </p>
    </div>
  );
}
