'use client';
import useSWR from 'swr';
import { fetcher } from "../../../lib/fetcher";

export default function AdminAiSuggestionsPage() {
  const { data: suggestions, error, isLoading } = useSWR('/api/admin/ai-suggestions', fetcher);
  if (error) return <div className="p-6 text-red-500">Error: {error.message}</div>;
  if (isLoading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">AI Suggestions</h1>
      <div className="bg-white p-6 rounded border shadow-sm">
         <p className="text-gray-500">Pending suggestions: {suggestions?.length || 0}</p>
      </div>
    </div>
  );
}
