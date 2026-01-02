export default function BillingPage() {
  return (
    <div className="space-y-6">
      {/* ===============================
          PAGE HEADER
      =============================== */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          Billing & Plan
        </h1>
        <p className="text-sm text-gray-500">
          Subscription details, usage limits, and billing transparency
        </p>
      </div>

      {/* ===============================
          GRID LAYOUT
      =============================== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* ===============================
            CURRENT PLAN CARD
        =============================== */}
        <div className="bg-white border border-blue-100 rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">
              Current Plan
            </h2>
            <span className="inline-flex rounded-full bg-blue-100 text-blue-700 px-2.5 py-1 text-xs font-medium">
              Trial
            </span>
          </div>

          <div className="text-2xl font-semibold text-gray-900">
            Starter Trial
          </div>

          <div className="mt-2 text-sm text-gray-500">
            Valid for 7 days
          </div>

          <div className="mt-4 text-xs text-gray-400">
            Trial gives limited AI access. Upgrade to continue after expiry.
          </div>

          <button className="mt-6 w-full rounded-md bg-blue-600 text-white py-2 text-sm font-medium hover:bg-blue-700 transition">
            Upgrade Plan
          </button>
        </div>

        {/* ===============================
            USAGE & LIMITS CARD
        =============================== */}
        <div className="bg-white border border-indigo-100 rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            AI Usage
          </h2>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">
                  AI-Active Campaigns
                </span>
                <span className="font-medium text-gray-900">
                  2 / 3
                </span>
              </div>

              {/* Progress Bar */}
              <div className="h-2 rounded bg-gray-200 overflow-hidden">
                <div className="h-full w-2/3 bg-indigo-500 rounded" />
              </div>
            </div>

            <div className="text-xs text-gray-400">
              Trial allows up to 3 AI-enabled campaigns.
            </div>
          </div>
        </div>

        {/* ===============================
            BILLING INFO CARD
        =============================== */}
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Billing Information
          </h2>

          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Transparent, usage-based pricing</li>
            <li>• No auto-applied charges</li>
            <li>• Invoices available after upgrade</li>
            <li>• Add-ons supported (Agency plan)</li>
          </ul>

          <div className="mt-4 text-xs text-gray-400">
            Payments and invoices will appear here once a paid plan is active.
          </div>
        </div>

      </div>

      {/* ===============================
          FOOTNOTE
      =============================== */}
      <div className="text-xs text-gray-400">
        All billing information is read-only. No changes are applied without explicit confirmation.
      </div>
    </div>
  );
}
