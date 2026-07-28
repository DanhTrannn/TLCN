import type { Metadata } from "next";
import "./globals.css";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: {
    default: "NÉT Studio | Thời trang nữ",
    template: "%s | NÉT Studio",
  },
  description: "Trang phục nữ tối giản, hiện đại và dễ phối cho phong cách mỗi ngày.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <Header />
          {children}
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
