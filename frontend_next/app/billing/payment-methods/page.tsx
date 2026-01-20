"use client";

export default function BillingPaymentMethodsPage() {
  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Payment Methods</h1>
        <p className="text-sm text-gray-500">
          Manage your saved payment methods and billing preferences.
        </p>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6">
        <div className="space-y-3 text-sm">
          <p className="text-gray-700 font-medium">
            No payment methods available
          </p>
          <p className="text-gray-500">
            Payment methods will appear here once you add a card during checkout.
          </p>
        </div>

        <div className="mt-6">
          <button
            disabled
            className="rounded-md bg-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 cursor-not-allowed"
          >
            Add Payment Method (Phase 5)
          </button>
        </div>
      </div>
    </div>
  );
}
