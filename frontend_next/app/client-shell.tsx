"use client";

import { useState } from "react";
import Sidebar from "./components/Sidebar";

export default function ClientShell({
  showSidebar,
}: {
  showSidebar: boolean;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!showSidebar) return null;

  return (
    <>
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
