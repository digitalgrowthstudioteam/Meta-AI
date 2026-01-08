"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { Toaster } from "react-hot-toast";

type SessionContext = {
  user: {
    email: string;
    is_admin: boolean;
  };
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const ctx = sessionStorage.getItem("session_context");
    if (ctx) {
      setSession(JSON.parse(ctx));
    }
    setLoaded(true);
  }, []);

  if (!loaded) {
    return (
      <div className="p-6 text-sm text-gray-500">
        Loading admin…
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-slate-50 overflow-hidden text-gray-900">
      <Toaster position="bottom-right" />

      {/* Overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* SIDEBAR */}
      <aside
        className={`
          fixed md:static z-50 inset-y-0 left-0 w-64 bg-white border-r
          flex flex-col transform transition-transform duration-200
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0
        `}
      >
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <div>
            <div className="text-sm uppercase tracking-wide text-blue-700">
              Admin Console
            </div>
            <div className="text-xs text-gray-500">
              Digital Growth Studio
            </div>
          </div>
          <button className="md:hidden" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <SectionLabel label="Overview" />
          <NavLink href="/admin/dashboard" current={pathname === "/admin/dashboard"}>
            Dashboard
          </NavLink>

          <SectionLabel label="Users" />
          <NavLink href="/admin/users" current={pathname === "/admin/users"}>
            Users & Impersonation
          </NavLink>

          <SectionLabel label="Controls" />
          <NavLink href="/admin/settings" current={pathname === "/admin/settings"}>
            Global Settings
          </NavLink>
          <NavLink href="/admin/metrics" current={pathname === "/admin/metrics"}>
            Metrics Sync
          </NavLink>

          <SectionLabel label="Audit" />
          <NavLink href="/admin/audit" current={pathname === "/admin/audit"}>
            Audit Logs
          </NavLink>
        </nav>

        <div className="px-4 py-3 border-t text-xs text-gray-500">
          Admin Only • Audited
        </div>
      </aside>

      {/* MAIN */}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="md:hidden flex items-center gap-3 px-4 py-3 border-b bg-white">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu size={22} />
          </button>
          <span className="text-sm font-medium">Admin Console</span>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}

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
          ? "bg-blue-100 text-blue-800 font-medium"
          : "text-gray-700 hover:bg-blue-50 hover:text-gray-900"
      }`}
    >
      {children}
    </a>
  );
}
