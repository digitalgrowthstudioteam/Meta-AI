"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";
import ClientShell from "./client-shell";

export default function ClientLayoutWrapper({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const showSidebar =
    pathname !== "/" &&
    pathname !== "/login" &&
    !pathname.startsWith("/admin");

  return (
    <div className="flex w-full min-h-screen bg-[#FFFCEB]">
      {/** Sidebar Area */}
      <ClientShell showSidebar={showSidebar} />

      {/** Main Content Area */}
      <div className="flex-1 w-full min-h-screen overflow-x-auto">
        {children}
      </div>
    </div>
  );
}
