"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { AdminNav } from "@/components/AdminNav";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";
import { canRoleAccessRoute, getRoleHomeRoute, getRoleLabel, STAFF_ROLES } from "@/lib/role-routes";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { customer, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !customer) {
      router.replace(`/login?returnTo=${encodeURIComponent(pathname)}`);
    }
  }, [customer, loading, router, pathname]);

  if (loading || !customer) {
    return (
      <main className="mx-auto max-w-[1680px] 2xl:max-w-[1800px] px-5 py-12 sm:px-6">
        <div className="admin-panel animate-pulse text-muted">Đang kiểm tra quyền truy cập…</div>
      </main>
    );
  }

  const isStaff = STAFF_ROLES.includes(customer.role as any);
  const hasAccess = isStaff && canRoleAccessRoute(customer.role, pathname);

  if (!hasAccess) {
    const roleHome = getRoleHomeRoute(customer.role);
    const roleLabel = getRoleLabel(customer.role);

    return (
      <main className="mx-auto max-w-3xl px-5 py-14 sm:px-6">
        <section className="surface-card p-8 text-center space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Icon name="shield" size={28} />
          </div>
          <h1 className="admin-heading">Không có quyền truy cập</h1>
          <p className="text-muted max-w-md mx-auto">
            Tài khoản của bạn ({customer.display_name} - {roleLabel}) không có quyền truy cập trực tiếp vào phân hệ này.
          </p>
          <div className="pt-2">
            <Link className="button-primary inline-flex items-center gap-2" href={roleHome}>
              <span>Quay về {roleLabel}</span>
              <Icon name="arrow-right" size={16} />
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1680px] 2xl:max-w-[1800px] px-4 py-5 sm:px-6 sm:py-8 lg:px-8">
      <div className="grid items-start gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]">
        <aside className="sticky top-16 z-30 -mx-1 rounded-2xl border border-line bg-surface/95 shadow-admin backdrop-blur lg:top-24 lg:mx-0">
          <div className="hidden border-b border-line px-5 py-4 lg:block">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Không gian quản trị</p>
          </div>
          <AdminNav />
        </aside>
        <main className="min-w-0 pb-8">{children}</main>
      </div>
    </div>
  );
}
