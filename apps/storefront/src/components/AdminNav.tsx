"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon, type IconName } from "@/components/ui/Icon";

const links: ReadonlyArray<{ href: string; label: string; icon: IconName }> = [
  { href: "/admin", label: "Tổng quan", icon: "dashboard" },
  { href: "/admin/products", label: "Sản phẩm", icon: "package" },
  { href: "/admin/orders", label: "Đơn hàng", icon: "receipt" },
  { href: "/admin/coupons", label: "Coupon", icon: "ticket" },
  { href: "/admin/reviews", label: "Đánh giá", icon: "star" },
  { href: "/admin/customers", label: "Khách hàng", icon: "users" },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Điều hướng quản trị" className="flex gap-1 overflow-x-auto p-1 lg:flex-col lg:overflow-visible lg:p-2">
      {links.map(({ href, label, icon }) => {
        const active = href === "/admin" ? pathname === href : pathname.startsWith(href);
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
