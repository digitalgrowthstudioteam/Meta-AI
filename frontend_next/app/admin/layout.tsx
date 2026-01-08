"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const adminNav = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/audit", label: "Audit Logs" },
  { href: "/admin/chat", label: "AI Chat" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  useEffect(() => {
    const ctxStr = sessionStorage.getItem("session_context");
    if (!ctxStr) {
      setIsAdmin(false);
      router.replace("/dashboard");
      return;
    }

    const ctx = JSON.parse(ctxStr);
    if (!ctx.user?.is_admin) {
      setIsAdmin(false);
      router.replace("/dashboard");
    } else {
      setIsAdmin(true);
    }
  }, [router]);

  if (isAdmin === null)
    return (
      <div className="p-6 text-sm text-gray-500">
        Loading admin panel...
      </div>
    );

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* SIDEBAR */}
      <aside className="w-56 bg-white border-r flex flex-col">
        <div className="px-4 py-3 border-b font-semibold text-gray-800">
          Admin Panel
        </div>

        <nav className="flex-1 py-2 space-y-1">
          {adminNav.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block px-4 py-2 text-sm rounded ${
                  active
                    ? "bg-blue-600 text-white"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t text-xs text-gray-400">
          © {new Date().getFullYear()} Meta-AI
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
