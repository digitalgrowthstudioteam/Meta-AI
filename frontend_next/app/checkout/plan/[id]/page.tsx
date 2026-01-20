"use client";

import { useSearchParams, useParams, useRouter } from "next/navigation";

const MOCK_PLANS = {
  starter: { name: "Starter", monthly: 499, yearly: 4999, aiLimit: 10 },
  pro: { name: "Pro", monthly: 1499, yearly: 14999, aiLimit: 25 },
  agency: { name: "Agency", monthly: 4999, yearly: 49999, aiLimit: 100 },
};

export default function CheckoutPage() {
  const { id } = useParams();
  const search = useSearchParams();
  const router = useRouter();

  const period = search.get("period") || "monthly";
  const plan = MOCK_PLANS[id as keyof typeof MOCK_PLANS];

  if (!plan) {
    return (
      <div className="p-6 text-red-600 text-sm">
        Invalid plan selected.
      </div>
    );
  }

  const price = period === "monthly" ? plan.monthly : plan.yearly;
  const suffix = period === "monthly" ? "/month" : "/year";

  const handleConfirm = () => {
    // Phase-2 mock: no payment, no backend
    router.push("/billing/success");
  };

  const handleCancel = () => {
    router.push("/pricing");
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Checkout</h1>
        <p className="text-sm text-gray-600">
          Review your plan and proceed to payment.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* LEFT - PLAN SUMMARY */}
        <div className="border rounded-lg p-6 bg-white shadow-sm space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">{plan.name} Plan</h2>

          <p className="text-sm text-gray-600">
            Billing: <span className="font-medium capitalize">{period}</span>
          </p>

          <p className="text-3xl font-bold text-gray-900">
            ₹{price}
            <span className="text-sm text-gray-500 ml-1">{suffix}</span>
          </p>

          <p className="text-xs text-gray-500">
            AI Campaign Limit: {plan.aiLimit}
          </p>

          <div className="pt-4 border-t space-y-2 text-sm text-gray-600">
            <p>✔ AI Campaign Optimization</p>
            <p>✔ Priority Analytics</p>
            <p>✔ Email Support</p>
          </div>
        </div>

        {/* RIGHT - ORDER SUMMARY */}
        <div className="border rounded-lg p-6 bg-white shadow-sm space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Order Summary</h2>

          <div className="flex justify-between text-sm">
            <span>{plan.name} ({period})</span>
            <span>₹{price}</span>
          </div>

          <div className="pt-4 border-t flex justify-between font-semibold text-gray-900">
            <span>Total</span>
            <span>₹{price}</span>
          </div>

          <button
            onClick={handleConfirm}
            className="w-full mt-4 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
          >
            Proceed to Payment
          </button>

          <button
            onClick={handleCancel}
            className="w-full rounded-md border px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
