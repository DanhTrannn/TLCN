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
  product_name: string;
  category_name: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  on_hand: number;
  opening_on_hand: number;
}

const PAGE_SIZE = 12;

export default function StoreInventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    apiFetch<InventoryItem[]>("/api/v1/admin/store/inventory")
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => {
    const set = new Set(items.map((i) => i.category_name).filter(Boolean));
    return Array.from(set).sort();
  }, [items]);

  const filtered = useMemo(() => {
    let result = items;
    if (category) {
      result = result.filter((i) => i.category_name === category);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          i.variant_sku.toLowerCase().includes(q) ||
          i.product_name.toLowerCase().includes(q) ||
          i.size_code.toLowerCase().includes(q) ||
          i.color_code.toLowerCase().includes(q)
      );
    }
    return result;
  }, [items, search, category]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

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
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <select
            className="admin-input"
            value={category}
            onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          >
            <option value="">Tất cả danh mục</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <div className="relative min-w-56">
            <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" name="search" size={16} />
            <input
              className="admin-input pl-9"
              placeholder="Tìm SKU, tên SP, size, màu…"
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              value={search}
            />
          </div>
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
          <p className="mt-3 text-muted">{search || category ? "Không tìm thấy sản phẩm phù hợp." : "Chưa có tồn kho."}</p>
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {paginated.map((item) => (
              <div key={item.variant_id} className="rounded-2xl border border-line bg-paper p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-mono text-xs font-semibold text-muted">{item.variant_sku}</p>
                    <p className="mt-1 text-sm font-medium text-ink">{item.product_name}</p>
                    <p className="text-xs text-muted">{item.size_code} / {item.color_code}</p>
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
                {item.category_name && (
                  <p className="mt-2 text-xs text-muted">Danh mục: {item.category_name}</p>
                )}
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

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <button
                className="admin-input px-3 py-1.5 text-sm disabled:opacity-40"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <Icon className="rotate-180" name="arrow-right" size={14} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={`admin-input px-3 py-1.5 text-sm ${p === page ? "font-semibold text-accent" : ""}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button
                className="admin-input px-3 py-1.5 text-sm disabled:opacity-40"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <Icon name="arrow-right" size={14} />
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
