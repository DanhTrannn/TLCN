"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api-client";
import { formatMetricVnd, formatVnd } from "@/lib/api";

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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<DashboardData>("/api/v1/admin/store/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Không thể tải dữ liệu."))
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

  if (error) {
    return (
      <section className="feedback-error">
        <h1 className="font-semibold">Không tải được dữ liệu cửa hàng</h1>
        <p className="mt-1">{error}</p>
      </section>
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
            {data.today_orders.toLocaleString("vi-VN")}
          </p>
          <p
            aria-label={formatVnd(data.today_revenue_vnd)}
            className="mt-4 text-xs text-paper/60"
            title={formatVnd(data.today_revenue_vnd)}
          >
            Doanh thu: {formatVnd(data.today_revenue_vnd)}
          </p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-sm text-muted">Tổng đơn</p>
          <p className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums">
            {data.total_orders.toLocaleString("vi-VN")}
          </p>
          <p className="mt-4 text-xs text-muted">
            {data.completed_orders.toLocaleString("vi-VN")} hoàn thành
          </p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-sm text-muted">Doanh thu</p>
          <p
            aria-label={formatVnd(data.total_revenue_vnd)}
            className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums"
            title={formatVnd(data.total_revenue_vnd)}
          >
            {formatMetricVnd(data.total_revenue_vnd)}
          </p>
          <p className="mt-4 text-xs text-muted">Tất cả thời gian</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Nhân sự vận hành</p>
            <Icon className="text-muted" name="users" size={18} />
          </div>
          <p className="mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums">
            {data.active_staff.toLocaleString("vi-VN")}
          </p>
          <p className="mt-4 text-xs text-muted">
            {data.low_stock_items > 0 ? (
              <span className="font-semibold text-danger">
                {data.low_stock_items} mặt hàng tồn kho thấp
              </span>
            ) : (
              "Tồn kho an toàn"
            )}
          </p>
        </article>
      </div>

      {data.low_stock_items > 0 && (
        <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-danger/25 bg-danger/5 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-danger/10 text-danger">
              <Icon name="alert" size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-danger">Cảnh báo tồn kho thấp</p>
              <p className="text-xs text-muted">
                Có {data.low_stock_items} biến thể sản phẩm tại cửa hàng đang dưới ngưỡng tồn kho an toàn.
              </p>
            </div>
          </div>
          <Link
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-danger/30 bg-surface px-3.5 py-2 text-xs font-semibold text-danger transition hover:bg-danger/10"
            href="/store/inventory"
          >
            Kiểm tra kho <Icon name="arrow-right" size={14} />
          </Link>
        </div>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/pos">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="bag" size={20} />
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
          <p className="mt-1 text-2xl font-semibold tabular-nums">{data.total_orders.toLocaleString("vi-VN")}</p>
        </Link>

        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/inventory">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="package" size={20} />
            {data.low_stock_items > 0 ? (
              <span className="inline-flex items-center rounded-full bg-danger/10 px-2.5 py-0.5 text-xs font-semibold text-danger">
                Cần bổ sung
              </span>
            ) : (
              <Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} />
            )}
          </div>
          <p className="mt-4 text-sm text-muted">Tồn kho</p>
          <p
            className={`mt-1 text-2xl font-semibold tabular-nums ${
              data.low_stock_items > 0 ? "text-danger" : ""
            }`}
          >
            {data.low_stock_items.toLocaleString("vi-VN")}
          </p>
        </Link>

        <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href="/store/staff">
          <div className="flex items-center justify-between">
            <Icon className="text-moss" name="users" size={20} />
            <Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} />
          </div>
          <p className="mt-4 text-sm text-muted">Nhân viên</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{data.active_staff.toLocaleString("vi-VN")}</p>
        </Link>
      </div>
    </div>
  );
}
