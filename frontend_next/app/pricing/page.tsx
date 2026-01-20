"use client";

import { useState } from "react";

const MOCK_PLANS = [
  {
    key: "starter",
    name: "Starter",
    desc: "Ideal for individuals starting with AI campaigns",
    monthly: 499,
    yearly: 4999,
  },
  {
    key: "pro",
    name: "Pro",
    desc: "Great for teams and growing businesses",
    monthly: 999,
    yearly: 9999,
  },
  {
    key: "agency",
    name: "Agency",
    desc: "Scale operations with dedicated features",
    monthly: 2999,
    yearly: 29999,
  },
];

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");

  return (
    <div className="space-y-8 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Pricing Plans</h1>
        <p className="text-sm text-gray-600">
          Choose a plan that fits your workflow
        </p>
      </div>

      {/* Billing Toggle */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setBillingCycle("monthly")}
          className={`px-4 py-2 rounded-md text-sm ${
            billingCycle === "monthly"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700"
          }`}
        >
          Monthly
        </button>
        <button
          onClick={() => setBillingCycle("yearly")}
          className={`px-4 py-2 rounded-md text-sm ${
            billingCycle === "yearly"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700"
          }`}
        >
          Yearly
        </button>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {MOCK_PLANS.map((plan) => (
          <div
            key={plan.key}
            className="border rounded-lg p-6 bg-white shadow-sm flex flex-col justify-between"
          >
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{plan.desc}</p>

              <div className="mt-4">
                {billingCycle === "monthly" ? (
                  <p className="text-3xl font-bold text-gray-900">
                    ₹{plan.monthly}
                    <span className="text-sm text-gray-500 ml-1">/mo</span>
                  </p>
                ) : (
                  <p className="text-3xl font-bold text-gray-900">
                    ₹{plan.yearly}
                    <span className="text-sm text-gray-500 ml-1">/yr</span>
                  </p>
                )}
              </div>
            </div>

            <button
              disabled
              className="mt-6 w-full rounded-md bg-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 cursor-not-allowed"
            >
              Not Available Yet
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
