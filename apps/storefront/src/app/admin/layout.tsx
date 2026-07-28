"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { AdminNav } from "@/components/AdminNav";
import { useAuth } from "@/lib/auth";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { customer, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !customer) {
      router.replace("/login?returnTo=/admin");
    }
  }, [customer, loading, router]);

  if (loading || !customer) {
    return <main className="mx-auto max-w-6xl px-6 py-14 text-ink/60">Đang kiểm tra quyền truy cập…</main>;
  }
  if (customer.role !== "admin") {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <h1 className="text-3xl font-semibold">Không có quyền truy cập</h1>
        <p className="mt-3 text-ink/65">Khu vực này chỉ dành cho quản trị viên.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8 flex flex-col gap-5 border-b border-ink/10 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Admin console</p>
          <h1 className="mt-2 text-3xl font-semibold">Quản lý website</h1>
        </div>
        <AdminNav />
      </div>
      {children}
    </main>
  );
}
