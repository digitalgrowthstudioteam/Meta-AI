"use client";

import "./globals.css";
import { ReactNode, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Toaster } from "react-hot-toast";
import Link from "next/link";
import { Menu, X, Shield } from "lucide-react";
import { apiFetch } from "./lib/fetcher";

type SessionContext = {
  user: {
    id: string;
    email: string;
    role?: string;
    is_admin?: boolean;
    is_impersonated?: boolean;
  };
  is_admin?: boolean;
  admin_view?: boolean;
  ad_account?: {
    id: string;
    name: string;
    meta_account_id: string;
  } | null;
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  /**
   * 🔒 HARD RULE
   * Admin routes must NEVER load user shell, session redirect logic,
   * or admin_view toggles.
   */
  if (pathname.startsWith("/admin")) {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">
          <Toaster position="bottom-right" />
          {children}
        </body>
      </html>
    );
  }

  /**
   * 🛑 ADMIN SHOULD NEVER ENTER USER ROUTES
   */
  if (
    pathname === "/dashboard" ||
    pathname.startsWith("/campaigns") ||
    pathname.startsWith("/ai-actions") ||
    pathname.startsWith("/billing") ||
    pathname.startsWith("/settings") ||
    pathname.startsWith("/reports")
  ) {
    return (
      <html lang="en">
        <body>
          <script
            dangerouslySetInnerHTML={{
              __html: `window.location.href='/admin/dashboard'`,
            }}
          />
        </body>
      </html>
    );
  }

  /**
   * PUBLIC ROUTES
   */
  if (pathname === "/" || pathname === "/login") {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">{children}</body>
      </html>
    );
  }

  /**
   * USER APP SHELL ONLY
   */
  return <UserShell>{children}</UserShell>;
}

/* ===================================================== */
/* ================= USER SHELL ONLY =================== */
/* ===================================================== */

function UserShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch("/api/session/context", {
          cache: "no-store",
        });

        if (res.ok) {
          setSession(await res.json());
        } else {
          setSession(null);
        }
      } catch {
        setSession(null);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  if (!loaded) {
    return (
      <html lang="en">
        <body className="flex h-screen items-center justify-center text-sm text-gray-500">
          Loading…
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />

        <div className="flex h-screen w-screen overflow-hidden">
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-40 bg-black/40 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          <aside
            className={`
              fixed z-50 inset-y-0 left-0 w-64 bg-white border-r
              flex flex-col transform transition-transform
              ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
              md:static md:translate-x-0
            `}
          >
            <div className="px-5 py-4 border-b flex justify-between items-center">
              <div>
                <div className="text-sm font-bold text-amber-700">
                  Digital Growth Studio
                </div>
                <div className="text-xs text-gray-500">Meta Ads AI</div>
              </div>
              <button className="md:hidden" onClick={() => setSidebarOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              <Nav href="/dashboard" active={pathname === "/dashboard"}>
                Dashboard
              </Nav>
              <Nav href="/campaigns" active={pathname.startsWith("/campaigns")}>
                Campaigns
              </Nav>
              <Nav href="/ai-actions" active={pathname === "/ai-actions"}>
                AI Actions
              </Nav>
              <Nav href="/reports" active={pathname === "/reports"}>
                Reports
              </Nav>
              <Nav href="/billing" active={pathname === "/billing"}>
                Billing
              </Nav>
              <Nav href="/settings" active={pathname === "/settings"}>
                Settings
              </Nav>

              {session?.user?.is_admin && (
                <>
                  <div className="pt-4 text-xs uppercase text-gray-400">
                    Admin
                  </div>
                  <Link
                    href="/admin/dashboard"
                    className="flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-amber-50"
                  >
                    <Shield size={16} />
                    Admin Console
                  </Link>
                </>
              )}
            </nav>
          </aside>

          <div className="flex flex-col flex-1">
            <header className="md:hidden flex items-center gap-3 px-4 py-3 border-b bg-white">
              <button onClick={() => setSidebarOpen(true)}>
                <Menu size={22} />
              </button>
              <span className="text-sm font-medium">Digital Growth Studio</span>
            </header>

            <main className="flex-1 overflow-y-auto p-4 md:p-8">
              <div className="max-w-7xl mx-auto">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

function Nav({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`block rounded-md px-3 py-2 text-sm ${
        active
          ? "bg-amber-100 text-amber-800 font-medium"
          : "text-gray-700 hover:bg-amber-50"
      }`}
    >
      {children}
    </Link>
  );
}
