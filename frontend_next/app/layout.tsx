import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import ClientLayoutWrapper from "./layout-wrapper";
import BlockGuard from "./block-guard"; // 🚀 NEW wrapper

export const metadata = {
  title: "Meta AI",
  description: "Digital Growth Studio",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen w-full bg-[#FFFCEB] text-gray-900 flex">
        <Toaster position="bottom-right" />

        {/**
         * BlockGuard reads cookies → decides overlay
         * This wraps the entire shell (except admin/login)
         */}
        <BlockGuard>
          <ClientLayoutWrapper>{children}</ClientLayoutWrapper>
        </BlockGuard>
      </body>
    </html>
  );
}
