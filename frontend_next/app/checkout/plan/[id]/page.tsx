"use client";

import { useParams } from "next/navigation";
import { useState } from "react";

const PLANS: Record<string, any> = {
  starter: {
    name: "Starter",
    desc: "Ideal for individuals starting with AI campaigns",
    monthly: 499,
    yearly: 4999,
  },
  pro: {
    name: "Pro",
    desc: "Great for teams and growing businesses",
    monthly: 999,
    yearly: 9999,
  },
  agency: {
    name: "Agency",
    desc: "Scale operations with dedicated features",
    monthly: 2999,
    yearly: 29999,
  },
};

export default function CheckoutPlanPage() {
  const params = useParams();
  const id = typeof params?.id === "string" ? params.id : "";

  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");

  const plan = PLANS[id];

  if (!plan) {
    return (
      <div className="p-6 text-sm text-red-600 bg-red-50 rounded border border-red-200">
        Invalid plan selected.
      </div>
    );
  }

  return (
    <div className="space-y-8 p-4">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Checkout — {plan.name}</h1>
        <p className="text-sm text-gray-600">Confirm your plan details before proceeding</p>
      </div>

      {/* Two Column Layout */}
      <div className="flex flex-col md:flex-row gap-6">
        
        {/* Left Column — Summary */}
        <div className="flex-1 space-y-4">
          <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 space-y-3">
            <h2 classname="text-base font-semibold text-gray-900">Plan Summary</h2>
            <p className="text-sm text-gray-600">{plan.desc}</p>

            <ul className="text-sm text-gray-700 space-y-2">
              <li>✔ Access to AI campaign tools</li>
              <li>✔ Dashboard & analytics</li>
              <li>✔ Priority support</li>
              <li>✔ Free 7-day trial included</li>
            </ul>
          </div>
        </div>

        {/* Right Column — Pricing */}
        <div className="w-full md:w-80 space-y-4">
          <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg p-6 space-y-4">
            <h3 className="text-base font-semibold text-gray-900">Billing Details</h3>

            {/* Toggle */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setBillingCycle("monthly")}
                className={`px-3 py-1 text-sm rounded ${
                  billingCycle === "monthly"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle("yearly")}
                className={`px-3 py-1 text-sm rounded ${
                  billingCycle === "yearly"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                Yearly
              </button>
            </div>

            {/* Price */}
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

            {/* Mock Checkout Button */}
            <button
              disabled
              className="w-full rounded-md bg-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 cursor-not-allowed"
            >
              Checkout Not Available (Phase 2)
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
