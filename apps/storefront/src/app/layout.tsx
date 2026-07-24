import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "TLCN Commerce Source",
  description: "Minimal source website for the TLCN batch lakehouse"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <header className="border-b border-ink/10 bg-paper/90 backdrop-blur">
          <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link className="font-semibold tracking-tight" href="/">
              TLCN Commerce
            </Link>
            <div className="flex gap-5 text-sm">
              <Link href="/products">Sản phẩm</Link>
              <Link href="/cart">Giỏ hàng</Link>
              <Link href="/orders">Đơn hàng</Link>
            </div>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}

