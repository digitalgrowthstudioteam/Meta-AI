"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { apiFetch } from "@/app/lib/fetcher";

type PlanRow = {
  id: number;
  name: string;
  monthly_price: number;
  yearly_price: number | null;
  max_ad_accounts: number | null;
  max_ai_campaigns: number;
  yearly_allowed: boolean;
  is_hidden: boolean;
  is_active: boolean;
};

type EditablePlan = {
  id: number;
  code: string;
  monthly_price: number;
  yearly_price: number;
  ad_account_limit: number;
  campaign_limit: number;
  is_custom: boolean;
};

export default function AdminPlansPage() {
  const [plans, setPlans] = useState<EditablePlan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiFetch("/admin/plans");
        if (!res.ok) {
          toast.error("Failed to load plans");
          return;
        }

        const data: PlanRow[] = await res.json();

        // Ignore FREE plan from UI
        const filtered = data.filter((p) => p.name.toLowerCase() !== "free");

        const mapped = filtered.map((p) => ({
          id: p.id,
          code: p.name.toLowerCase(),
          monthly_price: Math.round(p.monthly_price / 100),
          yearly_price: p.yearly_price ? Math.round(p.yearly_price / 100) : 0,
          ad_account_limit: p.max_ad_accounts ?? 0,
          campaign_limit: p.max_ai_campaigns ?? 0,
          is_custom: p.name.toLowerCase() === "enterprise"
        }));

        setPlans(mapped);
      } catch (err) {
        toast.error("Error loading plans");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const onChange = (index: number, field: keyof EditablePlan, value: string | number) => {
    setPlans((prev) => {
      const next = [...prev];
      (next[index] as any)[field] =
        field.includes("price") || field.includes("limit")
          ? Number(value)
          : value;
      return next;
    });
  };

  const onSave = async () => {
    try {
      toast.loading("Saving...", { id: "saving" });

      for (const p of plans) {
        const body = {
          monthly_price: p.monthly_price * 100,
          yearly_price: p.yearly_price ? p.yearly_price * 100 : null,
          max_ad_accounts: p.ad_account_limit,
          max_ai_campaigns: p.campaign_limit
        };

        const res = await apiFetch(`/admin/plans/${p.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Update failed");
        }
      }

      toast.success("Plans updated successfully", { id: "saving" });
    } catch (err: any) {
      toast.error(err.message || "Failed to save", { id: "saving" });
    }
  };

  if (loading) {
    return <div className="p-4 text-sm text-gray-600">Loading plans...</div>;
  }

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Plan Pricing & Limits</h1>
        <p className="text-sm text-gray-500">
          Manage pricing and usage limits for each subscription plan.
        </p>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-300 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="py-3 pl-4 pr-3 text-left font-medium text-gray-900 sm:pl-6">Plan</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Monthly</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Yearly</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Ad Accounts</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Campaign Limit</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200 bg-white">
            {plans.map((p, idx) => (
              <tr key={p.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 font-medium text-gray-900 sm:pl-6 capitalize">
                  {p.code}
                </td>
                <td className="px-3 py-4">
                  {p.is_custom ? (
                    <span className="text-gray-500">Custom Only</span>
                  ) : (
                    <input
                      type="number"
                      value={p.monthly_price}
                      onChange={(e) => onChange(idx, "monthly_price", e.target.value)}
                      className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                    />
                  )}
                </td>
                <td className="px-3 py-4">
                  {p.is_custom ? (
                    <span className="text-gray-500">Custom Only</span>
                  ) : (
                    <input
                      type="number"
                      value={p.yearly_price}
                      onChange={(e) => onChange(idx, "yearly_price", e.target.value)}
                      className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                    />
                  )}
                </td>
                <td className="px-3 py-4">
                  <input
                    type="number"
                    value={p.ad_account_limit}
                    onChange={(e) => onChange(idx, "ad_account_limit", e.target.value)}
                    className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                  />
                </td>
                <td className="px-3 py-4">
                  <input
                    type="number"
                    value={p.campaign_limit}
                    onChange={(e) => onChange(idx, "campaign_limit", e.target.value)}
                    className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="px-4 py-3 border-t bg-gray-50 text-right">
          <button
            onClick={onSave}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
