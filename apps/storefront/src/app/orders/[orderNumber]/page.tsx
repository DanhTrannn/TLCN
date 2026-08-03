"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { OrderStatusBadge, orderStatusShortLabel } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  cancelCustomerOrder,
  completeCustomerOrder,
  createOrderItemReview,
  getCommerceOrder,
  type CommerceOrderDetail,
  type CommerceOrderItem,
} from "@/lib/commerce";
import { createVietnamDateTimeFormatter, parseApiDateTime } from "@/lib/datetime";

const dateFormatter = createVietnamDateTimeFormatter({
  dateStyle: "medium",
  timeStyle: "short",
});

const timelineTimeFormatter = createVietnamDateTimeFormatter({
  hour: "2-digit",
  minute: "2-digit",
});

const timelineDateFormatter = createVietnamDateTimeFormatter({
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function timelineMarkerClasses(status: string): string {
  if (status === "cancelled" || status === "payment_failed") {
    return "border-danger bg-danger text-white ring-danger/10";
  }
  if (status === "completed") {
    return "border-ink bg-ink text-paper ring-ink/10";
  }
  return "border-moss bg-moss text-white ring-moss/10";
}

function RatingStars({ value }: { value: number }) {
  return (
    <span aria-label={`${value} trên 5 sao`} className="inline-flex gap-0.5 text-warning" role="img">
      {[1, 2, 3, 4, 5].map((star) => <Icon filled={star <= value} key={star} name="star" size={15} />)}
    </span>
  );
}

function ReviewForm({
  orderNumber,
  item,
  onCreated,
}: {
  orderNumber: string;
  item: CommerceOrderItem;
  onCreated: () => Promise<void>;
}) {
  const [rating, setRating] = useState(5);
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (item.review) {
    const labels = {
      pending: "Đang chờ duyệt",
      approved: "Đã hiển thị",
      rejected: "Bị từ chối",
    };
    return (
      <div className="mt-3 rounded-xl bg-surface p-3 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <RatingStars value={item.review.rating} />
          <span className="text-xs font-medium text-muted">{labels[item.review.status]}</span>
        </div>
        {item.review.content ? <p className="mt-1 text-muted">{item.review.content}</p> : null}
        {item.review.moderation_reason ? (
          <p className="mt-2 text-accent">Lý do: {item.review.moderation_reason}</p>
        ) : null}
      </div>
    );
  }

  async function submitReview() {
    setBusy(true);
    setError(null);
    try {
      await createOrderItemReview(orderNumber, item.public_id, {
        rating,
        content: content.trim() || null,
      });
      await onCreated();
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không gửi được đánh giá"
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 rounded-xl border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm">
          Số sao
          <select
            className="form-control ml-2 mt-0 inline-block min-h-11 w-auto py-2"
            value={rating}
            onChange={(event) => setRating(Number(event.target.value))}
          >
            {[5, 4, 3, 2, 1].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <input
          aria-label="Nhận xét đánh giá"
          className="form-control mt-0 min-w-48 flex-1"
          maxLength={2000}
          placeholder="Nhận xét (không bắt buộc)"
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
        <button
          className="button-primary px-4"
          disabled={busy}
          onClick={() => void submitReview()}
          type="button"
        >
          {busy ? "Đang gửi…" : "Gửi đánh giá"}
        </button>
      </div>
      {error ? <p className="mt-2 text-sm text-accent">{error}</p> : null}
    </div>
  );
}

export default function OrderDetailPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const router = useRouter();
  const [order, setOrder] = useState<CommerceOrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("Khách hàng thay đổi nhu cầu");
  const [cancelling, setCancelling] = useState(false);
  const [completing, setCompleting] = useState(false);

  const load = useCallback(async () => {
    if (!orderNumber) return;
    try {
      setOrder(await getCommerceOrder(orderNumber));
      setError(null);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        router.push(`/login?returnTo=/orders/${orderNumber}`);
        return;
      }
      setError("Không tìm thấy đơn hàng");
    }
  }, [orderNumber, router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function cancelOrder() {
    if (!order || cancelReason.trim().length < 3) return;
    setCancelling(true);
    setError(null);
    try {
      await cancelCustomerOrder(order.order_number, cancelReason.trim());
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof ApiError ? requestError.message : "Không hủy được đơn hàng"
      );
    } finally {
      setCancelling(false);
    }
  }

  async function completeOrder() {
    if (!order || order.status !== "confirmed") return;
    setCompleting(true);
    setError(null);
    try {
      await completeCustomerOrder(order.order_number);
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không xác nhận được việc nhận hàng"
      );
    } finally {
      setCompleting(false);
    }
  }

  if (error && !order) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <div className="rounded-3xl border border-accent/20 bg-accent/10 p-8 text-center">
          <p className="font-medium text-accent">{error}</p>
          <Link className="button-primary mt-5" href="/orders">
            Quay lại đơn hàng
          </Link>
        </div>
      </main>
    );
  }

  if (!order) {
    return <main className="mx-auto max-w-5xl px-6 py-14 text-muted">Đang tải…</main>;
  }

  return (
    <main className="mx-auto max-w-5xl px-5 py-10 sm:px-6 sm:py-14">
      <Link className="button-ghost -ml-3" href="/orders">
        <Icon className="rotate-180" name="arrow-right" size={17} />
        Danh sách đơn hàng
      </Link>

      <header className="surface-card mt-4 p-5 sm:p-7">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="eyebrow">Thông tin đơn hàng</p>
            <h1 className="mt-2 break-all text-2xl font-semibold sm:text-3xl">{order.order_number}</h1>
            <p className="mt-2 text-sm text-muted">
              Đặt hàng lúc {dateFormatter.format(parseApiDateTime(order.created_at))}
            </p>
          </div>
          <OrderStatusBadge status={order.status} />
        </div>

        {order.status === "paid" ? (
          <div className="mt-5 border-t border-line pt-5">
            <p className="text-sm font-medium">Bạn có thể hủy đơn trước khi cửa hàng xác nhận.</p>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                aria-label="Lý do hủy đơn"
                className="form-control mt-0 min-w-0 flex-1"
                maxLength={500}
                value={cancelReason}
                onChange={(event) => setCancelReason(event.target.value)}
              />
              <button
                className="button-accent"
                disabled={cancelling || cancelReason.trim().length < 3}
                onClick={() => void cancelOrder()}
                type="button"
              >
                {cancelling ? "Đang hủy…" : "Hủy đơn"}
              </button>
            </div>
          </div>
        ) : null}
        {order.status === "confirmed" ? (
          <div className="mt-5 flex flex-col gap-4 border-t border-line pt-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold">Đơn hàng đang được cửa hàng xử lý.</p>
              <p className="mt-1 text-sm text-muted">Chỉ xác nhận sau khi bạn đã nhận và kiểm tra hàng.</p>
            </div>
            <button
              className="button-primary shrink-0"
              disabled={completing}
              onClick={() => void completeOrder()}
              type="button"
            >
              <Icon name="check" size={17} />
              {completing ? "Đang xác nhận…" : "Đã nhận hàng"}
            </button>
          </div>
        ) : null}
        {error ? <p className="mt-4 text-sm text-accent">{error}</p> : null}
      </header>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_19rem]">
        <section className="surface-flat p-5 sm:p-6">
          <h2 className="text-lg font-semibold">Sản phẩm</h2>
          <ul className="mt-4 space-y-3">
            {order.items.map((item) => (
              <li key={item.public_id} className="rounded-2xl border border-line bg-paper p-3 sm:p-4">
                <div className="flex min-w-0 gap-3 sm:items-center sm:gap-4">
                  <div className="relative flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sand text-muted sm:h-24 sm:w-24">
                    {item.image_url ? (
                      <Image
                        alt={item.product_name}
                        className="object-cover"
                        fill
                        sizes="96px"
                        src={item.image_url}
                      />
                    ) : (
                      <Icon name="package" size={22} />
                    )}
                  </div>
                  <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="font-medium">{item.product_name}</p>
                      <p className="mt-1 text-sm text-muted">
                        {item.sku} · {item.size_code}/{item.color_code} · {formatVnd(item.unit_price_vnd)} × {item.quantity}
                      </p>
                    </div>
                    <p className="shrink-0 font-semibold">{formatVnd(item.line_total_vnd)}</p>
                  </div>
                </div>
                {order.status === "completed" ? (
                  <ReviewForm orderNumber={order.order_number} item={item} onCreated={load} />
                ) : null}
              </li>
            ))}
          </ul>
        </section>

        <aside className="h-fit min-w-0 rounded-3xl bg-ink p-6 text-paper lg:sticky lg:top-24">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-paper/65">Tổng đơn hàng</p>
          <div className="mt-5 space-y-3 text-sm">
            <p className="flex justify-between gap-4 text-paper/70">
              <span>Tạm tính</span><span>{formatVnd(order.subtotal_vnd)}</span>
            </p>
            {order.discount_amount_vnd > 0 ? (
              <p className="flex justify-between gap-4 text-emerald-300">
                <span>Giảm giá {order.coupon_code ? `(${order.coupon_code})` : ""}</span>
                <span>−{formatVnd(order.discount_amount_vnd)}</span>
              </p>
            ) : null}
            <p className="flex justify-between gap-4 text-paper/70">
              <span>Vận chuyển</span><span>{formatVnd(order.shipping_fee_vnd)}</span>
            </p>
          </div>
          <div className="mt-5 border-t border-paper/15 pt-5">
            <p className="text-sm text-paper/60">Tổng thanh toán</p>
            <p className="mt-1 max-w-full text-2xl font-semibold tabular-nums [overflow-wrap:anywhere]">
              {formatVnd(order.total_vnd)}
            </p>
          </div>
          {order.payment ? (
            <p className="mt-4 flex items-center justify-between gap-4 border-t border-paper/15 pt-4 text-sm">
              <span className="text-paper/60">Thanh toán</span>
              <span className="font-medium">
                {order.payment.status === "succeeded" ? "Thành công" : "Thất bại"}
              </span>
            </p>
          ) : null}
          {order.refund ? (
            <div className="mt-5 rounded-2xl bg-paper/10 p-4 text-sm">
              <p className="font-medium">Đã hoàn {formatVnd(order.refund.amount_vnd)}</p>
              <p className="mt-1 text-paper/60">{order.refund.reason}</p>
            </div>
          ) : null}
        </aside>
      </div>

      <section className="surface-flat mt-6 p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-moss/10 text-moss">
            <Icon name="truck" size={19} />
          </span>
          <div>
            <h2 className="font-semibold">Giao đến</h2>
            <p className="mt-2 text-sm font-medium">{order.receiver_name} · {order.receiver_phone}</p>
            <p className="mt-1 text-sm leading-6 text-muted">{order.shipping_address_text}</p>
          </div>
        </div>
      </section>

      <section className="surface-flat mt-6 p-5 sm:p-6">
        <h2 className="text-lg font-semibold">Trạng thái đơn hàng</h2>

        <ol className="mt-4 divide-y divide-line">
          {order.status_history.map((history, index) => {
            const transitionedAt = parseApiDateTime(history.transitioned_at);
            const isLatest = index === order.status_history.length - 1;

            return (
              <li
                key={`${history.transitioned_at}-${index}`}
                className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-4 py-4 first:pt-0 last:pb-0 sm:grid-cols-[5.5rem_minmax(0,1fr)]"
              >
                <div className="text-right">
                  <time
                    className="block text-sm font-semibold text-ink"
                    dateTime={history.transitioned_at}
                  >
                    {timelineTimeFormatter.format(transitionedAt)}
                  </time>
                  <span className="mt-0.5 block text-xs leading-4 text-muted">
                    {timelineDateFormatter.format(transitionedAt)}
                  </span>
                </div>

                <div className="flex min-w-0 items-start gap-3">
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ring-4 ${timelineMarkerClasses(history.to_status)}`}
                    aria-hidden="true"
                  >
                    <Icon name="check" size={12} />
                  </span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{orderStatusShortLabel(history.to_status)}</h3>
                      {isLatest ? (
                        <span className="rounded-full bg-ink px-2.5 py-1 text-[11px] font-semibold text-paper">
                          Hiện tại
                        </span>
                      ) : null}
                    </div>
                    {history.reason ? (
                      <p className="mt-1 text-sm leading-6 text-muted">{history.reason}</p>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </section>
    </main>
  );
}
