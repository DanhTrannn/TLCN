"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  formatVnd,
  getCart,
  removeCartItem,
  setCartItem,
  type Cart,
} from "@/lib/api";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";

export default function CartPage() {
  const { customer, loading: authLoading } = useAuth();
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setCart(await getCart());
      setError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login?returnTo=/cart");
        return;
      }
      setError("Không tải được giỏ hàng");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (authLoading) return;
    if (!customer) {
      router.push("/login?returnTo=/cart");
      return;
    }
    void refresh();
  }, [authLoading, customer, refresh, router]);

  async function updateQuantity(variantPublicId: string, quantity: number) {
    if (quantity < 1) return;
    setBusy(true);
    setError(null);
    try {
      setCart(await setCartItem(variantPublicId, quantity));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Cập nhật thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function remove(variantPublicId: string) {
    setBusy(true);
    setError(null);
    try {
      setCart(await removeCartItem(variantPublicId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xóa thất bại");
    } finally {
      setBusy(false);
    }
  }

  if (loading || authLoading) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-14">
        <div className="rounded-3xl border border-line bg-surface p-8 shadow-[0_18px_50px_rgba(19,35,31,0.08)]">
          <p className="text-muted">Đang tải giỏ hàng…</p>
        </div>
      </main>
    );
  }

  const items = cart?.items ?? [];
  const subtotal = cart?.subtotal_vnd ?? 0;
  const freeShippingThreshold = cart?.free_shipping_threshold_vnd ?? 0;
  const remainingForFreeShipping = Math.max(0, freeShippingThreshold - subtotal);
  const shippingProgress = freeShippingThreshold > 0
    ? Math.min(100, (subtotal / freeShippingThreshold) * 100)
    : 100;
  const canCheckout = items.length > 0 && items.every((item) => item.in_stock);

  return (
    <main className="mx-auto max-w-6xl px-6 py-12 sm:py-16">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">Đơn hàng của bạn</p>
          <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">Giỏ hàng</h1>
          <p className="mt-2 text-sm text-muted">
            {items.length > 0 ? `${items.length} sản phẩm đang chờ thanh toán` : "Chưa có sản phẩm nào trong giỏ"}
          </p>
        </div>
        {items.length > 0 ? (
          <Link className="text-sm font-semibold text-moss hover:text-accent" href="/products">
            + Tiếp tục mua sắm
          </Link>
        ) : null}
      </header>

      {error ? (
        <div className="mt-6 rounded-2xl border border-accent/30 bg-surface p-4 text-sm font-medium text-accent shadow-sm">
          {error}
        </div>
      ) : null}

      {items.length === 0 ? (
        <section className="mt-8 rounded-3xl border border-line bg-surface p-10 text-center shadow-[0_18px_50px_rgba(19,35,31,0.08)] sm:p-14">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-moss/10 text-moss">
            <Icon name="bag" size={27} />
          </div>
          <h2 className="mt-5 text-xl font-semibold">Giỏ hàng đang trống</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
            Khám phá các sản phẩm phù hợp và thêm vào giỏ để bắt đầu đơn hàng mới.
          </p>
          <Link className="mt-6 inline-flex rounded-full bg-ink px-7 py-3 text-sm font-semibold text-paper" href="/products">
            Khám phá sản phẩm
          </Link>
        </section>
      ) : (
        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <section className="rounded-3xl border border-line bg-surface p-4 shadow-[0_18px_50px_rgba(19,35,31,0.08)] sm:p-6">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <h2 className="text-lg font-semibold">Sản phẩm đã chọn</h2>
              <span className="rounded-full bg-paper px-3 py-1 text-xs font-semibold text-muted">
                {items.length} sản phẩm
              </span>
            </div>

            <ul className="mt-4 space-y-4">
              {items.map((item) => (
                <li
                  key={item.variant_public_id}
                  className="rounded-2xl border border-line bg-paper p-4 transition-shadow hover:shadow-[0_10px_28px_rgba(19,35,31,0.08)] sm:p-5"
                >
                  <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-4 sm:grid-cols-[6rem_minmax(0,1fr)]">
                    <Link
                      className="relative h-24 overflow-hidden rounded-2xl border border-line bg-surface"
                      href={`/products/${item.slug}`}
                    >
                      {item.image_url ? (
                        <Image
                          alt={item.product_name}
                          className="object-cover"
                          fill
                          sizes="96px"
                          src={item.image_url}
                        />
                      ) : (
                        <span className="flex h-full items-center justify-center text-xs text-ink/35">Không có ảnh</span>
                      )}
                    </Link>

                    <div className="min-w-0">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <Link className="font-semibold leading-6 hover:text-accent" href={`/products/${item.slug}`}>
                            {item.product_name}
                          </Link>
                          <p className="mt-1 text-xs text-muted">SKU: {item.sku}</p>
                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink/65">
                            <span className="rounded-full border border-line bg-surface px-3 py-1">Size {item.size_code}</span>
                            <span className="rounded-full border border-line bg-surface px-3 py-1">Màu {item.color_code}</span>
                            <span className={`rounded-full px-3 py-1 font-medium ${item.in_stock ? "bg-moss/10 text-moss" : "bg-accent/10 text-accent"}`}>
                              {item.in_stock ? "Còn hàng" : "Tạm hết hàng"}
                            </span>
                          </div>
                        </div>
                        <p className="shrink-0 text-lg font-semibold">{formatVnd(item.line_total_vnd)}</p>
                      </div>

                      <div className="mt-5 flex flex-wrap items-end justify-between gap-4 border-t border-line pt-4">
                        <div>
                          <p className="mb-2 text-xs font-medium uppercase tracking-[0.14em] text-muted">Số lượng</p>
                          <div className="inline-flex items-center rounded-full border border-line bg-surface p-1">
                            <button
                              aria-label={`Giảm số lượng ${item.product_name}`}
                              className="flex h-11 w-11 items-center justify-center rounded-full text-lg hover:bg-paper disabled:cursor-not-allowed disabled:opacity-35"
                              onClick={() => void updateQuantity(item.variant_public_id, item.quantity - 1)}
                              type="button"
                              disabled={busy || item.quantity <= 1}
                            >
                              −
                            </button>
                            <span className="w-10 text-center text-sm font-semibold">{item.quantity}</span>
                            <button
                              aria-label={`Tăng số lượng ${item.product_name}`}
                              className="flex h-11 w-11 items-center justify-center rounded-full text-lg hover:bg-paper disabled:cursor-not-allowed disabled:opacity-35"
                              onClick={() => void updateQuantity(item.variant_public_id, item.quantity + 1)}
                              type="button"
                              disabled={busy}
                            >
                              +
                            </button>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted">Đơn giá {formatVnd(item.unit_price_vnd)}</p>
                          <button
                            className="mt-2 text-sm font-medium text-muted underline decoration-ink/20 underline-offset-4 hover:text-accent disabled:opacity-50"
                            onClick={() => void remove(item.variant_public_id)}
                            type="button"
                            disabled={busy}
                          >
                            Xóa khỏi giỏ
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <aside className="rounded-3xl bg-ink p-6 text-paper shadow-[0_20px_55px_rgba(19,35,31,0.18)] lg:sticky lg:top-24">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-paper/65">Tóm tắt đơn hàng</p>
            <h2 className="mt-2 text-xl font-semibold">Thanh toán</h2>

            <div className="mt-6 rounded-2xl border border-paper/10 bg-paper/5 p-4">
              <p className="text-sm font-medium">
                {remainingForFreeShipping > 0
                  ? `Mua thêm ${formatVnd(remainingForFreeShipping)} để được miễn phí giao hàng`
                  : "Đơn hàng đã được miễn phí giao hàng"}
              </p>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-paper/15">
                <div className="h-full rounded-full bg-emerald-300" style={{ width: `${shippingProgress}%` }} />
              </div>
            </div>

            <dl className="mt-6 space-y-3 text-sm">
              <div className="flex justify-between gap-4 text-paper/70">
                <dt>Tạm tính</dt>
                <dd>{formatVnd(subtotal)}</dd>
              </div>
              <div className="flex justify-between gap-4 text-paper/70">
                <dt>Phí vận chuyển</dt>
                <dd>{cart?.shipping_fee_vnd === 0 ? "Miễn phí" : formatVnd(cart?.shipping_fee_vnd ?? 0)}</dd>
              </div>
            </dl>

            <div className="mt-5 border-t border-paper/15 pt-5">
              <div className="flex items-end justify-between gap-4">
                <p className="text-sm text-paper/60">Tổng cộng</p>
                <p className="text-2xl font-semibold">{formatVnd(cart?.total_vnd ?? 0)}</p>
              </div>
              <p className="mt-2 text-right text-xs text-paper/65">Đã bao gồm phí vận chuyển</p>
            </div>

            {canCheckout ? (
              <Link
                className="mt-6 flex w-full items-center justify-center rounded-full bg-paper px-6 py-3.5 text-sm font-semibold text-ink transition hover:bg-surface"
                href="/checkout"
              >
                Tiến hành thanh toán
              </Link>
            ) : (
              <div className="mt-6 rounded-2xl border border-accent/35 bg-accent/15 p-4 text-sm leading-6 text-paper">
                Hãy xóa hoặc điều chỉnh sản phẩm hết hàng trước khi thanh toán.
              </div>
            )}

            <p className="mt-4 text-center text-xs leading-5 text-paper/65">
              Coupon khả dụng được chọn ở bước thanh toán.
            </p>
          </aside>
        </div>
      )}
    </main>
  );
}
