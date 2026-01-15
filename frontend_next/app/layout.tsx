"use client";

import "./globals.css";
import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { Menu, X, Shield } from "lucide-react";
import { Toaster } from "react-hot-toast";
import { apiFetch } from "./lib/fetcher";

type SessionContext = {
  user: {
    id: string;
    email: string;
    role?: string;
    is_admin?: boolean;
    is_impersonated: boolean;
  };
  is_admin?: boolean;
  admin_view?: boolean;
  ad_account: {
    id: string;
    name: string;
    meta_account_id: string;
  } | null;
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [sessionLoaded, setSessionLoaded] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (pathname === "/" || pathname === "/login") {
        setSessionLoaded(true);
        return;
      }

      try {
        const res = await apiFetch("/api/session/context", {
          cache: "no-store",
        });

        if (res.ok) {
          const json = await res.json();
          setSession(json);
          sessionStorage.setItem("session_context", JSON.stringify(json));
        } else {
          setSession(null);
        }
      } catch {
        setSession(null);
      } finally {
        setSessionLoaded(true);
      }
    };

    load();
  }, [pathname]);

  const exitImpersonation = () => {
    sessionStorage.removeItem("impersonate_user");
    sessionStorage.removeItem("session_context");
    window.location.reload();
  };

  const toggleAdminView = async () => {
    const next = !session?.admin_view;
    document.cookie = `admin_view=${next}; path=/; SameSite=None; Secure`;
    window.location.href = next ? "/admin/dashboard" : "/dashboard";
  };

  // ADMIN SHELL
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

  // LOGIN / PUBLIC
  if (pathname === "/" || pathname === "/login") {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">{children}</body>
      </html>
    );
  }

  // APP SHELL
  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />

        {!sessionLoaded ? (
          <div className="flex h-screen items-center justify-center text-sm text-gray-500">
            Loading application context...
          </div>
        ) : (
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
                <SectionLabel label="Core" />
                <NavLink href="/dashboard" current={pathname === "/dashboard"}>
                  Dashboard
                </NavLink>
                <NavLink href="/campaigns" current={pathname.startsWith("/campaigns")}>
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
                <NavLink href="/settings" current={pathname === "/settings"}>
                  Settings
                </NavLink>

                {/* 🔥 ADMIN TOGGLE (ADMIN ONLY) */}
                {session?.user?.is_admin && (
                  <>
                    <SectionLabel label="Admin" />
                    <button
                      onClick={toggleAdminView}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md
                        text-gray-700 hover:bg-amber-50"
                    >
                      <Shield size={16} />
                      {session.admin_view ? "Switch to User View" : "Switch to Admin View"}
                    </button>
                  </>
                )}
              </nav>

              <div className="px-4 py-3 border-t text-xs text-gray-500">
                Secure • Server Sessions • AI Assisted
              </div>
            </aside>

            <div className="flex flex-col flex-1 min-w-0">
              {session?.user.is_impersonated && (
                <div className="bg-yellow-100 border-b px-4 py-2 flex justify-between text-sm">
                  <span>🔒 Viewing as {session.user.email}</span>
                  <button
                    onClick={exitImpersonation}
                    className="text-xs text-red-700"
                  >
                    Exit
                  </button>
                </div>
              )}

              {session?.ad_account && (
                <div className="bg-white border-b px-4 py-2 text-xs">
                  Active Ad Account: <strong>{session.ad_account.name}</strong>
                </div>
              )}

              <header className="md:hidden flex items-center gap-3 px-4 py-3 border-b bg-white">
                <button onClick={() => setSidebarOpen(true)}>
                  <Menu size={22} />
                </button>
                <span className="text-sm font-medium">Digital Growth Studio</span>
              </header>

              <main className="flex-1 overflow-y-auto p-4 md:p-8">
                <div className="max-w-7xl mx-auto space-y-6">{children}</div>
              </main>
            </div>
          </div>
        )}
      </body>
    </html>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="px-2 pt-4 pb-1 text-xs font-medium text-gray-400 uppercase">
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
    <Link
      href={href}
      className={`block rounded-md px-3 py-2 text-sm ${
        current
          ? "bg-amber-100 text-amber-800 font-medium"
          : "text-gray-700 hover:bg-amber-50"
      }`}
    >
      {children}
    </Link>
  );
}
