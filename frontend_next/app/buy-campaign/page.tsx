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

/* ----------------------------------
 * PRICING LOGIC (LOCKED)
 * ---------------------------------- */
function getPricing(qty: number) {
  if (qty >= 30) {
    return {
      price: 333,
      validityLabel: "1 Year",
      months: 12,
    };
  }
  if (qty >= 6) {
    return {
      price: 599,
      validityLabel: "6 Months",
      months: 6,
    };
  }
  return {
    price: 999,
    validityLabel: "3 Months",
    months: 3,
  };
}

/* ----------------------------------
 * PAGE
 * ---------------------------------- */
export default function BuyCampaignPage() {
  const [quantity, setQuantity] = useState(1);
  const [batches, setBatches] = useState<CampaignPurchaseBatch[]>([]);
  const [loading, setLoading] = useState(false);

  const pricing = getPricing(quantity);
  const totalAmount = pricing.price * quantity;

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
    loadBatches();
  }, []);

  /* ----------------------------------
   * PURCHASE HANDLER (SAFE STUB)
   * ---------------------------------- */
  const purchaseCampaigns = async () => {
    try {
      setLoading(true);
      await fetch("/api/campaign-purchases/buy", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quantity,
        }),
      });
      await loadBatches();
    } finally {
      setLoading(false);
    }
  };

  /* ----------------------------------
   * RENDER
   * ---------------------------------- */
  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <h1 className="text-xl font-semibold">Buy Campaign</h1>
        <p className="text-sm text-gray-500">
          Purchase AI access for additional campaigns (separate from subscription)
        </p>
      </div>

      {/* ===============================
          PLAN CARDS
      =============================== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PlanCard
          title="Starter Pack"
          range="0–5 Campaigns"
          price="₹999 / campaign"
          validity="3 Months"
          active={quantity <= 5}
        />
        <PlanCard
          title="Growth Pack"
          range="6–29 Campaigns"
          price="₹599 / campaign"
          validity="6 Months"
          active={quantity >= 6 && quantity < 30}
        />
        <PlanCard
          title="Scale Pack"
          range="30+ Campaigns"
          price="₹333 / campaign"
          validity="1 Year"
          active={quantity >= 30}
        />
      </div>

      {/* ===============================
          PURCHASE DETAILS
      =============================== */}
      <div className="bg-white border border-gray-200 rounded p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">
          Purchase Details
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
          <div>
            <label className="text-xs text-gray-500">Quantity</label>
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="mt-1 w-full border rounded px-2 py-1"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500">Price / Campaign</label>
            <div className="mt-1 font-medium">
              ₹{pricing.price}
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500">Validity</label>
            <div className="mt-1 font-medium">
              {pricing.validityLabel}
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500">Total Amount</label>
            <div className="mt-1 font-semibold text-lg">
              ₹{totalAmount}
            </div>
          </div>
        </div>

        <button
          onClick={purchaseCampaigns}
          disabled={loading}
          className="btn-primary"
        >
          {loading ? "Processing…" : "Buy Campaigns"}
        </button>

        <div className="text-xs text-gray-400">
          Purchased campaigns are tracked individually with expiry and usage.
          No automatic charges apply.
        </div>
      </div>

      {/* ===============================
          PURCHASED CAMPAIGNS
      =============================== */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">
          Purchased Campaigns
        </h2>

        {batches.length === 0 && (
          <div className="bg-white border rounded p-6 text-sm text-gray-600">
            No purchased campaigns yet.
          </div>
        )}

        {batches.length > 0 && (
          <div className="bg-white border rounded overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">Batch</th>
                  <th className="px-3 py-2">Total</th>
                  <th className="px-3 py-2">Used</th>
                  <th className="px-3 py-2">Remaining</th>
                  <th className="px-3 py-2">Expiry</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((b) => {
                  const pct =
                    b.quantity_total > 0
                      ? (b.quantity_used / b.quantity_total) * 100
                      : 0;

                  return (
                    <tr key={b.id} className="border-b last:border-0">
                      <td className="px-3 py-2 font-medium">
                        {b.id.slice(0, 8)}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {b.quantity_total}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {b.quantity_used}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {b.quantity_remaining}
                      </td>
                      <td className="px-3 py-2">
                        {b.expires_at}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`px-2 py-1 rounded text-xs ${
                            b.status === "active"
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {b.status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* FOOTNOTE */}
      <div className="text-xs text-gray-400">
        Admins can manually adjust usage, backdate consumption,
        and add campaign slots from the admin panel.
      </div>
    </div>
  );
}

/* ----------------------------------
 * COMPONENTS
 * ---------------------------------- */
function PlanCard({
  title,
  range,
  price,
  validity,
  active,
}: {
  title: string;
  range: string;
  price: string;
  validity: string;
  active: boolean;
}) {
  return (
    <div
      className={`border rounded-lg p-6 ${
        active
          ? "border-blue-500 bg-blue-50"
          : "border-gray-200 bg-white"
      }`}
    >
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-1 text-xs text-gray-500">{range}</div>

      <div className="mt-3 text-lg font-semibold">
        {price}
      </div>

      <div className="text-xs text-gray-500">
        Valid for {validity}
      </div>
    </div>
  );
}
