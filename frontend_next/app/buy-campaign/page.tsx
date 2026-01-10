"use client";

import { useEffect, useState } from "react";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type CampaignPurchaseBatch = {
  id: string;
  quantity_total: number;
  quantity_used: number;
  quantity_remaining: number;
  purchased_at: string;
  expires_at: string;
  status: "active" | "expired";
};

type PricingConfig = {
  slot_packs: Record<
    string,
    {
      price: number;
      valid_days: number;
      min_qty: number;
      max_qty?: number;
      label: string;
    }
  >;
  currency: string;
  tax_percentage: number;
};

declare global {
  interface Window {
    Razorpay: any;
  }
}

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function BuyCampaignPage() {
  const [quantity, setQuantity] = useState(1);
  const [batches, setBatches] = useState<CampaignPurchaseBatch[]>([]);
  const [pricingConfig, setPricingConfig] = useState<PricingConfig | null>(null);
  const [loading, setLoading] = useState(false);

  /* ----------------------------------
   * LOAD PRICING CONFIG
   * ---------------------------------- */
  const loadPricing = async () => {
    const res = await fetch("/api/admin/pricing-config/active", {
      credentials: "include",
    });
    if (!res.ok) return;
    setPricingConfig(await res.json());
  };

  /* ----------------------------------
   * LOAD PURCHASED CAMPAIGNS
   * ---------------------------------- */
  const loadBatches = async () => {
    try {
      const res = await fetch("/api/campaign-purchases", {
        credentials: "include",
      });
      if (!res.ok) return;
      const json = await res.json();
      setBatches(Array.isArray(json) ? json : []);
    } catch {}
  };

  useEffect(() => {
    loadPricing();
    loadBatches();
  }, []);

  if (!pricingConfig) {
    return <div className="p-4 text-sm">Loading pricing…</div>;
  }

  /* ----------------------------------
   * DERIVE PACK
   * ---------------------------------- */
  const packs = Object.values(pricingConfig.slot_packs);

  const selectedPack =
    packs.find(
      (p) =>
        quantity >= p.min_qty &&
        (p.max_qty === undefined || quantity <= p.max_qty)
    ) || packs[0];

  const totalAmount = selectedPack.price * quantity;

  /* ----------------------------------
   * PURCHASE FLOW
   * ---------------------------------- */
  const purchaseCampaigns = async () => {
    try {
      setLoading(true);

      // 1) Create order
      const orderRes = await fetch(
        `/api/billing/campaign-slots/buy?quantity=${quantity}`,
        { method: "POST", credentials: "include" }
      );
      if (!orderRes.ok) throw new Error("Order creation failed");
      const order = await orderRes.json();

      // 2) Open Razorpay
      const rzp = new window.Razorpay({
        key: order.key || order.currency,
        amount: order.amount,
        currency: order.currency,
        order_id: order.razorpay_order_id,
        handler: async (resp: any) => {
          // 3) Verify payment
          await fetch("/api/billing/razorpay/verify", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            }),
          });

          // 4) Finalize slots
          await fetch(
            `/api/billing/campaign-slots/finalize?payment_id=${order.payment_id}&quantity=${quantity}`,
            { method: "POST", credentials: "include" }
          );

          await loadBatches();
        },
      });

      rzp.open();
    } catch (e) {
      alert("Payment failed");
    } finally {
      setLoading(false);
    }
  };

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Buy Campaign</h1>
        <p className="text-sm text-gray-500">
          Purchase AI access for additional campaigns
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {packs.map((p) => {
          const active =
            quantity >= p.min_qty &&
            (p.max_qty === undefined || quantity <= p.max_qty);

          return (
            <div
              key={p.label}
              className={`border rounded-lg p-6 ${
                active
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 bg-white"
              }`}
            >
              <div className="text-sm font-semibold">{p.label}</div>
              <div className="mt-1 text-xs text-gray-500">
                {p.min_qty}+{p.max_qty ? ` to ${p.max_qty}` : ""} Campaigns
              </div>
              <div className="mt-3 text-lg font-semibold">
                ₹{p.price} / campaign
              </div>
              <div className="text-xs text-gray-500">
                Valid for {Math.round(p.valid_days / 30)} months
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white border rounded p-6 space-y-4">
        <div className="grid grid-cols-4 gap-4 text-sm">
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            className="border rounded px-2 py-1"
          />
          <div>₹{selectedPack.price}</div>
          <div>{Math.round(selectedPack.valid_days / 30)} Months</div>
          <div className="font-semibold">₹{totalAmount}</div>
        </div>

        <button
          onClick={purchaseCampaigns}
          disabled={loading}
          className="btn-primary"
        >
          {loading ? "Processing…" : "Buy Campaigns"}
        </button>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-medium">Purchased Campaigns</h2>

        {batches.length === 0 && (
          <div className="border rounded p-4 text-sm">
            No purchased campaigns yet.
          </div>
        )}

        {batches.length > 0 && (
          <table className="w-full text-sm border">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th>Batch</th>
                <th>Total</th>
                <th>Used</th>
                <th>Remaining</th>
                <th>Expiry</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id} className="border-b">
                  <td>{b.id.slice(0, 8)}</td>
                  <td>{b.quantity_total}</td>
                  <td>{b.quantity_used}</td>
                  <td>{b.quantity_remaining}</td>
                  <td>{b.expires_at}</td>
                  <td>{b.status.toUpperCase()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
