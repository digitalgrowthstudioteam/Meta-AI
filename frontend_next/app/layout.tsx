import "./globals.css";
import { ReactNode } from "react";
import { cookies } from "next/headers";
import { Toaster } from "react-hot-toast";
import UserShell from "./UserShell";

export const metadata = {
  title: "Digital Growth Studio - Meta Ads AI",
  description: "AI powered Meta Ads management platform",
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const cookieStore = cookies();
  const pathname = cookieStore.get("next-url")?.value || "/";

  // 🔐 SERVER-SIDE PRELOAD (ensures meta_ai_role cookie exists early)
  try {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/session/context`;
    await fetch(url, {
      credentials: "include",
      cache: "no-store",
      headers: { cookie: cookieStore.toString() },
    });
  } catch (_) {}

  const isAdmin = pathname.startsWith("/admin");
  const isPublic = pathname === "/" || pathname === "/login";

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />

        {isAdmin && children}

        {isPublic && !isAdmin && children}

        {!isAdmin && !isPublic && <UserShell>{children}</UserShell>}
      </body>
    </html>
  );
}
