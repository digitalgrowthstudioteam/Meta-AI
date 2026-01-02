// frontend_next/app/reports/page.tsx

export default function ReportsPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        Reports
      </h1>
      <p className="text-sm text-gray-500">
        Performance summaries and downloadable reports.
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        This section will include:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Campaign performance reports</li>
          <li>AI impact summaries</li>
          <li>Date-range exports</li>
          <li>Lead vs Sales comparison</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          Reports are generated from historical, immutable data.
        </div>
      </div>
    </div>
  );
}
