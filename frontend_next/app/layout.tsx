import "./globals.css";
import { ReactNode } from "react";
import { Toaster } from "react-hot-toast";

/**
 * RootLayout no longer tries to detect path server-side.
 * Public / User / Admin segmentation is handled by layouts.
 */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-amber-50 text-gray-900">
        <Toaster position="bottom-right" />
        {children}
      </body>
    </html>
  );
}
