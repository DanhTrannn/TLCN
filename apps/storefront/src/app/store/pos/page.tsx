"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/lib/auth";
import { ApiError, formatVnd } from "@/lib/api";
import { apiFetch } from "@/lib/api-client";

interface PosItem {
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  quantity: number;
}

interface SearchResult {
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  store_stock: number;
  global_stock: number;
}

export default function StorePosPage() {
  const { customer } = useAuth();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [searchCode, setSearchCode] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [selectedItem, setSelectedItem] = useState<SearchResult | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [cart, setCart] = useState<PosItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const storeId = customer?.store_id ?? 7;

  const searchProduct = useCallback(async () => {
    if (!searchCode.trim() || !storeId) return;
    setSearching(true);
    setError(null);
    setSelectedItem(null);
    try {
      const results = await apiFetch<SearchResult[]>(
        `/api/v1/pos/products?store_id=${storeId}&search=${encodeURIComponent(searchCode.trim())}`
      );
      setSearchResults(results);
      if (results.length === 1) {
        setSelectedItem(results[0]);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lỗi tìm kiếm");
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, [searchCode, storeId]);

  const addToCart = useCallback(() => {
    if (!selectedItem) return;
    setCart((prev) => {
      const existing = prev.find((i) => i.variant_id === selectedItem.variant_id);
      if (existing) {
        return prev.map((i) =>
          i.variant_id === selectedItem.variant_id
            ? { ...i, quantity: i.quantity + quantity }
            : i
        );
      }
      return [...prev, { ...selectedItem, quantity }];
    });
    setSearchCode("");
    setSearchResults([]);
    setSelectedItem(null);
    setQuantity(1);
    inputRef.current?.focus();
  }, [selectedItem, quantity]);

  const selectFromList = useCallback((item: SearchResult) => {
    setSelectedItem(item);
    setQuantity(1);
  }, []);

  const removeFromCart = useCallback((variantId: number) => {
    setCart((prev) => prev.filter((i) => i.variant_id !== variantId));
  }, []);

  const total = cart.reduce((sum, item) => sum + item.price_vnd * item.quantity, 0);

  const submitTransaction = useCallback(async () => {
    if (cart.length === 0 || !storeId) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await apiFetch<{
        order_number: string;
      }>("/api/v1/pos/transactions", {
        method: "POST",
        body: JSON.stringify({
          store_id: storeId,
          items: cart.map((i) => ({ variant_id: i.variant_id, quantity: i.quantity })),
          payment_method: "cash",
          amount_received_vnd: total,
        }),
      });
      alert(`Đơn ${result.order_number} đã tạo thành công!`);
      setCart([]);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lỗi tạo đơn");
    } finally {
      setSubmitting(false);
    }
  }, [cart, total, storeId, router]);

  if (!storeId) {
    return (
      <div>
        <h1 className="admin-heading">Bán hàng tại quầy</h1>
        <p className="mt-4 text-muted">Vui lòng chọn cửa hàng.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="admin-heading">Bán hàng tại quầy</h1>
      <p className="mt-1 text-sm text-muted">Cửa hàng: {customer?.store_name || "Chưa chọn"}</p>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_400px]">
        <section className="surface-card p-5">
          <h2 className="font-semibold">Tìm sản phẩm</h2>
          <div className="mt-4 flex gap-2">
            <input
              ref={inputRef}
              className="form-control flex-1"
              placeholder="Nhập tên hoặc mã SP (SKU)"
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchProduct()}
            />
            <button className="button-primary" onClick={searchProduct} disabled={searching}>
              {searching ? "Đang tìm..." : "Tìm"}
            </button>
          </div>

          {searchResults.length > 0 && !selectedItem && (
            <div className="mt-4 rounded-xl border divide-y">
              {searchResults.map((item) => (
                <button
                  key={item.variant_id}
                  className="flex w-full items-center justify-between p-3 text-left hover:bg-sand/40 transition"
                  onClick={() => selectFromList(item)}
                >
                  <div>
                    <p className="font-medium">{item.product_name}</p>
                    <p className="text-xs text-muted">
                      {item.sku} | {item.size_code} | {item.color_code}
                    </p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-semibold">{formatVnd(item.price_vnd)}</p>
                    <p className="text-muted">Kho: {item.store_stock}</p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {selectedItem && (
            <div className="mt-4 rounded-xl border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{selectedItem.product_name}</p>
                  <p className="text-sm text-muted">
                    SKU: {selectedItem.sku} | Size: {selectedItem.size_code} | Màu: {selectedItem.color_code}
                  </p>
                  <p className="text-sm text-muted">
                    Giá: {formatVnd(selectedItem.price_vnd)} | Tồn kho: {selectedItem.store_stock}
                  </p>
                </div>
                <button className="text-muted hover:text-ink" onClick={() => { setSelectedItem(null); setSearchResults([]); }}>
                  <Icon name="close" size={16} />
                </button>
              </div>
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

          {searchResults.length === 0 && searchCode && !searching && (
            <p className="mt-4 text-muted">Không tìm thấy sản phẩm nào.</p>
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
    </div>
  );
}
