"use client";

export default function AdminFeatureFlagsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Feature Flags</h1>

      <div className="rounded border bg-white p-4 text-sm space-y-4">
        <div className="text-gray-600">
          Toggle, rollout & experiment controls coming soon…
        </div>

        <div className="rounded border bg-gray-50 p-3 text-xs text-gray-500">
          No feature flags configured yet.
        </div>
      </div>
    </div>
  );
}
