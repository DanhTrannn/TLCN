"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";
import { EChart, type EChartsOption, BRAND_COLORS } from "@/components/ui/EChart";
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
  // Dual-Axis Bar & Line Chart Option:
  const trendOption: EChartsOption = useMemo(() => {
    if (!salesTrend?.points?.length) return {};
    const dates = salesTrend.points.map((p) => p.date.slice(5));
    const revenues = salesTrend.points.map((p) => p.revenue_vnd);
    const cogs = salesTrend.points.map((p) => p.cogs_vnd);
    const profits = salesTrend.points.map((p) => p.profit_vnd);

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: any) => {
          if (!Array.isArray(params)) return "";
          let tip = `<div class="font-bold text-xs mb-1">${params[0]?.axisValue}</div>`;
          params.forEach((item: any) => {
            tip += `<div class="flex items-center justify-between gap-4 text-xs">
              <span style="color:${item.color}">${item.seriesName}:</span>
              <span class="font-semibold">${formatVnd(Number(item.value) || 0)}</span>
            </div>`;
          });
          return tip;
        },
      },
      legend: {
        top: 0,
        textStyle: { color: "#5c4d3c", fontSize: 12 },
        data: ["Doanh thu", "Giá vốn (COGS)", "Lợi nhuận gộp"],
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "12%",
        top: "14%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#dcd8cf" } },
        axisLabel: { color: "#5c4d3c", fontSize: 11 },
      },
      yAxis: [
        {
          type: "value",
          axisLine: { show: false },
          axisLabel: {
            color: "#5c4d3c",
            formatter: (v: number) => formatMetricVnd(v),
            fontSize: 11,
          },
          splitLine: { lineStyle: { color: "rgba(0,0,0,0.06)", type: "dashed" } },
        },
      ],
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        {
          type: "slider",
          bottom: 0,
          height: 18,
          borderColor: "transparent",
          backgroundColor: "rgba(0,0,0,0.03)",
          fillerColor: "rgba(169, 71, 40, 0.2)",
        },
      ],
      series: [
        {
          name: "Doanh thu",
          type: "bar",
          data: revenues,
          itemStyle: { color: "#a94728", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 20,
        },
        {
          name: "Giá vốn (COGS)",
          type: "bar",
          data: cogs,
          itemStyle: { color: "#315b4f", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 20,
        },
        {
          name: "Lợi nhuận gộp",
          type: "line",
          data: profits,
          itemStyle: { color: "#059669" },
          lineStyle: { width: 3, color: "#059669" },
          smooth: true,
        },
      ],
    };
  }, [salesTrend]);

  // Donut Chart for Executive Fulfillment & Boom/Return Breakdown
  const executiveDonutOption: EChartsOption = useMemo(() => {
    const boomCount = Math.round((metrics.total_orders * metrics.boom_rate_percent) / 100);
    const returnCount = Math.round((metrics.total_orders * metrics.return_rate_percent) / 100);
    const deliveredCount = Math.max(0, metrics.total_orders - boomCount - returnCount);

    return {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          return `<div class="font-bold text-xs mb-1">${params.name}</div>
            <div class="text-xs">${Number(params.value).toLocaleString("vi-VN")} đơn (${params.percent}%)</div>`;
        },
      },
      legend: {
        bottom: 0,
        textStyle: { color: "#5c4d3c", fontSize: 11 },
      },
      series: [
        {
          name: "Cơ cấu đơn hàng",
          type: "pie",
          radius: ["42%", "70%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: "#fff",
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 12,
              fontWeight: "bold",
            },
          },
          data: [
            { value: deliveredCount, name: "Giao thành công", itemStyle: { color: "#059669" } },
            { value: boomCount, name: "Giao thất bại (Boom)", itemStyle: { color: "#e11d48" } },
            { value: returnCount, name: "Yêu cầu đổi trả", itemStyle: { color: "#d97706" } },
          ],
        },
      ],
    };
  }, [metrics]);

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

      {/* Interactive ECharts Visualizations */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Dual-Axis Trend Chart */}
        <section className="admin-panel lg:col-span-2 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-ink">Xu hướng Doanh thu & Lợi nhuận gộp theo ngày</h3>
              <p className="text-xs text-muted">Dữ liệu thực thời từ Lakehouse Mart (mart_sales_daily via Trino)</p>
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
            <EChart height={340} option={trendOption} />
          ) : (
            <div className="py-12 text-center text-sm text-muted">Không có dữ liệu xu hướng cho khoảng thời gian này.</div>
          )}
        </section>

        {/* Executive Fulfillment Donut */}
        <section className="admin-panel space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-ink">Cơ cấu Đơn hàng & Boom rate</h3>
            <p className="text-xs text-muted">Tỷ trọng giao thành công vs rủi ro hoàn hủy</p>
          </div>
          <EChart height={340} option={executiveDonutOption} />
        </section>
      </div>

      {/* Trend Summary Table */}
      {salesTrend?.points?.length ? (
        <section className="admin-panel space-y-3">
          <h3 className="text-base font-semibold text-ink">Bảng số liệu chi tiết gần nhất</h3>
          <div className="admin-table-shell max-h-60 overflow-y-auto">
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
        </section>
      ) : null}
    </div>
  );
}

