"use client";

import "./globals.css";
import { ReactNode, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";

/* ----------------------------------
 * TYPES
 * ---------------------------------- */
type SessionContext = {
  user: {
    id: string;
    email: string;
    is_admin: boolean;
    is_impersonated: boolean;
  };
  ad_account: {
    id: string;
    name: string;
    meta_account_id: string;
  } | null;
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();
  const isAdminRoute = pathname.startsWith("/admin");

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [sessionLoaded, setSessionLoaded] = useState(false);

  // ----------------------------------
  // LOAD SESSION CONTEXT
  // ----------------------------------
  useEffect(() => {
    if (
      pathname === "/" ||
      pathname === "/login"
    ) {
      setSessionLoaded(true);
      return;
    }

    (async () => {
      try {
        const res = await fetch("/api/session/context", {
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          setSession(null);
        } else {
          setSession(await res.json());
        }
      } catch {
        setSession(null);
      } finally {
        setSessionLoaded(true);
      }
    })();
  }, [pathname]);

  const exitImpersonation = () => {
    sessionStorage.clear();
    window.location.reload();
  };

  // ----------------------------------
  // PUBLIC PAGES
  // ----------------------------------
  if (pathname === "/" || pathname === "/login") {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">
          {children}
        </body>
      </html>
    );
  }

  if (!sessionLoaded) {
    return (
      <html lang="en">
        <body className="bg-amber-50 text-gray-900">
          <div className="p-6 text-sm text-gray-500">
            Loading application…
          </div>
        </body>
      </html>
    );
  }

  // ----------------------------------
  // 🔒 ADMIN LAYOUT (ISOLATED)
  // ----------------------------------
  if (isAdminRoute) {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">
          <main className="p-6 max-w-7xl mx-auto">
            {children}
          </main>
        </body>
      </html>
    );
  }

  // ----------------------------------
  // USER APP LAYOUT
  // ----------------------------------
  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <div className="flex h-screen w-screen overflow-hidden">
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-40 bg-black/40 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          <aside
            className={`
              fixed z-50 inset-y-0 left-0 w-64 bg-white border-r border-amber-100
              flex flex-col transform transition-transform duration-200
              ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
              md:static md:translate-x-0
            `}
          >
            <div className="px-5 py-4 border-b border-amber-100 flex items-center justify-between">
              <div>
                <div className="text-sm uppercase tracking-wide text-amber-700">
                  Digital Growth Studio
                </div>
                <div className="text-xs text-gray-500">
                  Meta Ads AI Platform
                </div>
              </div>
              <button
                className="md:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                <X size={20} />
              </button>
            </div>

            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
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
              <NavLink href="/reports" current={pathname === "/reports"}>
                Reports
              </NavLink>

              <SectionLabel label="Billing & Settings" />
              <NavLink href="/billing" current={pathname === "/billing"}>
                Billing
              </NavLink>
              <NavLink
                href="/buy-campaign"
                current={pathname === "/buy-campaign"}
              >
                Buy Campaign
              </NavLink>
              <NavLink href="/settings" current={pathname === "/settings"}>
                Settings
              </NavLink>
            </nav>

            <div className="px-4 py-3 border-t border-amber-100 text-xs text-gray-500">
              Secure • Read-only • AI Assisted
            </div>
          </aside>

          <div className="flex flex-col flex-1 min-w-0">
            {session?.user.is_impersonated && (
              <div className="bg-yellow-100 border-b border-yellow-300 px-4 py-2 flex items-center justify-between text-sm">
                <div className="text-yellow-900">
                  🔒 Viewing as{" "}
                  <span className="font-medium">
                    {session.user.email}
                  </span>
                </div>
                <button
                  onClick={exitImpersonation}
                  className="text-xs font-medium text-red-700 hover:underline"
                >
                  Exit Impersonation
                </button>
              </div>
            )}

            {session?.ad_account && (
              <div className="bg-white border-b px-4 py-2 text-xs text-gray-600">
                Active Ad Account:{" "}
                <strong>{session.ad_account.name}</strong>
              </div>
            )}

            <header className="md:hidden flex items-center gap-3 px-4 py-3 border-b bg-white">
              <button onClick={() => setSidebarOpen(true)}>
                <Menu size={22} />
              </button>
              <span className="text-sm font-medium">
                Digital Growth Studio
              </span>
            </header>

            <main className="flex-1 overflow-y-auto p-4 md:p-8">
              <div className="max-w-7xl mx-auto space-y-6">
                {children}
              </div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

/* ---------------------------------- */
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
