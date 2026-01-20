"use client";

import { Clock } from "lucide-react";

export default function BillingInvoicesPage() {
  const invoices: any[] = []; // Phase-2: empty only

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Invoices</h1>
        <p className="text-sm text-gray-500">
          View and download your past invoices and payment receipts.
        </p>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-base font-semibold leading-6 text-gray-900 mb-4">
            Invoice History
          </h3>

          {invoices.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed">
              <Clock className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">No invoices found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                      Invoice #
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Date
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Amount
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">Download</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {/* Phase-2: empty, no rows */}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
