"use client";

export default function AdminChatMonitorPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Chat Monitor</h1>

      <div className="rounded border bg-white p-4 text-sm">
        <div className="text-gray-600 mb-2">Support chats coming soon…</div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs sm:text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase">
              <tr>
                <th className="px-3 py-2 text-left">User</th>
                <th className="px-3 py-2 text-left">Last Message</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="px-3 py-2 text-gray-400 italic" colSpan={4}>
                  No active chats
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
