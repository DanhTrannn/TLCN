"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api-client";
import { formatMetricVnd, formatVnd } from "@/lib/api";
import { exportToCsv } from "@/lib/csv-export";

interface InventoryItem {
  store_id: number;
  store_name: string;
  variant_id: number;
  variant_sku: string;
  product_name: string;
  category_name: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  on_hand: number;
  opening_on_hand: number;
}

type StockStatusFilter = "all" | "in_stock" | "low_stock" | "out_of_stock";
type ViewMode = "table" | "grid";

const PAGE_SIZE = 15;

export default function StoreInventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters & display
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [stockStatus, setStockStatus] = useState<StockStatusFilter>("all");
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [page, setPage] = useState(1);

  const loadData = useCallback(() => {
    setRefreshing(true);
    apiFetch<InventoryItem[]>("/api/v1/admin/store/inventory")
      .then((res) => {
        setItems(res);
        setLastUpdated(new Date());
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Không thể tải dữ liệu tồn kho.");
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Overall metric computations
  const totalStock = useMemo(() => items.reduce((sum, i) => sum + i.on_hand, 0), [items]);
  const totalEstimatedValue = useMemo(
    () => items.reduce((sum, i) => sum + i.on_hand * i.price_vnd, 0),
    [items]
  );
  const outOfStockCount = useMemo(() => items.filter((i) => i.on_hand === 0).length, [items]);
  const lowStockCount = useMemo(
    () => items.filter((i) => i.on_hand > 0 && i.on_hand <= 5).length,
    [items]
  );
  const inStockCount = useMemo(() => items.filter((i) => i.on_hand > 5).length, [items]);

  const categories = useMemo(() => {
    const set = new Set(items.map((i) => i.category_name).filter(Boolean));
    return Array.from(set).sort();
  }, [items]);

  // Filtered dataset
  const filtered = useMemo(() => {
    let result = items;
    if (category) {
      result = result.filter((i) => i.category_name === category);
    }
    if (stockStatus === "out_of_stock") {
      result = result.filter((i) => i.on_hand === 0);
    } else if (stockStatus === "low_stock") {
      result = result.filter((i) => i.on_hand > 0 && i.on_hand <= 5);
    } else if (stockStatus === "in_stock") {
      result = result.filter((i) => i.on_hand > 5);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          i.variant_sku.toLowerCase().includes(q) ||
          i.product_name.toLowerCase().includes(q) ||
          i.size_code.toLowerCase().includes(q) ||
          i.color_code.toLowerCase().includes(q) ||
          i.category_name.toLowerCase().includes(q)
      );
    }
    return result;
  }, [items, search, category, stockStatus]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function handleExportCsv() {
    exportToCsv(
      `ton_kho_cua_hang_${new Date().toISOString().slice(0, 10)}`,
      [
        "Mã SKU",
        "Tên sản phẩm",
        "Danh mục",
        "Size",
        "Màu",
        "Giá bán (VNĐ)",
        "Tồn kho thực tế",
        "Tồn kho ban đầu",
        "Trạng thái",
      ],
      filtered.map((i) => [
        i.variant_sku,
        i.product_name,
        i.category_name,
        i.size_code,
        i.color_code,
        i.price_vnd,
        i.on_hand,
        i.opening_on_hand,
        i.on_hand === 0 ? "Hết hàng" : i.on_hand <= 5 ? "Sắp hết" : "Còn hàng",
      ])
    );
  }

  const storeName = items[0]?.store_name || "Cửa hàng";

  return (
    <section className="space-y-6">
      {/* Header */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Kho chi nhánh</p>
          <h1 className="admin-heading mt-2">Tồn kho cửa hàng</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            {storeName} · Quản lý danh mục biến thể, số lượng thực tế và đối soát xuất nhập tồn.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {lastUpdated ? (
            <span className="text-xs text-muted tabular-nums mr-1">
              Cập nhật lúc {lastUpdated.toLocaleTimeString("vi-VN")}
            </span>
          ) : null}
          <button
            className="button-secondary inline-flex items-center gap-1.5 h-10 px-3.5 text-xs font-semibold"
            disabled={refreshing}
            onClick={loadData}
            title="Làm mới dữ liệu tồn kho"
            type="button"
          >
            <Icon className={refreshing ? "animate-spin text-accent" : ""} name="rotate-ccw" size={15} />
            <span>Làm mới</span>
          </button>
        </div>
      </header>

      {error ? (
        <section className="feedback-error">
          <h1 className="font-semibold">Không tải được dữ liệu tồn kho</h1>
          <p className="mt-1">{error}</p>
          <button className="button-secondary mt-3 text-xs" onClick={loadData} type="button">
            Thử lại
          </button>
        </section>
      ) : null}

      {/* 4 Top KPI Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Mã biến thể (SKUs)</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="box" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-ink font-mono">
            {loading ? "..." : items.length.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted">Tổng mã biến thể tại chi nhánh</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Tổng tồn kho thực tế</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="package" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-ink font-mono">
            {loading ? "..." : totalStock.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted">Sản phẩm sẵn sàng bán tại quầy</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Ước tính giá trị tồn</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="cash" size={18} />
            </div>
          </div>
          <p
            aria-label={formatVnd(totalEstimatedValue)}
            className="mt-3 text-2xl font-bold tracking-tight text-accent font-mono truncate"
            title={formatVnd(totalEstimatedValue)}
          >
            {loading ? "..." : formatMetricVnd(totalEstimatedValue)}
          </p>
          <p className="mt-2 text-xs text-muted">Tính theo giá bán niêm yết</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Cảnh báo nhập hàng</p>
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                outOfStockCount > 0
                  ? "bg-danger/10 text-danger"
                  : lowStockCount > 0
                    ? "bg-warning/10 text-warning"
                    : "bg-sand text-muted"
              }`}
            >
              <Icon name="alert" size={18} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold tracking-tight font-mono ${
                outOfStockCount > 0
                  ? "text-danger"
                  : lowStockCount > 0
                    ? "text-warning"
                    : "text-ink"
              }`}
            >
              {loading ? "..." : outOfStockCount + lowStockCount}
            </span>
            <span className="text-xs text-muted">mã cần bổ sung</span>
          </div>
          <p className="mt-2 text-xs text-muted">
            {outOfStockCount} hết hàng · {lowStockCount} sắp hết (≤ 5)
          </p>
        </article>
      </div>

      {/* Filters and Search Toolbar */}
      <div className="flex flex-col gap-3.5 rounded-2xl border border-line bg-surface p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Icon
              className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted"
              name="search"
              size={16}
            />
            <input
              className="admin-input w-full pl-10 pr-9 text-sm"
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Tìm kiếm mã SKU, tên sản phẩm, size, màu..."
              value={search}
            />
            {search && (
              <button
                aria-label="Xóa tìm kiếm"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
                onClick={() => {
                  setSearch("");
                  setPage(1);
                }}
                type="button"
              >
                <Icon name="close" size={14} />
              </button>
            )}
          </div>

          {/* Controls Right */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Category Dropdown */}
            <select
              aria-label="Lọc theo danh mục"
              className="admin-input text-sm h-10 py-1.5 px-3 min-w-44"
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              value={category}
            >
              <option value="">Tất cả danh mục ({items.length})</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>

            {/* View Mode Toggle */}
            <div className="inline-flex rounded-xl border border-line bg-paper p-1">
              <button
                className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                  viewMode === "table"
                    ? "bg-ink text-paper shadow-xs"
                    : "text-muted hover:text-ink"
                }`}
                onClick={() => setViewMode("table")}
                title="Dạng bảng chi tiết"
                type="button"
              >
                <Icon name="receipt" size={14} />
                <span>Bảng</span>
              </button>
              <button
                className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                  viewMode === "grid"
                    ? "bg-ink text-paper shadow-xs"
                    : "text-muted hover:text-ink"
                }`}
                onClick={() => setViewMode("grid")}
                title="Dạng lưới thẻ"
                type="button"
              >
                <Icon name="dashboard" size={14} />
                <span>Lưới</span>
              </button>
            </div>

            {/* Export CSV */}
            <button
              className="button-secondary inline-flex items-center gap-1.5 h-10 px-3.5 text-xs font-semibold"
              disabled={filtered.length === 0}
              onClick={handleExportCsv}
              title="Xuất file CSV chuẩn Excel"
              type="button"
            >
              <Icon name="package" size={15} />
              <span>Xuất CSV</span>
            </button>
          </div>
        </div>

        {/* Status Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 border-t border-line/60 pt-3 text-xs">
          <span className="font-medium text-muted mr-1">Trạng thái:</span>
          <button
            className={`rounded-full px-3 py-1 font-semibold transition ${
              stockStatus === "all"
                ? "bg-ink text-paper"
                : "border border-line bg-paper text-muted hover:border-ink hover:text-ink"
            }`}
            onClick={() => {
              setStockStatus("all");
              setPage(1);
            }}
            type="button"
          >
            Tất cả ({items.length})
          </button>
          <button
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-semibold transition ${
              stockStatus === "in_stock"
                ? "bg-emerald-700 text-white"
                : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/20 dark:text-emerald-400"
            }`}
            onClick={() => {
              setStockStatus("in_stock");
              setPage(1);
            }}
            type="button"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Còn hàng ({inStockCount})
          </button>
          <button
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-semibold transition ${
              stockStatus === "low_stock"
                ? "bg-warning text-white"
                : "border border-warning/30 bg-warning/10 text-warning hover:bg-warning/20"
            }`}
            onClick={() => {
              setStockStatus("low_stock");
              setPage(1);
            }}
            type="button"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-warning" />
            Sắp hết (≤ 5) ({lowStockCount})
          </button>
          <button
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-semibold transition ${
              stockStatus === "out_of_stock"
                ? "bg-danger text-white"
                : "border border-danger/30 bg-danger/10 text-danger hover:bg-danger/20"
            }`}
            onClick={() => {
              setStockStatus("out_of_stock");
              setPage(1);
            }}
            type="button"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-danger" />
            Hết hàng (0) ({outOfStockCount})
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="space-y-4">
          <div className="h-14 animate-pulse rounded-2xl bg-sand/60" />
          <div className="h-64 animate-pulse rounded-2xl bg-sand/60" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="admin-panel text-center py-12">
          <Icon className="mx-auto text-muted mb-3" name="package" size={32} />
          <h2 className="text-base font-semibold text-ink">Không tìm thấy sản phẩm nào</h2>
          <p className="mt-1 text-sm text-muted">
            {search || category || stockStatus !== "all"
              ? "Hãy thử thay đổi điều kiện tìm kiếm hoặc bộ lọc trạng thái."
              : "Hiện chưa có dữ liệu tồn kho cho chi nhánh này."}
          </p>
          {(search || category || stockStatus !== "all") && (
            <button
              className="button-secondary mt-4 text-xs font-semibold"
              onClick={() => {
                setSearch("");
                setCategory("");
                setStockStatus("all");
                setPage(1);
              }}
              type="button"
            >
              Đặt lại bộ lọc
            </button>
          )}
        </div>
      ) : viewMode === "table" ? (
        /* Table View */
        <div className="admin-table-shell">
          <table>
            <thead>
              <tr>
                <th className="w-32">Mã SKU</th>
                <th>Sản phẩm &amp; Danh mục</th>
                <th className="w-36">Phân loại</th>
                <th className="w-32 text-right">Giá niêm yết</th>
                <th className="w-36 text-right">Tồn thực tế</th>
                <th className="w-28 text-right">Tồn ban đầu</th>
                <th className="w-32 text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((item) => (
                <tr className="transition-colors hover:bg-sand/30" key={item.variant_id}>
                  <td>
                    <span className="font-mono text-xs font-semibold rounded bg-sand/70 px-2 py-1 text-ink">
                      {item.variant_sku}
                    </span>
                  </td>
                  <td>
                    <div className="min-w-0 max-w-md">
                      <p className="font-medium text-ink leading-snug">{item.product_name}</p>
                      {item.category_name ? (
                        <p className="text-xs text-muted mt-0.5">{item.category_name}</p>
                      ) : null}
                    </div>
                  </td>
                  <td>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="inline-flex items-center rounded-md border border-line bg-paper px-2 py-0.5 text-xs font-medium">
                        Size {item.size_code}
                      </span>
                      <span className="inline-flex items-center rounded-md border border-line bg-paper px-2 py-0.5 text-xs font-medium text-muted">
                        {item.color_code}
                      </span>
                    </div>
                  </td>
                  <td className="text-right font-semibold whitespace-nowrap">
                    {formatVnd(item.price_vnd)}
                  </td>
                  <td className="text-right">
                    <div className="flex flex-col items-end gap-1">
                      <span className="text-sm font-bold tabular-nums">
                        {item.on_hand.toLocaleString("vi-VN")}
                      </span>
                      {/* Stock level bar */}
                      <div className="w-20 h-1.5 rounded-full bg-sand overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            item.on_hand === 0
                              ? "bg-danger"
                              : item.on_hand <= 5
                                ? "bg-warning"
                                : "bg-emerald-600"
                          }`}
                          style={{
                            width: `${Math.min(
                              100,
                              Math.max(
                                item.on_hand === 0 ? 0 : 10,
                                Math.round(
                                  (item.on_hand / Math.max(item.opening_on_hand || 20, 20)) * 100
                                )
                              )
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="text-right text-muted tabular-nums whitespace-nowrap">
                    {item.opening_on_hand > 0 ? item.opening_on_hand.toLocaleString("vi-VN") : "—"}
                  </td>
                  <td className="text-center whitespace-nowrap">
                    {item.on_hand === 0 ? (
                      <span className="inline-flex items-center gap-1 rounded-full border border-danger/30 bg-danger/10 px-2.5 py-0.5 text-xs font-semibold text-danger">
                        <span className="h-1.5 w-1.5 rounded-full bg-danger animate-pulse" />
                        Hết hàng
                      </span>
                    ) : item.on_hand <= 5 ? (
                      <span className="inline-flex items-center gap-1 rounded-full border border-warning/30 bg-warning/10 px-2.5 py-0.5 text-xs font-semibold text-warning">
                        <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                        Sắp hết
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        Còn hàng
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* Grid Cards View */
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {paginated.map((item) => (
            <article
              className="rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:shadow-admin hover:border-accent/25"
              key={item.variant_id}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <span className="font-mono text-xs font-semibold rounded bg-sand/70 px-2 py-0.5 text-ink">
                    {item.variant_sku}
                  </span>
                  <h3 className="mt-2 text-sm font-semibold text-ink line-clamp-2 leading-snug">
                    {item.product_name}
                  </h3>
                  {item.category_name ? (
                    <p className="mt-1 text-xs text-muted">{item.category_name}</p>
                  ) : null}
                </div>
                <div className="shrink-0">
                  {item.on_hand === 0 ? (
                    <span className="inline-flex items-center gap-1 rounded-full border border-danger/30 bg-danger/10 px-2.5 py-0.5 text-xs font-semibold text-danger">
                      Hết hàng
                    </span>
                  ) : item.on_hand <= 5 ? (
                    <span className="inline-flex items-center gap-1 rounded-full border border-warning/30 bg-warning/10 px-2.5 py-0.5 text-xs font-semibold text-warning">
                      Sắp hết
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                      Còn hàng
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-3.5 flex items-center gap-1.5">
                <span className="rounded-md border border-line bg-paper px-2 py-0.5 text-xs font-medium">
                  Size {item.size_code}
                </span>
                <span className="rounded-md border border-line bg-paper px-2 py-0.5 text-xs font-medium text-muted">
                  {item.color_code}
                </span>
              </div>

              <div className="mt-4 border-t border-line/60 pt-3 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted">Giá niêm yết</span>
                  <span className="text-sm font-bold text-ink">{formatVnd(item.price_vnd)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted">Tồn thực tế / Mở đầu</span>
                  <span className="font-semibold tabular-nums text-ink">
                    {item.on_hand.toLocaleString("vi-VN")}{" "}
                    <span className="text-muted font-normal">/ {item.opening_on_hand || "—"}</span>
                  </span>
                </div>
                {/* Stock progress */}
                <div className="h-1.5 w-full rounded-full bg-sand overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      item.on_hand === 0
                        ? "bg-danger"
                        : item.on_hand <= 5
                          ? "bg-warning"
                          : "bg-emerald-600"
                    }`}
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          item.on_hand === 0 ? 0 : 10,
                          Math.round(
                            (item.on_hand / Math.max(item.opening_on_hand || 20, 20)) * 100
                          )
                        )
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-xs text-muted">
            Hiển thị{" "}
            <span className="font-semibold text-ink">{(page - 1) * PAGE_SIZE + 1}</span> -{" "}
            <span className="font-semibold text-ink">
              {Math.min(page * PAGE_SIZE, filtered.length)}
            </span>{" "}
            trên tổng <span className="font-semibold text-ink">{filtered.length}</span> sản phẩm
          </p>

          <div className="flex items-center gap-1">
            <button
              aria-label="Trang trước"
              className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-line bg-surface text-ink transition hover:bg-sand disabled:pointer-events-none disabled:opacity-40"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              type="button"
            >
              <Icon className="rotate-180" name="arrow-right" size={14} />
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => {
              if (p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)) {
                return (
                  <button
                    className={`inline-flex h-9 min-w-[36px] items-center justify-center rounded-xl px-2.5 text-xs font-semibold transition ${
                      p === page
                        ? "bg-ink text-paper shadow-xs"
                        : "border border-line bg-surface text-ink hover:bg-sand"
                    }`}
                    key={p}
                    onClick={() => setPage(p)}
                    type="button"
                  >
                    {p}
                  </button>
                );
              }
              if (p === page - 2 || p === page + 2) {
                return (
                  <span className="px-1 text-xs text-muted" key={p}>
                    ...
                  </span>
                );
              }
              return null;
            })}

            <button
              aria-label="Trang sau"
              className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-line bg-surface text-ink transition hover:bg-sand disabled:pointer-events-none disabled:opacity-40"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              type="button"
            >
              <Icon name="arrow-right" size={14} />
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
