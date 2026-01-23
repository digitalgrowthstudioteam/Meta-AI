'use client';
import useSWR from 'swr';
import { fetcher } from "@/app/lib/fetcher";

export default function AdminMetricsPage() {
  const { data } = useSWR('/api/admin/metrics/sync-status', fetcher);
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Metrics Sync Status</h1>
      <div className="bg-white p-6 rounded border shadow-sm">
         <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
}
