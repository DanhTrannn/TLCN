"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["/admin", "Tổng quan"],
  ["/admin/products", "Sản phẩm"],
  ["/admin/orders", "Đơn hàng"],
  ["/admin/customers", "Khách hàng"],
] as const;

export function AdminNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Quản trị" className="flex flex-wrap gap-2">
      {links.map(([href, label]) => {
        const active = href === "/admin" ? pathname === href : pathname.startsWith(href);
        return (
          <Link
            className={`rounded-full border px-4 py-2 text-sm transition ${
              active ? "border-ink bg-ink text-paper" : "border-ink/15 bg-white/60 hover:border-ink/40"
            }`}
            href={href}
            key={href}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
