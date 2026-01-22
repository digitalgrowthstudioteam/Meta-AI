"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

// Pages allowed during hard block
const HARD_ALLOWED = ["/billing", "/logout"];

// Pages that should never be blocked
const PUBLIC_ALWAYS = ["/login", "/verify"];

export default function BlockGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  const [blockMode, setBlockMode] = useState<"none" | "soft" | "hard">("none");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);

    // Skip blocking for login/admin pages
    if (!pathname) return;

    if (PUBLIC_ALWAYS.includes(pathname) || pathname.startsWith("/admin")) {
      setBlockMode("none");
      return;
    }

    // Read cookie (set by session-context endpoint)
    const cookie = document.cookie
      .split("; ")
      .find((row) => row.startsWith("meta_ai_block="));

    const value = cookie?.split("=")[1] || "none";

    if (value === "soft") {
      setBlockMode("soft");
    } else if (value === "hard") {
      // Hard block logic: force billing redirect if not allowed page
      if (!HARD_ALLOWED.some((p) => pathname.startsWith(p))) {
        router.replace("/billing?upgrade=1");
      }
      setBlockMode("hard");
    } else {
      setBlockMode("none");
    }
  }, [pathname, router]);

  // Avoid flashing before hydration
  if (!hydrated) return null;

  return (
    <>
      {children}

      {blockMode === "soft" && <SoftBlockOverlay />}
      {blockMode === "hard" && !HARD_ALLOWED.some((p) => pathname.startsWith(p)) && (
        <HardBlockOverlay />
      )}
    </>
  );
}

// =========================
// UI COMPONENTS
// =========================

function SoftBlockOverlay() {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm z-[1000] flex items-center justify-center pointer-events-auto">
      <div className="bg-white p-6 rounded-xl shadow-lg max-w-md w-[90%] text-center">
        <h2 className="text-lg font-semibold text-gray-800">
          Trial Ended — Grace Period Active
        </h2>
        <p className="text-sm text-gray-600 mt-2">
          Some features are limited. Upgrade to continue full access.
        </p>
        <a
          href="/billing?upgrade=1"
          className="inline-block mt-4 px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium shadow hover:bg-indigo-500"
        >
          Upgrade Plan
        </a>
      </div>
    </div>
  );
}

function HardBlockOverlay() {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm z-[1000] flex items-center justify-center pointer-events-auto">
      <div className="bg-white p-6 rounded-xl shadow-lg max-w-md w-[90%] text-center">
        <h2 className="text-lg font-semibold text-gray-800">
          Subscription Required
        </h2>
        <p className="text-sm text-gray-600 mt-2">
          Your access has expired. Please upgrade to continue using the dashboard.
        </p>
        <a
          href="/billing?upgrade=1"
          className="inline-block mt-4 px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium shadow hover:bg-indigo-500"
        >
          Go to Billing
        </a>
      </div>
    </div>
  );
}
