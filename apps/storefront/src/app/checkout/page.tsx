"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  ApiError,
  checkout,
  formatVnd,
  getCart,
  type Cart,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function CheckoutPage() {
  const { customer, loading: authLoading } = useAuth();
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [receiverName, setReceiverName] = useState("");
  const [receiverPhone, setReceiverPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const idempotencyKey = useRef<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = await getCart();
      setCart(c);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login?returnTo=/checkout");
        return;
      }
      setError("Không tải được giỏ hàng");
    } finally {
      setLoading(false);
    }
  }, [customer, router]);

  useEffect(() => {
    if (authLoading) return;
    if (!customer) {
      router.push("/login?returnTo=/checkout");
      return;
    }
    if (!idempotencyKey.current) {
      idempotencyKey.current = crypto.randomUUID();
    }
    void load();
  }, [authLoading, customer, load, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await checkout(idempotencyKey.current, {
        receiver_name: receiverName.trim(),
        receiver_phone: receiverPhone.trim(),
        shipping_address_text: address.trim(),
      });
      router.push(`/checkout/result/${encodeURIComponent(result.order_number)}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Checkout không thành công");
      setSubmitting(false);
    }
  }

  if (loading || authLoading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <p className="text-ink/60">Đang tải…</p>
      </main>
    );
  }

  if (cart && cart.items.length === 0) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <h1 className="text-3xl font-semibold">Thanh toán</h1>
        <p className="mt-6 text-ink/65">Giỏ hàng trống, không thể thanh toán.</p>
      </main>
    );
  }

  if (cart && cart.items.some((item) => !item.in_stock)) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14">
        <h1 className="text-3xl font-semibold">Thanh toán</h1>
        <p className="mt-6 text-accent">
          Giỏ hàng có sản phẩm hết hàng hoặc đã ngừng bán. Vui lòng quay lại giỏ hàng để điều chỉnh.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-14">
      <h1 className="text-3xl font-semibold">Thanh toán</h1>

      <div className="mt-8 grid grid-cols-1 gap-10 md:grid-cols-[1fr_20rem]">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm">
            Người nhận
            <input
              className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2"
              value={receiverName}
              onChange={(e) => setReceiverName(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm">
            Số điện thoại
            <input
              className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2"
              value={receiverPhone}
              onChange={(e) => setReceiverPhone(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm">
            Địa chỉ giao hàng
            <textarea
              className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2"
              rows={3}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              required
            />
          </label>
          {error ? <p className="text-sm text-accent">{error}</p> : null}
          <button
            className="w-full rounded-full bg-ink px-6 py-3 text-paper disabled:opacity-60"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Đang xử lý…" : "Xác nhận thanh toán"}
          </button>
        </form>

        <aside className="rounded-3xl border border-ink/10 bg-white/60 p-6">
          <h2 className="font-medium">Tóm tắt</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {cart?.items.map((item) => (
              <li key={item.variant_public_id} className="flex justify-between">
                <span className="text-ink/70">
                  {item.product_name} × {item.quantity}
                </span>
                <span>{formatVnd(item.line_total_vnd)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 space-y-1 border-t border-ink/10 pt-4 text-sm">
            <p className="flex justify-between text-ink/70">
              <span>Tạm tính</span>
              <span>{formatVnd(cart?.subtotal_vnd)}</span>
            </p>
            <p className="flex justify-between text-ink/70">
              <span>Vận chuyển</span>
              <span>{formatVnd(cart?.shipping_fee_vnd)}</span>
            </p>
            <p className="flex justify-between text-lg font-semibold">
              <span>Tổng</span>
              <span>{formatVnd(cart?.total_vnd)}</span>
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
