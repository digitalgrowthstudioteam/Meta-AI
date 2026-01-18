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

  // 🔐 SERVER-SIDE PRELOAD (ensures meta_ai_role cookie exists early)
  try {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/session/context`;
    await fetch(url, {
      credentials: "include",
      cache: "no-store",
      headers: {
        cookie: cookieStore.toString(),
      },
    });
  } catch (_) {}

  // NOTE:
  // We let `/admin/**` be handled by /app/admin/layout.tsx
  // We let `/login` and `/` be handled normally
  // Everything else uses UserShell

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />
        {children}
      </body>
    </html>
  );
}