function SalesDashboard({ metrics }: { metrics: SalesMetricsResponse }) {
  // Category Share Donut:
  const categoryOption: EChartsOption = useMemo(() => {
    return {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          return `<div class="font-bold text-xs mb-1">${params.name}</div>
            <div class="text-xs">Doanh thu: <b>${formatVnd(Number(params.value) || 0)}</b></div>
            <div class="text-xs text-muted">Tỷ trọng: <b>${params.percent}%</b></div>`;
        },
      },
      legend: {
        orient: "horizontal",
        bottom: 0,
        textStyle: { color: "#5c4d3c", fontSize: 11 },
      },
      series: [
        {
          name: "Danh mục",
          type: "pie",
          radius: ["42%", "72%"],
          itemStyle: { borderRadius: 6, borderColor: "#fff", borderWidth: 2 },
          data: metrics.category_shares.map((cat, idx) => ({
            name: cat.category_name,
            value: cat.revenue_vnd,
            itemStyle: { color: BRAND_COLORS[idx % BRAND_COLORS.length] },
          })),
        },
      ],
    };
  }, [metrics.category_shares]);

  // Top Products Horizontal Bar Chart:
  const topProductsOption: EChartsOption = useMemo(() => {
    const prods = [...metrics.top_selling_products].reverse();
    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: any) => {
          const item = params[0];
          return `<div class="font-bold text-xs mb-1">${item?.axisValue}</div>
            <div class="text-xs">Doanh thu: <b>${formatVnd(Number(item?.value) || 0)}</b></div>`;
        },
      },
      grid: { left: "3%", right: "8%", top: "4%", bottom: "4%", containLabel: true },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { formatter: (v: number) => formatMetricVnd(v), fontSize: 10 },
        splitLine: { lineStyle: { color: "rgba(0,0,0,0.06)", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: prods.map((p) => p.product_name),
        axisLine: { lineStyle: { color: "#dcd8cf" } },
        axisLabel: { color: "#152722", fontSize: 11, width: 140, overflow: "truncate" },
      },
      series: [
        {
          type: "bar",
          data: prods.map((p) => p.revenue_vnd),
          itemStyle: { color: "#a94728", borderRadius: [0, 4, 4, 0] },
          barMaxWidth: 20,
        },
      ],
    };
  }, [metrics.top_selling_products]);

  // Store Contributions Column Chart:
  const storeOption: EChartsOption = useMemo(() => {
    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: any) => {
          const item = params[0];
          return `<div class="font-bold text-xs mb-1">${item?.axisValue}</div>
            <div class="text-xs">Doanh thu: <b>${formatVnd(Number(item?.value) || 0)}</b></div>`;
        },
      },
      grid: { left: "3%", right: "4%", top: "8%", bottom: "14%", containLabel: true },
      xAxis: {
        type: "category",
        data: metrics.store_contributions.map((s) => s.store_name),
        axisLabel: { color: "#5c4d3c", fontSize: 11, interval: 0, rotate: 15 },
        axisLine: { lineStyle: { color: "#dcd8cf" } },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { formatter: (v: number) => formatMetricVnd(v), fontSize: 10 },
        splitLine: { lineStyle: { color: "rgba(0,0,0,0.06)", type: "dashed" } },
      },
      series: [
        {
          name: "Doanh thu",
          type: "bar",
          data: metrics.store_contributions.map((s) => s.revenue_vnd),
          itemStyle: { color: "#152722", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 32,
        },
      ],
    };
  }, [metrics.store_contributions]);

  return (
    <div className="space-y-6">
      {/* Store Contributions Chart */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Đóng góp Doanh thu theo Chi nhánh & Kênh</h3>
          <p className="text-xs text-muted">Phân tích hiệu quả kinh doanh đa kênh (Multi-city & Online)</p>
        </div>
        <EChart height={280} option={storeOption} />
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Selling Products */}
        <section className="admin-panel space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-ink">Top Sản phẩm bán chạy</h3>
            <p className="text-xs text-muted">Xếp hạng theo tổng doanh thu phát sinh trên DWH</p>
          </div>
          <EChart height={300} option={topProductsOption} />
        </section>

        {/* Category Share */}
        <section className="admin-panel space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-ink">Tỷ trọng Doanh thu Danh mục</h3>
            <p className="text-xs text-muted">Cơ cấu doanh số mặt hàng theo Data Mart</p>
          </div>
          <EChart height={300} option={categoryOption} />
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
  const gaugeOption: EChartsOption = useMemo(() => {
    const pct = metrics.target_achievement_percent;
    const color = pct >= 80 ? "#059669" : pct >= 50 ? "#d97706" : "#e11d48";

    return {
      series: [
        {
          type: "gauge",
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 120,
          splitNumber: 4,
          itemStyle: { color },
          progress: {
            show: true,
            roundCap: true,
            width: 14,
          },
          pointer: {
            icon: "roundRect",
            length: "60%",
            width: 5,
            offsetCenter: [0, "-12%"],
          },
          axisLine: {
            roundCap: true,
            lineStyle: {
              width: 14,
              color: [
                [0.5, "rgba(225, 29, 72, 0.25)"],
                [0.8, "rgba(217, 119, 6, 0.25)"],
                [1, "rgba(5, 150, 105, 0.25)"],
              ],
            },
          },
          axisTick: { show: false },
          splitLine: { length: 8, lineStyle: { width: 1, color: "#dcd8cf" } },
          axisLabel: {
            distance: 18,
            color: "#6b7280",
            fontSize: 10,
            formatter: "{value}%",
          },
          title: {
            offsetCenter: [0, "26%"],
            fontSize: 13,
            color: "#152722",
            fontWeight: "bold",
          },
          detail: {
            fontSize: 24,
            offsetCenter: [0, "-2%"],
            valueAnimation: true,
            formatter: "{value}%",
            color,
            fontWeight: "bold",
          },
          data: [
            {
              value: pct,
              name: "Tiến độ ngày",
            },
          ],
        },
      ],
    };
  }, [metrics.target_achievement_percent]);

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
                metrics.target_achievement_percent >= 80
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
          <p className="mt-3 text-xs text-muted">Biến thể có tồn kho ≤ 5</p>
        </article>
      </div>

      {/* Target Gauge Visualization */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Đồng hồ Tiến độ Doanh số Chỉ tiêu (Daily Target Gauge)</h3>
          <p className="text-xs text-muted">Mức độ hoàn thành chỉ tiêu doanh thu ngày của chi nhánh</p>
        </div>
        <EChart height={280} option={gaugeOption} />
      </section>

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
  const stockOption: EChartsOption = useMemo(() => {
    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
      },
      legend: {
        bottom: 0,
        textStyle: { color: "#5c4d3c", fontSize: 11 },
      },
      grid: { left: "3%", right: "4%", top: "8%", bottom: "15%", containLabel: true },
      xAxis: {
        type: "category",
        data: ["Tổng kho trung tâm", "Hệ thống Cửa hàng"],
        axisLine: { lineStyle: { color: "#dcd8cf" } },
      },
      yAxis: {
        type: "value",
        axisLabel: { formatter: (v: number) => v.toLocaleString("vi-VN") },
        splitLine: { lineStyle: { color: "rgba(0,0,0,0.06)", type: "dashed" } },
      },
      series: [
        {
          name: "Số lượng tồn kho (Units)",
          type: "bar",
          data: [metrics.warehouse_stock_units, metrics.store_stock_units],
          itemStyle: { color: "#152722", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 56,
        },
      ],
    };
  }, [metrics]);

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
          <p className="text-xs text-muted">Tỷ lệ phân tán hàng hóa theo dữ liệu mart_inventory_health</p>
        </div>
        <EChart height={280} option={stockOption} />

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
  const opsDonutOption: EChartsOption = useMemo(() => {
    return {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          return `<div class="font-bold text-xs mb-1">${params.name}</div>
            <div class="text-xs">Số lượng: <b>${Number(params.value).toLocaleString("vi-VN")}</b> (${params.percent}%)</div>`;
        },
      },
      legend: { bottom: 0, textStyle: { color: "#5c4d3c", fontSize: 11 } },
      series: [
        {
          name: "Vận hành",
          type: "pie",
          radius: ["42%", "72%"],
          itemStyle: { borderRadius: 6, borderColor: "#fff", borderWidth: 2 },
          data: [
            { value: Math.max(1, 100 - metrics.boom_orders_count), name: "Giao nhận bình thường", itemStyle: { color: "#059669" } },
            { value: metrics.boom_orders_count, name: "Boom hàng (Giao thất bại)", itemStyle: { color: "#e11d48" } },
            { value: metrics.shipping_sla_violations_count, name: "Vi phạm SLA", itemStyle: { color: "#d97706" } },
            { value: metrics.return_requests_count, name: "Yêu cầu đổi trả", itemStyle: { color: "#3d647a" } },
          ],
        },
      ],
    };
  }, [metrics]);

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

      {/* Logistics Performance Donut */}
      <section className="admin-panel space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">Chỉ số Hiệu suất Giao vận & Tỷ lệ Boom (Logistics Mart)</h3>
          <p className="text-xs text-muted">Dữ liệu tổng hợp từ mart_logistics_performance</p>
        </div>
        <EChart height={290} option={opsDonutOption} />
      </section>
    </div>
  );
}

