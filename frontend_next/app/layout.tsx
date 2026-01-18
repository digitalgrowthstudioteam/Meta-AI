import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import { headers } from "next/headers";

export default function RootLayout({ children }: { children: ReactNode }) {
  const h = headers();
  const path = h.get("x-pathname") || "";

  const isAdmin = path.startsWith("/admin");
  const isLogin = path.startsWith("/login");
  const isHome = path === "/";

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
