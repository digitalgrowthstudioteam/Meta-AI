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
      <body className="bg-gray-50 text-gray-900">
        <div className="flex h-screen w-screen overflow-hidden">
          {/* SIDEBAR */}
          <aside className="w-64 border-r bg-white">
            <div className="p-4 font-semibold">
              Digital Growth Studio
            </div>

            <nav className="space-y-1 px-2">
              <NavLink href="/dashboard" current={pathname === "/dashboard"}>
                Dashboard
              </NavLink>
              <NavLink href="/campaigns" current={pathname === "/campaigns"}>
                Campaigns
              </NavLink>
              <NavLink href="/ai-actions" current={pathname === "/ai-actions"}>
                AI Actions
              </NavLink>
              <NavLink href="/audience-insights" current={pathname === "/audience-insights"}>
                Audience Insights
              </NavLink>
              <NavLink href="/reports" current={pathname === "/reports"}>
                Reports
              </NavLink>
              <NavLink href="/buy-campaign" current={pathname === "/buy-campaign"}>
                Buy Campaign
              </NavLink>
              <NavLink href="/billing" current={pathname === "/billing"}>
                Billing
              </NavLink>
              <NavLink href="/settings" current={pathname === "/settings"}>
                Settings
              </NavLink>
            </nav>
          </aside>

          {/* MAIN */}
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </body>
    </html>
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
      className={`block rounded px-3 py-2 text-sm ${
        current
          ? "bg-blue-50 text-blue-700 font-medium"
          : "text-gray-700 hover:bg-gray-100"
      }`}
    >
      {children}
    </a>
  );
}
