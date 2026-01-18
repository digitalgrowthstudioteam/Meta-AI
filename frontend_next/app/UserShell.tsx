"use client";

import { ReactNode, useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Menu, X, Shield } from "lucide-react";

type SessionContext = {
  user: {
    id: string;
    email: string;
    role?: string;
    is_admin?: boolean;
    is_impersonated?: boolean;
  } | null;
};

export default function UserShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // 🟢 FIXED URL — always hit /api/session/context
        const backend = `${process.env.NEXT_PUBLIC_API_URL}/api/session/context`;

        const res = await fetch(backend, {
          credentials: "include",
          cache: "no-store",
        });

        setSession(res.ok ? await res.json() : null);
      } catch {
        setSession(null);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  const isAdmin =
    session?.user?.is_admin === true ||
    session?.user?.role === "admin";

  if (!loaded) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-gray-500">
        Loading…
      </div>
    );
  }

  return (
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
          <Nav href="/dashboard" active={pathname.startsWith("/dashboard")}>Dashboard</Nav>
          <Nav href="/campaigns" active={pathname.startsWith("/campaigns")}>Campaigns</Nav>
          <Nav href="/ai-actions" active={pathname.startsWith("/ai-actions")}>AI Actions</Nav>
          <Nav href="/reports" active={pathname.startsWith("/reports")}>Reports</Nav>
          <Nav href="/billing" active={pathname.startsWith("/billing")}>Billing</Nav>
          <Nav href="/settings" active={pathname.startsWith("/settings")}>Settings</Nav>

          {isAdmin && (
            <>
              <div className="pt-4 text-xs uppercase text-gray-400">Admin</div>
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
