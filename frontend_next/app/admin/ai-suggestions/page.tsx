'use client';

import useSWR from 'swr';
import { fetcher } from "../../../lib/fetcher";

export default function AdminAiSuggestionsPage() {
  // FIX: call backend admin route directly
  const { data, error, isLoading } = useSWR('/admin/ai-suggestions', fetcher);

  const suggestions = Array.isArray(data) ? data : [];

  if (error) {
    return (
      <div className="p-6 text-red-500">
        Error loading AI suggestions
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6 text-gray-500">
        Loading AI Suggestions...
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">AI Suggestions</h1>

      <div className="bg-white p-6 rounded border shadow-sm">
        <p className="text-gray-600">
          Pending suggestions: <span className="font-semibold">{suggestions.length}</span>
        </p>
      </div>
    </div>
  );
}
