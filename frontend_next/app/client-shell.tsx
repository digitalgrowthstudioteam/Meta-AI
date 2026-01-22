"use client";

import { useState } from "react";
import Sidebar from "./components/Sidebar";
import { useBilling } from "./context/BillingContext";

export default function ClientShell({
  showSidebar,
}: {
  showSidebar: boolean;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { status, trial_days_left, grace_days_left } = useBilling();

  if (!showSidebar) return null;

  const renderBadge = () => {
    if (status === "trial") {
      return (
        <div className="bg-yellow-500 text-white text-xs px-2 py-1 rounded">
          Trial: {trial_days_left} days left
        </div>
      );
    }
    if (status === "grace") {
      return (
        <div className="bg-orange-500 text-white text-xs px-2 py-1 rounded">
          Trial ended — {grace_days_left} grace days left
        </div>
      );
    }
    if (status === "expired") {
      return (
        <div className="bg-red-600 text-white text-xs px-2 py-1 rounded">
          Upgrade Required
        </div>
      );
    }
    return null;
  };

  return (
    <>
      {/* Top Badge */}
      <div className="fixed top-2 right-2 z-40">
        {renderBadge()}
      </div>

      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="md:hidden fixed top-3 left-3 z-50 bg-white border rounded-md px-3 py-2 text-sm shadow"
      >
        Menu
      </button>

      {/* Sidebar */}
      <Sidebar
        mobileOpen={mobileOpen}
        closeMobile={() => setMobileOpen(false)}
      />
    </>
  );
}
