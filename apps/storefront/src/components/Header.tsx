"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";

const customerLinks: ReadonlyArray<{ href: string; label: string; icon: IconName }> = [
  { href: "/products", label: "Sản phẩm", icon: "search" },
  { href: "/wishlist", label: "Yêu thích", icon: "heart" },
  { href: "/cart", label: "Giỏ hàng", icon: "bag" },
  { href: "/orders", label: "Đơn hàng", icon: "receipt" },
];

export function Header() {
  const { customer, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);
  const isAdminArea = pathname.startsWith("/admin");

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

  if (isAdminArea) {
    return (
      <header className="sticky top-0 z-50 border-b border-white/10 bg-ink text-paper shadow-[0_10px_32px_rgba(8,22,18,0.2)]">
        <div className="mx-auto flex min-h-16 max-w-7xl items-center justify-between gap-4 px-5 sm:px-6">
          <Link className="group flex items-center gap-3" href="/admin">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-xs font-bold tracking-[0.12em] text-white transition group-hover:bg-danger">
              D&K
            </span>
            <span>
              <span className="block text-sm font-semibold leading-tight">D&K Admin</span>
              <span className="block text-xs text-paper/60">Vận hành cửa hàng</span>
            </span>
          </Link>

          <div className="flex items-center gap-2">
            <Link
              className="hidden min-h-11 items-center gap-2 rounded-full border border-white/15 px-4 text-sm font-semibold text-paper/80 transition hover:border-white/30 hover:bg-white/10 hover:text-paper sm:inline-flex"
              href="/"
            >
              <Icon name="external" size={17} />
              Xem cửa hàng
            </Link>
            {loading ? null : customer ? (
              <>
                <span className="hidden max-w-40 truncate text-sm text-paper/65 lg:inline">
                  {customer.display_name}
                </span>
                <button
                  aria-label="Đăng xuất khỏi trang quản trị"
                  className="flex h-11 min-w-11 items-center justify-center gap-2 rounded-full bg-white/10 px-3 text-sm font-semibold transition hover:bg-white/20 disabled:opacity-50"
                  disabled={loggingOut}
                  onClick={() => void handleLogout()}
                  type="button"
                >
                  <Icon name="logout" size={18} />
                  <span className="hidden sm:inline">{loggingOut ? "Đang thoát…" : "Đăng xuất"}</span>
                </button>
              </>
            ) : null}
          </div>
        </div>
      </header>
    );
  }

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-line/80 bg-paper/95 shadow-[0_8px_30px_rgba(21,39,34,0.05)] backdrop-blur-xl">
        <nav className="mx-auto flex min-h-16 max-w-6xl items-center justify-between gap-5 px-5 sm:px-6" aria-label="Điều hướng chính">
          <Link className="group flex shrink-0 items-center gap-3" href="/">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-ink text-xs font-bold tracking-[0.12em] text-paper transition group-hover:bg-moss" aria-hidden="true">
              D&K
            </span>
            <span className="font-serif text-xl font-semibold tracking-[-0.02em]">D&K</span>
          </Link>

          <div className="hidden items-center gap-1 rounded-full border border-line bg-surface p-1 sm:flex">
            {customerLinks.map(({ href, label }) => {
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  aria-current={active ? "page" : undefined}
                  className={`min-h-10 whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition ${
                    active ? "bg-ink text-paper shadow-sm" : "text-muted hover:bg-paper hover:text-ink"
                  }`}
                  href={href}
                  key={href}
                >
                  {label}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            {customer?.role === "admin" ? (
              <Link className="hidden min-h-11 items-center gap-2 rounded-full px-3 text-sm font-semibold text-accent hover:bg-accent/5 lg:inline-flex" href="/admin">
                <Icon name="dashboard" size={17} />
                Quản trị
              </Link>
            ) : null}
            {loading ? null : customer ? (
              <>
                <span className="hidden max-w-28 truncate text-sm text-muted xl:inline">{customer.display_name}</span>
                <button
                  aria-label="Đăng xuất"
                  className="flex h-11 min-w-11 items-center justify-center rounded-full border border-line bg-surface text-muted transition hover:border-ink/25 hover:text-ink disabled:opacity-50"
                  disabled={loggingOut}
                  onClick={() => void handleLogout()}
                  type="button"
                >
                  <Icon name="logout" size={18} />
                </button>
              </>
            ) : (
              <Link className="button-primary px-4" href="/login">
                <Icon name="user" size={17} />
                <span className="hidden min-[390px]:inline">Đăng nhập</span>
              </Link>
            )}
          </div>
        </nav>
      </header>

      <nav
        aria-label="Điều hướng nhanh trên di động"
        className="fixed inset-x-3 bottom-3 z-50 grid grid-cols-4 rounded-2xl border border-line bg-surface/95 p-1.5 shadow-lift backdrop-blur-xl sm:hidden"
      >
        {customerLinks.map(({ href, label, icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={`flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl text-xs font-semibold transition ${
                active ? "bg-ink text-paper" : "text-muted hover:bg-paper hover:text-ink"
              }`}
              href={href}
              key={href}
            >
              <Icon filled={active && icon === "heart"} name={icon} size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
