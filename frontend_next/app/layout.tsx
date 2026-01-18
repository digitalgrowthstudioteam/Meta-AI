import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import ClientLayoutWrapper from "./layout-wrapper";

export const metadata = {
  title: "Meta AI",
  description: "Digital Growth Studio",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen w-full bg-[#FFFCEB] text-gray-900 flex">
        <Toaster position="bottom-right" />
        <ClientLayoutWrapper>{children}</ClientLayoutWrapper>
      </body>
    </html>
  );
}
