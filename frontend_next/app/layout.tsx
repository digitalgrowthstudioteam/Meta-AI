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
      <body className="bg-amber-50 text-gray-900 flex">
        <Toaster position="bottom-right" />
        <ClientShell showSidebar={showSidebar}>{children}</ClientShell>
      </body>
    </html>
  );
}
