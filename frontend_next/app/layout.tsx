import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import { cookies } from "next/headers";

export default function RootLayout({ children }: { children: ReactNode }) {
  // Read path written by middleware
  const c = cookies();
  const pathname = c.get("next-url")?.value || "";

  // Exclusion rules
  const isAdmin = pathname.startsWith("/admin");
  const isLogin = pathname.startsWith("/login");
  const isHome = pathname === "/";

  const showSidebar = !(isAdmin || isLogin || isHome);

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900 flex">
        <Toaster position="bottom-right" />

        {showSidebar && <Sidebar />}

        <div className="flex-1 min-h-screen overflow-y-auto">
          {children}
        </div>
      </body>
    </html>
  );
}
