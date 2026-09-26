"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";
import {
  ApiError,
  formatMetricVnd,
  formatVnd,
  getAdminRoleMetrics,
  getAdminSalesTrend,
  type DailySalesTrendPoint,
  type ExecutiveMetricsResponse,
  type InventoryMetricsResponse,
  type MarketingMetricsResponse,
  type OperationsMetricsResponse,
  type ReconciliationVariance,
  type RoleMetricsResponse,
  type SalesMetricsResponse,
  type SalesTrendResponse,
  type StoreMetricsResponse,
  type SystemMetricsResponse,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface TabItem {
  id: string;
  label: string;
  badge: string;
  icon: IconName;
  description: string;
}

const ALL_ROLES: TabItem[] = [
  {
    id: "executive",
    label: "Ban Giám đốc",
    badge: "CEO / Board",
    icon: "dashboard",
    description: "Doanh thu thuần, tỷ suất lợi nhuận gộp, GMV và xu hướng tăng trưởng tài chính toàn doanh nghiệp",
  },
  {
    id: "sales",
    label: "Kinh doanh & Chiến lược",
    badge: "Sales & Strategy",
    icon: "bar-chart",
    description: "Đóng góp doanh thu chi nhánh, xếp hạng sản phẩm bán chạy và tỷ trọng danh mục",
  },
  {
    id: "store",
    label: "Quản lý Cửa hàng",
    badge: "Store Operations",
    icon: "store",
    description: "Chỉ số doanh thu thực thời, tiến độ chỉ tiêu ngày và cảnh báo tồn kho tại cửa hàng",
  },
  {
    id: "inventory",
    label: "Kho & Chuỗi cung ứng",
    badge: "Supply Chain",
    icon: "box",
    description: "Giá trị định giá tồn kho, tỷ lệ phân bổ tổng kho vs điểm bán, và kiểm soát hết hàng",
  },
  {
    id: "operations",
    label: "Vận hành & Logistics",
    badge: "Fulfillment & Delivery",
    icon: "truck",
    description: "Đơn chờ xuất hàng, vi phạm SLA giao nhận, tỷ lệ boom hàng và yêu cầu đổi trả",
  },
  {
    id: "marketing",
    label: "Marketing & Phễu chuyển đổi",
    badge: "Growth & Funnel",
    icon: "ticket",
    description: "Phễu chuyển đổi 4 tầng (Xem -> Giỏ -> Thanh toán -> Mua), tỷ lệ hoàn tất và hiệu suất chiến dịch",
  },
  {
    id: "system",
    label: "Kỹ thuật & Đối soát",
    badge: "Data Governance",
    icon: "shield",
    description: "Trạng thái đường ống dữ liệu CDC/ETL, SLA độ trễ Lakehouse và đối soát sai lệch OLTP",
  },
];

const ROLE_CANONICAL_MAP: Record<string, string> = {
  executive: "executive",
  admin: "executive",
  sales: "sales",
  sales_manager: "sales",
  marketing: "marketing",
  marketing_manager: "marketing",
  store: "store",
  store_manager: "store",
  inventory: "inventory",
  inventory_manager: "inventory",
  operations: "operations",
  operations_manager: "operations",
  system: "system",
  system_admin: "system",
};

const metricValueClasses =
  "mt-3 max-w-full truncate whitespace-nowrap text-[clamp(1.25rem,1.8vw,1.75rem)] font-semibold leading-tight tracking-[-0.03em] tabular-nums";


function ExecutiveDashboard({
  metrics,
  salesTrend,
  trendDays,
  onTrendDaysChange,
}: {
  metrics: ExecutiveMetricsResponse;
  salesTrend: SalesTrendResponse | null;
  trendDays: number;
  onTrendDaysChange: (days: number) => void;
}) {
  const maxRevenue = useMemo(() => {
    if (!salesTrend?.points?.length) return 1;
    return Math.max(...salesTrend.points.map((p) => p.revenue_vnd), 1);
  }, [salesTrend]);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-6 text-paper shadow-lift">
          <div className="flex items-center justify-between">
            <p className="text-sm text-paper/70">Doanh thu thuần (Net Revenue)</p>
            <Icon className="text-paper/65" name="dashboard" size={18} />
          </div>
          <p aria-label={formatVnd(metrics.net_revenue_vnd)} className={metricValueClasses} title={formatVnd(metrics.net_revenue_vnd)}>
            {formatMetricVnd(metrics.net_revenue_vnd)}
          </p>
          <p className="mt-3 text-xs text-paper/60">Doanh thu đã trừ hoàn tiền</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Tổng giá trị hàng hóa (GMV)</p>
            <Icon className="text-muted" name="receipt" size={18} />
          </div>
          <p aria-label={formatVnd(metrics.gmv_vnd)} className={metricValueClasses} title={formatVnd(metrics.gmv_vnd)}>
            {formatMetricVnd(metrics.gmv_vnd)}
          </p>
          <p className="mt-3 text-xs text-muted">Tổng đơn không bị hủy</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Lợi nhuận gộp (Gross Profit)</p>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                metrics.gross_margin_percent >= 0
                  ? "border border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                  : "border border-rose-500/25 bg-rose-500/10 text-rose-700 dark:text-rose-400"
              }`}
            >
              Biên {metrics.gross_margin_percent}%
            </span>
          </div>
          <p aria-label={formatVnd(metrics.gross_profit_vnd)} className={metricValueClasses} title={formatVnd(metrics.gross_profit_vnd)}>
            {formatMetricVnd(metrics.gross_profit_vnd)}
          </p>
          <p className="mt-3 text-xs text-muted">Doanh thu thuần trừ giá vốn</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Giá vốn hàng bán (COGS)</p>
            <Icon className="text-muted" name="box" size={18} />
          </div>
          <p aria-label={formatVnd(metrics.cogs_vnd)} className={metricValueClasses} title={formatVnd(metrics.cogs_vnd)}>
            {formatMetricVnd(metrics.cogs_vnd)}
          </p>
          <p className="mt-3 text-xs text-muted">Bình quân gia quyền di động</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Tổng số đơn hàng</p>
            <Icon className="text-muted" name="package" size={18} />
          </div>
          <p className={metricValueClasses}>{metrics.total_orders.toLocaleString("vi-VN")}</p>
          <p className="mt-3 text-xs text-muted">Toàn bộ đơn hàng ghi nhận</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Giá trị đơn TB (AOV)</p>
            <Icon className="text-muted" name="cash" size={18} />
          </div>
          <p aria-label={formatVnd(metrics.aov_vnd)} className={metricValueClasses} title={formatVnd(metrics.aov_vnd)}>
            {formatMetricVnd(metrics.aov_vnd)}
          </p>
          <p className="mt-3 text-xs text-muted">Bình quân mỗi đơn hoàn tất</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Tỷ lệ Boom hàng</p>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                metrics.boom_rate_percent > 5
                  ? "border border-rose-500/25 bg-rose-500/10 text-rose-700 dark:text-rose-400"
                  : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
              }`}
            >
              {metrics.boom_rate_percent}%
            </span>
          </div>
          <p className={`${metricValueClasses} ${metrics.boom_rate_percent > 5 ? "text-danger" : ""}`}>
            {metrics.boom_rate_percent}%
          </p>
          <p className="mt-3 text-xs text-muted">Giao thất bại khách hủy nhận</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Tỷ lệ Đổi trả</p>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                metrics.return_rate_percent > 3
                  ? "border border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-400"
                  : "border border-line bg-paper text-muted"
              }`}
            >
              {metrics.return_rate_percent}%
            </span>
          </div>
          <p className={metricValueClasses}>{metrics.return_rate_percent}%</p>
          <p className="mt-3 text-xs text-muted">Yêu cầu hoàn trả sản phẩm</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Tỷ suất LN gộp (Gross Margin)</p>
            <Icon className="text-muted" name="bar-chart" size={18} />
          </div>
          <p
            className={`${metricValueClasses} ${
              metrics.gross_margin_percent >= 0 ? "text-emerald-700 dark:text-emerald-400" : "text-danger"
            }`}
          >
            {metrics.gross_margin_percent}%
          </p>
          <p className="mt-3 text-xs text-muted">Hiệu quả giá vốn doanh thu</p>
        </article>
      </div>

      {/* Daily Sales & Profit Trend Visualization */}
      <section className="admin-panel space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">Xu hướng Doanh thu & Lợi nhuận gộp theo ngày</h3>
            <p className="text-xs text-muted">Dữ liệu tổng hợp từ các đơn hàng thực tế trong kỳ</p>
          </div>
          <div className="flex items-center gap-1.5 rounded-xl border border-line bg-paper p-1">
            {[7, 14, 30].map((days) => (
              <button
                className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${
                  trendDays === days ? "bg-ink text-paper shadow-xs" : "text-muted hover:text-ink"
                }`}
                key={days}
                onClick={() => onTrendDaysChange(days)}
                type="button"
              >
                {days} ngày
              </button>
            ))}
          </div>
        </div>

        {salesTrend?.points?.length ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="h-3 w-3 rounded-sm bg-accent" /> Doanh thu (Revenue)
              </span>
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="h-3 w-3 rounded-sm bg-emerald-600" /> Lợi nhuận gộp (Profit)
              </span>
            </div>

            {/* Bar Chart Visualization */}
            <div className="flex h-48 items-end gap-1.5 overflow-x-auto rounded-xl border border-line bg-paper/50 px-3 pb-3 pt-6 sm:gap-2">
              {salesTrend.points.map((pt) => {
                const revHeight = maxRevenue > 0 ? Math.max(4, Math.round((pt.revenue_vnd / maxRevenue) * 100)) : 4;
                const profitHeight =
                  maxRevenue > 0 ? Math.max(2, Math.round((Math.max(0, pt.profit_vnd) / maxRevenue) * 100)) : 2;

                return (
                  <div
                    className="group relative flex h-full min-w-[28px] flex-1 flex-col justify-end items-center"
                    key={pt.date}
                  >
                    <div className="flex w-full items-end justify-center gap-1">
                      <div
                        className="w-full max-w-[12px] rounded-t bg-accent transition-all group-hover:brightness-110"
                        style={{ height: `${revHeight}%` }}
                        title={`${pt.date} - Doanh thu: ${formatVnd(pt.revenue_vnd)}`}
                      />
                      <div
                        className="w-full max-w-[12px] rounded-t bg-emerald-600 transition-all group-hover:brightness-110"
                        style={{ height: `${profitHeight}%` }}
                        title={`${pt.date} - Lợi nhuận: ${formatVnd(pt.profit_vnd)}`}
                      />
                    </div>
                    <span className="mt-1.5 truncate text-[10px] text-muted">
                      {pt.date.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Trend Summary Table */}
            <div className="admin-table-shell max-h-64 overflow-y-auto">
              <table>
                <thead>
                  <tr>
                    <th>Ngày</th>
                    <th className="text-right">Doanh thu</th>
                    <th className="text-right">Giá vốn (COGS)</th>
                    <th className="text-right">Lợi nhuận gộp</th>
                    <th className="text-right">Số đơn</th>
                  </tr>
                </thead>
                <tbody>
                  {salesTrend.points.slice(-7).map((pt) => (
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
          <div className="py-8 text-center text-sm text-muted">Không có dữ liệu xu hướng cho khoảng thời gian này.</div>
        )}
      </section>
    </div>
  );
}

function SalesDashboard({ metrics }: { metrics: SalesMetricsResponse }) {
  const totalStoreRevenue = useMemo(
    () => metrics.store_contributions.reduce((acc, s) => acc + s.revenue_vnd, 0),
    [metrics.store_contributions]
  );

  return (
    <div className="space-y-6">
      {/* Store Contributions */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Đóng góp Doanh thu theo Chi nhánh & Kênh</h3>
          <p className="text-xs text-muted">Phân tích hiệu quả kinh doanh đa kênh (Multi-city & Online)</p>
        </div>

        <div className="space-y-3.5">
          {metrics.store_contributions.map((store) => {
            const share = totalStoreRevenue > 0 ? Math.round((store.revenue_vnd / totalStoreRevenue) * 100) : 0;
            return (
              <div className="space-y-1.5 rounded-xl border border-line bg-paper/60 p-3.5" key={store.store_id ?? "online"}>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Icon className="text-accent" name="store" size={16} />
                    <span className="font-semibold text-ink">{store.store_name}</span>
                    <span className="text-xs text-muted">({store.order_count} đơn hàng)</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-ink">{formatVnd(store.revenue_vnd)}</span>
                    <span className="ml-2 text-xs font-semibold text-accent">({share}%)</span>
                  </div>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-sand">
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-300"
                    style={{ width: `${Math.max(share, 1)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Selling Products */}
        <section className="admin-panel space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-ink">Top Sản phẩm bán chạy</h3>
            <p className="text-xs text-muted">Xếp hạng theo tổng doanh thu phát sinh</p>
          </div>

          <div className="admin-table-shell">
            <table>
              <thead>
                <tr>
                  <th className="w-12 text-center">#</th>
                  <th>Sản phẩm</th>
                  <th className="text-right">Đã bán</th>
                  <th className="text-right">Doanh thu</th>
                </tr>
              </thead>
              <tbody>
                {metrics.top_selling_products.map((prod, idx) => (
                  <tr key={prod.product_id}>
                    <td className="text-center font-bold text-muted">
                      {idx < 3 ? (
                        <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-accent/15 text-xs text-accent">
                          {idx + 1}
                        </span>
                      ) : (
                        idx + 1
                      )}
                    </td>
                    <td className="max-w-[180px] truncate font-medium text-ink" title={prod.product_name}>
                      {prod.product_name}
                    </td>
                    <td className="text-right font-semibold">{prod.units_sold}</td>
                    <td className="text-right font-semibold text-accent">{formatVnd(prod.revenue_vnd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Category Share */}
        <section className="admin-panel space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-ink">Tỷ trọng Doanh thu Danh mục</h3>
            <p className="text-xs text-muted">Tỷ trọng cơ cấu doanh số theo phân loại mặt hàng</p>
          </div>

          <div className="space-y-3">
            {metrics.category_shares.map((cat) => (
              <div className="space-y-1.5 rounded-xl border border-line bg-paper/50 p-3" key={cat.category_id}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-ink">{cat.category_name}</span>
                  <div className="text-right">
                    <span className="font-semibold">{formatVnd(cat.revenue_vnd)}</span>
                    <span className="ml-2 text-xs font-bold text-emerald-600">({cat.share_percent}%)</span>
                  </div>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-sand">
                  <div
                    className="h-full rounded-full bg-emerald-600 transition-all duration-300"
                    style={{ width: `${Math.max(cat.share_percent, 1)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function StoreDashboard({
  metrics,
  isAdmin,
  selectedStoreId,
  onStoreChange,
  availableStores,
}: {
  metrics: StoreMetricsResponse;
  isAdmin: boolean;
  selectedStoreId?: number;
  onStoreChange: (storeId: number) => void;
  availableStores: Array<{ store_id: number; name: string }>;
}) {
  return (
    <div className="space-y-6">
      {/* Store Selector for Admin */}
      <div className="flex flex-col gap-3 rounded-2xl border border-line bg-paper/70 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Icon className="text-accent" name="store" size={20} />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">Cửa hàng đang xem</p>
            <p className="font-bold text-ink sm:text-lg">
              {metrics.store_name || "Chi nhánh chưa xác định"}
            </p>
          </div>
        </div>

        {isAdmin && availableStores.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted" htmlFor="store-select">
              Đổi chi nhánh:
            </label>
            <select
              className="rounded-xl border border-line bg-surface px-3 py-1.5 text-sm font-semibold text-ink shadow-xs outline-none focus:border-accent"
              id="store-select"
              onChange={(e) => onStoreChange(Number(e.target.value))}
              value={selectedStoreId ?? availableStores[0]?.store_id}
            >
              {availableStores.map((st) => (
                <option key={st.store_id} value={st.store_id}>
                  {st.name} (ID: {st.store_id})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Store Metrics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-5 text-paper shadow-lift">
          <div className="flex items-center justify-between">
            <p className="text-xs text-paper/70">Doanh thu hôm nay</p>
            <Icon className="text-paper/65" name="cash" size={16} />
          </div>
          <p aria-label={formatVnd(metrics.store_revenue_today_vnd)} className={metricValueClasses} title={formatVnd(metrics.store_revenue_today_vnd)}>
            {formatMetricVnd(metrics.store_revenue_today_vnd)}
          </p>
          <p className="mt-3 text-xs text-paper/60">Ghi nhận trong ngày</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Số đơn hôm nay</p>
            <Icon className="text-muted" name="receipt" size={16} />
          </div>
          <p className={metricValueClasses}>{metrics.store_orders_count}</p>
          <p className="mt-3 text-xs text-muted">Đơn hoàn tất tại cửa hàng</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Tiến độ chỉ tiêu ngày</p>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                metrics.target_achievement_percent >= 100
                  ? "border border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                  : "border border-line bg-paper text-muted"
              }`}
            >
              {metrics.target_achievement_percent}%
            </span>
          </div>
          <p className={`${metricValueClasses} text-emerald-700 dark:text-emerald-400`}>
            {metrics.target_achievement_percent}%
          </p>
          <p className="mt-3 text-xs text-muted">Mục tiêu 20.000.000₫/ngày</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Tồn kho thấp tại cửa hàng</p>
            <Icon className={metrics.low_stock_at_store_count > 0 ? "text-danger" : "text-muted"} name="alert" size={16} />
          </div>
          <p className={`${metricValueClasses} ${metrics.low_stock_at_store_count > 0 ? "text-danger" : ""}`}>
            {metrics.low_stock_at_store_count}
          </p>
          <p className="mt-3 text-xs text-muted">Biến thể còn dưới 5 đơn vị</p>
        </article>
      </div>

      {/* Low Stock Warning Alert */}
      {metrics.low_stock_at_store_count > 0 && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-900 dark:text-amber-300">
          <Icon className="shrink-0 text-warning" name="alert" size={18} />
          <div>
            <p className="font-semibold">Cảnh báo tồn kho cửa hàng</p>
            <p className="mt-0.5 text-xs">
              Có {metrics.low_stock_at_store_count} mặt hàng đang chạm ngưỡng cảnh báo tồn kho (≤ 5 chiếc). Vui lòng yêu cầu điều chuyển hàng từ Tổng kho.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function InventoryDashboard({ metrics }: { metrics: InventoryMetricsResponse }) {
  const totalUnits = metrics.warehouse_stock_units + metrics.store_stock_units;
  const whShare = totalUnits > 0 ? Math.round((metrics.warehouse_stock_units / totalUnits) * 100) : 0;
  const storeShare = totalUnits > 0 ? 100 - whShare : 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-6 text-paper shadow-lift">
          <div className="flex items-center justify-between">
            <p className="text-sm text-paper/70">Tổng giá trị định giá tồn kho</p>
            <Icon className="text-paper/65" name="box" size={18} />
          </div>
          <p aria-label={formatVnd(metrics.total_inventory_value_vnd)} className={metricValueClasses} title={formatVnd(metrics.total_inventory_value_vnd)}>
            {formatMetricVnd(metrics.total_inventory_value_vnd)}
          </p>
          <p className="mt-3 text-xs text-paper/60">Tính theo giá vốn (Cost Price)</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Lô hàng nhập kho sản xuất</p>
            <Icon className="text-muted" name="box" size={18} />
          </div>
          <p className={metricValueClasses}>{metrics.inbound_batches_count}</p>
          <p className="mt-3 text-xs text-muted">Phiếu nhập kho đã ghi nhận</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted">Mặt hàng hết hàng (Stockout)</p>
            <Icon className={metrics.stockout_count > 0 ? "text-danger" : "text-muted"} name="alert" size={18} />
          </div>
          <p className={`${metricValueClasses} ${metrics.stockout_count > 0 ? "text-danger" : ""}`}>
            {metrics.stockout_count}
          </p>
          <p className="mt-3 text-xs text-muted">Biến thể có tồn kho = 0</p>
        </article>
      </div>

      {/* Stock Split Visualization */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Phân bổ Tồn kho: Tổng kho vs Điểm bán</h3>
          <p className="text-xs text-muted">Tỷ lệ phân tán hàng hóa trong mạng lưới cung ứng</p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1.5 font-semibold text-ink">
              <span className="h-3 w-3 rounded-full bg-accent" /> Tổng kho trung tâm ({metrics.warehouse_stock_units.toLocaleString("vi-VN")} chiếc - {whShare}%)
            </span>
            <span className="flex items-center gap-1.5 font-semibold text-ink">
              <span className="h-3 w-3 rounded-full bg-moss" /> Các cửa hàng ({metrics.store_stock_units.toLocaleString("vi-VN")} chiếc - {storeShare}%)
            </span>
          </div>
          <div className="flex h-3.5 w-full overflow-hidden rounded-full bg-sand">
            <div className="bg-accent transition-all duration-300" style={{ width: `${whShare}%` }} />
            <div className="bg-moss transition-all duration-300" style={{ width: `${storeShare}%` }} />
          </div>
        </div>

        <div className="pt-2">
          <Link className="button-secondary text-xs" href="/admin/inbound">
            <Icon name="box" size={15} />
            Quản lý phiếu nhập kho sản xuất
          </Link>
        </div>
      </section>
    </div>
  );
}

function OperationsDashboard({ metrics }: { metrics: OperationsMetricsResponse }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          className="admin-panel min-w-0 overflow-hidden transition hover:border-accent hover:shadow-md"
          href="/admin/orders"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Đơn chờ xuất hàng</p>
            <Icon className="text-muted" name="receipt" size={16} />
          </div>
          <p className={`${metricValueClasses} ${metrics.pending_fulfillment_count > 0 ? "text-warning" : ""}`}>
            {metrics.pending_fulfillment_count}
          </p>
          <p className="mt-3 text-xs text-muted">Đã thanh toán / Chờ xử lý</p>
        </Link>

        <Link
          className="admin-panel min-w-0 overflow-hidden transition hover:border-accent hover:shadow-md"
          href="/admin/logistics"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Vi phạm SLA giao vận</p>
            <Icon className={metrics.shipping_sla_violations_count > 0 ? "text-danger" : "text-muted"} name="truck" size={16} />
          </div>
          <p className={`${metricValueClasses} ${metrics.shipping_sla_violations_count > 0 ? "text-danger" : ""}`}>
            {metrics.shipping_sla_violations_count}
          </p>
          <p className="mt-3 text-xs text-muted">Đơn chậm trễ hoặc lỗi giao</p>
        </Link>

        <Link
          className="admin-panel min-w-0 overflow-hidden transition hover:border-accent hover:shadow-md"
          href="/admin/orders?status=failed_delivery"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Đơn giao thất bại (Boom)</p>
            <Icon className={metrics.boom_orders_count > 0 ? "text-danger" : "text-muted"} name="alert" size={16} />
          </div>
          <p className={`${metricValueClasses} ${metrics.boom_orders_count > 0 ? "text-danger" : ""}`}>
            {metrics.boom_orders_count}
          </p>
          <p className="mt-3 text-xs text-muted">Khách từ chối nhận hàng</p>
        </Link>

        <Link
          className="admin-panel min-w-0 overflow-hidden transition hover:border-accent hover:shadow-md"
          href="/admin/returns"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Yêu cầu đổi trả cần duyệt</p>
            <Icon className="text-muted" name="rotate-ccw" size={16} />
          </div>
          <p className={`${metricValueClasses} ${metrics.return_requests_count > 0 ? "text-accent" : ""}`}>
            {metrics.return_requests_count}
          </p>
          <p className="mt-3 text-xs text-muted">Yêu cầu trả hàng từ khách</p>
        </Link>
      </div>

      <section className="admin-panel space-y-3">
        <h3 className="text-base font-semibold text-ink">Quy trình Vận hành Đơn & SLA Giao nhận</h3>
        <p className="text-xs text-muted">
          Giám sát liên tục các mắt xích từ chốt đơn đến giao hàng tận tay khách nhằm tối ưu chi phí hoàn và giữ vững cam kết SLA.
        </p>
      </section>
    </div>
  );
}

function MarketingDashboard({ metrics }: { metrics: MarketingMetricsResponse }) {
  const maxStepCount = useMemo(() => {
    if (!metrics.funnel_steps.length) return 1;
    return Math.max(...metrics.funnel_steps.map((s) => s.count), 1);
  }, [metrics.funnel_steps]);

  return (
    <div className="space-y-6">
      {/* Top Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <article className="min-w-0 overflow-hidden rounded-2xl bg-ink p-5 text-paper shadow-lift">
          <p className="text-xs text-paper/70">Tỷ lệ chuyển đổi tổng thể</p>
          <p className={`${metricValueClasses} text-emerald-400`}>{metrics.conversion_rate_percent}%</p>
          <p className="mt-3 text-xs text-paper/60">Lượt xem chuyển thành đơn mua</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-xs text-muted">Tổng lượt truy cập phễu</p>
          <p className={metricValueClasses}>{metrics.total_visitors.toLocaleString("vi-VN")}</p>
          <p className="mt-3 text-xs text-muted">Lượt xem sản phẩm được ghi nhận</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <p className="text-xs text-muted">Tổng đơn mua thành công</p>
          <p className={`${metricValueClasses} text-accent`}>{metrics.total_purchases.toLocaleString("vi-VN")}</p>
          <p className="mt-3 text-xs text-muted">Đơn hàng hoàn tất thanh toán</p>
        </article>
      </div>

      {/* 4-Step Conversion Funnel Visualization */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Phễu chuyển đổi E-commerce (Conversion Funnel)</h3>
          <p className="text-xs text-muted">Theo dõi tỷ lệ suy giảm qua từng bước trong hành trình khách hàng</p>
        </div>

        <div className="space-y-3">
          {metrics.funnel_steps.map((step, idx) => {
            const widthPct = maxStepCount > 0 ? Math.max(10, Math.round((step.count / maxStepCount) * 100)) : 10;
            const prevStep = idx > 0 ? metrics.funnel_steps[idx - 1] : null;
            const dropoffPct =
              prevStep && prevStep.count > 0
                ? Math.round(((prevStep.count - step.count) / prevStep.count) * 100)
                : null;

            return (
              <div className="space-y-1.5 rounded-xl border border-line bg-paper/60 p-3.5" key={step.step_name}>
                <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="font-semibold text-ink">
                    {idx + 1}. {step.step_name}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-ink">{step.count.toLocaleString("vi-VN")}</span>
                    <span className="text-xs font-semibold text-accent">({step.conversion_rate_percent}%)</span>
                    {dropoffPct !== null && (
                      <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-[11px] font-semibold text-rose-700 dark:text-rose-400">
                        Rơi rụng -{dropoffPct}%
                      </span>
                    )}
                  </div>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full bg-sand">
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-300"
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <Link className="button-secondary text-xs" href="/admin/coupons">
          <Icon name="ticket" size={15} />
          Quản lý mã giảm giá (Coupons)
        </Link>
        <Link className="button-secondary text-xs" href="/admin/reviews">
          <Icon name="star" size={15} />
          Đánh giá & Phản hồi khách hàng
        </Link>
      </div>
    </div>
  );
}

function SystemDashboard({ metrics }: { metrics: SystemMetricsResponse }) {
  const allMatch = metrics.reconciliation_variance.every((v: ReconciliationVariance) => v.variance_percent === 0);

  return (
    <div className="space-y-6">
      {/* Pipeline Status Banner */}
      <div className="grid gap-4 sm:grid-cols-2">
        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">Trạng thái đường ống dữ liệu CDC</p>
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <p className="mt-3 text-xl font-bold capitalize text-emerald-700 dark:text-emerald-400">
            {metrics.pipeline_status === "healthy" ? "Hoạt động ổn định (Healthy)" : metrics.pipeline_status}
          </p>
          <p className="mt-2 text-xs text-muted">Đồng bộ liên tục từ MySQL sang Lakehouse</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">SLA độ trễ làm mới (Freshness SLA)</p>
            <Icon className="text-muted" name="shield" size={16} />
          </div>
          <p className={metricValueClasses}>{metrics.data_freshness_sla_minutes} phút</p>
          <p className="mt-2 text-xs text-muted">Cam kết trễ dữ liệu tối đa của Lakehouse</p>
        </article>
      </div>

      {/* Reconciliation Gate Table */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Đối soát Dữ liệu (Reconciliation Gate: OLTP vs Lakehouse)</h3>
          <p className="text-xs text-muted">Kiểm thử toàn vẹn dữ liệu giữa cơ sở dữ liệu giao dịch và kho báo cáo BI</p>
        </div>

        {allMatch && (
          <div className="flex items-center gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-900 dark:text-emerald-300">
            <Icon className="shrink-0 text-emerald-600" name="check" size={20} />
            <div>
              <p className="font-semibold">Dữ liệu đối soát 100% khớp (Variance = 0.0%)</p>
              <p className="mt-0.5 text-xs">
                Toàn bộ chỉ số số lượng đơn và doanh thu giữa MySQL OLTP và Iceberg Lakehouse hoàn toàn đồng nhất.
              </p>
            </div>
          </div>
        )}

        <div className="admin-table-shell">
          <table>
            <thead>
              <tr>
                <th>Chỉ số nghiệp vụ</th>
                <th className="text-right">Nguồn OLTP</th>
                <th className="text-right">Kho Lakehouse</th>
                <th className="text-right">Độ lệch (Variance)</th>
                <th className="text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {metrics.reconciliation_variance.map((row: ReconciliationVariance) => (
                <tr key={row.metric_name}>
                  <td className="font-semibold text-ink">{row.metric_name}</td>
                  <td className="text-right tabular-nums">{row.oltp_value.toLocaleString("vi-VN")}</td>
                  <td className="text-right tabular-nums">{row.lakehouse_value.toLocaleString("vi-VN")}</td>
                  <td className="text-right tabular-nums font-semibold">
                    {row.variance_percent.toFixed(2)}%
                  </td>
                  <td className="text-center">
                    {row.variance_percent === 0 ? (
                      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                        <Icon name="check" size={12} /> Khớp
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/25 bg-rose-500/10 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:text-rose-400">
                        Lệch
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function AnalyticsHubContent() {
  const { customer, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();

  const isAdmin = customer?.role === "admin";
  const userRole = customer?.role || "";
  const userCanonicalRole = ROLE_CANONICAL_MAP[userRole] || "";

  const [initialized, setInitialized] = useState<boolean>(false);
  const [activeRole, setActiveRole] = useState<string>("");
  const [selectedStoreId, setSelectedStoreId] = useState<number>(1);
  const [availableStores, setAvailableStores] = useState<Array<{ store_id: number; name: string }>>([]);
  const [trendDays, setTrendDays] = useState<number>(30);

  const [roleMetrics, setRoleMetrics] = useState<RoleMetricsResponse | null>(null);
  const [salesTrend, setSalesTrend] = useState<SalesTrendResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initial role resolution from URL query or user canonical role
  useEffect(() => {
    if (authLoading || !customer) return;

    const urlRole = searchParams.get("role");
    let targetRole: string;

    if (urlRole && ALL_ROLES.some((r) => r.id === urlRole)) {
      targetRole = urlRole;
    } else {
      targetRole = isAdmin ? "executive" : userCanonicalRole;
    }

    setActiveRole(targetRole);
    setInitialized(true);
  }, [authLoading, customer, isAdmin, userCanonicalRole, searchParams]);

  const handleRoleChange = useCallback((newRole: string) => {
    if (newRole !== activeRole) {
      setRoleMetrics(null);
      setLoading(true);
      setError(null);
      setActiveRole(newRole);
    }
  }, [activeRole]);

  // Fetch metrics data whenever activeRole, selectedStoreId, or trendDays change
  const fetchData = useCallback(async () => {
    if (!customer || !initialized || !activeRole) return;

    // RBAC check: non-admin can only access their authorized canonical role
    if (!isAdmin && activeRole !== userCanonicalRole) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const storeParam = activeRole === "store" ? (isAdmin ? selectedStoreId : undefined) : undefined;
      const metricsData = await getAdminRoleMetrics<RoleMetricsResponse>(activeRole, storeParam);
      setRoleMetrics(metricsData);

      // If sales metrics loaded, extract available stores for the store selector
      if (activeRole === "sales") {
        const salesData = metricsData as SalesMetricsResponse;
        const validStores = salesData.store_contributions
          .filter((s): s is { store_id: number; store_name: string; revenue_vnd: number; order_count: number } => s.store_id !== null)
          .map((s) => ({ store_id: s.store_id, name: s.store_name }));
        if (validStores.length > 0) {
          setAvailableStores(validStores);
        }
      }

      // If executive or sales, fetch trend data
      if (activeRole === "executive" || activeRole === "sales") {
        const trendData = await getAdminSalesTrend(trendDays);
        setSalesTrend(trendData);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải dữ liệu phân tích.");
    } finally {
      setLoading(false);
    }
  }, [customer, initialized, activeRole, isAdmin, userCanonicalRole, selectedStoreId, trendDays]);

  useEffect(() => {
    if (initialized && activeRole) {
      void fetchData();
    }
  }, [initialized, activeRole, fetchData]);

  // Populate default stores if not yet populated
  useEffect(() => {
    if (availableStores.length === 0) {
      setAvailableStores([
        { store_id: 1, name: "Chi nhánh Quận 1 (Flagship HCM)" },
        { store_id: 2, name: "Chi nhánh Hoàn Kiếm (Hà Nội)" },
      ]);
    }
  }, [availableStores.length]);

  if (authLoading || !initialized) {
    return (
      <div className="space-y-5">
        {[0, 1, 2].map((i) => (
          <div className="h-32 animate-pulse rounded-2xl bg-sand/60" key={i} />
        ))}
      </div>
    );
  }

  // Non-admin trying to access unauthorized role
  const isUnauthorizedRole = !isAdmin && activeRole !== userCanonicalRole;

  // Filter visible tabs based on RBAC
  const visibleTabs = isAdmin ? ALL_ROLES : ALL_ROLES.filter((t) => t.id === userCanonicalRole);

  const currentTabInfo = ALL_ROLES.find((t) => t.id === activeRole) || ALL_ROLES[0];

  return (
    <section className="space-y-6">
      {/* Header */}
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Phân tích kinh doanh đa chiều</p>
          <h1 className="admin-heading mt-1">Báo cáo BI Lakehouse</h1>
          <p className="mt-1.5 max-w-2xl text-xs sm:text-sm text-muted">
            Trung tâm dữ liệu điều hành đa vai trò, tích hợp mô hình Medallion Lakehouse.
          </p>
        </div>
      </header>

      {/* Admin Role Simulator Switcher */}
      {isAdmin && (
        <aside className="rounded-2xl border border-accent/20 bg-paper/90 p-4 shadow-xs">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-accent animate-ping" />
              <span className="text-xs font-bold uppercase tracking-wider text-accent">
                Admin Role Simulator:
              </span>
              <span className="text-xs text-muted hidden sm:inline">
                (Mô phỏng góc nhìn nghiệp vụ cho thuyết trình & demo)
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {ALL_ROLES.map((r) => {
                const isCurrent = activeRole === r.id;
                return (
                  <button
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition ${
                      isCurrent
                        ? "bg-accent text-white shadow-xs"
                        : "border border-line bg-surface text-ink hover:border-accent/40"
                    }`}
                    key={r.id}
                    onClick={() => handleRoleChange(r.id)}
                    type="button"
                  >
                    <Icon name={r.icon} size={13} />
                    {r.label}
                  </button>
                );
              })}
            </div>
          </div>
        </aside>
      )}

      {/* Role Tabs Bar */}
      <div className="border-b border-line">
        <nav aria-label="Vai trò phân tích" className="flex gap-2 overflow-x-auto pb-2">
          {visibleTabs.map((tab) => {
            const active = activeRole === tab.id;
            return (
              <button
                aria-current={active ? "page" : undefined}
                className={`flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                  active
                    ? "bg-ink text-paper shadow-sm"
                    : "text-muted hover:bg-paper hover:text-ink"
                }`}
                key={tab.id}
                onClick={() => handleRoleChange(tab.id)}
                type="button"
              >
                <Icon name={tab.icon} size={16} />
                <span>{tab.label}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    active ? "bg-white/20 text-white" : "bg-sand text-muted"
                  }`}
                >
                  {tab.badge}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Role Description Bar */}
      {!isUnauthorizedRole && (
        <div className="flex items-center justify-between rounded-xl border border-line bg-surface px-4 py-2.5 text-xs text-muted">
          <div className="flex items-center gap-2">
            <Icon className="text-accent" name={currentTabInfo.icon} size={16} />
            <span>{currentTabInfo.description}</span>
          </div>
          <button
            className="font-medium text-accent hover:underline disabled:opacity-50"
            disabled={loading}
            onClick={() => void fetchData()}
            type="button"
          >
            {loading ? "Đang tải…" : "Làm mới"}
          </button>
        </div>
      )}

      {/* RBAC Access Denied Warning */}
      {isUnauthorizedRole && (
        <div className="feedback-error space-y-2 p-5">
          <div className="flex items-center gap-2">
            <Icon className="text-danger" name="alert" size={18} />
            <h2 className="font-bold">Không có quyền truy cập (Access Denied)</h2>
          </div>
          <p className="text-xs sm:text-sm">
            Tài khoản của bạn chỉ được cấp quyền xem góc nhìn dành cho{" "}
            <strong>{ALL_ROLES.find((r) => r.id === userCanonicalRole)?.label || userRole}</strong>.
            Vui lòng chuyển lại tab được cấp phép.
          </p>
          <button
            className="button-secondary mt-2 text-xs"
            onClick={() => handleRoleChange(userCanonicalRole)}
            type="button"
          >
            Quay về dashboard của bạn
          </button>
        </div>
      )}

      {/* Error Feedback */}
      {error && !isUnauthorizedRole && (
        <div className="feedback-error">
          <p className="font-semibold">Lỗi khi tải dữ liệu phân tích</p>
          <p className="mt-1 text-xs">{error}</p>
        </div>
      )}

      {/* Loading Skeleton */}
      {!isUnauthorizedRole && (loading || !roleMetrics || roleMetrics.role !== activeRole) && (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div className="h-28 animate-pulse rounded-2xl bg-sand/60" key={i} />
            ))}
          </div>
        </div>
      )}

      {/* Main Role Dashboards */}
      {!isUnauthorizedRole && !loading && roleMetrics && roleMetrics.role === activeRole && (
        <>
          {activeRole === "executive" && (
            <ExecutiveDashboard
              metrics={roleMetrics as ExecutiveMetricsResponse}
              onTrendDaysChange={setTrendDays}
              salesTrend={salesTrend}
              trendDays={trendDays}
            />
          )}

          {activeRole === "sales" && (
            <SalesDashboard metrics={roleMetrics as SalesMetricsResponse} />
          )}

          {activeRole === "store" && (
            <StoreDashboard
              availableStores={availableStores}
              isAdmin={isAdmin}
              metrics={roleMetrics as StoreMetricsResponse}
              onStoreChange={setSelectedStoreId}
              selectedStoreId={selectedStoreId}
            />
          )}

          {activeRole === "inventory" && (
            <InventoryDashboard metrics={roleMetrics as InventoryMetricsResponse} />
          )}

          {activeRole === "operations" && (
            <OperationsDashboard metrics={roleMetrics as OperationsMetricsResponse} />
          )}

          {activeRole === "marketing" && (
            <MarketingDashboard metrics={roleMetrics as MarketingMetricsResponse} />
          )}

          {activeRole === "system" && (
            <SystemDashboard metrics={roleMetrics as SystemMetricsResponse} />
          )}
        </>
      )}
    </section>
  );
}

export default function AnalyticsHubPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-5">
          {[0, 1, 2].map((i) => (
            <div className="h-32 animate-pulse rounded-2xl bg-sand/60" key={i} />
          ))}
        </div>
      }
    >
      <AnalyticsHubContent />
    </Suspense>
  );
}
