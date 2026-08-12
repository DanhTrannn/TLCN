"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";
import { ApiError, formatVnd, getAdminOverview, type AdminOverview } from "@/lib/api";

const orderStages = [
  { key: "paid_orders", label: "Chờ xác nhận", tone: "bg-warning", description: "Đã thanh toán" },
  { key: "confirmed_orders", label: "Đã xác nhận", tone: "bg-moss", description: "Đang xử lý" },
  { key: "completed_orders", label: "Hoàn tất", tone: "bg-ink", description: "Đã hoàn thành" },
  { key: "cancelled_orders", label: "Đã hủy", tone: "bg-muted", description: "Đã hoàn tiền" },
] as const;

const metricValueClasses =
  "mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums";

const compactVndFormatter = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 1,
});

function formatMetricVnd(amount: number): string {
  const absoluteAmount = Math.abs(amount);
  if (absoluteAmount >= 1_000_000_000_000) {
    return `${compactVndFormatter.format(amount / 1_000_000_000_000)} nghìn tỷ ₫`;
  }
  if (absoluteAmount >= 1_000_000_000) {
    return `${compactVndFormatter.format(amount / 1_000_000_000)} tỷ ₫`;
  }
  if (absoluteAmount >= 1_000_000) {
    return `${compactVndFormatter.format(amount / 1_000_000)} triệu ₫`;
  }
  return formatVnd(amount);
}

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminOverview().then(setData).catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : "Không tải được dashboard"));
  }, []);

  if (error) return <section className="feedback-error"><h1 className="font-semibold">Không tải được dashboard</h1><p className="mt-1">{error}</p></section>;
  if (!data) return <div className="space-y-5">{[0, 1, 2].map((item) => <div className="h-32 animate-pulse rounded-2xl bg-sand/60" key={item} />)}</div>;

  const totalOrders = orderStages.reduce((total, stage) => total + data[stage.key], 0);
  const quickLinks: ReadonlyArray<{ label: string; value: number; href: string; icon: IconName }> = [
    { label: "Sản phẩm đang bán", value: data.active_products, href: "/admin/products", icon: "package" },
    { label: "Biến thể đang bán", value: data.active_variants, href: "/admin/products", icon: "dashboard" },
    { label: "Coupon còn hiệu lực", value: data.active_coupons, href: "/admin/coupons", icon: "ticket" },
    { label: "Tổng đánh giá", value: data.total_reviews, href: "/admin/reviews", icon: "star" },
  ];

  return (
    <section className="space-y-7">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Tổng quan vận hành</p>
          <h1 className="admin-heading mt-2">Dashboard quản trị</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">Theo dõi doanh thu, luồng đơn và công việc cần xử lý trực tiếp từ OLTP.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="button-secondary" href="/admin/products"><Icon name="package" size={17} />Sản phẩm</Link>
          <Link className="button-primary" href="/admin/orders"><Icon name="receipt" size={17} />Xử lý đơn</Link>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-6 text-paper shadow-lift">
          <div className="flex items-center justify-between"><p className="text-sm text-paper/70">Doanh thu thuần</p><Icon className="text-paper/65" name="dashboard" /></div>
          <p aria-label={formatVnd(data.net_revenue_vnd)} className={metricValueClasses} title={formatVnd(data.net_revenue_vnd)}>{formatMetricVnd(data.net_revenue_vnd)}</p>
          <p className="mt-4 text-xs text-paper/60">Đã thu trừ full refund</p>
        </article>
        <article className="admin-panel min-w-0 overflow-hidden"><p className="text-sm text-muted">Tổng đã thu</p><p aria-label={formatVnd(data.gross_revenue_vnd)} className={metricValueClasses} title={formatVnd(data.gross_revenue_vnd)}>{formatMetricVnd(data.gross_revenue_vnd)}</p><p className="mt-4 text-xs text-muted">Payment thành công</p></article>
        <article className="admin-panel min-w-0 overflow-hidden"><p className="text-sm text-muted">Đã hoàn tiền</p><p aria-label={formatVnd(data.refunded_amount_vnd)} className={`${metricValueClasses} text-danger`} title={formatVnd(data.refunded_amount_vnd)}>{formatMetricVnd(data.refunded_amount_vnd)}</p><p className="mt-4 text-xs text-muted">Full refund của đơn hủy</p></article>
        <article className="admin-panel min-w-0 overflow-hidden"><p className="text-sm text-muted">Khách hàng</p><p className={metricValueClasses}>{data.customers.toLocaleString("vi-VN")}</p><p className="mt-4 text-xs text-muted">Tài khoản customer</p></article>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <article className="admin-panel">
          <div className="flex items-center justify-between gap-4"><div><h2 className="text-xl font-semibold">Luồng đơn hàng</h2><p className="mt-1 text-sm text-muted">{totalOrders.toLocaleString("vi-VN")} đơn trong hệ thống</p></div><Link className="button-ghost px-3 text-accent" href="/admin/orders">Xem tất cả <Icon name="arrow-right" size={16} /></Link></div>
          <div className="mt-7 space-y-5">
            {orderStages.map((stage) => {
              const count = data[stage.key];
              const width = totalOrders > 0 ? Math.max(2, Math.round((count / totalOrders) * 100)) : 0;
              return <div key={stage.key}><div className="flex items-end justify-between gap-4"><div><p className="font-semibold">{stage.label}</p><p className="text-xs text-muted">{stage.description}</p></div><p className="text-lg font-semibold">{count.toLocaleString("vi-VN")}</p></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-sand"><div className={`h-full rounded-full ${stage.tone}`} style={{ width: `${width}%` }} /></div></div>;
            })}
          </div>
        </article>

        <article className="admin-panel">
          <h2 className="text-xl font-semibold">Cần xử lý</h2><p className="mt-1 text-sm text-muted">Ưu tiên trong phiên làm việc này.</p>
          <div className="mt-5 divide-y divide-line">
            <Link className="flex min-h-14 items-center justify-between gap-4 rounded-lg px-2 transition hover:bg-paper hover:text-accent" href="/admin/orders"><span>Đơn chờ xác nhận</span><strong className="rounded-full bg-warning/10 px-3 py-1 text-warning">{data.paid_orders}</strong></Link>
            <Link className="flex min-h-14 items-center justify-between gap-4 rounded-lg px-2 transition hover:bg-paper hover:text-accent" href="/admin/products"><span>Biến thể sắp hết hàng</span><strong className="rounded-full bg-danger/10 px-3 py-1 text-danger">{data.low_stock_variants}</strong></Link>
          </div>
        </article>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        {quickLinks.map((item) => (
          <Link className="group min-w-0 overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/25 hover:shadow-admin" href={item.href} key={item.label}>
            <div className="flex items-center justify-between"><Icon className="text-moss" name={item.icon} size={20} /><Icon className="text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={17} /></div>
            <p className="mt-4 text-sm text-muted">{item.label}</p><p className="mt-1 max-w-full text-2xl font-semibold tabular-nums [overflow-wrap:anywhere]">{item.value.toLocaleString("vi-VN")}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
