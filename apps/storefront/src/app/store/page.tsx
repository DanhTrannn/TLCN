"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/api";

interface DashboardData {
  store_name: string;
  today_orders: number;
  today_revenue_vnd: number;
  total_orders: number;
  completed_orders: number;
  total_revenue_vnd: number;
  low_stock_items: number;
  active_staff: number;
}

export default function StoreDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<DashboardData>("/api/v1/admin/store/dashboard")
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div>
        <div className="h-8 w-48 animate-pulse rounded bg-sand/60" />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-32 animate-pulse rounded-2xl bg-sand/60" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="admin-panel text-muted">Không thể tải dữ liệu.</div>;
  }

  return (
    <div>
      <p className="eyebrow">Tổng quan vận hành</p>
      <h1 className="admin-heading mt-2">Quản lý cửa hàng</h1>
      <p className="mt-2 text-sm leading-6 text-muted">{data.store_name}</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-6 text-paper shadow-lift">
          <div className="flex items-center justify-between">
            <p className="text-sm text-paper/70">Đơn hôm nay</p>
            <Icon className="text-paper/65" name="receipt" />
          </div>
          <p className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums">
            {data.today_orders}
          </p>
          <p className="mt-4 text-xs text-paper/60">{formatVnd(data.today_revenue_vnd)}</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-sm text-muted">Tổng đơn</p>
          <p className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums">
            {data.total_orders}
          </p>
          <p className="mt-4 text-xs text-muted">{data.completed_orders} hoàn thành</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-sm text-muted">Doanh thu</p>
          <p className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums">
            {formatVnd(data.total_revenue_vnd)}
          </p>
          <p className="mt-4 text-xs text-muted">Tất cả thời gian</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-sm text-muted">Nhân viên</p>
          <p className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums">
            {data.active_staff}
          </p>
          <p className="mt-4 text-xs text-muted">{data.low_stock_items} tồn kho thấp</p>
        </article>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/pos">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="cart" size={20} />
            <Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} />
          </div>
          <p className="mt-4 text-sm text-muted">Bán hàng</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">POS</p>
        </Link>

        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/orders">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="receipt" size={20} />
            <Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} />
          </div>
          <p className="mt-4 text-sm text-muted">Đơn hàng</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{data.total_orders}</p>
        </Link>

        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/inventory">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="package" size={20} />
            <Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} />
          </div>
          <p className="mt-4 text-sm text-muted">Tồn kho</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{data.low_stock_items}</p>
        </Link>

        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/staff">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="users" size={20} />
            <Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} />
          </div>
          <p className="mt-4 text-sm text-muted">Nhân viên</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{data.active_staff}</p>
        </Link>
      </div>
    </div>
  );
}
