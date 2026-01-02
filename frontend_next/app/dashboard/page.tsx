"use client";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* ================= HEADER ================= */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            Dashboard
          </h1>
          <p className="text-sm text-gray-500">
            Overview of your Meta Ads and AI activity
          </p>
        </div>

        <div className="text-xs text-gray-500">
          Meta account: Not connected
        </div>
      </div>

      {/* ================= KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Campaigns"
          value="—"
          hint="Synced from Meta"
        />
        <KpiCard
          label="AI-Active Campaigns"
          value="—"
          hint="Counts toward your plan"
        />
        <KpiCard
          label="Latest AI Action"
          value="—"
          hint="Most recent recommendation"
        />
        <KpiCard
          label="Account Status"
          value="Disconnected"
          hint="Meta Ads account"
          warning
        />
      </div>

      {/* ================= AI ACTIVITY ================= */}
      <div className="bg-white border border-gray-200 rounded p-6 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            Recent AI Activity
          </h2>
          <p className="text-xs text-gray-500">
            Latest AI recommendations generated for your campaigns
          </p>
        </div>

        <div className="space-y-3 text-sm">
          <EmptyRow text="No AI actions generated yet." />
        </div>
      </div>

      {/* ================= CAMPAIGN SNAPSHOT ================= */}
      <div className="bg-white border border-gray-200 rounded p-6 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            Campaign Snapshot
          </h2>
          <p className="text-xs text-gray-500">
            High-level breakdown by objective and status
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SnapshotItem
            label="Lead Campaigns"
            value="—"
          />
          <SnapshotItem
            label="Sales Campaigns"
            value="—"
          />
          <SnapshotItem
            label="Paused Campaigns"
            value="—"
          />
        </div>
      </div>

      {/* ================= FOOTNOTE ================= */}
      <div className="text-xs text-gray-400">
        All data is read-only and synced from Meta Ads Manager.
        Changes are applied directly inside Meta.
      </div>
    </div>
  );
}

/* ===============================
   UI COMPONENTS
=============================== */

function KpiCard({
  label,
  value,
  hint,
  warning,
}: {
  label: string;
  value: string;
  hint: string;
  warning?: boolean;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded p-5 space-y-1">
      <div className="text-xs text-gray-500">
        {label}
      </div>
      <div
        className={`text-xl font-semibold ${
          warning ? "text-red-600" : "text-gray-900"
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-gray-400">
        {hint}
      </div>
    </div>
  );
}

function SnapshotItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="border border-gray-200 rounded p-4">
      <div className="text-xs text-gray-500">
        {label}
      </div>
      <div className="text-lg font-semibold text-gray-900">
        {value}
      </div>
    </div>
  );
}

function EmptyRow({ text }: { text: string }) {
  return (
    <div className="border border-dashed border-gray-200 rounded p-4 text-gray-500">
      {text}
    </div>
  );
}
