'use client';

import useSWR from 'swr';
// FIXED: Use relative path
import { fetcher } from "../../../lib/fetcher";

export default function AdminAiActionsLogPage() {
  const { data: actions, error, isLoading } = useSWR('/api/admin/ai-actions', fetcher);

  if (error) return <div className="p-6 text-red-500">Error loading logs: {error.message}</div>;
  if (isLoading) return <div className="p-6 text-gray-500">Loading AI Logs...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Global AI Action Queue</h1>
        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
          {actions?.length || 0} Records
        </span>
      </div>

      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Campaign ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {(!actions || actions.length === 0) ? (
              <tr><td colSpan={5} className="text-center py-8 text-gray-500">No logs found.</td></tr>
            ) : (
              actions.map((action: any) => (
                <tr key={action.id}>
                  <td className="px-6 py-4 text-sm font-medium">{action.action_type}</td>
                  <td className="px-6 py-4 text-sm">{action.status}</td>
                  <td className="px-6 py-4 text-xs font-mono text-gray-500">{action.campaign_id}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">{action.reason}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {action.created_at ? new Date(action.created_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
