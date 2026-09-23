import type { Metadata } from "next";
import "./globals.css";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { LocationProvider } from "@/components/LocationContext";
import { MiniCartDrawer } from "@/components/MiniCartDrawer";
import { AuthProvider } from "@/lib/auth";
import { CartProvider } from "@/lib/cart-context";

export const metadata: Metadata = {
  title: {
    default: "D&K | Thời trang nữ",
    template: "%s | D&K",
  },
  description: "Trang phục nữ tối giản, hiện đại và dễ phối cho phong cách mỗi ngày.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <CartProvider>
            <LocationProvider>
              <Header />
              {children}
              <Footer />
              <MiniCartDrawer />
            </LocationProvider>
          </CartProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
