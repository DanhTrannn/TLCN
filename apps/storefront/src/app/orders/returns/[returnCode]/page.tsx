"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ReturnStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  cancelCustomerReturnRequest,
  getCustomerReturnDetail,
  type ReturnRequestDetail,
} from "@/lib/commerce";
import { createVietnamDateTimeFormatter, parseApiDateTime } from "@/lib/datetime";

const dateFormatter = createVietnamDateTimeFormatter({
  dateStyle: "medium",
  timeStyle: "short",
});

const RETURN_STAGES = [
  {
    key: "pending_review",
    title: "1. Gửi yêu cầu",
    description: "Chờ cửa hàng tiếp nhận & xem xét",
  },
  {
    key: "approved",
    title: "2. Admin phê duyệt",
    description: "Đã duyệt, sẵn sàng nhận hàng gửi về",
  },
  {
    key: "goods_received",
    title: "3. Kho nhận hàng",
    description: "Kho đã nhận kiện hàng & kiểm tra",
  },
  {
    key: "completed",
    title: "4. Hoàn tất & Hoàn tiền",
    description: "Đã hoàn tất thủ tục & hoàn tiền",
  },
];

const STAGE_INDEX_MAP: Record<string, number> = {
  pending_review: 0,
  approved: 1,
  goods_received: 2,
  completed: 3,
};

function inspectionBadge(status: string) {
  switch (status) {
    case "passed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
          <Icon name="check" size={12} />
          Đạt chuẩn
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/25 bg-rose-500/10 px-2.5 py-0.5 text-xs font-semibold text-rose-700 dark:text-rose-400">
          <Icon name="close" size={12} />
          Không đạt
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-line bg-paper px-2.5 py-0.5 text-xs font-medium text-muted">
          Chờ kiểm định
        </span>
      );
  }
}

