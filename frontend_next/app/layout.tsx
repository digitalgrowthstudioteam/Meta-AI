import "./globals.css";
import { ReactNode } from "react";
import { cookies } from "next/headers";
import { Toaster } from "react-hot-toast";
import UserShell from "./UserShell";

export default async function RootLayout({ children }: { children: ReactNode }) {
  const cookieStore = cookies();
  const pathname = cookieStore.get("next-url")?.value || "/";

  const isAdmin = pathname.startsWith("/admin");
  const isPublic = pathname === "/" || pathname === "/login";

  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />

        {/* ADMIN bypasses UserShell */}
        {isAdmin && children}

        {/* PUBLIC routes bypass UserShell */}
        {isPublic && !isAdmin && children}

        {/* Everything else → UserShell */}
        {!isAdmin && !isPublic && <UserShell>{children}</UserShell>}
      </body>
    </html>
  );
}
