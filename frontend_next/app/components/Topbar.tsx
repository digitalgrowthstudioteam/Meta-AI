"use client";

import { useBilling } from "../context/BillingContext";
import { useRouter } from "next/navigation";

export default function Topbar() {
  const router = useRouter();
  const {
    status,
    trial_days_left,
    grace_days_left,
    block,
    loading,
  } = useBilling();

  if (loading) {
    return (
      <div className="w-full h-12 border-b border-gray-200 bg-white flex items-center px-4 text-sm text-gray-500">
        Loading billing status...
      </div>
    );
  }

  const renderStatus = () => {
    if (status === "trial") {
      return (
        <span className="inline-block text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 font-medium">
          Trial — {trial_days_left} days left
        </span>
      );
    }

    if (status === "grace") {
      return (
        <span className="inline-block text-xs px-2 py-1 rounded bg-amber-100 text-amber-700 font-medium">
          Grace — {grace_days_left} days left
        </span>
      );
    }

    if (block.hard_block) {
      return (
        <span className="inline-block text-xs px-2 py-1 rounded bg-red-100 text-red-700 font-medium">
          Expired — Upgrade Required
        </span>
      );
    }

    return (
      <span className="inline-block text-xs px-2 py-1 rounded bg-green-100 text-green-700 font-medium">
        Active
      </span>
    );
  };

  return (
    <div className="w-full h-12 border-b border-gray-200 bg-white flex items-center justify-between px-4 z-30">
      {/* Left */}
      <div className="flex items-center gap-2">{renderStatus()}</div>

      {/* Right */}
      <button
        onClick={() => router.push("/billing")}
        className="text-sm text-indigo-600 font-medium hover:text-indigo-500"
      >
        Billing →
      </button>
    </div>
  );
}
