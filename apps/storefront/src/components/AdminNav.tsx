"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon, type IconName } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";
import { canRoleAccessRoute } from "@/lib/role-routes";

interface NavItem {
  href: string;
  label: string;
  icon: IconName;
}

const ALL_ADMIN_LINKS: ReadonlyArray<NavItem> = [
  { href: "/admin", label: "Tổng quan", icon: "dashboard" },
  { href: "/admin/analytics", label: "Báo cáo BI Lakehouse", icon: "bar-chart" },
  { href: "/admin/products", label: "Sản phẩm", icon: "package" },
  { href: "/admin/inbound", label: "Nhập kho sản xuất", icon: "box" },
  { href: "/admin/orders", label: "Đơn hàng", icon: "receipt" },
  { href: "/admin/returns", label: "Đổi trả & Hoàn tiền", icon: "rotate-ccw" },
  { href: "/admin/logistics", label: "Vận chuyển", icon: "truck" },
  { href: "/admin/coupons", label: "Coupon", icon: "ticket" },
  { href: "/admin/reviews", label: "Đánh giá", icon: "star" },
  { href: "/admin/customers", label: "Khách hàng", icon: "users" },
];

export function AdminNav() {
  const pathname = usePathname();
  const { customer, loading } = useAuth();

  let visibleLinks: NavItem[] = [...ALL_ADMIN_LINKS];

  if (!loading && customer) {
    if (customer.role === "admin") {
      visibleLinks = [...ALL_ADMIN_LINKS];
    } else if (customer.role === "store_manager") {
      visibleLinks = [
        { href: "/store", label: "Cửa hàng của tôi", icon: "store" },
        { href: "/admin/analytics?role=store", label: "Báo cáo Cửa hàng", icon: "bar-chart" },
      ];
    } else if (customer.role === "sales_manager") {
      visibleLinks = [
        { href: "/admin/analytics?role=sales", label: "Báo cáo Kinh doanh", icon: "bar-chart" },
      ];
    } else if (customer.role === "marketing_manager") {
      visibleLinks = [
        { href: "/admin/analytics?role=marketing", label: "Báo cáo Marketing", icon: "bar-chart" },
        { href: "/admin/coupons", label: "Coupon", icon: "ticket" },
        { href: "/admin/reviews", label: "Đánh giá", icon: "star" },
      ];
    } else if (customer.role === "inventory_manager") {
      visibleLinks = [
        { href: "/admin/inbound", label: "Nhập kho sản xuất", icon: "box" },
        { href: "/admin/products", label: "Sản phẩm", icon: "package" },
        { href: "/admin/analytics?role=inventory", label: "Báo cáo Tồn kho", icon: "bar-chart" },
      ];
    } else if (customer.role === "operations_manager") {
      visibleLinks = [
        { href: "/admin/analytics?role=operations", label: "Báo cáo Vận hành", icon: "bar-chart" },
        { href: "/admin/orders", label: "Đơn hàng", icon: "receipt" },
        { href: "/admin/returns", label: "Đổi trả & Hoàn tiền", icon: "rotate-ccw" },
        { href: "/admin/logistics", label: "Vận chuyển", icon: "truck" },
      ];
    } else if (customer.role === "system_admin") {
      visibleLinks = [
        { href: "/admin/analytics?role=system", label: "Đối soát Dữ liệu", icon: "shield" },
      ];
    } else {
      visibleLinks = ALL_ADMIN_LINKS.filter((item) =>
        canRoleAccessRoute(customer.role, item.href)
      );
    }
  }

  return (
    <nav aria-label="Điều hướng quản trị" className="flex gap-1 overflow-x-auto p-1 lg:flex-col lg:overflow-visible lg:p-2">
      {visibleLinks.map(({ href, label, icon }) => {
        const basePath = href.split("?")[0];
        const active =
          basePath === "/admin"
            ? pathname === basePath
            : pathname.startsWith(basePath);

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
