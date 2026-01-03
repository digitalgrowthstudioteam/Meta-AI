"use client";

import "./globals.css";
import Link from "next/link";
import { ReactNode } from "react";
import clsx from "clsx";

type Props = {
  children: ReactNode;
};

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/campaigns", label: "Campaigns", primary: true },
  { href: "/ai-actions", label: "AI Actions" },
  { href: "/audience-insights", label: "Audience Insights" },
  { href: "/reports", label: "Reports" },
  { href: "/buy-campaign", label: "Buy Campaign" },
  { href: "/billing", label: "Billing" },
  { href: "/settings", label: "Settings" },
];

export default function RootLayout({ children }: Props) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <div className="flex h-screen w-screen overflow-hidden">
          
          {/* SIDEBAR */}
          <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div className="h-16 flex items-center px-6 border-b border-gray-200">
              <div className="font-semibold text-base tracking-tight">
                Digital Growth Studio
              </div>
            </div>

            <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
              {NAV_ITEMS.map((item) => (
                <SidebarLink
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  primary={item.primary}
                />
              ))}
            </nav>
          </aside>

          {/* MAIN */}
          <div className="flex flex-col flex-1 min-w-0">
            <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
              <div className="text-sm text-gray-600">
                Meta Ads AI • Development Mode (Auth Disabled)
              </div>
            </header>

            <main className="flex-1 overflow-y-auto p-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

function SidebarLink({
  href,
  label,
  primary,
}: {
  href: string;
  label: string;
  primary?: boolean;
}) {
  return (
    <Link
      href={href}
      className={clsx(
        "flex items-center rounded px-3 py-2 transition",
        "text-gray-700 hover:bg-gray-100",
        primary && "font-medium"
      )}
    >
      {label}
    </Link>
  );
}
