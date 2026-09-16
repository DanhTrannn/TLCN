"use client";

import { useEffect, useState } from "react";

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
}

export default function StoreInventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<InventoryItem[]>("/admin/store/inventory")
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="admin-panel animate-pulse text-muted">Đang tải…</div>;
  }

  return (
    <div>
      <h1 className="admin-heading">Tồn kho cửa hàng</h1>

      {items.length === 0 ? (
        <div className="admin-panel mt-4 text-muted">Chưa có tồn kho.</div>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs font-semibold uppercase tracking-wider text-muted">
                <th className="px-3 py-2">SKU</th>
                <th className="px-3 py-2">Size</th>
                <th className="px-3 py-2">Màu</th>
                <th className="px-3 py-2 text-right">Giá</th>
                <th className="px-3 py-2 text-right">Tồn kho</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.variant_id} className="border-b border-line/50">
                  <td className="px-3 py-2.5 font-mono text-xs">{item.variant_sku}</td>
                  <td className="px-3 py-2.5">{item.size_code}</td>
                  <td className="px-3 py-2.5">{item.color_code}</td>
                  <td className="px-3 py-2.5 text-right">{formatVnd(item.price_vnd)}</td>
                  <td className={`px-3 py-2.5 text-right font-semibold ${item.on_hand <= 5 ? "text-danger" : ""}`}>
                    {item.on_hand}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
