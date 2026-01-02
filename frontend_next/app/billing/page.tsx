// frontend_next/app/billing/page.tsx

export default function BillingPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        Billing
      </h1>
      <p className="text-sm text-gray-500">
        Subscription details, invoices, and payment history.
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        This section will show:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Current subscription plan</li>
          <li>Active AI campaign limits</li>
          <li>Invoices & payment receipts</li>
          <li>Add-on campaign charges (Agency only)</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          Billing is transparent and usage-bound. No hidden costs.
        </div>
      </div>
    </div>
  );
}
