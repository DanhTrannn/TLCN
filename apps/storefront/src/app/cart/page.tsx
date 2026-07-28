"use client";

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
      <main className="mx-auto max-w-4xl px-6 py-14">
        <p className="text-ink/60">Đang tải…</p>
      </main>
    );
  }

  const items = cart?.items ?? [];

  return (
    <main className="mx-auto max-w-4xl px-6 py-14">
      <h1 className="text-3xl font-semibold">Giỏ hàng</h1>
      {error ? <p className="mt-4 text-sm text-accent">{error}</p> : null}

      {items.length === 0 ? (
        <div className="mt-8 rounded-3xl border border-dashed border-ink/25 p-10 text-ink/65">
          Giỏ hàng trống.{" "}
          <Link className="text-accent" href="/products">
            Tiếp tục mua sắm
          </Link>
        </div>
      ) : (
        <>
          <ul className="mt-8 divide-y divide-ink/10">
            {items.map((item) => (
              <li key={item.variant_public_id} className="flex items-center gap-4 py-4">
                <div className="h-16 w-16 overflow-hidden rounded-xl bg-ink/5">
                  {item.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={item.image_url} alt={item.product_name} className="h-full w-full object-cover" />
                  ) : null}
                </div>
                <div className="flex-1">
                  <p className="font-medium">{item.product_name}</p>
                  <p className="text-sm text-ink/60">
                    {item.size_code} / {item.color_code}
                  </p>
                  <p className="text-sm text-ink/60">{formatVnd(item.unit_price_vnd)}</p>
                  {item.in_stock ? null : <p className="text-xs text-accent">Tạm hết hàng</p>}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    className="h-8 w-8 rounded-full border border-ink/20 disabled:opacity-50"
                    onClick={() => updateQuantity(item.variant_public_id, item.quantity - 1)}
                    type="button"
                    disabled={busy || item.quantity <= 1}
                  >
                    −
                  </button>
                  <span className="w-8 text-center">{item.quantity}</span>
                  <button
                    className="h-8 w-8 rounded-full border border-ink/20 disabled:opacity-50"
                    onClick={() => updateQuantity(item.variant_public_id, item.quantity + 1)}
                    type="button"
                    disabled={busy}
                  >
                    +
                  </button>
                </div>
                <div className="w-28 text-right font-medium">{formatVnd(item.line_total_vnd)}</div>
                <button
                  className="text-sm text-ink/50 hover:text-accent disabled:opacity-50"
                  onClick={() => remove(item.variant_public_id)}
                  type="button"
                  disabled={busy}
                >
                  Xóa
                </button>
              </li>
            ))}
          </ul>

          <div className="mt-8 space-y-2 border-t border-ink/10 pt-6 text-right">
            <p className="text-ink/70">Tạm tính: {formatVnd(cart?.subtotal_vnd)}</p>
            <p className="text-ink/70">Phí vận chuyển: {formatVnd(cart?.shipping_fee_vnd)}</p>
            <p className="text-xl font-semibold">Tổng: {formatVnd(cart?.total_vnd)}</p>
            {items.every((item) => item.in_stock) ? (
              <Link
                className="mt-4 inline-block rounded-full bg-ink px-8 py-3 text-paper"
                href="/checkout"
              >
                Thanh toán
              </Link>
            ) : (
              <p className="mt-4 text-sm text-accent">
                Hãy xóa hoặc điều chỉnh các sản phẩm không còn khả dụng trước khi thanh toán.
              </p>
            )}
          </div>
        </>
      )}
    </main>
  );
}
