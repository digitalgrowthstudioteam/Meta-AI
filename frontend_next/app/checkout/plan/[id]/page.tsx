"use client";

import { useRouter, useSearchParams } from "next/navigation";

const MOCK_PLANS = {
  starter: { name: "Starter", monthly: 499, yearly: 4999 },
  pro: { name: "Pro", monthly: 999, yearly: 9999 },
  agency: { name: "Agency", monthly: 2999, yearly: 29999 },
  enterprise: { name: "Enterprise" },
};

export default function CheckoutPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const planId = params.id;
  const plan = MOCK_PLANS[planId as keyof typeof MOCK_PLANS];

  const searchParams = useSearchParams();
  const cycle = (searchParams.get("cycle") as "monthly" | "yearly") || "monthly";

  if (!plan || planId === "enterprise") {
    return (
      <div className="p-6 rounded-lg bg-red-50 border text-red-700 text-sm">
        Enterprise cannot be purchased online. Contact sales.
      </div>
    );
  }

  const amount = cycle === "monthly" ? plan.monthly : plan.yearly;

  const onCheckout = () => {
    router.push("/billing/success");
  };

  return (
    <div className="space-y-6 p-4 max-w-xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Checkout</h1>
        <p className="text-sm text-gray-500">Review your plan before continuing</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm ring-1 ring-gray-900/5 p-6 space-y-4">
        <div>
          <div className="text-sm text-gray-500">Plan</div>
          <div className="text-lg font-medium text-gray-900">{plan.name}</div>
        </div>

        <div>
          <div className="text-sm text-gray-500">Billing Cycle</div>
          <div className="text-base font-medium text-gray-900 capitalize">
            {cycle}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-500">Total</div>
          <div className="text-3xl font-bold text-gray-900">₹{amount}</div>
        </div>
      </div>

      <button
        onClick={onCheckout}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
      >
        Proceed to Payment
      </button>

      <p className="text-xs text-gray-400">
        Phase-2 mock only — no backend integration yet
      </p>
    </div>
  );
}
