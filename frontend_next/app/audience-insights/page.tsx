// frontend_next/app/audience-insights/page.tsx

export default function AudienceInsightsPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        Audience Insights
      </h1>
      <p className="text-sm text-gray-500">
        AI-driven audience analysis and suggestions (read-only).
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        This section will include:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Top-performing audience segments</li>
          <li>Audience overlap analysis</li>
          <li>Expansion & exclusion suggestions</li>
          <li>Lead vs Sales audience separation</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          Audience changes require explicit user approval.
        </div>
      </div>
    </div>
  );
}
