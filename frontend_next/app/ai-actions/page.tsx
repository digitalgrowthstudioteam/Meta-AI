'use client';

import useSWR from 'swr';
import { fetcher } from '@/lib/fetcher';

export default function AdminAiActionsLogPage() {
  // ADMIN API: Fetches system-wide log of AI actions
  const { data: actions, error, isLoading } = useSWR('/api/admin/ai-actions', fetcher);

  if (error) return <div className="p-6 text-red-500">Error loading System Logs: {error.message}</div>;
  if (isLoading) return <div className="p-6 text-gray-500">Loading Global AI Queue...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Global AI Action Queue</h1>
          <p className="text-sm text-gray-500">System-wide log of all AI decisions and executions.</p>
        </div>
        <span className="bg-purple-100 text-purple-800 text-xs font-medium px-2.5 py-0.5 rounded">
          {actions?.length || 0} Records Found
        </span>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Campaign ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reasoning</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {actions?.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  No AI actions found in system logs.
                </td>
              </tr>
            ) : (
              actions?.map((action: any) => (
                <tr key={action.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {action.action_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={\`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                      \${action.status === 'executed' ? 'bg-green-100 text-green-800' : 
                        action.status === 'failed' ? 'bg-red-100 text-red-800' : 
                        action.status === 'pending' ? 'bg-blue-100 text-blue-800' : 
                        'bg-gray-100 text-gray-800'}\`}>
                      {action.status?.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-mono">
                    {action.campaign_id}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-sm truncate" title={action.reason}>
                    {action.reason || 'No specific reason logged'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
EOF
