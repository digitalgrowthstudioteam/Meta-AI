"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetcher } from "../lib/fetcher";

type PublicPlan = {
  name: string;
  code: string;
  monthly_price: number;
  yearly_price: number | null;
  yearly_allowed: boolean;
  ai_limit: number;
  currency: string;
};

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [plans, setPlans] = useState<PublicPlan[]>([]);
  const [loading, setLoading] = useState(true);

  const router = useRouter();

  useEffect(() => {
    const loadPlans = async () => {
      try {
        // IMPORTANT: Updated for correct backend path + cookies
        const res = await apiFetch("/public/plans");
        const data = await res.json();
        setPlans(data || []);
      } catch (err) {
        console.error("Failed to load plans", err);
      } finally {
        setLoading(false);
      }
    };

    loadPlans();
  }, []);

  const handleSelect = (planCode: string) => {
    router.push(`/checkout/plan/${planCode}?cycle=${billingCycle}`);
  };

  if (loading) {
    return <div className="p-4 text-sm text-gray-600">Loading plans...</div>;
  }

  // hide FREE plan
  const visiblePlans = plans.filter((p) => p.code !== "free");

  return (
    <div className="space-y-8 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Pricing Plans</h1>
        <p className="text-sm text-gray-600">Choose a plan that fits your workflow</p>
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
          disabled={!visiblePlans.some((p) => p.yearly_allowed)}
        >
          Yearly
        </button>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {visiblePlans.map((plan) => {
          const pricePaise =
            billingCycle === "monthly" || !plan.yearly_allowed
              ? plan.monthly_price
              : plan.yearly_price || plan.monthly_price;

          const price = Math.round(pricePaise / 100);
          const suffix = billingCycle === "monthly" ? "/mo" : "/yr";

          return (
            <div
              key={plan.code}
              className="border rounded-lg p-6 bg-white shadow-sm flex flex-col justify-between"
            >
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                <p className="text-sm text-gray-500 mt-1">
                  {plan.ai_limit} AI campaigns included
                </p>

                <div className="mt-4">
                  <p className="text-3xl font-bold text-gray-900">
                    ₹{price}
                    <span className="text-sm text-gray-500 ml-1">{suffix}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Billed {billingCycle === "monthly" ? "monthly" : "yearly"}
                  </p>
                </div>
              </div>

              <button
                onClick={() => handleSelect(plan.code)}
                className="mt-6 w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
              >
                Upgrade
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
