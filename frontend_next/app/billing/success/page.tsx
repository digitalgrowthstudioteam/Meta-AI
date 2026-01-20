"use client";

import { CheckCircle } from "lucide-react";
import Link from "next/link";

export default function BillingSuccessPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center space-y-6">
      <CheckCircle className="h-16 w-16 text-green-600" />

      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-gray-900">
          Payment Successful!
        </h1>
        <p className="text-sm text-gray-600">
          Your subscription has been updated. You can now manage your billing details.
        </p>
      </div>

      <div className="space-x-3">
        <Link
          href="/billing"
          className="px-4 py-2 rounded-md bg-indigo-600 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
        >
          Go to Billing
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
