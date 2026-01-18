"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/fetcher";

type Session = {
  user?: {
    is_admin?: boolean;
  } | null;
};

export default function Sidebar() {
  const [session, setSession] = useState<Session | null>(null);

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

  return (
    <aside className="w-56 shrink-0 bg-white border-r h-screen overflow-y-auto px-3 py-4 space-y-1">
      <div className="px-2 pb-3 text-xs uppercase tracking-wide text-gray-600">
        Menu
      </div>

      <NavItem href="/dashboard" label="Dashboard" />
      <NavItem href="/campaigns" label="Campaigns" />
      <NavItem href="/ai-actions" label="AI Actions" />
      <NavItem href="/reports" label="Reports" />
      <NavItem href="/billing" label="Billing" />
      <NavItem href="/settings" label="Settings" />

      {isAdmin && (
        <>
          <div className="pt-3 mt-3 border-t px-2 pb-1 text-xs uppercase tracking-wide text-gray-600">
            Admin
          </div>
          <NavItem href="/admin/dashboard" label="Admin Console" />
        </>
      )}
    </aside>
  );
}

function NavItem({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="block rounded px-3 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-gray-900"
    >
      {label}
    </Link>
  );
}
