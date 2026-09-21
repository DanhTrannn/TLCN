"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ReturnStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  getAdminReturnsList,
  type ReturnRequestDetail,
} from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

const FILTER_TABS = [
  { id: "", label: "Tất cả" },
  { id: "pending_review", label: "Chờ duyệt" },
  { id: "approved", label: "Chờ nhận hàng" },
  { id: "goods_received", label: "Đã nhận hàng" },
  { id: "completed", label: "Đã hoàn tất" },
  { id: "rejected", label: "Từ chối" },
  { id: "cancelled", label: "Đã hủy" },
];

const PAGE_SIZE = 20;

export default function AdminReturnsPage() {
  const [statusTab, setStatusTab] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [returns, setReturns] = useState<ReturnRequestDetail[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
      const res = await getAdminReturnsList({
        status: statusTab || undefined,
        search: debouncedSearch || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      setReturns(res.items);
      setTotal(res.total);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được danh sách yêu cầu đổi trả"
      );
    } finally {
      setLoading(false);
    }
  }, [statusTab, debouncedSearch, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <section>
      <header className="flex flex-col gap-4">
        <div>
          <p className="eyebrow">Return &amp; refund operations</p>
          <h1 className="admin-heading mt-2">Đổi trả &amp; Hoàn tiền</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            Quản lý tiếp nhận yêu cầu, kiểm định hàng hóa thu hồi và giải ngân hoàn tiền cho khách hàng.
          </p>
        </div>

        {/* Filters and Search Bar */}
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          {/* Filter tabs */}
          <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto rounded-2xl border border-line bg-surface p-1.5 shadow-admin">
            {FILTER_TABS.map((tab) => {
              const active = statusTab === tab.id;
              return (
                <button
                  className={`shrink-0 rounded-xl px-3.5 py-2 text-xs font-semibold transition sm:text-sm ${
                    active
                      ? "bg-ink text-paper shadow-sm"
                      : "text-muted hover:bg-paper hover:text-ink"
                  }`}
                  key={tab.id}
                  onClick={() => {
                    setStatusTab(tab.id);
                    setPage(0);
                  }}
                  type="button"
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Search input */}
          <div className="relative w-full max-w-sm">
            <Icon
              className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted"
              name="search"
              size={16}
            />
            <input
              className="admin-input w-full pl-10 pr-4"
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm mã RT-, mã đơn, tên, SĐT..."
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
        </div>
      </header>

      {error ? <div className="feedback-error mt-5">{error}</div> : null}

      {loading ? (
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : returns.length === 0 ? (
        <div className="surface-card mt-6 p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sand text-muted">
            <Icon name="rotate-ccw" size={24} />
          </div>
          <h2 className="mt-4 text-base font-semibold text-ink">
            Không tìm thấy yêu cầu đổi trả nào
          </h2>
          <p className="mt-1 text-sm text-muted">
            {search || statusTab
              ? "Không có kết quả phù hợp với bộ lọc hiện tại. Hãy thử thay đổi từ khóa hoặc tab trạng thái."
              : "Hiện chưa có yêu cầu đổi trả nào được gửi trong hệ thống."}
          </p>
          {search || statusTab ? (
            <button
              className="button-secondary mt-4"
              onClick={() => {
                setStatusTab("");
                setSearch("");
              }}
              type="button"
            >
              Đặt lại bộ lọc
            </button>
          ) : null}
        </div>
      ) : (
        <div className="admin-table-shell mt-6">
          <table>
            <thead>
              <tr>
                <th>Mã yêu cầu</th>
                <th>Mã đơn hàng</th>
                <th>Khách hàng</th>
                <th>Số lượng món</th>
                <th>Tổng tiền hoàn</th>
                <th>Trạng thái</th>
                <th>Thời gian tạo</th>
                <th className="text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {returns.map((item) => {
                const totalItemsCount =
                  item.items?.reduce((acc, curr) => acc + curr.quantity, 0) ||
                  item.items?.length ||
                  1;

                return (
                  <tr key={item.return_code}>
                    <td>
                      <Link
                        className="font-mono font-semibold text-accent hover:underline"
                        href={`/admin/returns/${item.return_code}`}
                      >
                        {item.return_code}
                      </Link>
                    </td>
                    <td>
                      <Link
                        className="font-mono text-xs font-medium text-ink hover:underline"
                        href={`/admin/orders/${item.order_number}`}
                      >
                        {item.order_number}
                      </Link>
                    </td>
                    <td>
                      <div>
                        <p className="font-semibold text-ink">
                          {item.customer_name ||
                            item.bank_info?.bank_account_holder ||
                            "Khách hàng"}
                        </p>
                        {item.customer_phone ? (
                          <p className="text-xs text-muted">{item.customer_phone}</p>
                        ) : null}
                      </div>
                    </td>
                    <td>
                      <span className="font-medium text-ink">{totalItemsCount} món</span>
                    </td>
                    <td>
                      <span className="font-semibold text-ink">
                        {formatVnd(item.total_refund_amount_vnd)}
                      </span>
                    </td>
                    <td>
                      <ReturnStatusBadge status={item.status} />
                    </td>
                    <td>
                      <time className="text-xs text-muted">
                        {formatVietnamDateTime(item.created_at)}
                      </time>
                    </td>
                    <td className="text-right">
                      <Link
                        className="button-secondary inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold"
                        href={`/admin/returns/${item.return_code}`}
                      >
                        <span>Chi tiết</span>
                        <Icon name="chevron-right" size={14} />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination bar */}
          {totalPages > 1 ? (
            <div className="flex flex-col items-center justify-between gap-3 border-t border-line px-5 py-4 sm:flex-row">
              <span className="text-xs text-muted">
                Hiển thị {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} trong tổng số{" "}
                <strong>{total}</strong> yêu cầu
              </span>
              <div className="flex items-center gap-2">
                <button
                  className="button-secondary px-3 py-1.5 text-xs"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  type="button"
                >
                  Trang trước
                </button>
                <span className="text-xs font-medium text-ink">
                  Trang {page + 1} / {totalPages}
                </span>
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
          ) : (
            <div className="border-t border-line px-5 py-3 text-xs text-muted">
              Tổng số <strong>{total}</strong> yêu cầu
            </div>
          )}
        </div>
      )}
    </section>
  );
}
