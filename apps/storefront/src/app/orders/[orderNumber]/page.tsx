"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { OrderStatusBadge, orderStatusLabel } from "@/components/OrderStatusBadge";
import { ApiError, formatVnd, getOrder, type OrderDetail } from "@/lib/api";

const dateFormatter = new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium",
  timeStyle: "short",
});

const PAYMENT_STATUS_LABEL: Record<string, string> = {
  succeeded: "Thành công",
  failed: "Thất bại",
};

const TRANSITION_SOURCE_LABEL: Record<string, string> = {
  checkout: "Hệ thống checkout",
  admin: "Quản trị viên",
  system: "Hệ thống",
};

export default function OrderDetailPage() {
  const params = useParams<{ orderNumber: string }>();
  const orderNumber = params.orderNumber;
  const router = useRouter();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderNumber) return;
    getOrder(orderNumber)
      .then(setOrder)
      .catch((requestError) => {
        if (requestError instanceof ApiError && requestError.status === 401) {
          router.push(`/login?returnTo=/orders/${orderNumber}`);
          return;
        }
        setError("Không tìm thấy đơn hàng");
      });
  }, [orderNumber, router]);

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <div className="rounded-3xl border border-accent/20 bg-accent/10 p-8 text-center">
          <p className="font-medium text-accent">{error}</p>
          <Link className="mt-5 inline-flex rounded-full bg-ink px-5 py-2.5 text-sm text-paper" href="/orders">
            Quay lại đơn hàng
          </Link>
        </div>
      </main>
    );
  }

  if (!order) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-14">
        <div className="animate-pulse rounded-3xl border border-ink/10 bg-white/70 p-8">
          <div className="h-4 w-28 rounded-full bg-ink/10" />
          <div className="mt-5 h-9 w-72 max-w-full rounded-full bg-ink/10" />
          <div className="mt-8 h-48 rounded-2xl bg-ink/5" />
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-12 sm:py-16">
      <Link className="inline-flex items-center gap-2 text-sm font-medium text-ink/60 transition hover:text-accent" href="/orders">
        <span aria-hidden="true">←</span> Danh sách đơn hàng
      </Link>

      <header className="mt-5 rounded-3xl border border-ink/10 bg-white/80 p-6 shadow-[0_14px_40px_rgba(19,35,31,0.07)] sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">Chi tiết đơn hàng</p>
            <h1 className="mt-3 break-all text-2xl font-semibold tracking-tight sm:text-4xl">{order.order_number}</h1>
            <p className="mt-2 text-sm text-ink/55">Đặt lúc {dateFormatter.format(new Date(order.created_at))}</p>
          </div>
          <OrderStatusBadge status={order.status} />
        </div>
      </header>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(18rem,0.55fr)]">
        <section className="rounded-3xl border border-ink/10 bg-white/75 p-5 sm:p-7">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold">Sản phẩm</h2>
            <span className="rounded-full bg-ink/5 px-3 py-1 text-xs font-medium text-ink/60">
              {order.items.length} dòng sản phẩm
            </span>
          </div>
          <ul className="mt-5 space-y-3">
            {order.items.map((item) => (
              <li key={item.sku} className="rounded-2xl border border-ink/10 bg-paper/65 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="font-medium">{item.product_name}</p>
                    <p className="mt-1 text-sm text-ink/55">
                      SKU {item.sku} · {item.size_code} / {item.color_code}
                    </p>
                    <p className="mt-1 text-sm text-ink/55">
                      {formatVnd(item.unit_price_vnd)} × {item.quantity}
                    </p>
                  </div>
                  <p className="shrink-0 font-semibold">{formatVnd(item.line_total_vnd)}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <aside className="h-fit rounded-3xl border border-ink/10 bg-ink p-6 text-paper shadow-[0_16px_40px_rgba(19,35,31,0.16)] lg:sticky lg:top-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-paper/55">Thanh toán</p>
          <div className="mt-5 space-y-3 text-sm">
            <p className="flex justify-between gap-4 text-paper/70">
              <span>Tạm tính</span>
              <span>{formatVnd(order.subtotal_vnd)}</span>
            </p>
            <p className="flex justify-between gap-4 text-paper/70">
              <span>Vận chuyển</span>
              <span>{formatVnd(order.shipping_fee_vnd)}</span>
            </p>
          </div>
          <div className="mt-5 border-t border-paper/15 pt-5">
            <p className="text-sm text-paper/60">Tổng thanh toán</p>
            <p className="mt-1 text-2xl font-semibold">{formatVnd(order.total_vnd)}</p>
          </div>
        </aside>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <section className="rounded-3xl border border-ink/10 bg-white/75 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">Giao hàng</p>
          <h2 className="mt-3 text-lg font-semibold">{order.receiver_name}</h2>
          <p className="mt-2 text-sm text-ink/60">{order.receiver_phone}</p>
          <p className="mt-3 text-sm leading-6 text-ink/70">{order.shipping_address_text}</p>
        </section>

        {order.payment ? (
          <section className="rounded-3xl border border-ink/10 bg-white/75 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">Giao dịch</p>
                <h2 className="mt-3 text-lg font-semibold">{order.payment.payment_reference}</h2>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${order.payment.status === "succeeded" ? "bg-moss/10 text-moss" : "bg-accent/10 text-accent"}`}>
                {PAYMENT_STATUS_LABEL[order.payment.status] ?? order.payment.status}
              </span>
            </div>
            <p className="mt-3 text-sm text-ink/60">{formatVnd(order.payment.amount_vnd)}</p>
            <p className="mt-1 text-sm text-ink/50">{dateFormatter.format(new Date(order.payment.attempted_at))}</p>
            {order.payment.failure_code ? (
              <p className="mt-3 rounded-xl bg-accent/10 px-3 py-2 text-sm text-accent">Lý do lỗi: {order.payment.failure_code}</p>
            ) : null}
          </section>
        ) : (
          <section className="rounded-3xl border border-dashed border-ink/20 bg-white/45 p-6 text-sm text-ink/55">
            Chưa có thông tin thanh toán.
          </section>
        )}
      </div>

      <section className="mt-6 rounded-3xl border border-ink/10 bg-white/75 p-6 sm:p-7">
        <h2 className="text-lg font-semibold">Lịch sử trạng thái</h2>
        <ol className="mt-5 space-y-5">
          {order.status_history.map((history, index) => (
            <li key={`${history.transitioned_at}-${index}`} className="grid grid-cols-[auto_minmax(0,1fr)] gap-4">
              <div className="mt-1.5 h-3 w-3 rounded-full bg-moss ring-4 ring-moss/10" aria-hidden="true" />
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
                <div>
                  <p className="font-medium">
                    {history.from_status ? `${orderStatusLabel(history.from_status)} → ` : ""}
                    {orderStatusLabel(history.to_status)}
                  </p>
                  <p className="mt-1 text-sm text-ink/50">
                    {TRANSITION_SOURCE_LABEL[history.transition_source] ?? history.transition_source}
                  </p>
                </div>
                <time className="shrink-0 text-sm text-ink/50" dateTime={history.transitioned_at}>
                  {dateFormatter.format(new Date(history.transitioned_at))}
                </time>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
