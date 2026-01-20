"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch } from "../lib/fetcher";

type Session = {
  user?: {
    is_admin?: boolean;
  } | null;
};

export default function Sidebar({
  mobileOpen,
  closeMobile,
}: {
  mobileOpen: boolean;
  closeMobile: () => void;
}) {
  const [session, setSession] = useState<Session | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch("/api/session/context", { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        setSession(data);
      } catch {}
    })();
  }, []);

  const isAdmin = session?.user?.is_admin === true;

  const handleLogout = async () => {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch {}
    router.push("/login");
  };

  return (
    <>
      {/* Mobile Overlay */}
      <div
        className={`fixed inset-0 bg-black/40 z-40 md:hidden transition-opacity duration-200 ${
          mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={closeMobile}
      />

      {/* Sidebar Panel */}
      <aside
        className={`fixed z-50 inset-y-0 left-0 w-56 bg-white border-r px-3 py-4 space-y-1 h-screen overflow-y-auto
        transform transition-transform duration-200
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        md:translate-x-0 md:static md:flex-shrink-0`}
      >
        <div className="flex items-center justify-between px-2 pb-3">
          <div className="text-xs uppercase tracking-wide text-gray-600">Menu</div>
          <button
            className="md:hidden text-gray-600 hover:text-gray-900"
            onClick={closeMobile}
          >
            ✕
          </button>
        </div>

        {/* Main Links */}
        <NavItem href="/dashboard" label="Dashboard" pathname={pathname} onClick={closeMobile} />
        <NavItem href="/campaigns" label="Campaigns" pathname={pathname} onClick={closeMobile} />
        <NavItem href="/ai-actions" label="AI Actions" pathname={pathname} onClick={closeMobile} />
        <NavItem href="/reports" label="Reports" pathname={pathname} onClick={closeMobile} />

        {/* NEW: Pricing Page */}
        <NavItem href="/pricing" label="Pricing" pathname={pathname} onClick={closeMobile} />

        <NavItem href="/billing" label="Billing" pathname={pathname} onClick={closeMobile} />
        <NavItem href="/settings" label="Settings" pathname={pathname} onClick={closeMobile} />

        {/* Admin Section */}
        {isAdmin && (
          <>
            <div className="pt-3 mt-3 border-t px-2 pb-1 text-xs uppercase tracking-wide text-gray-600">
              Admin
            </div>
            <NavItem
              href="/admin/dashboard"
              label="Admin Console"
              pathname={pathname}
              onClick={closeMobile}
            />
          </>
        )}

        {/* Logout */}
        <div className="mt-4 pt-4 border-t">
          <button
            onClick={handleLogout}
            className="w-full text-left rounded px-3 py-2 text-sm text-red-600 hover:bg-red-50 font-medium"
          >
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}

/* ---------------- Nav Item ---------------- */

function NavItem({
  href,
  label,
  pathname,
  onClick,
}: {
  href: string;
  label: string;
  pathname: string;
  onClick: () => void;
}) {
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));

  return (
    <Link
      href={href}
      onClick={onClick}
      className={`block rounded px-3 py-2 text-sm transition-colors ${
        active
          ? "bg-blue-50 text-blue-700 font-medium"
          : "text-gray-700 hover:bg-blue-50 hover:text-gray-900"
      }`}
    >
      {label}
    </Link>
  );
}
