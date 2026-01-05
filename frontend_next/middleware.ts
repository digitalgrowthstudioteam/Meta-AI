"use client";

import "./globals.css";
import { ReactNode, useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";

export default function RootLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // --------------------------------------------------
  // PUBLIC PAGES — NO DASHBOARD LAYOUT
  // --------------------------------------------------
  if (pathname === "/" || pathname === "/login") {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">{children}</body>
      </html>
    );
  }

  // --------------------------------------------------
  // RESPONSIVE APP LAYOUT (MOBILE / TABLET / DESKTOP)
  // --------------------------------------------------
  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <div className="flex h-screen overflow-hidden">
          {/* MOBILE OVERLAY */}
          {open && (
            <div
              className="fixed inset-0 z-30 bg-black/40 md:hidden"
              onClick={() => setOpen(false)}
            />
          )}

          {/* SIDEBAR */}
          <aside
            className={`fixed z-40 h-full w-64 bg-white border-r border-amber-100 flex flex-col transform transition-transform md:static md:translate-x-0 ${
              open ? "translate-x-0" : "-translate-x-full"
            }`}
          >
            <div className="px-5 py-4 border-b border-amber-100">
              <div className="text-sm uppercase tracking-wide text-amber-700">
                Digital Growth Studio
              </div>
              <div className="text-xs text-gray-500">Meta Ads AI Platform</div>
            </div>

            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              <SectionLabel label="Core" />
              <NavLink href="/dashboard" current={pathname === "/dashboard"}>Dashboard</NavLink>
              <NavLink href="/campaigns" current={pathname === "/campaigns"}>Campaigns</NavLink>
              <NavLink href="/ai-actions" current={pathname === "/ai-actions"}>AI Actions</NavLink>

              <SectionLabel label="Insights" />
              <NavLink href="/audience-insights" current={pathname === "/audience-insights"}>Audience Insights</NavLink>
              <NavLink href="/industry-benchmarks" current={pathname === "/industry-benchmarks"}>Industry Benchmarks</NavLink>
              <NavLink href="/reports" current={pathname === "/reports"}>Reports</NavLink>

              <SectionLabel label="Billing & Settings" />
              <NavLink href="/buy-campaign" current={pathname === "/buy-campaign"}>Buy Campaign</NavLink>
              <NavLink href="/billing" current={pathname === "/billing"}>Billing</NavLink>
              <NavLink href="/settings" current={pathname === "/settings"}>Settings</NavLink>
            </nav>

            <div className="px-4 py-3 border-t border-amber-100 text-xs text-gray-500">
              Secure • Read-only • AI Assisted
            </div>
          </aside>

          {/* MAIN */}
          <div className="flex flex-col flex-1">
            {/* MOBILE HEADER */}
            <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b">
              <button onClick={() => setOpen(!open)}>
                {open ? <X size={22} /> : <Menu size={22} />}
              </button>
              <div className="text-sm font-semibold">Digital Growth Studio</div>
            </header>

            <main className="flex-1 overflow-y-auto p-4 md:p-8">
              <div className="max-w-7xl mx-auto space-y-6">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="px-2 pt-4 pb-1 text-xs font-medium text-gray-400 uppercase tracking-wide">
      {label}
    </div>
  );
}

function NavLink({ href, current, children }: { href: string; current: boolean; children: ReactNode }) {
  return (
    <a
      href={href}
      className={`block rounded-md px-3 py-2 text-sm transition ${
        current
          ? "bg-amber-100 text-amber-800 font-medium"
          : "text-gray-700 hover:bg-amber-50 hover:text-gray-900"
      }`}
    >
      {children}
    </a>
  );
}
