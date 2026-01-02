// frontend_next/app/dashboard/page.tsx

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        Dashboard
      </h1>
      <p className="text-sm text-gray-500">
        Account-level overview and performance summary will appear here.
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        This section will show:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Connected ad accounts</li>
          <li>Active campaigns</li>
          <li>AI performance summary</li>
          <li>Spend & ROI snapshots</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          (Coming soon — read-only insights only)
        </div>
      </div>
    </div>
  );
}
