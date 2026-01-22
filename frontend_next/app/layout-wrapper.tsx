"use client";

import { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import ClientShell from "./client-shell";
import Topbar from "./components/Topbar";
import { BillingProvider, useBilling } from "./context/BillingContext";

function BillingGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { block, loading } = useBilling();

  if (loading) return <div className="p-6">Loading...</div>;

  // Hard block → redirect to billing page
  if (block.hard_block) {
    router.replace("/billing");
    return null;
  }

  return <>{children}</>;
}

export default function ClientLayoutWrapper({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const showSidebar =
    pathname !== "/" &&
    pathname !== "/login" &&
    !pathname.startsWith("/admin");

  return (
    <BillingProvider>
      <BillingGate>
        <div className="flex w-full min-h-screen bg-[#FFFCEB]">
          {/** SIDEBAR (LEFT FIXED) */}
          <ClientShell showSidebar={showSidebar} />

          {/** CONTENT AREA (TOPBAR + CHILDREN) */}
          <div className="flex-1 w-full min-h-screen flex flex-col overflow-hidden">
            <Topbar />
            <div className="flex-1 overflow-x-auto overflow-y-auto">
              {children}
            </div>
          </div>
        </div>
      </BillingGate>
    </BillingProvider>
  );
}
