import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import { cookies } from "next/headers";
import ClientShell from "./client-shell";

export const metadata = {
  title: "Meta AI",
  description: "Digital Growth Studio",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const c = cookies();
  const pathname = c.get("next-url")?.value || "";

  const isAdmin = pathname.startsWith("/admin");
  const isLogin = pathname.startsWith("/login");
  const isHome = pathname === "/";

  const showSidebar = !(isAdmin || isLogin || isHome);

  return (
    <html lang="en">
      <body className="min-h-screen w-full bg-[#FFFCEB] text-gray-900 flex">
        <Toaster position="bottom-right" />

        {/* Main App Shell */}
        <div className="flex min-h-screen w-full">
          <ClientShell showSidebar={showSidebar}>
            {/* Page Container */}
            <main className="flex-1 min-h-screen px-6 py-6 space-y-6">
              {children}
            </main>
          </ClientShell>
        </div>
      </body>
    </html>
  );
}
