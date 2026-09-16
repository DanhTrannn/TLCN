"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { StoreNav } from "@/components/StoreNav";
import { useAuth } from "@/lib/auth";

export default function StoreLayout({ children }: { children: ReactNode }) {
  const { customer, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !customer) {
      router.replace("/login?returnTo=/store");
    }
  }, [customer, loading, router]);

  if (loading || !customer) {
    return (
      <main className="mx-auto max-w-7xl px-5 py-12 sm:px-6">
        <div className="admin-panel animate-pulse text-muted">Đang kiểm tra quyền truy cập…</div>
      </main>
    );
  }

  if (customer.role !== "store_manager" && customer.role !== "admin") {
    return (
      <main className="mx-auto max-w-3xl px-5 py-14 sm:px-6">
        <section className="surface-card p-8 text-center">
          <h1 className="admin-heading">Không có quyền truy cập</h1>
          <p className="mt-3 text-muted">Khu vực này chỉ dành cho quản lý cửa hàng.</p>
        </section>
      </main>
    );
  }

  return (
    <div className="mx-auto min-h-[calc(100vh-4rem)] max-w-7xl px-4 py-5 sm:px-6 sm:py-8">
      <div className="grid items-start gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]">
        <aside className="sticky top-16 z-30 -mx-1 rounded-2xl border border-line bg-surface/95 shadow-admin backdrop-blur lg:top-24 lg:mx-0">
          <div className="hidden border-b border-line px-5 py-4 lg:block">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Quản lý cửa hàng</p>
            {customer.store_name && (
              <p className="mt-1 text-sm font-semibold text-ink">{customer.store_name}</p>
            )}
          </div>
          <StoreNav />
        </aside>
        <main className="min-w-0 pb-8">{children}</main>
      </div>
    </div>
  );
}