function MarketingDashboard({ metrics }: { metrics: MarketingMetricsResponse }) {
  const funnelOption: EChartsOption = useMemo(() => {
    return {
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          return `<div class="font-bold text-xs mb-1">${params.name}</div>
            <div class="text-xs">Số lượng: <b>${Number(params.value).toLocaleString("vi-VN")}</b></div>`;
        },
      },
      legend: { bottom: 0, textStyle: { color: "#5c4d3c", fontSize: 11 } },
      series: [
        {
          name: "Phễu chuyển đổi",
          type: "funnel",
          left: "15%",
          top: "8%",
          bottom: "15%",
          width: "70%",
          min: 0,
          maxSize: "100%",
          sort: "descending",
          gap: 3,
          label: {
            show: true,
            position: "inside",
            formatter: "{b}: {c}",
            color: "#fff",
            fontSize: 11,
            fontWeight: "bold",
          },
          itemStyle: {
            borderColor: "#fff",
            borderWidth: 1,
          },
          data: metrics.funnel_steps.map((s, idx) => ({
            value: s.count,
            name: s.step_name.split("(")[0].trim(),
            itemStyle: { color: BRAND_COLORS[idx % BRAND_COLORS.length] },
          })),
        },
      ],
    };
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
        <EChart height={320} option={funnelOption} />
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

  const reconOption: EChartsOption = useMemo(() => {
    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
      },
      legend: { bottom: 0, textStyle: { color: "#5c4d3c", fontSize: 11 } },
      grid: { left: "3%", right: "4%", top: "8%", bottom: "15%", containLabel: true },
      xAxis: {
        type: "category",
        data: metrics.reconciliation_variance.map((v) => v.metric_name),
        axisLine: { lineStyle: { color: "#dcd8cf" } },
      },
      yAxis: {
        type: "value",
        axisLabel: { formatter: (v: number) => formatMetricVnd(v) },
        splitLine: { lineStyle: { color: "rgba(0,0,0,0.06)", type: "dashed" } },
      },
      series: [
        {
          name: "OLTP MySQL",
          type: "bar",
          data: metrics.reconciliation_variance.map((v) => v.oltp_value),
          itemStyle: { color: "#315b4f", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 36,
        },
        {
          name: "Lakehouse Iceberg",
          type: "bar",
          data: metrics.reconciliation_variance.map((v) => v.lakehouse_value),
          itemStyle: { color: "#a94728", borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 36,
        },
      ],
    };
  }, [metrics.reconciliation_variance]);

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

      {/* Reconciliation Comparison Chart */}
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

        <EChart height={280} option={reconOption} />
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
            Trung tâm dữ liệu điều hành đa vai trò, tích hợp trực tiếp Apache ECharts và Trino Distributed Query Engine.
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
