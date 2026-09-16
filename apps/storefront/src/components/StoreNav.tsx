"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon, type IconName } from "@/components/ui/Icon";

const links: ReadonlyArray<{ href: string; label: string; icon: IconName }> = [
  { href: "/store", label: "Tổng quan", icon: "dashboard" },
  { href: "/store/pos", label: "POS", icon: "bag" },
  { href: "/store/orders", label: "Đơn hàng", icon: "receipt" },
  { href: "/store/inventory", label: "Tồn kho", icon: "package" },
  { href: "/store/staff", label: "Nhân viên", icon: "users" },
];

export function StoreNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Điều hướng cửa hàng" className="flex gap-1 overflow-x-auto p-1 lg:flex-col lg:overflow-visible lg:p-2">
      {links.map(({ href, label, icon }) => {
        const active = href === "/store" ? pathname === href : pathname.startsWith(href);
        return (
          <Link
            aria-current={active ? "page" : undefined}
            className={`flex min-h-11 shrink-0 items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition ${
              active
                ? "bg-ink text-paper shadow-sm"
                : "text-muted hover:bg-paper hover:text-ink"
            }`}
            href={href}
            key={href}
          >
            <Icon name={icon} size={18} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
