"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { ApiError, formatVnd, getOrders, type OrderListItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const dateFormatter = new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium",
  timeStyle: "short",
});

function OrderSkeleton() {
  return (
    <div className="animate-pulse rounded-3xl border border-ink/10 bg-white/70 p-5 sm:p-6">
      <div className="h-5 w-36 rounded-full bg-ink/10" />
      <div className="mt-4 h-4 w-64 max-w-full rounded-full bg-ink/10" />
      <div className="mt-6 h-7 w-28 rounded-full bg-ink/10 sm:ml-auto" />
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
        <p className="mt-3 text-sm leading-6 text-ink/60 sm:text-base">
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
        <section className="mt-8 rounded-3xl border border-dashed border-ink/25 bg-white/50 px-6 py-12 text-center sm:px-10">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-ink text-2xl text-paper" aria-hidden="true">
            ◇
          </div>
          <h2 className="mt-5 text-xl font-semibold">Bạn chưa có đơn hàng</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink/60">
            Khám phá danh mục sản phẩm và hoàn tất đơn hàng đầu tiên của bạn.
          </p>
          <Link className="mt-6 inline-flex rounded-full bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:bg-moss" href="/products">
            Khám phá sản phẩm
          </Link>
        </section>
      ) : (
        <ul className="mt-8 space-y-4">
          {items.map((order) => (
            <li key={order.order_number}>
              <Link
                href={`/orders/${order.order_number}`}
                className="group block rounded-3xl border border-ink/10 bg-white/80 p-5 shadow-[0_12px_36px_rgba(19,35,31,0.06)] transition duration-200 hover:-translate-y-0.5 hover:border-accent/35 hover:bg-white hover:shadow-[0_18px_48px_rgba(19,35,31,0.11)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 focus-visible:ring-offset-4 focus-visible:ring-offset-paper sm:p-6"
              >
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex min-w-0 items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-moss/10 font-semibold text-moss" aria-hidden="true">
                      #
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <h2 className="truncate text-base font-semibold tracking-tight sm:text-lg">{order.order_number}</h2>
                        <OrderStatusBadge status={order.status} />
                      </div>
                      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-sm text-ink/55">
                        <span>{dateFormatter.format(new Date(order.created_at))}</span>
                        <span className="hidden sm:inline" aria-hidden="true">•</span>
                        <span>{order.item_count} sản phẩm</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-end justify-between gap-6 border-t border-ink/10 pt-4 sm:block sm:border-0 sm:pt-0 sm:text-right">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-ink/45">Tổng thanh toán</p>
                      <p className="mt-1 text-xl font-semibold text-ink">{formatVnd(order.total_vnd)}</p>
                    </div>
                    <span className="text-sm font-semibold text-accent transition group-hover:translate-x-1 sm:mt-3 sm:inline-flex">
                      Xem chi tiết →
                    </span>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {cursor ? (
        <div className="mt-9 flex justify-center">
          <button
            className="rounded-full border border-ink/20 bg-white/70 px-7 py-3 text-sm font-medium shadow-sm transition hover:border-ink/40 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
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
