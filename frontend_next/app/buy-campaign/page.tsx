// frontend_next/app/buy-campaign/page.tsx

export default function BuyCampaignPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        Buy Campaign
      </h1>
      <p className="text-sm text-gray-500">
        Purchase AI access for additional campaigns.
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        Campaign purchase rules:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>0–5 campaigns: ₹999 per campaign (3 months)</li>
          <li>6–29 campaigns: ₹599 per campaign (6 months)</li>
          <li>30+ campaigns: ₹333 per campaign (1 year)</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          Purchased campaigns are tracked separately from subscriptions.
        </div>
      </div>
    </div>
  );
}
