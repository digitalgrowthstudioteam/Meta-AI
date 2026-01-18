"use client";

import "./globals.css";
import { ReactNode, useState } from "react";
import { Toaster } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import { cookies } from "next/headers";

export default function RootLayout({ children }: { children: ReactNode }) {
  // Read path written by middleware
  const c = cookies();
  const pathname = c.get("next-url")?.value || "";

  // Exclusion rules
  const isAdmin = pathname.startsWith("/admin");
  const isLogin = pathname.startsWith("/login");
  const isHome = pathname === "/";

  const showSidebar = !(isAdmin || isLogin || isHome);

  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900 flex">
        <Toaster position="bottom-right" />

        {/* mobile toggle button */}
        {showSidebar && (
          <button
            className="fixed top-3 left-3 z-50 md:hidden bg-white border rounded-md px-3 py-2 text-sm shadow"
            onClick={() => setMobileOpen(true)}
          >
            Menu
          </button>
        )}

        {/* sidebar */}
        {showSidebar && (
          <Sidebar mobileOpen={mobileOpen} closeMobile={() => setMobileOpen(false)} />
        )}

        {/* overlay */}
        {mobileOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-40 md:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}

        <div className="flex-1 min-h-screen overflow-y-auto">
          {children}
        </div>
      </body>
    </html>
  );
}
