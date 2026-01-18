import "./globals.css";
import { ReactNode } from "react";
import { cookies } from "next/headers";
import { Toaster } from "react-hot-toast";
import UserShell from "./UserShell";

export default async function RootLayout({ children }: { children: ReactNode }) {
  const cookieStore = cookies();
  const pathname = cookieStore.get("next-url")?.value || "";

  // 🔐 SERVER-SIDE PRELOAD (writes meta_ai_role cookie early)
  try {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/session/context`;
    await fetch(url, {
      credentials: "include",
      cache: "no-store",
      headers: {
        cookie: cookieStore.toString(),
      },
    });
  } catch (_) {}

  // ============================
  // 1. ADMIN → HARD BYPASS
  // ============================
  if (pathname.startsWith("/admin")) {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">
          <Toaster position="bottom-right" />
          {children}
        </body>
      </html>
    );
  }

  // ============================
  // 2. PUBLIC PAGES
  // ============================
  if (pathname === "/" || pathname === "/login") {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-gray-900">
          <Toaster position="bottom-right" />
          {children}
        </body>
      </html>
    );
  }

  // ============================
  // 3. USER SHELL (Client-side)
  // ============================
  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />
        <UserShell>{children}</UserShell>
      </body>
    </html>
  );
}
