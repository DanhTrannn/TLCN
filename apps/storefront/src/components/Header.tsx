"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/lib/auth";

const customerLinks = [
  ["/products", "Sản phẩm"],
  ["/wishlist", "Yêu thích"],
  ["/cart", "Giỏ hàng"],
  ["/orders", "Đơn hàng"],
] as const;

export function Header() {
  const { customer, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      router.push("/");
      router.refresh();
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-ink/10 bg-paper/90 shadow-[0_8px_30px_rgba(19,35,31,0.04)] backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-3.5" aria-label="Điều hướng chính">
        <Link className="group flex items-center gap-3 font-semibold tracking-tight" href="/">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-xs font-bold tracking-wider text-paper transition group-hover:bg-moss" aria-hidden="true">
            NÉT
          </span>
          <span className="hidden sm:inline">NÉT Studio</span>
        </Link>

        <div className="order-3 flex w-full items-center gap-1 overflow-x-auto rounded-2xl border border-ink/10 bg-white/55 p-1 text-sm sm:order-none sm:w-auto">
          {customerLinks.map(([href, label]) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                className={`whitespace-nowrap rounded-xl px-3 py-2 font-medium transition ${
                  active ? "bg-ink text-paper shadow-sm" : "text-ink/65 hover:bg-white hover:text-ink"
                }`}
                href={href}
                key={href}
                aria-current={active ? "page" : undefined}
              >
                {label}
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-3 text-sm">
          {customer?.role === "admin" ? (
            <Link
              className={`rounded-full px-3 py-1.5 font-semibold transition ${
                pathname.startsWith("/admin") ? "bg-accent text-white" : "text-accent hover:bg-accent/10"
              }`}
              href="/admin"
            >
              Quản trị
            </Link>
          ) : null}
          {loading ? null : customer ? (
            <div className="flex items-center gap-3">
              <span className="hidden max-w-32 truncate text-ink/60 lg:inline">{customer.display_name}</span>
              <button
                className="rounded-full border border-ink/15 bg-white/60 px-3 py-1.5 font-medium transition hover:border-ink/30 hover:bg-white disabled:opacity-50"
                disabled={loggingOut}
                onClick={handleLogout}
                type="button"
              >
                {loggingOut ? "Đang thoát…" : "Đăng xuất"}
              </button>
            </div>
          ) : (
            <Link className="rounded-full bg-ink px-4 py-2 font-medium text-paper transition hover:bg-moss" href="/login">
              Đăng nhập
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
