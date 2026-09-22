"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  getAdminInboundReceiptDetail,
  type InboundReceiptDetail,
} from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

function CostDeltaBadge({
  prevCost,
  newCost,
}: {
  prevCost: number;
  newCost: number;
}) {
  if (prevCost === 0) {
    return (
      <span className="inline-flex items-center rounded-md border border-sky-200 bg-sky-50 px-2 py-0.5 text-xs font-semibold text-sky-800">
        Khởi tạo giá vốn
      </span>
    );
  }

  const delta = newCost - prevCost;
  if (delta === 0) {
    return (
      <span className="inline-flex items-center rounded-md border border-gray-200 bg-gray-50 px-2 py-0.5 text-xs font-medium text-gray-600">
        Không đổi (0%)
      </span>
    );
  }

  const absPercent = Math.abs((delta / prevCost) * 100).toFixed(1);
  if (delta > 0) {
    return (
      <span className="inline-flex items-center rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800">
        +{formatVnd(delta)} (+{absPercent}%)
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800">
      -{formatVnd(Math.abs(delta))} (-{absPercent}%)
    </span>
  );
}

export default function AdminInboundReceiptDetailPage() {
  const { receiptCode } = useParams<{ receiptCode: string }>();
  const router = useRouter();

  const [detail, setDetail] = useState<InboundReceiptDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!receiptCode) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminInboundReceiptDetail(receiptCode);
      setDetail(data);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        router.push(`/login?returnTo=/admin/inbound/${receiptCode}`);
        return;
      }
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tìm thấy thông tin phiếu nhập kho."
      );
    } finally {
      setLoading(false);
    }
  }, [receiptCode, router]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-48 animate-pulse rounded bg-sand/60" />
        <div className="h-40 animate-pulse rounded-2xl bg-sand/60" />
        <div className="h-80 animate-pulse rounded-2xl bg-sand/60" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="surface-card p-12 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sand text-muted">
          <Icon name="box" size={24} />
        </div>
        <h1 className="mt-4 text-lg font-semibold text-ink">
          Không tìm thấy phiếu nhập kho
        </h1>
        <p className="mt-1 text-sm text-muted">
          {error || "Phiếu nhập kho không tồn tại hoặc bạn không có quyền xem."}
        </p>
        <Link className="button-secondary mt-5" href="/admin/inbound">
          ← Quay lại danh sách nhập kho
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumb */}
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink"
            href="/admin/inbound"
          >
            <span>←</span>
            Quay lại danh sách nhập kho
          </Link>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="font-mono text-2xl font-bold tracking-tight text-ink">
              {detail.receipt_code}
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Hoàn tất
            </span>
          </div>
          <p className="mt-1 text-xs text-muted">
            Nhập kho lúc: {formatVietnamDateTime(detail.created_at)} · Người tạo:{" "}
            <strong className="text-ink">{detail.created_by_name || "Admin"}</strong>
          </p>
        </div>
      </header>

      {/* Card 1: Overview Information & Metrics */}
      <article className="admin-panel">
        <div className="flex items-center gap-3 border-b border-line pb-3">
          <Icon className="text-moss" name="box" size={20} />
          <h2 className="font-semibold text-ink">Thông tin đợt nhập xưởng</h2>
        </div>

        <div className="mt-5 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Mã phiếu nhập
            </p>
            <p className="font-mono font-bold text-ink">{detail.receipt_code}</p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Tên đợt sản xuất
            </p>
            <p className="font-medium text-ink">{detail.batch_name}</p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Người thực hiện
            </p>
            <p className="font-medium text-ink">
              {detail.created_by_name || "Quản trị viên"}
            </p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Thời gian ghi nhận
            </p>
            <time className="text-sm text-ink">
              {formatVietnamDateTime(detail.created_at)}
            </time>
          </div>
        </div>

        {/* Notes section */}
        <div className="mt-4 rounded-xl border border-line bg-paper/50 p-3.5">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted">
            Ghi chú xưởng sản xuất
          </p>
          <p className="mt-1 text-sm text-ink whitespace-pre-wrap">
            {detail.notes || "Không có ghi chú"}
          </p>
        </div>

        {/* Metric Summary row */}
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-line bg-surface p-4">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Tổng số lượng sản phẩm
            </p>
            <p className="mt-1 text-2xl font-bold font-mono text-ink">
              {detail.total_items_count.toLocaleString("vi-VN")}{" "}
              <span className="text-sm font-normal text-muted">sản phẩm</span>
            </p>
          </div>

          <div className="rounded-2xl border border-line bg-surface p-4">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Tổng chi phí sản xuất
            </p>
            <p className="mt-1 text-2xl font-bold font-mono text-accent">
              {formatVnd(detail.total_cost_vnd)}
            </p>
          </div>
        </div>
      </article>

      {/* Card 2: Items Table with Costing Audit */}
      <article className="admin-panel">
        <div className="flex items-center justify-between border-b border-line pb-3">
          <div className="flex items-center gap-3">
            <Icon className="text-moss" name="package" size={20} />
            <h2 className="font-semibold text-ink">
              Chi tiết sản phẩm nhập kho &amp; Đối soát giá vốn ({detail.items.length})
            </h2>
          </div>
        </div>

        <div className="admin-table-shell mt-5">
          <table>
            <thead>
              <tr>
                <th>Sản phẩm &amp; SKU</th>
                <th>Phân loại</th>
                <th className="text-right">Số lượng</th>
                <th className="text-right">Đơn giá xưởng</th>
                <th className="text-center">Biến động giá vốn (Cũ → Mới)</th>
                <th className="text-right">Thành tiền</th>
              </tr>
            </thead>
            <tbody>
              {detail.items.map((item) => (
                <tr key={item.item_id}>
                  <td>
                    <div>
                      <p className="font-semibold text-ink">{item.product_name}</p>
                      <p className="font-mono text-xs text-muted">{item.sku}</p>
                    </div>
                  </td>
                  <td>
                    <span className="inline-flex rounded-lg bg-paper px-2.5 py-1 text-xs font-medium text-ink">
                      Size {item.size_code} / {item.color_code}
                    </span>
                  </td>
                  <td className="text-right font-mono font-medium text-ink">
                    {item.quantity.toLocaleString("vi-VN")}
                  </td>
                  <td className="text-right font-mono text-ink">
                    {formatVnd(item.unit_cost_vnd)}
                  </td>
                  <td>
                    <div className="flex flex-col items-center gap-1">
                      <div className="inline-flex items-center gap-1.5 font-mono text-xs">
                        <span className="text-muted line-through">
                          {formatVnd(item.previous_cost_price_vnd)}
                        </span>
                        <Icon className="text-muted" name="arrow-right" size={13} />
                        <span className="font-bold text-moss">
                          {formatVnd(item.new_cost_price_vnd)}
                        </span>
                      </div>
                      <CostDeltaBadge
                        newCost={item.new_cost_price_vnd}
                        prevCost={item.previous_cost_price_vnd}
                      />
                    </div>
                  </td>
                  <td className="text-right font-mono font-semibold text-accent">
                    {formatVnd(item.total_cost_vnd)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t-2 border-line bg-paper/40 font-semibold text-ink">
              <tr>
                <td className="py-3.5" colSpan={2}>
                  Tổng cộng
                </td>
                <td className="py-3.5 text-right font-mono">
                  {detail.total_items_count.toLocaleString("vi-VN")}
                </td>
                <td className="py-3.5" colSpan={2} />
                <td className="py-3.5 text-right font-mono text-accent">
                  {formatVnd(detail.total_cost_vnd)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </article>
    </div>
  );
}
