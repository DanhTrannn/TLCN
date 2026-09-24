"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";
import {
  ApiError,
  formatMetricVnd,
  formatVnd,
  getAdminOverview,
  getAdminSalesTrend,
  type AdminOverview,
} from "@/lib/api";
import type { DailySalesTrendPoint } from "@/lib/commerce";

const orderStages = [
  { key: "paid_orders", label: "Chờ xác nhận", tone: "bg-warning", description: "Đã thanh toán" },
  { key: "confirmed_orders", label: "Đã xác nhận", tone: "bg-moss", description: "Đang xử lý" },
  { key: "completed_orders", label: "Hoàn tất", tone: "bg-ink", description: "Đã hoàn thành" },
  { key: "cancelled_orders", label: "Đã hủy", tone: "bg-muted", description: "Đã hoàn tiền" },
] as const;

const metricValueClasses =
  "mt-4 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums";

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [salesTrend, setSalesTrend] = useState<DailySalesTrendPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(() => {
    setRefreshing(true);
    Promise.all([
      getAdminOverview(),
      getAdminSalesTrend(7).catch(() => ({ days: 7, points: [] })),
    ])
      .then(([overviewData, trendData]) => {
        setData(overviewData);
        setSalesTrend(trendData.points || []);
        setLastUpdated(new Date());
        setError(null);
      })
      .catch((requestError) => {
        setError(requestError instanceof ApiError ? requestError.message : "Không tải được dashboard");
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading && !data) {
    return (
      <div className="space-y-5">
        {[0, 1, 2].map((item) => (
          <div className="h-32 animate-pulse rounded-2xl bg-sand/60" key={item} />
        ))}
      </div>
    );
  }

  if (error && !data) {
    return (
      <section className="feedback-error">
        <h1 className="font-semibold">Không tải được dashboard</h1>
        <p className="mt-1">{error}</p>
        <button
          className="button-secondary mt-3 text-xs"
          onClick={loadData}
          type="button"
        >
          Thử lại
        </button>
      </section>
    );
  }

  if (!data) return null;

  const totalOrders = orderStages.reduce((total, stage) => total + data[stage.key], 0);
  const quickLinks: ReadonlyArray<{ label: string; value: number; href: string; icon: IconName }> = [
    { label: "Sản phẩm đang bán", value: data.active_products, href: "/admin/products", icon: "package" },
    { label: "Biến thể đang bán", value: data.active_variants, href: "/admin/products", icon: "dashboard" },
    { label: "Coupon còn hiệu lực", value: data.active_coupons, href: "/admin/coupons", icon: "ticket" },
    { label: "Tổng đánh giá", value: data.total_reviews, href: "/admin/reviews", icon: "star" },
  ];

  const boomCount = data.boom_orders_count ?? 0;
  const returnCount = data.return_orders_count ?? 0;

  return (
    <section className="space-y-7">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Tổng quan vận hành</p>
          <h1 className="admin-heading mt-2">Dashboard quản trị</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">Theo dõi doanh thu, luồng đơn và công việc cần xử lý trực tiếp từ OLTP.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {lastUpdated ? (
            <span className="text-xs text-muted tabular-nums mr-1">
              Cập nhật lúc {lastUpdated.toLocaleTimeString("vi-VN")}
            </span>
          ) : null}
          <button
            className="button-secondary inline-flex items-center gap-1.5 h-10 px-3.5 text-xs font-semibold"
            disabled={refreshing}
            onClick={loadData}
            title="Làm mới dữ liệu dashboard"
            type="button"
          >
            <Icon className={refreshing ? "animate-spin text-accent" : ""} name="rotate-ccw" size={15} />
            <span>Làm mới</span>
          </button>
          <Link className="button-secondary" href="/admin/products"><Icon name="package" size={17} />Sản phẩm</Link>
          <Link className="button-primary" href="/admin/orders"><Icon name="receipt" size={17} />Xử lý đơn</Link>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-6 text-paper shadow-lift">
          <div className="flex items-center justify-between"><p className="text-sm text-paper/70">Doanh thu thuần</p><Icon className="text-paper/65" name="dashboard" /></div>
          <p aria-label={formatVnd(data.net_revenue_vnd)} className={metricValueClasses} title={formatVnd(data.net_revenue_vnd)}>{formatMetricVnd(data.net_revenue_vnd)}</p>
          <p className="mt-4 text-xs text-paper/60">Đã thu trừ full refund</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Giá vốn hàng bán (COGS)</p>
            <Icon className="text-muted" name="box" size={18} />
          </div>
          <p aria-label={formatVnd(data.cogs_vnd ?? 0)} className={metricValueClasses} title={formatVnd(data.cogs_vnd ?? 0)}>
            {formatMetricVnd(data.cogs_vnd ?? 0)}
          </p>
          <p className="mt-4 text-xs text-muted">Bình quân gia quyền di động</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Lợi nhuận gộp</p>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                (data.gross_margin_percent ?? 0) >= 0
                  ? "border border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                  : "border border-rose-500/25 bg-rose-500/10 text-rose-700 dark:text-rose-400"
              }`}
            >
              Tỷ suất {data.gross_margin_percent ?? 0}%
            </span>
          </div>
          <p aria-label={formatVnd(data.gross_profit_vnd ?? 0)} className={metricValueClasses} title={formatVnd(data.gross_profit_vnd ?? 0)}>
            {formatMetricVnd(data.gross_profit_vnd ?? 0)}
          </p>
          <p className="mt-4 text-xs text-muted">Doanh thu thuần trừ giá vốn</p>
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
            <Link className="flex min-h-14 items-center justify-between gap-4 rounded-lg px-2 transition hover:bg-paper hover:text-accent" href="/admin/orders">
              <span>Đơn chờ xác nhận</span>
              <strong className={`rounded-full px-3 py-1 ${data.paid_orders > 0 ? "bg-warning/10 text-warning" : "bg-muted/10 text-muted"}`}>
                {data.paid_orders}
              </strong>
            </Link>
            <Link
              className="flex min-h-14 items-center justify-between gap-4 rounded-lg px-2 transition hover:bg-paper hover:text-accent"
              href="/admin/orders?status=failed_delivery"
            >
              <span>Đơn giao thất bại (Boom)</span>
              <strong
                className={`rounded-full px-3 py-1 ${
                  boomCount > 0
                    ? "border border-rose-500/25 bg-rose-500/10 text-rose-700 dark:text-rose-400 font-semibold"
                    : "bg-muted/10 text-muted"
                }`}
              >
                {boomCount}
              </strong>
            </Link>
            <Link
              className="flex min-h-14 items-center justify-between gap-4 rounded-lg px-2 transition hover:bg-paper hover:text-accent"
              href="/admin/returns"
            >
              <span>Yêu cầu đổi trả</span>
              <strong
                className={`rounded-full px-3 py-1 ${
                  returnCount > 0
                    ? "border border-amber-500/25 bg-warning/10 text-warning font-semibold"
                    : "bg-muted/10 text-muted"
                }`}
              >
                {returnCount}
              </strong>
            </Link>
            <Link className="flex min-h-14 items-center justify-between gap-4 rounded-lg px-2 transition hover:bg-paper hover:text-accent" href="/admin/products">
              <span>Biến thể sắp hết hàng</span>
              <strong className={`rounded-full px-3 py-1 ${data.low_stock_variants > 0 ? "bg-danger/10 text-danger" : "bg-muted/10 text-muted"}`}>
                {data.low_stock_variants}
              </strong>
            </Link>
          </div>
        </article>
      </div>

      {/* 7-Day Sales & Profit Mini Trend */}
      <article className="admin-panel">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold">Xu hướng doanh thu &amp; lợi nhuận</h2>
              <span className="rounded-full bg-sand px-2.5 py-0.5 text-xs font-semibold text-muted">7 ngày qua</span>
            </div>
            <p className="mt-1 text-sm text-muted">Tổng hợp doanh thu thuần, giá vốn và lợi nhuận gộp theo từng ngày từ OLTP.</p>
          </div>
          <Link
            className="button-ghost inline-flex items-center gap-1.5 px-3 text-accent text-sm font-medium"
            href="/admin/analytics?role=executive"
          >
            <span>Báo cáo BI chi tiết</span>
            <Icon name="arrow-right" size={16} />
          </Link>
        </div>

        {salesTrend.length > 0 ? (
          <div className="mt-6 space-y-4">
            <div className="flex flex-wrap items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="h-3 w-3 rounded-sm bg-accent" /> Doanh thu thuần
              </span>
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="h-3 w-3 rounded-sm bg-emerald-600" /> Lợi nhuận gộp
              </span>
            </div>

            {/* Compact Bar Chart */}
            <div className="flex h-36 items-end gap-2 overflow-x-auto rounded-xl border border-line bg-paper/50 px-3 pb-3 pt-6">
              {salesTrend.map((pt) => {
                const maxRev = Math.max(...salesTrend.map((p) => p.revenue_vnd), 1);
                const revHeight = maxRev > 0 ? Math.max(6, Math.round((pt.revenue_vnd / maxRev) * 100)) : 6;
                const profitHeight = maxRev > 0 ? Math.max(3, Math.round((Math.max(0, pt.profit_vnd) / maxRev) * 100)) : 3;

                return (
                  <div
                    className="group relative flex h-full min-w-[36px] flex-1 flex-col items-center justify-end"
                    key={pt.date}
                  >
                    <div className="flex w-full items-end justify-center gap-1">
                      <div
                        className="w-full max-w-[14px] rounded-t bg-accent transition-all group-hover:brightness-110"
                        style={{ height: `${revHeight}%` }}
                        title={`${pt.date} - Doanh thu: ${formatVnd(pt.revenue_vnd)}`}
                      />
                      <div
                        className={`w-full max-w-[14px] rounded-t transition-all group-hover:brightness-110 ${
                          pt.profit_vnd >= 0 ? "bg-emerald-600" : "bg-rose-500"
                        }`}
                        style={{ height: `${profitHeight}%` }}
                        title={`${pt.date} - Lợi nhuận gộp: ${formatVnd(pt.profit_vnd)}`}
                      />
                    </div>
                    <span className="mt-2 text-[11px] font-medium text-muted tabular-nums group-hover:text-ink">
                      {pt.date.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Daily Breakdown Table */}
            <div className="admin-table-shell overflow-x-auto">
              <table>
                <thead>
                  <tr>
                    <th>Ngày</th>
                    <th className="text-right">Doanh thu thuần</th>
                    <th className="text-right">Giá vốn (COGS)</th>
                    <th className="text-right">Lợi nhuận gộp</th>
                    <th className="text-right">Số đơn</th>
                  </tr>
                </thead>
                <tbody>
                  {salesTrend.map((pt) => (
                    <tr key={pt.date}>
                      <td className="font-medium text-ink">{pt.date}</td>
                      <td className="text-right font-semibold">{formatVnd(pt.revenue_vnd)}</td>
                      <td className="text-right text-muted">{formatVnd(pt.cogs_vnd)}</td>
                      <td
                        className={`text-right font-semibold ${
                          pt.profit_vnd >= 0 ? "text-emerald-700 dark:text-emerald-400" : "text-danger"
                        }`}
                      >
                        {formatVnd(pt.profit_vnd)}
                      </td>
                      <td className="text-right">{pt.orders_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-line bg-paper/30 p-6 text-center text-sm text-muted">
            Chưa có dữ liệu xu hướng doanh thu trong 7 ngày qua.
          </div>
        )}
      </article>

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
