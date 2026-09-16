"use client";

import { useMemo, useState } from "react";
import { useEffect } from "react";

import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/api";

interface InventoryItem {
  store_id: number;
  store_name: string;
  variant_id: number;
  variant_sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  on_hand: number;
  opening_on_hand: number;
}

export default function StoreInventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiFetch<InventoryItem[]>("/api/v1/admin/store/inventory")
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter(
      (i) =>
        i.variant_sku.toLowerCase().includes(q) ||
        i.size_code.toLowerCase().includes(q) ||
        i.color_code.toLowerCase().includes(q)
    );
  }, [items, search]);

  const totalStock = items.reduce((sum, i) => sum + i.on_hand, 0);
  const lowStock = items.filter((i) => i.on_hand <= 5).length;

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="admin-heading">Tồn kho cửa hàng</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            {items.length} sản phẩm · {totalStock} tồn kho{lowStock > 0 ? ` · ${lowStock} sắp hết` : ""}
          </p>
        </div>
        <div className="relative min-w-64">
          <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" name="search" size={16} />
          <input
            className="admin-input pl-9"
            placeholder="Tìm SKU, size, màu…"
            onChange={(e) => setSearch(e.target.value)}
            value={search}
          />
        </div>
      </header>

      {loading ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-32 animate-pulse rounded-2xl bg-sand/60" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="admin-panel mt-6 text-center">
          <Icon className="mx-auto text-moss" name="package" size={24} />
          <p className="mt-3 text-muted">{search ? "Không tìm thấy sản phẩm phù hợp." : "Chưa có tồn kho."}</p>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((item) => (
            <div key={item.variant_id} className="rounded-2xl border border-line bg-paper p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-mono text-xs font-semibold text-muted">{item.variant_sku}</p>
                  <p className="mt-1 text-sm font-medium text-ink">{item.size_code} / {item.color_code}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    item.on_hand <= 5
                      ? "bg-danger/10 text-danger"
                      : item.on_hand <= 10
                        ? "bg-warning/10 text-warning"
                        : "bg-success/10 text-success"
                  }`}
                >
                  {item.on_hand}
                </span>
              </div>
              <div className="mt-3 flex items-center justify-between border-t border-line pt-3 text-sm">
                <span className="text-muted">Giá bán</span>
                <span className="font-semibold">{formatVnd(item.price_vnd)}</span>
              </div>
              {item.opening_on_hand > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted">Mở đầu</span>
                  <span className="text-muted">{item.opening_on_hand}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
