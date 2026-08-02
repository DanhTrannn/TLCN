"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd, getOrders, type OrderListItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { createVietnamDateTimeFormatter, parseApiDateTime } from "@/lib/datetime";

const dateFormatter = createVietnamDateTimeFormatter({
  dateStyle: "medium",
  timeStyle: "short",
});

function OrderSkeleton() {
  return (
    <div className="animate-pulse rounded-3xl border border-line bg-surface p-5 sm:p-6">
      <div className="flex items-center justify-between gap-4">
        <div><div className="h-5 w-36 rounded-full bg-ink/10" /><div className="mt-2 h-3 w-44 rounded-full bg-ink/10" /></div>
        <div className="h-7 w-24 rounded-full bg-ink/10" />
      </div>
      <div className="mt-5 flex gap-4 rounded-2xl bg-paper p-3">
        <div className="h-16 w-16 shrink-0 rounded-xl bg-ink/10" />
        <div className="flex-1"><div className="h-4 w-48 max-w-full rounded-full bg-ink/10" /><div className="mt-3 h-3 w-64 max-w-full rounded-full bg-ink/10" /></div>
      </div>
      <div className="mt-5 flex items-center justify-between border-t border-line pt-5">
        <div className="h-7 w-32 rounded-full bg-ink/10" />
        <div className="h-11 w-32 rounded-full bg-ink/10" />
      </div>
    </div>
  );
}

export default function OrdersPage() {
  const { customer, loading: authLoading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<OrderListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (cur: string | null) => {
      setLoading(true);
      setError(null);
      try {
        const response = await getOrders(cur ?? undefined);
        setItems((previous) => (cur ? [...previous, ...response.items] : response.items));
        setCursor(response.next_cursor);
      } catch (requestError) {
        if (requestError instanceof ApiError && requestError.status === 401) {
          router.push("/login?returnTo=/orders");
          return;
        }
        setError("Không tải được đơn hàng. Vui lòng thử lại.");
      } finally {
        setLoading(false);
      }
    },
    [router]
  );

  useEffect(() => {
    if (authLoading) return;
    if (!customer) {
      router.push("/login?returnTo=/orders");
      return;
    }
    void load(null);
  }, [authLoading, customer, load, router]);

  return (
    <main className="mx-auto min-h-[70vh] max-w-5xl px-6 py-12 sm:py-16">
      <header className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Tài khoản</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Đơn hàng của tôi</h1>
        <p className="mt-3 text-sm leading-6 text-muted sm:text-base">
          Theo dõi trạng thái, tổng tiền và xem lại chi tiết những đơn hàng đã đặt.
        </p>
      </header>

      {error ? (
        <div className="mt-8 flex flex-col gap-3 rounded-2xl border border-accent/20 bg-accent/10 px-5 py-4 text-sm text-accent sm:flex-row sm:items-center sm:justify-between">
          <p>{error}</p>
          <button className="font-semibold underline underline-offset-4" onClick={() => void load(null)} type="button">
            Thử lại
          </button>
        </div>
      ) : null}

      {loading && items.length === 0 ? (
        <div className="mt-8 space-y-4" aria-label="Đang tải đơn hàng">
          <OrderSkeleton />
          <OrderSkeleton />
          <OrderSkeleton />
        </div>
      ) : !loading && items.length === 0 ? (
        <section className="mt-8 rounded-3xl border border-dashed border-ink/25 bg-surface px-6 py-12 text-center sm:px-10">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-ink text-paper" aria-hidden="true">
            <Icon name="receipt" size={24} />
          </div>
          <h2 className="mt-5 text-xl font-semibold">Bạn chưa có đơn hàng</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
            Khám phá danh mục sản phẩm và hoàn tất đơn hàng đầu tiên của bạn.
          </p>
          <Link className="mt-6 inline-flex rounded-full bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:bg-moss" href="/products">
            Khám phá sản phẩm
          </Link>
        </section>
      ) : (
        <ul className="mt-8 space-y-5">
          {items.map((order) => {
            const previewItems = order.preview_items ?? [];
            const remainingItems = Math.max(order.item_count - previewItems.length, 0);

            return (
              <li key={order.order_number}>
                <article className="rounded-3xl border border-line bg-surface p-5 shadow-[0_12px_36px_rgba(19,35,31,0.06)] sm:p-6">
                  <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex min-w-0 items-start gap-3">
                      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-moss/10 text-moss" aria-hidden="true">
                        <Icon name="receipt" size={20} />
                      </span>
                      <div className="min-w-0">
                        <h2 className="break-all text-base font-semibold tracking-tight sm:text-lg">{order.order_number}</h2>
                        <p className="mt-1 text-sm text-muted">{dateFormatter.format(parseApiDateTime(order.created_at))}</p>
                      </div>
                    </div>
                    <OrderStatusBadge status={order.status} />
                  </header>

                  <ul className="mt-5 space-y-3" aria-label={`Sản phẩm trong đơn ${order.order_number}`}>
                    {previewItems.map((item) => (
                      <li className="flex min-w-0 gap-3 rounded-2xl border border-line bg-paper p-3 sm:items-center sm:gap-4" key={item.sku}>
                        <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sand text-muted sm:h-20 sm:w-20">
                          {item.image_url ? (
                            <img alt={item.product_name} className="h-full w-full object-cover" loading="lazy" src={item.image_url} />
                          ) : (
                            <Icon name="package" size={21} />
                          )}
                        </div>
                        <div className="flex min-w-0 flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div className="min-w-0">
                            <p className="line-clamp-2 font-semibold text-ink">{item.product_name}</p>
                            <p className="mt-1 text-xs leading-5 text-muted">
                              {item.sku} · Size {item.size_code} · {item.color_code} · SL {item.quantity}
                            </p>
                          </div>
                          <p className="shrink-0 text-sm font-semibold tabular-nums sm:text-right">{formatVnd(item.line_total_vnd)}</p>
                        </div>
                      </li>
                    ))}
                  </ul>

                  {remainingItems > 0 ? (
                    <p className="mt-3 text-sm font-medium text-muted">+ {remainingItems} sản phẩm khác</p>
                  ) : null}

                  <footer className="mt-5 flex flex-col gap-4 border-t border-line pt-5 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted">Tổng thanh toán</p>
                      <p className="mt-1 max-w-full text-xl font-semibold tabular-nums [overflow-wrap:anywhere]">{formatVnd(order.total_vnd)}</p>
                    </div>
                    <Link
                      className="button-secondary group w-full sm:w-auto"
                      href={`/orders/${order.order_number}`}
                    >
                      Xem chi tiết
                      <Icon className="transition group-hover:translate-x-1" name="arrow-right" size={17} />
                    </Link>
                  </footer>
                </article>
              </li>
            );
          })}
        </ul>
      )}

      {cursor ? (
        <div className="mt-9 flex justify-center">
          <button
            className="rounded-full border border-ink/20 bg-surface px-7 py-3 text-sm font-medium shadow-sm transition hover:border-ink/40 hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
            onClick={() => void load(cursor)}
            type="button"
            disabled={loading}
          >
            {loading ? "Đang tải…" : "Tải thêm đơn hàng"}
          </button>
        </div>
      ) : null}
    </main>
  );
}
