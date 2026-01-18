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

  return <ClientShell showSidebar={showSidebar}>{children}</ClientShell>;
}
