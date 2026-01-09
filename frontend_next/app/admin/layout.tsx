"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Menu, X, ChevronRight, ChevronDown } from "lucide-react";
import { Toaster } from "react-hot-toast";

type SessionContext = {
  user: {
    email: string;
    is_admin: boolean;
  };
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Load session
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/session/context", {
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          router.replace("/login");
          return;
        }

        const data = await res.json();
        setSession(data);
      } catch {
        router.replace("/login");
      } finally {
        setLoaded(true);
      }
    })();
  }, [router]);

  if (!loaded) {
    return <div className="p-6 text-sm text-gray-500">Loading admin…</div>;
  }

  if (!session?.user.is_admin) {
    return <div className="p-6 text-sm text-red-600">Access denied — Admin only.</div>;
  }

  return (
    <div className="flex h-screen w-screen bg-slate-50 overflow-hidden text-gray-900">
      <Toaster position="bottom-right" />

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

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
            <div className="text-sm uppercase tracking-wide text-blue-700">Admin Console</div>
            <div className="text-xs text-gray-500">Digital Growth Studio</div>
          </div>
          <button className="md:hidden" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 px-2 py-3 space-y-1 overflow-y-auto">
          <SidebarGroup label="Dashboard">
            <NavItem href="/admin/dashboard" pathname={pathname}>Overview</NavItem>
          </SidebarGroup>

          <SidebarGroup label="Users">
            <NavItem href="/admin/users" pathname={pathname}>Users & Impersonation</NavItem>
            <NavItem href="/admin/chat" pathname={pathname}>Chat Monitor</NavItem>
          </SidebarGroup>

          <SidebarGroup label="Campaigns & AI">
            <NavItem href="/admin/campaigns" pathname={pathname}>Campaigns</NavItem>
            <NavItem href="/admin/ai-actions" pathname={pathname}>AI Actions Queue</NavItem>
            <NavItem href="/admin/ai-suggestions" pathname={pathname}>AI Suggestions</NavItem>
          </SidebarGroup>

          <SidebarGroup label="Billing">
            <NavItem href="/admin/billing" pathname={pathname}>Subscriptions</NavItem>
            <NavItem href="/admin/invoices" pathname={pathname}>Invoices</NavItem>
            <NavItem href="/admin/razorpay" pathname={pathname}>Razorpay Logs</NavItem>
          </SidebarGroup>

          <SidebarGroup label="Audit & Compliance">
            <NavItem href="/admin/audit" pathname={pathname}>Audit Logs</NavItem>
            <NavItem href="/admin/reports" pathname={pathname}>Reports</NavItem>
          </SidebarGroup>

          <SidebarGroup label="System">
            <NavItem href="/admin/settings" pathname={pathname}>Global Settings</NavItem>
            <NavItem href="/admin/metrics" pathname={pathname}>Metrics Sync</NavItem>
            <NavItem href="/admin/feature-flags" pathname={pathname}>Feature Flags</NavItem>
            <NavItem href="/admin/risk" pathname={pathname}>Risk & Safety</NavItem>
          </SidebarGroup>
        </nav>

        <div className="px-4 py-3 border-t text-xs text-gray-500">Admin Only • Audited</div>
      </aside>

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

/* -------------------- COMPONENTS -------------------- */

function SidebarGroup({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="space-y-1">
      <button
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600 hover:bg-gray-100 rounded"
        onClick={() => setOpen(!open)}
      >
        <span>{label}</span>
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>
      {open && <div className="ml-2 space-y-1">{children}</div>}
    </div>
  );
}

function NavItem({
  href,
  pathname,
  children,
}: {
  href: string;
  pathname: string;
  children: ReactNode;
}) {
  const active = pathname.startsWith(href);
  return (
    <a
      href={href}
      className={`block rounded px-3 py-2 text-sm ${
        active
          ? "bg-blue-100 text-blue-800 font-medium"
          : "text-gray-700 hover:bg-blue-50 hover:text-gray-900"
      }`}
    >
      {children}
    </a>
  );
}
