"use client";

import { ReactNode, useState } from "react";
import Sidebar from "./components/Sidebar";

export default function ClientShell({
  children,
  showSidebar,
}: {
  children: ReactNode;
  showSidebar: boolean;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {showSidebar && (
        <button
          onClick={() => setMobileOpen(true)}
          className="fixed top-3 left-3 z-50 md:hidden bg-white border rounded-md px-3 py-2 text-sm shadow"
        >
          Menu
        </button>
      )}

      {showSidebar && (
        <Sidebar mobileOpen={mobileOpen} closeMobile={() => setMobileOpen(false)} />
      )}

      {children}
    </>
  );
}
