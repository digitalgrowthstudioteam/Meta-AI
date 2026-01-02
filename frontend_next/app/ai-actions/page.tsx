// frontend_next/app/ai-actions/page.tsx

export default function AIActionsPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        AI Actions
      </h1>
      <p className="text-sm text-gray-500">
        Explainable AI recommendations generated for your campaigns.
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        This section will display:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Campaign-level AI recommendations</li>
          <li>Suggested budget or bid changes</li>
          <li>Pause / scale signals</li>
          <li>Confidence & reasoning (explainable AI)</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          No actions are auto-applied. Approval-based workflow only.
        </div>
      </div>
    </div>
  );
}