export default function CustomerReturnDetailPage() {
  const { returnCode } = useParams<{ returnCode: string }>();
  const router = useRouter();

  const [detail, setDetail] = useState<ReturnRequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const load = useCallback(async () => {
    if (!returnCode) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCustomerReturnDetail(returnCode);
      setDetail(data);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        router.push(`/login?returnTo=/orders/returns/${returnCode}`);
        return;
      }
      setError("Không tìm thấy thông tin yêu cầu đổi trả.");
    } finally {
      setLoading(false);
    }
  }, [returnCode, router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCancelRequest() {
    if (!returnCode) return;
    setCancelling(true);
    setError(null);
    try {
      const updated = await cancelCustomerReturnRequest(returnCode);
      setDetail(updated);
      setShowCancelConfirm(false);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không thể hủy yêu cầu đổi trả."
      );
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-5xl px-5 py-10 sm:px-6 sm:py-14 text-muted">
        Đang tải thông tin yêu cầu đổi trả…
      </main>
    );
  }

  if (error && !detail) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <div className="rounded-3xl border border-accent/20 bg-accent/10 p-8 text-center">
          <p className="font-medium text-accent">{error}</p>
          <Link className="button-primary mt-5" href="/orders">
            Quay lại danh sách đơn hàng
          </Link>
        </div>
      </main>
    );
  }

  if (!detail) return null;

  const currentStageIndex = STAGE_INDEX_MAP[detail.status] ?? -1;
  const isRejected = detail.status === "rejected";
  const isCancelled = detail.status === "cancelled";

  return (
    <main className="mx-auto max-w-5xl px-5 py-10 sm:px-6 sm:py-14">
      {/* Navigation link */}
      <div className="flex flex-wrap items-center gap-2">
        <Link className="button-ghost -ml-3" href={`/orders/${detail.order_number}`}>
          <Icon className="rotate-180" name="arrow-right" size={17} />
          Đơn hàng {detail.order_number}
        </Link>
      </div>

      {/* Main Header */}
      <header className="surface-card mt-4 p-5 sm:p-7">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500/10 text-amber-600">
                <Icon name="rotate-ccw" size={17} />
              </span>
              <p className="eyebrow">Tiến trình Đổi / Trả hàng</p>
            </div>
            <h1 className="mt-2 font-mono text-2xl font-semibold sm:text-3xl">
              {detail.return_code}
            </h1>
            <p className="mt-1 text-sm text-muted">
              Tạo lúc {dateFormatter.format(parseApiDateTime(detail.created_at))}
              {" · "}Đơn hàng gốc:{" "}
              <Link
                className="font-medium text-ink hover:underline"
                href={`/orders/${detail.order_number}`}
              >
                {detail.order_number}
              </Link>
            </p>
          </div>
          <div className="flex flex-col items-start gap-3 sm:items-end">
            <ReturnStatusBadge className="text-sm px-4 py-1.5" status={detail.status} />

            {/* Cancel Button if pending */}
            {detail.status === "pending_review" && !showCancelConfirm ? (
              <button
                className="button-accent text-xs"
                disabled={cancelling}
                onClick={() => setShowCancelConfirm(true)}
                type="button"
              >
                Hủy yêu cầu đổi trả
              </button>
            ) : null}
          </div>
        </div>

        {/* Cancellation Confirmation Bar */}
        {showCancelConfirm ? (
          <div className="mt-5 rounded-2xl border border-danger/30 bg-danger/5 p-4">
            <p className="text-sm font-semibold text-danger">
              Bạn có chắc chắn muốn hủy yêu cầu đổi / trả này?
            </p>
            <p className="mt-1 text-xs text-muted">
              Sau khi hủy, yêu cầu sẽ đóng lại và không thể phục hồi.
            </p>
            <div className="mt-3 flex items-center gap-3">
              <button
                className="button-accent text-xs px-4"
                disabled={cancelling}
                onClick={() => void handleCancelRequest()}
                type="button"
              >
                {cancelling ? "Đang hủy…" : "Xác nhận hủy"}
              </button>
              <button
                className="button-secondary text-xs px-4"
                disabled={cancelling}
                onClick={() => setShowCancelConfirm(false)}
                type="button"
              >
                Không, giữ lại
              </button>
            </div>
          </div>
        ) : null}

        {/* Alert for Rejected */}
        {isRejected ? (
          <div className="mt-5 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4">
            <div className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-rose-500 text-white">
                <Icon name="close" size={14} />
              </span>
              <div>
                <p className="text-sm font-semibold text-rose-800 dark:text-rose-300">
                  Yêu cầu đổi / trả đã bị từ chối
                </p>
                {detail.admin_note ? (
                  <p className="mt-1 text-xs text-rose-700 dark:text-rose-400">
                    Lý do từ chối: {detail.admin_note}
                  </p>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {/* Alert for Cancelled */}
        {isCancelled ? (
          <div className="mt-5 rounded-2xl border border-line bg-paper p-4">
            <p className="text-sm font-medium text-muted">
              Yêu cầu đổi / trả này đã được hủy.
            </p>
          </div>
        ) : null}

        {error ? <p className="mt-4 text-sm text-accent">{error}</p> : null}
      </header>

      {/* 4-Stage Visual Stepper */}
      {!isCancelled && (
        <section className="surface-flat mt-6 p-5 sm:p-6">
          <h2 className="text-base font-semibold text-ink">Các bước xử lý yêu cầu</h2>
          <p className="mt-0.5 text-xs text-muted">
            Theo dõi tiến độ từ lúc gửi yêu cầu đến khi nhận tiền hoàn vào tài khoản.
          </p>

          <div className="mt-6 grid gap-4 sm:grid-cols-4">
            {RETURN_STAGES.map((stage, idx) => {
              const isFailedStage = isRejected && idx === 1;
              const isStepCompleted =
                !isRejected &&
                (currentStageIndex > idx || (detail.status === "completed" && idx === 3));
              const isCurrent =
                !isRejected && detail.status !== "completed" && currentStageIndex === idx;

              return (
                <div
                  className={`relative flex flex-col justify-between rounded-2xl border p-4 transition ${
                    isFailedStage
                      ? "border-rose-500/40 bg-rose-500/10 text-rose-800 dark:text-rose-300"
                      : isStepCompleted || isCurrent
                        ? "border-moss/40 bg-moss/5 text-ink"
                        : "border-line bg-paper/50 text-muted opacity-70"
                  }`}
                  key={stage.key}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                        isFailedStage
                          ? "bg-rose-500 text-white"
                          : isStepCompleted
                            ? "bg-moss text-white"
                            : isCurrent
                              ? "bg-ink text-paper"
                              : "bg-line text-muted"
                      }`}
                    >
                      {isFailedStage ? (
                        <Icon name="close" size={14} />
                      ) : isStepCompleted ? (
                        <Icon name="check" size={14} />
                      ) : (
                        idx + 1
                      )}
                    </span>
                    {isCurrent ? (
                      <span className="rounded-full bg-ink px-2 py-0.5 text-[10px] font-semibold text-paper">
                        Hiện tại
                      </span>
                    ) : null}
                    {detail.status === "completed" && idx === 3 ? (
                      <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                        Hoàn tất
                      </span>
                    ) : null}
                    {isFailedStage ? (
                      <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                        Từ chối
                      </span>
                    ) : null}
                  </div>

                  <div className="mt-3">
                    <h3 className="font-semibold text-sm">{stage.title}</h3>
                    <p className="mt-1 text-xs leading-relaxed text-muted">
                      {stage.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Return Items and Information Grid */}
      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        {/* Left Column: Return Items Table */}
        <section className="surface-flat p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-ink">Sản phẩm yêu cầu đổi trả</h2>
            <span className="text-xs text-muted">{detail.items.length} sản phẩm</span>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-line text-xs uppercase tracking-wider text-muted">
                <tr>
                  <th className="pb-3 pr-4 font-semibold">Sản phẩm</th>
                  <th className="pb-3 px-3 font-semibold text-center">Số lượng</th>
                  <th className="pb-3 px-3 font-semibold text-right">Hoàn tiền</th>
                  <th className="pb-3 pl-3 font-semibold text-right">Kiểm định</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/70">
                {detail.items.map((item) => (
                  <tr key={item.return_item_id} className="hover:bg-paper/40">
                    <td className="py-3.5 pr-4 align-top">
                      <p className="font-medium text-ink">
                        {item.product_name || "Sản phẩm"}
                      </p>
                      <p className="mt-0.5 text-xs text-muted">
                        {item.sku ? `SKU: ${item.sku}` : ""}
                        {item.variant_title ? ` · ${item.variant_title}` : ""}
                      </p>
                    </td>
                    <td className="py-3.5 px-3 text-center align-top font-semibold">
                      {item.quantity}
                    </td>
                    <td className="py-3.5 px-3 text-right align-top font-semibold text-ink">
                      {formatVnd(item.refund_amount_vnd)}
                    </td>
                    <td className="py-3.5 pl-3 text-right align-top">
                      {inspectionBadge(item.inspection_status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Refund summary line */}
          <div className="mt-5 flex items-center justify-between border-t border-line pt-4 text-sm">
            <span className="text-muted">Tổng số tiền hoàn lại:</span>
            <span className="text-lg font-bold text-ink">
              {formatVnd(detail.total_refund_amount_vnd)}
            </span>
          </div>
        </section>

        {/* Right Column: Return Info Card */}
        <aside className="space-y-5">
          {/* Card: Bank Account for Refund */}
          {detail.bank_info ? (
            <div className="surface-flat p-5">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
                <Icon name="cash" size={17} />
                Tài khoản nhận hoàn tiền
              </h3>
              <div className="mt-3 space-y-2 text-xs">
                <div>
                  <span className="text-muted block">Ngân hàng</span>
                  <span className="font-semibold text-ink text-sm">
                    {detail.bank_info.bank_name}
                  </span>
                </div>
                <div>
                  <span className="text-muted block">Số tài khoản</span>
                  <span className="font-mono font-semibold text-ink text-sm">
                    {detail.bank_info.bank_account_number}
                  </span>
                </div>
                <div>
                  <span className="text-muted block">Chủ tài khoản</span>
                  <span className="font-semibold text-ink text-sm uppercase">
                    {detail.bank_info.bank_account_holder}
                  </span>
                </div>
              </div>
            </div>
          ) : null}

          {/* Card: Customer Reason & Admin Note */}
          <div className="surface-flat p-5">
            <h3 className="text-sm font-semibold text-ink">Chi tiết yêu cầu</h3>
            <div className="mt-3 space-y-3 text-xs">
              <div>
                <span className="text-muted block font-medium">Lý do từ khách hàng:</span>
                <p className="mt-1 rounded-xl bg-paper p-3 text-ink leading-relaxed">
                  {detail.customer_reason}
                </p>
              </div>

              {detail.admin_note ? (
                <div>
                  <span className="text-muted block font-medium">Ghi chú từ quản trị viên:</span>
                  <p className="mt-1 rounded-xl bg-paper p-3 text-ink leading-relaxed">
                    {detail.admin_note}
                  </p>
                </div>
              ) : null}

              {detail.reviewed_at ? (
                <p className="text-muted">
                  Thời gian duyệt: {dateFormatter.format(parseApiDateTime(detail.reviewed_at))}
                </p>
              ) : null}

              {detail.resolved_at ? (
                <p className="text-muted">
                  Thời gian xử lý: {dateFormatter.format(parseApiDateTime(detail.resolved_at))}
                </p>
              ) : null}
            </div>

            {/* Proof Images */}
            {detail.image_urls && detail.image_urls.length > 0 ? (
              <div className="mt-4 border-t border-line pt-4">
                <span className="text-xs font-semibold text-muted uppercase tracking-wider">
                  Hình ảnh minh chứng ({detail.image_urls.length})
                </span>
                <div className="mt-2 flex flex-wrap gap-2">
                  {detail.image_urls.map((url, idx) => (
                    <a
                      className="group relative flex h-16 w-16 items-center justify-center overflow-hidden rounded-xl border border-line bg-sand hover:border-accent"
                      href={url}
                      key={idx}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        alt={`Ảnh minh chứng ${idx + 1}`}
                        className="h-full w-full object-cover transition group-hover:scale-105"
                        src={url}
                      />
                    </a>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </aside>
      </div>
    </main>
  );
}
