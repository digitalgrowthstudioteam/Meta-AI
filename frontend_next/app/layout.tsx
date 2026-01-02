"use client";

import "./globals.css";
import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Props = {
  children: ReactNode;
};

export default function RootLayout({ children }: Props) {
  const router = useRouter();
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    async function verifySession() {
      try {
        const res = await fetch("/auth/me", {
          credentials: "include",
        });

        if (!res.ok) {
          router.replace("/auth/login");
          return;
        }
      } catch {
        router.replace("/auth/login");
        return;
      } finally {
        setCheckingSession(false);
      }
    }

    verifySession();
  }, [router]);

  /* ===============================
     LOADING STATE (SESSION CHECK)
  =============================== */
  if (checkingSession) {
    return (
      <html lang="en">
        <body className="bg-gray-100 text-gray-900">
          <div className="flex items-center justify-center h-screen">
            <div className="text-sm text-gray-500">
              Verifying session…
            </div>
          </div>
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body className="bg-gray-100 text-gray-900">
        <div className="flex h-screen w-screen overflow-hidden">
          
          {/* ===============================
              SIDEBAR
          =============================== */}
          <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div className="h-16 flex items-center px-6 border-b border-gray-200 font-semibold text-lg">
              Digital Growth Studio
            </div>

            <nav className="flex-1 px-4 py-4 space-y-1 text-sm">
              <SidebarLink href="/dashboard" label="Dashboard" />
              <SidebarLink href="/campaigns" label="Campaigns" />
              <SidebarLink href="/ai-actions" label="AI Actions" />
              <SidebarLink href="/audience-insights" label="Audience Insights" />
              <SidebarLink href="/billing" label="Billing" />
              <SidebarLink href="/buy-campaign" label="Buy Campaign" />
              <SidebarLink href="/reports" label="Reports" />
              <SidebarLink href="/settings" label="Settings" />
            </nav>
          </aside>

          {/* ===============================
              MAIN CONTENT
          =============================== */}
          <div className="flex flex-col flex-1">
            <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6">
              <div className="text-sm text-gray-600">
                Meta Ads AI • Read-only Intelligence Mode
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

/* ===============================
   SIDEBAR LINK
=============================== */
function SidebarLink({
  href,
  label,
}: {
  href: string;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="block rounded px-3 py-2 text-gray-700 hover:bg-gray-100 transition"
    >
      {label}
    </Link>
  );
}
