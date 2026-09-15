"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";
import { ApiError, formatVnd } from "@/lib/api";

interface PosItem {
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  quantity: number;
}

export default function PosPage() {
  const { customer } = useAuth();
  const router = useRouter();
  const [searchCode, setSearchCode] = useState("");
  const [searchResult, setSearchResult] = useState<any>(null);
  const [quantity, setQuantity] = useState(1);
  const [cart, setCart] = useState<PosItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchProduct = useCallback(async () => {
    if (!searchCode.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/v1/pos/products?store_id=1&search=${encodeURIComponent(searchCode.trim())}`,
        { credentials: "include" }
      );
      if (!response.ok) throw new ApiError("Không tìm thấy sản phẩm", response.status);
      const results = await response.json();
      setSearchResult(results[0] || null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lỗi tìm kiếm");
    } finally {
      setSearching(false);
    }
  }, [searchCode]);

  const addToCart = useCallback(() => {
    if (!searchResult) return;
    setCart((prev) => {
      const existing = prev.find((i) => i.variant_id === searchResult.variant_id);
      if (existing) {
        return prev.map((i) =>
          i.variant_id === searchResult.variant_id
            ? { ...i, quantity: i.quantity + quantity }
            : i
        );
      }
      return [...prev, { ...searchResult, quantity }];
    });
    setSearchCode("");
    setSearchResult(null);
    setQuantity(1);
  }, [searchResult, quantity]);

  const removeFromCart = useCallback((variantId: number) => {
    setCart((prev) => prev.filter((i) => i.variant_id !== variantId));
  }, []);

  const total = cart.reduce((sum, item) => sum + item.price_vnd * item.quantity, 0);

  const submitTransaction = useCallback(async () => {
    if (cart.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/pos/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          store_id: 1,
          items: cart.map((i) => ({ variant_id: i.variant_id, quantity: i.quantity })),
          payment_method: "cash",
          amount_received_vnd: total,
        }),
      });
      if (!response.ok) throw new ApiError("Tạo đơn thất bại", response.status);
      const result = await response.json();
      alert(`Đơn ${result.order_number} đã tạo thành công!`);
      setCart([]);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lỗi tạo đơn");
    } finally {
      setSubmitting(false);
    }
  }, [cart, total, router]);

  return (
    <main className="page-shell">
      <header>
        <h1 className="page-heading">Bán hàng tại quầy</h1>
        <p className="mt-2 text-muted">Store: {customer?.display_name || "N/A"}</p>
      </header>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_400px]">
        <section className="surface-card p-5">
          <h2 className="font-semibold">Nhập sản phẩm</h2>
          <div className="mt-4 flex gap-2">
            <input
              className="form-control flex-1"
              placeholder="Nhập mã sản phẩm (SKU)"
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchProduct()}
            />
            <button className="button-primary" onClick={searchProduct} disabled={searching}>
              {searching ? "Đang tìm..." : "Tìm"}
            </button>
          </div>

          {searchResult && (
            <div className="mt-4 rounded-xl border p-4">
              <p className="font-medium">{searchResult.product_name}</p>
              <p className="text-sm text-muted">
                SKU: {searchResult.sku} | Size: {searchResult.size_code} | Màu: {searchResult.color_code}
              </p>
              <p className="text-sm text-muted">
                Giá: {formatVnd(searchResult.price_vnd)} | Tồn kho: {searchResult.store_stock}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <input
                  className="form-control w-20"
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                />
                <button className="button-primary" onClick={addToCart}>Thêm vào giỏ</button>
              </div>
            </div>
          )}
        </section>

        <section className="surface-card p-5">
          <h2 className="font-semibold">Giỏ hàng</h2>
          {cart.length === 0 ? (
            <p className="mt-4 text-muted">Chưa có sản phẩm</p>
          ) : (
            <div className="mt-4 space-y-3">
              {cart.map((item) => (
                <div key={item.variant_id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <p className="text-sm">{item.product_name}</p>
                    <p className="text-xs text-muted">
                      {item.sku} | {item.quantity} x {formatVnd(item.price_vnd)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>{formatVnd(item.price_vnd * item.quantity)}</span>
                    <button className="text-danger" onClick={() => removeFromCart(item.variant_id)}>
                      <Icon name="trash" size={16} />
                    </button>
                  </div>
                </div>
              ))}
              <div className="border-t pt-3">
                <div className="flex justify-between font-semibold">
                  <span>Tổng cộng</span>
                  <span>{formatVnd(total)}</span>
                </div>
              </div>
            </div>
          )}

          {error && <p className="feedback-error mt-4">{error}</p>}

          <button
            className="button-accent mt-4 w-full"
            onClick={submitTransaction}
            disabled={submitting || cart.length === 0}
          >
            {submitting ? "Đang xử lý..." : "Thanh toán"}
          </button>
        </section>
      </div>
    </main>
  );
}
