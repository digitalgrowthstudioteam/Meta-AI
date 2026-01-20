"use client";

import { useState } from "react";
import toast from "react-hot-toast";

type PlanRow = {
  code: string;
  monthly_price: number;
  yearly_price: number;
  currency: string;
  is_custom?: boolean;
};

const mockPlans: PlanRow[] = [
  { code: "starter", monthly_price: 999, yearly_price: 9999, currency: "INR" },
  { code: "pro", monthly_price: 2499, yearly_price: 24999, currency: "INR" },
  { code: "agency", monthly_price: 5999, yearly_price: 59999, currency: "INR" },
  { code: "enterprise", monthly_price: 0, yearly_price: 0, currency: "INR", is_custom: true },
];

export default function AdminPlansPage() {
  const [plans, setPlans] = useState<PlanRow[]>(mockPlans);

  const onChange = (index: number, field: keyof PlanRow, value: string | number) => {
    setPlans((prev) => {
      const copy = [...prev];
      // convert number fields
      if (field === "monthly_price" || field === "yearly_price") {
        copy[index][field] = Number(value);
      } else {
        copy[index][field] = value as any;
      }
      return copy;
    });
  };

  const onSave = () => {
    toast.success("Pricing saved (Phase-2 mock only)");
  };

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Plan Pricing</h1>
        <p className="text-sm text-gray-500">
          Manage pricing and billing settings for each plan level.
        </p>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-300 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="py-3 pl-4 pr-3 text-left font-medium text-gray-900 sm:pl-6">Plan</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Monthly Price</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Yearly Price</th>
              <th className="px-3 py-3 text-left font-medium text-gray-900">Currency</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200 bg-white">
            {plans.map((p, idx) => (
              <tr key={p.code}>
                {/* Plan Label */}
                <td className="whitespace-nowrap py-4 pl-4 pr-3 font-medium text-gray-900 sm:pl-6 capitalize">
                  {p.code}
                </td>

                {/* Monthly */}
                <td className="px-3 py-4">
                  {p.is_custom ? (
                    <span className="text-gray-500">Custom only</span>
                  ) : (
                    <input
                      type="number"
                      value={p.monthly_price}
                      onChange={(e) => onChange(idx, "monthly_price", e.target.value)}
                      className="w-28 rounded border border-gray-300 px-2 py-1 text-sm"
                    />
                  )}
                </td>

                {/* Yearly */}
                <td className="px-3 py-4">
                  {p.is_custom ? (
                    <span className="text-gray-500">Custom only</span>
                  ) : (
                    <input
                      type="number"
                      value={p.yearly_price}
                      onChange={(e) => onChange(idx, "yearly_price", e.target.value)}
                      className="w-28 rounded border border-gray-300 px-2 py-1 text-sm"
                    />
                  )}
                </td>

                {/* Currency */}
                <td className="px-3 py-4">
                  <select
                    value={p.currency}
                    onChange={(e) => onChange(idx, "currency", e.target.value)}
                    disabled={p.is_custom}
                    className="w-24 rounded border border-gray-300 px-2 py-1 text-sm disabled:bg-gray-100"
                  >
                    <option value="INR">INR</option>
                    <option value="USD">USD</option>
                  </select>
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

      <p className="text-xs text-gray-400">
        Phase-2 mock only — backend integration in Phase-4.
      </p>
    </div>
  );
}
