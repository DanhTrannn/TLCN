"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { CreateInboundModal } from "@/components/admin/CreateInboundModal";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  getAdminInboundReceipts,
  type InboundReceiptSummary,
} from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

const PAGE_SIZE = 20;

export default function AdminInboundReceiptsPage() {
  const [search, setSearch] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [receipts, setReceipts] = useState<InboundReceiptSummary[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Overall metric totals
  const [metrics, setMetrics] = useState<{
    totalCount: number;
    totalItems: number;
    totalCost: number;
  }>({
    totalCount: 0,
    totalItems: 0,
    totalCost: 0,
  });

  // Modal open state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAdminInboundReceipts({
        search: debouncedSearch || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      setReceipts(res.items);
      setTotal(res.total);

      // Compute sums for the stat cards
      const sumItems = res.items.reduce((acc, r) => acc + r.total_items_count, 0);
      const sumCost = res.items.reduce((acc, r) => acc + r.total_cost_vnd, 0);

      // If viewing first page without search, update global metrics
      if (!debouncedSearch && page === 0) {
        setMetrics({
          totalCount: res.total,
          totalItems: sumItems,
          totalCost: sumCost,
        });
      } else {
        // Update with current view if searching or paginating
        setMetrics((prev) => ({
          totalCount: res.total,
          totalItems: debouncedSearch ? sumItems : prev.totalItems,
          totalCost: debouncedSearch ? sumCost : prev.totalCost,
        }));
      }
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được danh sách phiếu nhập kho"
      );
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <section className="space-y-6">
      {/* Header */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Production &amp; Inbound Operations</p>
          <h1 className="admin-heading mt-2">Nhập kho sản xuất</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            Quản lý các đợt nhập thành phẩm từ xưởng sản xuất nội bộ và cập nhật giá vốn hàng bán (COGS).
          </p>
        </div>

        <div>
          <button
            className="button-primary inline-flex items-center gap-2"
            onClick={() => setIsCreateModalOpen(true)}
            type="button"
          >
            <Icon name="plus" size={17} />
            <span>Tạo phiếu nhập mới</span>
          </button>
        </div>
      </header>

      {/* Top Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Tổng đợt nhập xưởng</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="box" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-ink font-mono">
            {metrics.totalCount.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted">Phiếu nhập kho đã hoàn tất</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Tổng sản phẩm đã nhập</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="package" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-ink font-mono">
            {metrics.totalItems.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted">Chiếc / cái thành phẩm xuất xưởng</p>
        </article>

        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Tổng chi phí sản xuất</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="cash" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-accent font-mono">
            {formatVnd(metrics.totalCost)}
          </p>
          <p className="mt-2 text-xs text-muted">Tổng giá trị thành phẩm nhập xưởng</p>
        </article>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full max-w-md">
          <Icon
            className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted"
            name="search"
            size={16}
          />
          <input
            className="admin-input w-full pl-10 pr-9"
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo mã phiếu (IB-...), tên đợt..."
            type="search"
            value={search}
          />
          {search ? (
            <button
              aria-label="Xóa tìm kiếm"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
              onClick={() => setSearch("")}
              type="button"
            >
              <Icon name="close" size={14} />
            </button>
          ) : null}
        </div>

        <div className="text-xs text-muted">
          Tìm thấy <strong className="text-ink">{total}</strong> phiếu nhập kho
        </div>
      </div>

      {error ? (
        <div className="feedback-error" role="alert">
          <Icon name="alert" size={18} />
          <span>{error}</span>
        </div>
      ) : null}

      {/* Table Section */}
      {loading ? (
        <div className="h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : receipts.length === 0 ? (
        <div className="surface-card p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sand text-muted">
            <Icon name="box" size={24} />
          </div>
          <h2 className="mt-4 text-base font-semibold text-ink">
            Chưa có phiếu nhập kho nào
          </h2>
          <p className="mt-1 text-sm text-muted">
            {search
              ? "Không có phiếu nhập kho nào phù hợp với từ khóa tìm kiếm."
              : "Hệ thống chưa ghi nhận đợt nhập thành phẩm nào từ xưởng may."}
          </p>
          <div className="mt-4 flex justify-center gap-3">
            {search ? (
              <button
                className="button-secondary"
                onClick={() => setSearch("")}
                type="button"
              >
                Đặt lại tìm kiếm
              </button>
            ) : (
              <button
                className="button-primary inline-flex items-center gap-2"
                onClick={() => setIsCreateModalOpen(true)}
                type="button"
              >
                <Icon name="plus" size={16} />
                <span>Tạo phiếu nhập đầu tiên</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="admin-table-shell">
          <table>
            <thead>
              <tr>
                <th>Mã phiếu</th>
                <th>Tên đợt sản xuất</th>
                <th className="text-right">Số lượng SP</th>
                <th className="text-right">Tổng chi phí SX</th>
                <th>Trạng thái</th>
                <th>Người thực hiện</th>
                <th>Thời gian nhập</th>
                <th className="text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((item) => (
                <tr key={item.receipt_id}>
                  <td>
                    <Link
                      className="font-mono font-semibold text-accent hover:underline"
                      href={`/admin/inbound/${item.receipt_code}`}
                    >
                      {item.receipt_code}
                    </Link>
                  </td>
                  <td>
                    <p className="font-medium text-ink line-clamp-1">
                      {item.batch_name}
                    </p>
                  </td>
                  <td className="text-right font-medium text-ink font-mono">
                    {item.total_items_count.toLocaleString("vi-VN")}
                  </td>
                  <td className="text-right font-mono font-semibold text-ink">
                    {formatVnd(item.total_cost_vnd)}
                  </td>
                  <td>
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      Hoàn tất
                    </span>
                  </td>
                  <td>
                    <span className="text-sm text-ink">
                      {item.created_by_name || "Admin"}
                    </span>
                  </td>
                  <td>
                    <time className="text-xs text-muted">
                      {formatVietnamDateTime(item.created_at)}
                    </time>
                  </td>
                  <td className="text-right">
                    <Link
                      className="button-secondary inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold"
                      href={`/admin/inbound/${item.receipt_code}`}
                    >
                      <span>Chi tiết</span>
                      <Icon name="chevron-right" size={14} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 ? (
        <div className="flex items-center justify-between border-t border-line pt-4 text-sm text-muted">
          <p>
            Trang <strong className="text-ink">{page + 1}</strong> /{" "}
            <strong className="text-ink">{totalPages}</strong> (tổng{" "}
            <strong className="text-ink">{total}</strong> phiếu)
          </p>
          <div className="flex gap-2">
            <button
              className="button-secondary px-3 py-1.5 text-xs"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              type="button"
            >
              Trang trước
            </button>
            <button
              className="button-secondary px-3 py-1.5 text-xs"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              type="button"
            >
              Trang sau
            </button>
          </div>
        </div>
      ) : null}

      {/* Modal create inbound receipt */}
      <CreateInboundModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={() => {
          void load();
        }}
      />
    </section>
  );
}
