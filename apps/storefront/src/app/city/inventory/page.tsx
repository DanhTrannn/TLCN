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
}

const PAGE_SIZE = 20;

export default function CityInventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [storeFilter, setStoreFilter] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    apiFetch<InventoryItem[]>("/api/v1/admin/city/inventory")
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => {
    const set = new Set(items.map((i) => i.category_name).filter(Boolean));
    return Array.from(set).sort();
  }, [items]);

  const storeNames = useMemo(() => {
    const set = new Set(items.map((i) => i.store_name).filter(Boolean));
    return Array.from(set).sort();
  }, [items]);

  const filtered = useMemo(() => {
    let result = items;
    if (storeFilter) {
      result = result.filter((i) => i.store_name === storeFilter);
    }
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
  }, [items, search, category, storeFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Inventory overview</p>
          <h1 className="admin-heading mt-2">Tồn kho thành phố</h1>
          <p className="mt-2 text-sm leading-6 text-muted">{items.length} sản phẩm · {storeNames.length} cửa hàng</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <select
            className="admin-input"
            value={storeFilter}
            onChange={(e) => { setStoreFilter(e.target.value); setPage(1); }}
          >
            <option value="">Tất cả cửa hàng</option>
            {storeNames.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
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
              placeholder="Tìm SKU, tên SP…"
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              value={search}
            />
          </div>
        </div>
      </header>

      {loading ? (
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : (
        <div className="admin-table-shell mt-6">
          <table>
            <thead>
              <tr>
                <th>Sản phẩm</th>
                <th>Cửa hàng</th>
                <th>Danh mục</th>
                <th>Size / Màu</th>
                <th className="text-right">Giá</th>
                <th className="text-right">Tồn kho</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((item) => (
                <tr key={`${item.store_id}-${item.variant_id}`}>
                  <td>
                    <p className="font-mono text-xs font-semibold text-muted">{item.variant_sku}</p>
                    <p className="mt-1 text-sm font-medium">{item.product_name}</p>
                  </td>
                  <td>
                    <p className="text-sm">{item.store_name}</p>
                  </td>
                  <td>
                    <p className="text-sm">{item.category_name}</p>
                  </td>
                  <td>
                    <p className="text-sm">{item.size_code} / {item.color_code}</p>
                  </td>
                  <td className="text-right font-semibold">{formatVnd(item.price_vnd)}</td>
                  <td className="text-right">
                    <span
                      className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${
                        item.on_hand <= 5
                          ? "border-danger/25 bg-danger/10 text-danger"
                          : item.on_hand <= 10
                            ? "border-warning/25 bg-warning/10 text-warning"
                            : "border-success/20 bg-success/10 text-success"
                      }`}
                    >
                      {item.on_hand}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="p-10 text-center">
              <Icon className="mx-auto text-moss" name="package" size={24} />
              <p className="mt-3 text-muted">{search || category || storeFilter ? "Không tìm thấy sản phẩm phù hợp." : "Chưa có tồn kho."}</p>
            </div>
          )}
        </div>
      )}

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
    </section>
  );
}
