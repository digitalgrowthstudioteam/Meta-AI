"use client";

import { AlertCircle } from "lucide-react";
import Link from "next/link";

export default function BillingFailurePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center space-y-6">
      <AlertCircle className="h-16 w-16 text-red-600" />

      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-gray-900">
          Payment Failed
        </h1>
        <p className="text-sm text-gray-600">
          Something went wrong while processing your payment. Please try again.
        </p>
      </div>

      <div className="space-x-3">
        <Link
          href="/pricing"
          className="px-4 py-2 rounded-md bg-indigo-600 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
        >
          Retry Payment
        </Link>

        <Link
          href="/dashboard"
          className="px-4 py-2 rounded-md bg-gray-200 text-sm font-semibold text-gray-700 hover:bg-gray-300"
        >
          Dashboard
        </Link>
      </div>
    </div>
  );
}
