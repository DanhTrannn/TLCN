"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  getAdminOverview,
  type AdminOverview,
} from "@/lib/api";

const orderStages = [
  { key: "paid_orders", label: "Chờ xác nhận", tone: "bg-amber-500" },
  { key: "confirmed_orders", label: "Đã xác nhận", tone: "bg-sky-600" },
  { key: "shipping_orders", label: "Đang giao hàng", tone: "bg-indigo-600" },
  { key: "completed_orders", label: "Hoàn tất", tone: "bg-emerald-600" },
  { key: "boom_orders_count", label: "Giao thất bại (COD)", tone: "bg-rose-600" },
  { key: "cancelled_orders", label: "Đã hủy", tone: "bg-slate-400" },
] as const;

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(() => {
    setRefreshing(true);
    getAdminOverview()
      .then((overviewData) => {
        setData(overviewData);
        setLastUpdated(new Date());
        setError(null);
      })
      .catch((requestError) => {
        setError(requestError instanceof ApiError ? requestError.message : "Không tải được dữ liệu");
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
      <div className="space-y-6">
        <div className="h-14 animate-pulse rounded-2xl bg-sand/60" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((item) => (
            <div className="h-24 animate-pulse rounded-2xl bg-sand/60" key={item} />
          ))}
        </div>
        <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="h-72 animate-pulse rounded-2xl bg-sand/50" />
          <div className="h-72 animate-pulse rounded-2xl bg-sand/50" />
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <section className="feedback-error">
        <h1 className="font-semibold text-lg">Không tải được dữ liệu</h1>
        <p className="mt-1 text-sm">{error}</p>
        <button
          className="button-secondary mt-4 text-xs font-semibold"
          onClick={loadData}
          type="button"
        >
          Thử lại
        </button>
      </section>
    );
  }

  if (!data) return null;

  const shippingCount = (data.shipping_orders ?? 0) + (data.delivered_orders ?? 0);
  const boomCount = data.boom_orders_count ?? 0;
  const returnCount = data.return_orders_count ?? 0;
  const totalOrders =
    data.paid_orders +
    data.confirmed_orders +
    shippingCount +
    data.completed_orders +
    boomCount +
    data.cancelled_orders +
    returnCount;

  const completionRate = totalOrders > 0 ? Math.round((data.completed_orders / totalOrders) * 100) : 0;
  const urgentCount = data.paid_orders + boomCount + returnCount + (data.low_stock_variants > 0 ? 1 : 0);

  const quickLinks = [
    { label: "Sản phẩm", value: data.active_products, href: "/admin/products" },
    { label: "Biến thể", value: data.active_variants, href: "/admin/products" },
    { label: "Mã giảm giá", value: data.active_coupons, href: "/admin/coupons" },
    { label: "Đánh giá", value: data.total_reviews, href: "/admin/reviews" },
  ];

  return (
    <section className="space-y-6">
      {/* HEADER GỌN GÀNG */}
      <header className="flex flex-wrap items-center justify-end gap-2">
        {lastUpdated ? (
          <span className="text-xs text-muted tabular-nums mr-auto">
            Cập nhật lúc {lastUpdated.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
          </span>
        ) : null}
        <button
          className="button-secondary inline-flex items-center gap-1.5 h-9 px-3 text-xs font-semibold"
          disabled={refreshing}
          onClick={loadData}
          title="Làm mới"
          type="button"
        >
          <Icon className={refreshing ? "animate-spin text-accent" : ""} name="rotate-ccw" size={13} />
          <span>Làm mới</span>
        </button>
        <Link className="button-secondary h-9 px-3 text-xs font-semibold" href="/admin/products">
          Sản phẩm
        </Link>
        <Link className="button-primary h-9 px-3.5 text-xs font-semibold" href="/admin/orders">
          Xử lý đơn
        </Link>
      </header>

      {/* BANNER SANG TRUNG TÂM BI LAKEHOUSE */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-accent/25 bg-gradient-to-r from-accent/10 via-moss/5 to-surface px-5 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
            OLAP
          </span>
          <h2 className="text-sm font-bold text-ink">
            Trung tâm Phân tích Dữ liệu BI Lakehouse
          </h2>
        </div>
        <Link
          className="button-primary whitespace-nowrap text-xs font-semibold px-3.5 py-2 self-start sm:self-auto"
          href="/admin/analytics"
        >
          Mở Báo cáo BI →
        </Link>
      </div>

      {/* TẦNG 1: 4 THẺ TÁC VỤ ƯU TIÊN */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          className="admin-panel p-4 transition hover:-translate-y-0.5 hover:border-amber-500/50"
          href="/admin/orders"
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
            Chờ xác nhận
          </p>
          <p className="mt-2 text-2xl font-extrabold text-ink tabular-nums">
            {data.paid_orders} <span className="text-xs font-normal text-muted">đơn</span>
          </p>
        </Link>

        <Link
          className="admin-panel p-4 transition hover:-translate-y-0.5 hover:border-rose-500/50 border-rose-500/20 bg-rose-500/[0.02]"
          href="/admin/orders?status=failed_delivery"
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-rose-700 dark:text-rose-400">
            Rủi ro COD (Thất bại)
          </p>
          <p className="mt-2 text-2xl font-extrabold text-rose-700 dark:text-rose-400 tabular-nums">
            {boomCount} <span className="text-xs font-normal text-muted">đơn</span>
          </p>
        </Link>

        <Link
          className="admin-panel p-4 transition hover:-translate-y-0.5 hover:border-indigo-500/50"
          href="/admin/returns"
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-muted">
            Khiếu nại &amp; Đổi trả
          </p>
          <p className="mt-2 text-2xl font-extrabold text-ink tabular-nums">
            {returnCount} <span className="text-xs font-normal text-muted">yêu cầu</span>
          </p>
        </Link>

        <Link
          className="admin-panel p-4 transition hover:-translate-y-0.5 hover:border-danger/50"
          href="/admin/products"
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-muted">
            Cảnh báo tồn kho
          </p>
          <p className="mt-2 text-2xl font-extrabold text-ink tabular-nums">
            {data.low_stock_variants} <span className="text-xs font-normal text-muted">biến thể</span>
          </p>
        </Link>
      </div>

      {/* TẦNG 2: 2 CỘT CHÍNH */}
      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        {/* CỘT TRÁI: HÀNG ĐỢI XỬ LÝ */}
        <article className="admin-panel p-5">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <h2 className="text-base font-bold text-ink">Công việc cần xử lý ngay</h2>
            <span className="rounded-full bg-sand px-2.5 py-0.5 text-xs font-bold text-ink tabular-nums">
              {urgentCount} việc
            </span>
          </div>

          <div className="divide-y divide-line/60">
            <div className="flex items-center justify-between gap-4 py-3">
              <div>
                <p className="text-sm font-semibold text-ink">
                  Đơn hàng chờ duyệt xuất kho
                </p>
                <span className="text-xs font-bold text-amber-700 tabular-nums">
                  {data.paid_orders} đơn
                </span>
              </div>
              <Link
                className="button-secondary text-xs font-semibold px-3 py-1.5"
                href="/admin/orders"
              >
                Xử lý
              </Link>
            </div>

            <div className="flex items-center justify-between gap-4 py-3">
              <div>
                <p className="text-sm font-semibold text-rose-700">
                  Đơn giao thất bại (Rủi ro COD)
                </p>
                <span className="text-xs font-bold text-rose-700 tabular-nums">
                  {boomCount} đơn
                </span>
              </div>
              <Link
                className="button-secondary text-xs font-semibold px-3 py-1.5 border-rose-500/30 text-rose-700 hover:bg-rose-50"
                href="/admin/orders?status=failed_delivery"
              >
                Xem đơn
              </Link>
            </div>

            <div className="flex items-center justify-between gap-4 py-3">
              <div>
                <p className="text-sm font-semibold text-ink">
                  Yêu cầu khiếu nại &amp; Đổi trả
                </p>
                <span className="text-xs font-bold text-muted tabular-nums">
                  {returnCount} yêu cầu
                </span>
              </div>
              <Link
                className="button-secondary text-xs font-semibold px-3 py-1.5"
                href="/admin/returns"
              >
                Kiểm tra
              </Link>
            </div>

            <div className="flex items-center justify-between gap-4 py-3">
              <div>
                <p className="text-sm font-semibold text-ink">
                  Biến thể chạm ngưỡng hết hàng
                </p>
                <span className="text-xs font-bold text-muted tabular-nums">
                  {data.low_stock_variants} biến thể
                </span>
              </div>
              <Link
                className="button-secondary text-xs font-semibold px-3 py-1.5"
                href="/admin/inbound"
              >
                Nhập kho
              </Link>
            </div>
          </div>
        </article>

        {/* CỘT PHẢI: LUỒNG ĐƠN HÀNG */}
        <div className="space-y-4">
          <article className="admin-panel p-5">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink">Luồng luân chuyển đơn</h2>
              <span className="text-xs font-bold text-emerald-700 tabular-nums">
                {completionRate}% hoàn tất
              </span>
            </div>

            <div className="mt-4 space-y-3.5">
              {orderStages.map((stage) => {
                const count =
                  stage.key === "shipping_orders"
                    ? shippingCount
                    : stage.key === "boom_orders_count"
                    ? boomCount
                    : (data[stage.key as keyof AdminOverview] as number) ?? 0;
                const percent = totalOrders > 0 ? Math.round((count / totalOrders) * 100) : 0;
                const barWidth = totalOrders > 0 ? Math.max(3, percent) : 0;

                return (
                  <div key={stage.key}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-ink">{stage.label}</span>
                      <div className="flex items-center gap-1.5 tabular-nums">
                        <strong className="font-bold text-ink">{count.toLocaleString("vi-VN")}</strong>
                        <span className="text-muted text-[11px]">({percent}%)</span>
                      </div>
                    </div>
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-sand/70">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${stage.tone}`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-5 pt-3 border-t border-line flex items-center justify-between text-xs">
              <span className="text-muted tabular-nums">Tổng {totalOrders.toLocaleString("vi-VN")} đơn</span>
              <Link className="font-semibold text-accent hover:underline" href="/admin/logistics">
                Cổng Logistics →
              </Link>
            </div>
          </article>

          {/* Khách hàng */}
          <article className="admin-panel p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted">Khách hàng kích hoạt</p>
              <p className="text-xl font-bold text-ink tabular-nums">
                {data.customers.toLocaleString("vi-VN")}
              </p>
            </div>
            <Link className="text-xs font-semibold text-accent hover:underline" href="/admin/customers">
              Quản lý →
            </Link>
          </article>
        </div>
      </div>

      {/* TẦNG 3: 4 LỐI TẮT TỐI GIẢN */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {quickLinks.map((item) => (
          <Link
            className="admin-panel p-4 transition hover:-translate-y-0.5 hover:border-accent/40"
            href={item.href}
            key={item.label}
          >
            <p className="text-xs text-muted">{item.label}</p>
            <p className="mt-1 text-xl font-bold text-ink tabular-nums">{item.value.toLocaleString("vi-VN")}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
