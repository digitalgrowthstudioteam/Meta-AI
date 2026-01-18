"use client";

import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import { usePathname } from "next/navigation";
import ClientShell from "./client-shell";

export const metadata = {
  title: "Meta AI",
  description: "Digital Growth Studio",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const showSidebar =
    pathname !== "/" &&
    pathname !== "/login" &&
    !pathname.startsWith("/admin");

  return (
    <html lang="en">
      <body className="min-h-screen w-full bg-[#FFFCEB] text-gray-900 flex">
        <Toaster position="bottom-right" />

        <div className="flex min-h-screen w-full">
          <ClientShell showSidebar={showSidebar}>
            <main className="flex-1 min-h-screen px-6 py-6 space-y-6">
              {children}
            </main>
          </ClientShell>
        </div>
      </body>
    </html>
  );
}
