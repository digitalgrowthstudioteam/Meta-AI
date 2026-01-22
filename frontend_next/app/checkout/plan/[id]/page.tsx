"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/app/lib/fetcher";

type PublicPlan = {
  id: number;
  name: string;
  code: string;
  monthly_price: number;
  yearly_price: number | null;
  yearly_allowed: boolean;
  ai_limit: number;
  currency: string;
};

export default function CheckoutPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const planCode = params.id;
  const searchParams = useSearchParams();
  const cycle = (searchParams.get("cycle") as "monthly" | "yearly") || "monthly";

  const [plans, setPlans] = useState<PublicPlan[]>([]);
  const [plan, setPlan] = useState<PublicPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const loadPlans = async () => {
      try {
        // IMPORTANT: UPDATED PATH
        const res = await apiFetch("/api/public/plans");
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

  useEffect(() => {
    const p = plans.find((x) => x.code.toLowerCase() === planCode.toLowerCase());
    if (p) setPlan(p);
  }, [plans, planCode]);

  if (loading) {
    return <div className="p-4 text-sm text-gray-600">Loading checkout...</div>;
  }

  if (!plan) {
    return (
      <div className="p-6 rounded-lg bg-red-50 border text-red-700 text-sm">
        Invalid or unavailable plan.
      </div>
    );
  }

  const amountPaise =
    cycle === "yearly" && plan.yearly_allowed && plan.yearly_price
      ? plan.yearly_price
      : plan.monthly_price;

  const displayAmount = Math.round(amountPaise / 100);

  const loadRazorpayScript = () =>
    new Promise((resolve) => {
      if (typeof window === "undefined") return resolve(false);
      if ((window as any).Razorpay) return resolve(true);
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });

  const onCheckout = async () => {
    setBusy(true);

    const loaded = await loadRazorpayScript();
    if (!loaded) {
      alert("Failed to load Razorpay Checkout.");
      setBusy(false);
      return;
    }

    try {
      // IMPORTANT: UPDATED PATH
      const backendResp = await apiFetch(
        `/api/billing/subscription/manual?plan_id=${plan.id}&cycle=${cycle}`,
        { method: "POST" }
      );

      if (!backendResp.ok) {
        router.push("/billing/failure");
        return;
      }

      const data = await backendResp.json();
      const key = data.key;

      const options: any = {
        key,
        name: "Meta-AI Billing",
        description: `${plan.name} (${cycle})`,
        order_id: data.razorpay_order_id,
        notes: {
          plan_id: plan.id.toString(),
          cycle,
        },
        handler: async function (response: any) {
          try {
            const verifyResp = await apiFetch("/api/billing/razorpay/verify", {
              method: "POST",
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });

            if (verifyResp.ok) {
              router.push("/billing/success");
            } else {
              router.push("/billing/failure");
            }
          } catch (err) {
            console.error("Verify failed:", err);
            router.push("/billing/failure");
          }
        },
        modal: {
          ondismiss: function () {
            router.push("/billing/failure");
          },
        },
        customer: {
          name: "Billing User",
          email: "billing@example.com",
        },
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.open();

    } catch (err) {
      console.error("Checkout failed:", err);
      router.push("/billing/failure");
    } finally {
      setBusy(false);
    }
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
          <div className="text-3xl font-bold text-gray-900">
            ₹{displayAmount}
          </div>
        </div>
      </div>

      <button
        onClick={onCheckout}
        disabled={busy}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
      >
        {busy ? "Processing..." : "Proceed to Payment"}
      </button>
    </div>
  );
}
