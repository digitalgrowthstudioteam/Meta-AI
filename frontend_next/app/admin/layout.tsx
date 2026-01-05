"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";

export default function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      {/* ADMIN HEADER */}
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Admin Console
          </h1>
          <p className="text-xs text-gray-500">
            Audit • Rollback • System Safety (Read-only)
          </p>
        </div>
      </div>

      {/* ADMIN CONTENT */}
      <div className="space-y-4">{children}</div>
    </div>
  );
}
