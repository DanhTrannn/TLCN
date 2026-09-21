"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { ReturnStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  getAdminReturnDetail,
  inspectAndResolveAdminReturn,
  receiveAdminReturn,
  reviewAdminReturn,
  type ReturnRequestDetail,
} from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `key-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export default function AdminReturnDetailPage() {
  const { returnCode } = useParams<{ returnCode: string }>();
  const router = useRouter();

  const [detail, setDetail] = useState<ReturnRequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Inspection state for goods_received
  const [inspectionMap, setInspectionMap] = useState<Record<number, "passed" | "failed">>({});
  const [adminNote, setAdminNote] = useState<string>("");

  // Reject Modal state
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  // Image preview modal
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!returnCode) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminReturnDetail(returnCode);
      setDetail(data);
      // Initialize inspection map from items
      const initialMap: Record<number, "passed" | "failed"> = {};
      data.items.forEach((item) => {
        initialMap[item.return_item_id] =
          item.inspection_status === "failed" ? "failed" : "passed";
      });
      setInspectionMap(initialMap);
      if (data.admin_note) {
        setAdminNote(data.admin_note);
      }
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        router.push(`/login?returnTo=/admin/returns/${returnCode}`);
        return;
      }
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tìm thấy thông tin yêu cầu đổi trả."
      );
    } finally {
      setLoading(false);
    }
  }, [returnCode, router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleApprove() {
    if (!returnCode) return;
    setBusy(true);
    setActionError(null);
    try {
      await reviewAdminReturn(returnCode, "approved", adminNote.trim() || undefined);
      await load();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Duyệt yêu cầu đổi trả thất bại."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!returnCode) return;
    if (!rejectReason.trim()) {
      setActionError("Vui lòng nhập lý do từ chối.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await reviewAdminReturn(returnCode, "rejected", rejectReason.trim());
      setIsRejectOpen(false);
      setRejectReason("");
      await load();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Từ chối yêu cầu đổi trả thất bại."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleReceive() {
    if (!returnCode) return;
    setBusy(true);
    setActionError(null);
    try {
      await receiveAdminReturn(returnCode);
      await load();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Xác nhận nhận hàng thất bại."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleInspectAndResolve() {
    if (!returnCode || !detail) return;
    setBusy(true);
    setActionError(null);
    try {
      const payloadItems = detail.items.map((it) => ({
        return_item_id: it.return_item_id,
        inspection_status: inspectionMap[it.return_item_id] ?? "passed",
      }));
      const idempotencyKey = generateIdempotencyKey();
      await inspectAndResolveAdminReturn(
        returnCode,
        {
          items: payloadItems,
          admin_note: adminNote.trim() || null,
        },
        idempotencyKey
      );
      await load();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Kiểm định và giải ngân thất bại."
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded-lg bg-sand/60" />
        <div className="h-64 animate-pulse rounded-2xl bg-sand/60" />
        <div className="h-64 animate-pulse rounded-2xl bg-sand/60" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="surface-card p-12 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-danger/10 text-danger">
          <Icon name="close" size={24} />
        </div>
        <h1 className="mt-4 text-lg font-semibold text-ink">
          {error || "Không tìm thấy yêu cầu đổi trả"}
        </h1>
        <p className="mt-2 text-sm text-muted">
          Yêu cầu đổi trả không tồn tại hoặc đã bị xóa khỏi hệ thống.
        </p>
        <Link className="button-secondary mt-6 inline-flex" href="/admin/returns">
          ← Quay lại danh sách đổi trả
        </Link>
      </div>
    );
  }

  // Live refund calculation when in inspection mode (goods_received)
  const isGoodsReceived = detail.status === "goods_received";
  const liveRefundAmount = detail.items.reduce((sum, item) => {
    const status = inspectionMap[item.return_item_id] ?? "passed";
    return status === "passed" ? sum + item.refund_amount_vnd : sum;
  }, 0);

  const passedCount = detail.items.filter(
    (item) => (inspectionMap[item.return_item_id] ?? "passed") === "passed"
  ).length;
  const failedCount = detail.items.length - passedCount;

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink"
            href="/admin/returns"
          >
            <span>←</span>
            Quay lại danh sách đổi trả
          </Link>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-ink font-mono">
              {detail.return_code}
            </h1>
            <ReturnStatusBadge className="text-sm px-3.5 py-1" status={detail.status} />
          </div>
          <p className="mt-1 text-xs text-muted">
            Tạo lúc: {formatVietnamDateTime(detail.created_at)}
            {detail.reviewed_at ? (
              <span> · Duyệt lúc: {formatVietnamDateTime(detail.reviewed_at)}</span>
            ) : null}
            {detail.resolved_at ? (
              <span> · Hoàn tất lúc: {formatVietnamDateTime(detail.resolved_at)}</span>
            ) : null}
          </p>
        </div>
      </header>

      {actionError ? <div className="feedback-error">{actionError}</div> : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        {/* Left Column: Cards 1 & 2 */}
        <div className="space-y-6">
          {/* Card 1: Customer & Refund Bank Account Info */}
          <article className="admin-panel">
            <div className="flex items-center gap-3 border-b border-line pb-3">
              <Icon className="text-moss" name="users" />
              <h2 className="font-semibold text-ink">Thông tin Khách hàng &amp; Tài khoản Hoàn tiền</h2>
            </div>

            <div className="mt-4 grid gap-6 sm:grid-cols-2">
              {/* Customer contact */}
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-xs text-muted">Khách hàng</p>
                  <p className="font-semibold text-ink">
                    {detail.customer_name ||
                      detail.bank_info?.bank_account_holder ||
                      "Khách hàng"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Số điện thoại</p>
                  <p className="font-medium text-ink">
                    {detail.customer_phone ? (
                      <a
                        className="text-accent hover:underline"
                        href={`tel:${detail.customer_phone}`}
                      >
                        {detail.customer_phone}
                      </a>
                    ) : (
                      "—"
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Email</p>
                  <p className="font-medium text-ink">
                    {detail.customer_email ? (
                      <a
                        className="text-accent hover:underline"
                        href={`mailto:${detail.customer_email}`}
                      >
                        {detail.customer_email}
                      </a>
                    ) : (
                      "—"
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Đơn hàng liên kết</p>
                  <Link
                    className="inline-flex items-center gap-1 font-mono font-semibold text-accent hover:underline"
                    href={`/admin/orders/${detail.order_number}`}
                  >
                    {detail.order_number}
                    <Icon name="chevron-right" size={14} />
                  </Link>
                </div>
              </div>

              {/* Bank Transfer Details (Card for accounting) */}
              <div className="rounded-2xl border border-line bg-paper p-4">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted">
                  <Icon name="shield" size={14} />
                  Tài khoản nhận tiền hoàn
                </div>
                {detail.bank_info ? (
                  <dl className="mt-3 space-y-2 text-sm">
                    <div>
                      <dt className="text-xs text-muted">Ngân hàng</dt>
                      <dd className="font-semibold text-ink">{detail.bank_info.bank_name}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Số tài khoản</dt>
                      <dd className="font-mono text-base font-bold text-accent">
                        {detail.bank_info.bank_account_number}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Chủ tài khoản</dt>
                      <dd className="font-semibold uppercase text-ink">
                        {detail.bank_info.bank_account_holder}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p className="mt-3 text-xs text-muted">
                    Không có thông tin tài khoản ngân hàng được ghi nhận.
                  </p>
                )}
              </div>
            </div>

            {/* Customer Reason & Evidence Images */}
            <div className="mt-6 border-t border-line pt-4 space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Lý do yêu cầu đổi trả từ khách hàng
                </p>
                <blockquote className="mt-2 rounded-xl border border-line bg-paper p-3.5 text-sm leading-6 text-ink">
                  {detail.customer_reason || "Khách hàng không cung cấp lý do cụ thể."}
                </blockquote>
              </div>

              {/* Image previews */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Hình ảnh bằng chứng đính kèm ({detail.image_urls?.length || 0})
                </p>
                {detail.image_urls && detail.image_urls.length > 0 ? (
                  <div className="mt-2.5 flex flex-wrap gap-3">
                    {detail.image_urls.map((imgUrl, idx) => (
                      <button
                        className="group relative h-20 w-20 overflow-hidden rounded-xl border border-line bg-sand transition hover:ring-2 hover:ring-accent"
                        key={`${imgUrl}-${idx}`}
                        onClick={() => setPreviewImage(imgUrl)}
                        title="Bấm để phóng to hình ảnh"
                        type="button"
                      >
                        <Image
                          alt={`Bằng chứng ${idx + 1}`}
                          className="object-cover transition group-hover:scale-105"
                          fill
                          sizes="80px"
                          src={imgUrl}
                          unoptimized
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-ink/30 opacity-0 transition group-hover:opacity-100">
                          <Icon className="text-paper" name="search" size={16} />
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="mt-1 text-xs text-muted">Không có ảnh bằng chứng đính kèm.</p>
                )}
              </div>
            </div>
          </article>

          {/* Card 2: Items Table & Inspection Form */}
          <article className="admin-panel">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-3">
                <Icon className="text-moss" name="package" />
                <h2 className="font-semibold text-ink">
                  Sản phẩm đổi trả &amp; {isGoodsReceived ? "Kiểm định chất lượng" : "Kết quả kiểm định"}
                </h2>
              </div>
              <span className="text-xs text-muted">{detail.items.length} mặt hàng</span>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-line text-xs font-semibold uppercase text-muted">
                    <th className="pb-3 pr-4">Sản phẩm</th>
                    <th className="pb-3 px-3 text-center">SL</th>
                    <th className="pb-3 px-3 text-right">Đơn giá hoàn</th>
                    <th className="pb-3 px-3 text-right">Tổng tiền hoàn</th>
                    <th className="pb-3 pl-4 text-center">
                      {isGoodsReceived ? "Kiểm định chất lượng" : "Trạng thái kiểm định"}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {detail.items.map((item) => {
                    const proratedUnitPrice =
                      item.quantity > 0
                        ? Math.round(item.refund_amount_vnd / item.quantity)
                        : 0;

                    const itemInspection =
                      inspectionMap[item.return_item_id] ??
                      (item.inspection_status === "failed" ? "failed" : "passed");

                    return (
                      <tr key={item.return_item_id}>
                        <td className="py-4 pr-4">
                          <p className="font-semibold text-ink">
                            {item.product_name || "Sản phẩm"}
                          </p>
                          <p className="mt-0.5 text-xs text-muted">
                            SKU: <span className="font-mono">{item.sku || "—"}</span>
                            {item.variant_title ? ` · Phân loại: ${item.variant_title}` : ""}
                          </p>
                        </td>
                        <td className="py-4 px-3 text-center font-medium">
                          {item.quantity}
                        </td>
                        <td className="py-4 px-3 text-right font-medium text-muted">
                          {formatVnd(proratedUnitPrice)}
                        </td>
                        <td className="py-4 px-3 text-right font-semibold text-ink">
                          {formatVnd(item.refund_amount_vnd)}
                        </td>
                        <td className="py-4 pl-4 text-center">
                          {isGoodsReceived ? (
                            /* Radio choices during goods_received inspection */
                            <div className="inline-flex items-center gap-2 rounded-xl border border-line bg-paper p-1">
                              <button
                                className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                                  itemInspection === "passed"
                                    ? "bg-emerald-600 text-white shadow-sm"
                                    : "text-muted hover:text-ink"
                                }`}
                                onClick={() =>
                                  setInspectionMap((prev) => ({
                                    ...prev,
                                    [item.return_item_id]: "passed",
                                  }))
                                }
                                type="button"
                              >
                                <Icon name="check" size={13} />
                                <span>Đạt chuẩn</span>
                              </button>
                              <button
                                className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                                  itemInspection === "failed"
                                    ? "bg-rose-600 text-white shadow-sm"
                                    : "text-muted hover:text-ink"
                                }`}
                                onClick={() =>
                                  setInspectionMap((prev) => ({
                                    ...prev,
                                    [item.return_item_id]: "failed",
                                  }))
                                }
                                type="button"
                              >
                                <Icon name="close" size={13} />
                                <span>Không đạt</span>
                              </button>
                            </div>
                          ) : (
                            /* Read-only status when not inspecting */
                            <div>
                              {item.inspection_status === "passed" ? (
                                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                                  <Icon name="check" size={12} />
                                  Đạt chuẩn
                                </span>
                              ) : item.inspection_status === "failed" ? (
                                <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/25 bg-rose-500/10 px-2.5 py-0.5 text-xs font-semibold text-rose-700 dark:text-rose-400">
                                  <Icon name="close" size={12} />
                                  Không đạt
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 rounded-full border border-line bg-paper px-2.5 py-0.5 text-xs font-medium text-muted">
                                  Chờ kiểm định
                                </span>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Inspection Live Summary Calculation (active when goods_received) */}
            {isGoodsReceived ? (
              <div className="mt-4 rounded-2xl border border-line bg-paper p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                    Tính toán hoàn tiền sau kiểm định
                  </span>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                      ✓ {passedCount} món đạt (Nhập kho)
                    </span>
                    <span className="font-semibold text-rose-600 dark:text-rose-400">
                      ✕ {failedCount} món không đạt
                    </span>
                  </div>
                </div>
                <dl className="mt-3 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-muted">Tổng yêu cầu ban đầu:</dt>
                    <dd>{formatVnd(detail.total_refund_amount_vnd)}</dd>
                  </div>
                  <div className="flex justify-between text-base font-bold text-ink border-t border-line pt-2">
                    <dt>Số tiền giải ngân thực tế:</dt>
                    <dd className="text-accent">{formatVnd(liveRefundAmount)}</dd>
                  </div>
                </dl>
              </div>
            ) : null}
          </article>
        </div>

        {/* Right Column: Card 3 Action Controls */}
        <aside className="space-y-6">
          <article className="admin-panel">
            <div className="flex items-center gap-3 border-b border-line pb-3">
              <Icon className="text-moss" name="shield" />
              <h2 className="font-semibold text-ink">Thao tác xử lý</h2>
            </div>

            {/* Action controls based on status */}
            <div className="mt-4 space-y-4">
              {/* STATUS: pending_review */}
              {detail.status === "pending_review" ? (
                <div className="space-y-3">
                  <p className="text-xs leading-5 text-muted">
                    Yêu cầu đổi trả mới được gửi. Vui lòng xem xét lý do và hình ảnh bằng chứng trước khi duyệt.
                  </p>
                  <label className="field-label" htmlFor="admin-review-note">
                    Ghi chú của quản trị viên (tùy chọn)
                    <input
                      className="admin-input mt-1 w-full"
                      id="admin-review-note"
                      onChange={(e) => setAdminNote(e.target.value)}
                      placeholder="Ghi chú phản hồi cho khách..."
                      type="text"
                      value={adminNote}
                    />
                  </label>
                  <div className="flex flex-col gap-2 pt-2">
                    <button
                      className="button-primary w-full justify-center"
                      disabled={busy}
                      onClick={() => void handleApprove()}
                      type="button"
                    >
                      <Icon name="check" size={16} />
                      {busy ? "Đang xử lý…" : "Duyệt yêu cầu"}
                    </button>
                    <button
                      className="button-danger w-full justify-center"
                      disabled={busy}
                      onClick={() => {
                        setActionError(null);
                        setIsRejectOpen(true);
                      }}
                      type="button"
                    >
                      <Icon name="close" size={16} />
                      Từ chối yêu cầu
                    </button>
                  </div>
                </div>
              ) : null}

              {/* STATUS: approved */}
              {detail.status === "approved" ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-accent/20 bg-accent/5 p-3 text-xs text-accent">
                    <p className="font-semibold">Yêu cầu đã được phê duyệt</p>
                    <p className="mt-1 text-muted">
                      Đang chờ khách gửi kiện hàng về kho. Khi nhận được hàng tại kho, bấm xác nhận để tiến hành kiểm định.
                    </p>
                  </div>
                  <button
                    className="button-primary w-full justify-center"
                    disabled={busy}
                    onClick={() => void handleReceive()}
                    type="button"
                  >
                    <Icon name="package" size={16} />
                    {busy ? "Đang xử lý…" : "Xác nhận đã nhận hàng về kho"}
                  </button>
                </div>
              ) : null}

              {/* STATUS: goods_received */}
              {detail.status === "goods_received" ? (
                <div className="space-y-4">
                  <div className="rounded-xl border border-sky-500/20 bg-sky-500/5 p-3 text-xs text-sky-700 dark:text-sky-300">
                    <p className="font-semibold">Hàng đã về kho</p>
                    <p className="mt-1 text-muted">
                      Vui lòng kiểm tra từng sản phẩm ở bảng bên trái (Đạt chuẩn / Không đạt) và xác nhận giải ngân số tiền hoàn.
                    </p>
                  </div>

                  <label className="field-label" htmlFor="admin-inspect-note">
                    Ghi chú kiểm định &amp; giải ngân
                    <textarea
                      className="admin-input mt-1 w-full"
                      id="admin-inspect-note"
                      onChange={(e) => setAdminNote(e.target.value)}
                      placeholder="Ghi chú kết quả kiểm tra hoặc mã giao dịch hoàn tiền..."
                      rows={3}
                      value={adminNote}
                    />
                  </label>

                  <div className="rounded-xl border border-line bg-paper p-3 text-xs">
                    <div className="flex justify-between font-medium">
                      <span>Số tiền sẽ giải ngân:</span>
                      <strong className="text-sm font-bold text-accent">
                        {formatVnd(liveRefundAmount)}
                      </strong>
                    </div>
                  </div>

                  <button
                    className="button-primary w-full justify-center"
                    disabled={busy}
                    onClick={() => void handleInspectAndResolve()}
                    type="button"
                  >
                    <Icon name="check" size={16} />
                    {busy ? "Đang giải ngân…" : "Xác nhận kiểm định & Giải ngân hoàn tiền"}
                  </button>
                </div>
              ) : null}

              {/* STATUS: completed */}
              {detail.status === "completed" ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-emerald-800 dark:text-emerald-300">
                    <div className="flex items-center gap-2 font-semibold text-sm">
                      <Icon name="check" size={18} />
                      Đã hoàn tất quy trình
                    </div>
                    <p className="mt-2 text-xs leading-5">
                      Kiểm định đã hoàn thành và số tiền{" "}
                      <strong>{formatVnd(detail.total_refund_amount_vnd)}</strong> đã được ghi nhận hoàn trả cho khách.
                    </p>
                    {detail.resolved_at ? (
                      <p className="mt-1 text-xs text-muted">
                        Thời gian: {formatVietnamDateTime(detail.resolved_at)}
                      </p>
                    ) : null}
                  </div>
                  {detail.admin_note ? (
                    <div className="rounded-xl border border-line bg-paper p-3 text-xs">
                      <p className="font-semibold text-muted">Ghi chú quản trị viên:</p>
                      <p className="mt-1 text-ink">{detail.admin_note}</p>
                    </div>
                  ) : null}
                </div>
              ) : null}

              {/* STATUS: rejected */}
              {detail.status === "rejected" ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-800 dark:text-rose-300">
                    <div className="flex items-center gap-2 font-semibold text-sm">
                      <Icon name="close" size={18} />
                      Yêu cầu đã bị từ chối
                    </div>
                    {detail.admin_note ? (
                      <div className="mt-2 text-xs">
                        <p className="font-semibold">Lý do từ chối:</p>
                        <p className="mt-1 text-ink">{detail.admin_note}</p>
                      </div>
                    ) : null}
                    {detail.reviewed_at ? (
                      <p className="mt-2 text-xs text-muted">
                        Thời gian: {formatVietnamDateTime(detail.reviewed_at)}
                      </p>
                    ) : null}
                  </div>
                </div>
              ) : null}

              {/* STATUS: cancelled */}
              {detail.status === "cancelled" ? (
                <div className="rounded-xl border border-line bg-paper p-4 text-muted">
                  <div className="flex items-center gap-2 font-semibold text-sm text-ink">
                    <Icon name="close" size={18} />
                    Khách hàng đã hủy yêu cầu
                  </div>
                  <p className="mt-2 text-xs leading-5">
                    Yêu cầu đổi trả này đã bị người mua chủ động hủy bỏ. Không cần thao tác thêm.
                  </p>
                </div>
              ) : null}
            </div>
          </article>
        </aside>
      </div>

      {/* Rejection Modal */}
      <AdminModal
        busy={busy}
        description="Vui lòng cung cấp lý do từ chối yêu cầu đổi trả này. Lý do sẽ được thông báo đến khách hàng."
        onClose={() => setIsRejectOpen(false)}
        open={isRejectOpen}
        title={`Từ chối yêu cầu ${detail.return_code}`}
      >
        <div className="space-y-4">
          {actionError ? <div className="feedback-error">{actionError}</div> : null}
          <label className="field-label" htmlFor="reject-reason-input">
            Lý do từ chối <span className="text-danger">*</span>
            <textarea
              autoFocus
              className="admin-input mt-1 w-full"
              id="reject-reason-input"
              maxLength={1000}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Nhập lý do chi tiết..."
              rows={4}
              value={rejectReason}
            />
          </label>
          <div className="flex justify-end gap-3 pt-2">
            <button
              className="button-secondary"
              disabled={busy}
              onClick={() => setIsRejectOpen(false)}
              type="button"
            >
              Hủy
            </button>
            <button
              className="button-danger"
              disabled={busy || !rejectReason.trim()}
              onClick={() => void handleReject()}
              type="button"
            >
              {busy ? "Đang xử lý…" : "Xác nhận từ chối"}
            </button>
          </div>
        </div>
      </AdminModal>

      {/* Image Preview Modal */}
      {previewImage ? (
        <AdminModal
          busy={false}
          onClose={() => setPreviewImage(null)}
          open={Boolean(previewImage)}
          title="Bằng chứng đổi trả"
        >
          <div className="flex flex-col items-center">
            <div className="relative max-h-[70vh] w-full min-h-[300px]">
              <Image
                alt="Ảnh bằng chứng kích thước đầy đủ"
                className="object-contain"
                fill
                sizes="(max-width: 768px) 100vw, 768px"
                src={previewImage}
                unoptimized
              />
            </div>
            <div className="mt-4 flex w-full justify-end">
              <button
                className="button-secondary"
                onClick={() => setPreviewImage(null)}
                type="button"
              >
                Đóng
              </button>
            </div>
          </div>
        </AdminModal>
      ) : null}
    </div>
  );
}
