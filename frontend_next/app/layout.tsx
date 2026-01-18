import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import { cookies } from "next/headers";
import { useState } from "react";

export default function RootLayout({ children }: { children: ReactNode }) {
  // determine path from cookie
  const c = cookies();
  const pathname = c.get("next-url")?.value || "";

  const isAdmin = pathname.startsWith("/admin");
  const isLogin = pathname.startsWith("/login");
  const isHome = pathname === "/";

  const showSidebar = !(isAdmin || isLogin || isHome);

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900 flex min-h-screen">
        <Toaster position="bottom-right" />

        {/* client sidebar wrapper */}
        <ClientSidebarWrapper showSidebar={showSidebar}>
          {children}
        </ClientSidebarWrapper>
      </body>
    </html>
  );
}

// client component wrapper to handle state
"use client";
function ClientSidebarWrapper({
  children,
  showSidebar,
}: {
  children: ReactNode;
  showSidebar: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* mobile top bar toggle */}
      {showSidebar && (
        <div className="md:hidden fixed top-0 left-0 right-0 z-30 bg-white border-b flex items-center px-3 py-2">
          <button
            className="text-gray-700 mr-3"
            onClick={() => setOpen(true)}
          >
            ☰
          </button>
          <div className="text-sm font-medium">Menu</div>
        </div>
      )}

      {/* sidebar */}
      {showSidebar && (
        <Sidebar open={open} onClose={() => setOpen(false)} />
      )}

      {/* content */}
      <div className={`flex-1 min-h-screen overflow-y-auto ${showSidebar ? "md:ml-56" : ""} pt-12 md:pt-0`}>
        {children}
      </div>
    </>
  );
}
