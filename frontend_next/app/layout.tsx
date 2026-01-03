"use client";

import "./globals.css";
import { ReactNode } from "react";
import { usePathname } from "next/navigation";

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <div className="flex h-screen w-screen overflow-hidden">
          {/* SIDEBAR */}
          <aside className="w-64 bg-white border-r border-amber-100 flex flex-col">
            {/* BRAND */}
            <div className="px-5 py-4 border-b border-amber-100">
              <div className="text-sm uppercase tracking-wide text-amber-700">
                Digital Growth Studio
              </div>
              <div className="text-xs text-gray-500">
                Meta Ads AI Platform
              </div>
            </div>

            {/* NAV */}
            <nav className="flex-1 px-3 py-4 space-y-1">
              <SectionLabel label="Core" />
              <NavLink href="/dashboard" current={pathname === "/dashboard"}>
                Dashboard
              </NavLink>
              <NavLink href="/campaigns" current={pathname === "/campaigns"}>
                Campaigns
              </NavLink>
              <NavLink href="/ai-actions" current={pathname === "/ai-actions"}>
                AI Actions
              </NavLink>

              <SectionLabel label="Insights" />
              <NavLink
                href="/audience-insights"
                current={pathname === "/audience-insights"}
              >
                Audience Insights
              </NavLink>
              <NavLink href="/reports" current={pathname === "/reports"}>
                Reports
              </NavLink>

              <SectionLabel label="Billing & Settings" />
              <NavLink
                href="/buy-campaign"
                current={pathname === "/buy-campaign"}
              >
                Buy Campaign
              </NavLink>
              <NavLink href="/billing" current={pathname === "/billing"}>
                Billing
              </NavLink>
              <NavLink href="/settings" current={pathname === "/settings"}>
                Settings
              </NavLink>
            </nav>

            {/* FOOTER */}
            <div className="px-4 py-3 border-t border-amber-100 text-xs text-gray-500">
              Dev Mode • Auth Disabled
            </div>
          </aside>

          {/* MAIN */}
          <main className="flex-1 overflow-y-auto p-8">
            <div className="max-w-7xl mx-auto space-y-6">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}

/* -------------------------------------------------- */
/* COMPONENTS */
/* -------------------------------------------------- */

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="px-2 pt-4 pb-1 text-xs font-medium text-gray-400 uppercase tracking-wide">
      {label}
    </div>
  );
}

function NavLink({
  href,
  current,
  children,
}: {
  href: string;
  current: boolean;
  children: ReactNode;
}) {
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
